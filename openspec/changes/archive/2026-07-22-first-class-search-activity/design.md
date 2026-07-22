## Context

FB 与 XHS 已经通过 `search.execute` 在真实页面执行搜索。Cloud 也已有单场 `budget.searches` 和按关键词的 `SearchFrequencyLimiter`，但它们只控制一次会话内的自治搜索尝试；搜索既不在账号级 `RiskAction` 中，也没有跨平台一致的成功回执。当前 `RoleDispatcher` 在命令下发后立即 `markSearched`，把“已下发”误当成“平台已执行”。XHS 与 FB 的成功路径通常只回 `page.cards`，Cloud 无法区分未提交、已提交但无结果、已提交后失败和结果已就绪。

本变更横跨 control、Cloud、Edge 和 Console，并会改变协议可选字段、账号风险计数、搜索调度和运营可见口径。2026-06-24 的概念池设计曾明确不把搜索接入 `RiskController`；本设计在具备 Edge 执行事实后有意替代该边界。

## Goals / Non-Goals

**Goals:**

- 把搜索建模为与 view、like 同级的账号平台活动，受账号分钟、小时、自然日配额和可选慢启动夹逼。
- 对 FB 全站搜索、FB 容器搜索和 XHS 搜索形成同一事实语义，并保留各平台自己的页面验证。
- 只在 Edge 证明平台动作实际发生后持久计数；未提交不得计数，提交后失败也不得漏记。
- 区分自治发现、任务定位和运营搜索，并区分全站与容器范围。
- 让概念词的 `searched` 状态跟随平台事实，而不是跟随命令下发。
- 在 Console 中展示搜索配额、当日用量与饱和状态，并保持 Cloud/Console 枚举漂移哨兵有效。

**Non-Goals:**

- 不把搜索加入按 noteId 去重的 `InteractionAction`、互动内容账本或点赞/收藏/评论流。
- 不新增协议消息类型，不把搜索结果内容或原始关键词写入风险计数表。
- 不移除单场搜索预算或按关键词限频；它们继续作为自治搜索的尝试控制。
- 不把本变更扩大为搜索排序、推荐算法或 UI 搜索入口重做。
- 不构建或发布 Edge 桌面安装包。

## Decisions

### D1. `search` 是 `RiskAction`，不是 `InteractionAction`

Cloud 的 `RiskAction`、配额配置、风险计数、当日活动和 Console 镜像新增 `search`。`InteractionAction` 保持 `like | collect | comment`，搜索不要求 noteId，不进入内容互动去重与互动 feed。这样账号活动总量可被风控读取，又不会把“发现内容”误称为“对内容互动”。

账号处于 `restricted` / `frozen` 时，`zeroInteractionQuotas` 只保留被动 `view`，`search` 与其他平台主动行为一样清零。操作员搜索沿用既有“权限可绕过预闸、事实不可免记”规则。

### D2. 执行回执表达平台事实，不表达命令成功

沿用 `search.execute` 与 `action.completed`，增加可选字段：

- `activityId`: Cloud 生成的搜索活动关联 ID；旧命令缺失时 Edge 可回退到命令 envelope ID。
- `purpose`: `discovery | task_targeting | operator`。
- `scope`: `global | container`。
- `actuated`: 是否已经提交搜索或发起搜索导航，平台已可观察。
- `searchOutcome`: `results_ready | no_results | failed_after_submit | not_submitted`。
- `resultCount`: 当前可见且去重后的结果数（未知时省略）。

`ok` 表达后置目标是否完成；`actuated` 表达平台事实。故“提交后页面未就绪”是 `ok=false, actuated=true, searchOutcome=failed_after_submit`，仍须计数；“找不到搜索框”是 `ok=false, actuated=false, searchOutcome=not_submitted`，不得计数。

每条搜索命令最多产生一个终态搜索回执。`page.cards` 继续承载内容卡片，不代替行为回执。

### D3. 能力协商保护加性协议演进

新增 build capability `search_activity_receipt_v1`。Cloud 仅在连接声明该能力时等待并消费新事实字段：

- 新 Edge：Cloud 生成 `activityId`，下发目的/范围；Edge 回传终态；Cloud 按 `actuated` 记事实。
- 旧 Edge：继续旧搜索流程，自治概念词维持下发后 `markSearched` 的兼容行为；Cloud 不凭旧 `page.cards` 反推或伪造风险事实。

这允许先部署兼容 Cloud，再逐步更新 Edge。能力缺失会体现在日志/诊断中，但不会把旧客户端的未知状态伪装为新事实。

### D4. 尝试控制与既成事实分账

自治搜索下发前依次经过账号风险预闸、`SearchFrequencyLimiter` 和 `budget.searches`。通过并实际下发后：

- `SearchFrequencyLimiter.recordSearch` 与 `budget.searches` 立即记录一次尝试，避免命令在途时重复下发；
- 对支持新能力的 Edge，Cloud 保存有界的 `activityId -> keyword` 待决关联；
- 只有终态回执 `actuated=true` 才发布内部 `search.occurred`，由 `RiskController.record('search')` 无条件记录既成事实；
- 只有关联到自治概念词且 `actuated=true` 才 `ConceptStore.markSearched`；未提交释放待决关联但不标已搜。

任务定位和运营搜索也产生同样的风险事实，但不消耗自治概念池单场预算，也不操作概念词状态。Cloud 用有限容量与会话清理约束待决 map；重复/未知 `activityId` 不重复记账，并留下可诊断日志。

### D5. 搜索采用独立、可配置的安全上限

默认 daily 配额为 conservative=5、normal=10、aggressive=20；独立 minute=1、hour=4。数值作为代码 never-brick 默认和 `quota_config` 新 action 的初始化值，运营后续可按档位热更新。

可选慢启动曲线同时加入 search 天花板：XHS D1-2=2、D3-4=3、D5-7=5；FB D1-2=1、D3-4=2、D5=3、D6=4、D7=5。默认未开启慢启动的账号仍直接使用安全上限；本变更不恢复已删除的全局账号年龄强制冷启动。

### D6. 平台验证分别实现，事实语义保持一致

- XHS：输入关键词后、首次 Enter 提交前设置本地提交观测；导航到与关键词一致的搜索页后统计去重卡片。提交后未到搜索页回 `failed_after_submit`。
- FB 全站：`Page.navigate` 成功发起搜索即为已执行；搜索结果 surface 验证后区分有结果/无结果，验证失败回 `failed_after_submit`。
- FB 容器：在容器搜索控件真正提交后标记已执行；候选为零是 `ok=true, no_results`，提交前失败是 `not_submitted`。

平台选择器与 URL 校验仍由各自实现拥有，协议只统一事实边界。

### D7. 风险计数不保存关键词

`risk_counters` 只新增 `action='search'` 事实，继续保存账号、时间和动作类型；不保存 raw keyword、purpose 或结果内容。关键词仍只存在于既有概念池/命令链路。Console 展示计数与限额，不展示搜索词历史，避免把风险账本变成检索日志。

## Risks / Trade-offs

- **旧 Edge 的搜索事实缺口**：能力缺失时无法追溯真实执行。通过显式 capability、兼容旧行为和不伪造计数控制；更新 Edge 后才获得完整事实。
- **提交后失败增加计数看似反直觉**：平台已经观察到动作，漏记会放大后续活动。用 `ok` 与 `actuated` 双维度保留结果质量与风险事实。
- **重复终态可能双计数**：Cloud 以 `activityId` 做一次性消费；未知或重复回执只诊断，不重复发布事实。
- **新 action 触发旧 PG CHECK 约束**：用前向 migration 扩展约束，并同步启动自建 DDL；部署前后均验证写入与 dashboard 聚合。
- **配额默认过紧影响发现**：搜索仍有 5/10/20 日上限，且可热配置；任务/运营授权可按既有权限规则绕过预闸，但实际发生仍计数。
- **结果数只是当前可见值**：`resultCount` 明确为可见去重数，不宣称平台总结果数；无法确定时省略。

## Migration Plan

1. 先合入并部署向后兼容的 Cloud：协议字段均可选，识别新 capability，PG 约束与配额配置支持 `search`；旧 Edge 不生成搜索事实。
2. 合入 Edge 源码并通过 FB/XHS focused tests 与 typecheck；本变更不打包，已安装客户端保持旧能力直到后续正式发布。
3. 合入并部署 Console dev，使新动作、配额和今日活动可见；对未知动作仍保持中性回落。
4. 在 dev 使用支持该 capability 的 Edge 做有界验证：至少覆盖一次 `actuated=true` 与一次 `not_submitted`，确认前者计数、后者不计数且概念词落态一致。
5. 回滚时先回滚 Console，再回滚 Cloud 业务逻辑；数据库新增 action/配额行和放宽的 CHECK 约束可安全保留。Edge 新字段对旧 Cloud 为加性，但生产发布应保持 Cloud 先于 Edge。

## Open Questions

无。默认配额、兼容策略和部署顺序在本设计中已确定；若后续真实运行数据表明需要调参，通过既有配额配置通道完成，不另改协议。
