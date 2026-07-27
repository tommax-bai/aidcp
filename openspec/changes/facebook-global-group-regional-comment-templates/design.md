## Context

Facebook 群目录当前用 `facebook_group_target_scope(group_url, account_group_label)` 表达适用范围：有映射才可被相同 `accounts.group_label` 的账号认领，零映射表示未设置并 fail-closed。候选计数、自动认领和执行前重验都依赖账号投影新鲜度及标签等值连接。该模型没有“全局”状态，不能把空范围改解释为全局，否则会把既有未配置数据静默放行。

Facebook 评论正文当前由每账号 `account_facebook_comment_config` 决定。缺配置行时读模型默认 `generated`；`template` 模式无账号模板时会在选群前以 `empty_template` 停止。评论实际目标来自 membership 账本，目标群的 `region` 已存在于 `facebook_group_target`，但正文解析没有读取它。Cloud 选择正文，Edge 只接收最终文本，因此本次不需要协议或 Edge 改动。

该变更横跨 Cloud 数据模型/调度、Console 管理面和 DEV 数据迁移。它必须保持账号投影新鲜度、一群一账号唯一锁、风险/配额、审批、确定性校验及平台确认等现有边界。

## Goals / Non-Goals

**Goals:**

- 显式表达并管理 `global`、`restricted + labels`、`restricted + empty` 三种群目标范围。
- 让全局目标对任意 Facebook 账号可选，包括当前 `group_label` 为空的账号，但仍要求账号投影存在、新鲜且平台匹配。
- 在群组管理页按现有群区域维护多条通用评论模板。
- 以稳定优先级解析 Facebook 评论正文来源，并让缺失原因可审计。
- 把变更生效时的现存群目标一次性、原子地设为全局，且不改 membership 或其它群事实。

**Non-Goals:**

- 不把“未设置范围”重新解释为全局，也不把“全局分组”存成伪账号标签。
- 不为无区域群增加跨区域或任意模板兜底，不从园区/方向推断区域。
- 不自动生成搜索关键词；关键词为空时保留主干既有“直接读取群内首帖”的定位模式。
- 不改变评论审批策略、联系方式注入、正文校验、风控配额、去重或平台成功判定。
- 不修改 Edge 协议/执行器，不在本变更中发布 OL 或构建桌面安装包。

## Decisions

### 1. 在群目标事实行增加显式范围模式

`facebook_group_target` 增加 `account_scope_mode TEXT NOT NULL`，取值仅为 `restricted|global`，新目标默认 `restricted`。`facebook_group_target_scope` 继续只存真实账号分组标签：

- `global`：标签映射不参与资格判断；API 写全局时清空映射，避免隐藏范围以后意外复活。
- `restricted` 且标签非空：只允许标签匹配账号。
- `restricted` 且标签为空：未设置范围，任何账号都不能自动/裸池认领。

API/DTO 增加 `accountScopeMode`，保留 `accountGroupLabels` 以兼容现有消费者。旧写请求只带 `accountGroupLabels` 时按 `restricted` 处理；`global` 与非空标签同时提交属于矛盾输入，整块拒绝。

未采用“把 `__global__` 存进标签表”：伪标签会与真实账号分组校验、facets 和账号改组语义混在一起，并可能被运营创建同名真实分组。

未采用“空标签即全局”：这会把所有既有未配置群静默放行，破坏当前 fail-closed 契约。

### 2. 全局资格仍依赖新鲜 Facebook 账号投影

候选计数、`nextJoinCandidate`、`claimNext` 和 `revalidateScopedAssignment` 使用同一个资格谓词：

`target.account_scope_mode = 'global' OR EXISTS matching target_scope for account.group_label`

外层仍必须命中当前 account 的新鲜 `automation_account_projection` 且平台为 Facebook。只有 `restricted` 分支要求非空 `group_label`；全局分支允许未分组 Facebook 账号。目标启用态、join gating、未被全局占用及每账号单飞条件保持不变。

执行前重验发现投影陈旧时继续返回 `projection_stale`；从 global 改为不匹配的 restricted 时，只释放 `assigned|joining`，不改写任何平台终态。这样“全局”扩展的是业务范围，不是绕过账号身份或新鲜度闸。

### 3. 管理面使用互斥三态，而不是多选中的特殊字符串

群组列表返回 `accountScopeMode` 与标签全集；UI 显示：

- `全局分组`
- 一个或多个真实账号分组标签
- `未设置适用分组`

导入和批量范围编辑先选“全局”或“指定账号分组”；指定模式下标签可为空，空即显式未设置。筛选通过显式 scope-mode 参数表达全局/未设置，真实标签继续用精确标签过滤。写成功后展示数据库回读，不用本地乐观值冒充真态。

### 4. 区域通用模板由 Cloud 持久化，区域键与群目录精确一致

新增自动化域持久化配置 `facebook_region_comment_template_config`（或等价命名），每个规范化非空 `region` 一行，`comment_templates` 为 JSONB 字符串数组，并记录 `updated_at/updated_by`。写入时 trim、丢空、去重并限制数量/单条长度；空数组表示该区域未配置可用通用模板。

Panel API 提供列表读和单区域整组替换写，写请求的区域必须是当前群目标 facets 中存在的精确区域，避免手工拼写产生永远不会命中的配置。Console 将该配置放在 `/facebook-groups` 的“通用评论模板”区，按区域编辑多条模板并回显更新时间。

模板在 automation 权威内读写；API 组合根通过既有命令/视图边界接入，不能让 API 进程成为第二个写者。运行时按目标 `group_url` 连接 `facebook_group_target.region` 解析，避免调用方自行信任区域字符串。

未增加无区域/全局模板：需求明确要求“根据本次加群群的区域”，跨区域兜底会在运营无法察觉时发错地域文案。

### 5. 正文来源在确定目标群后按显式优先级解析

评论链路先选择 pinned 或 coverage 目标群；关键词只决定有词搜索或空词首帖定位，随后解析正文：

1. 账号显式 `generated`：调用既有 composer；区域模板不覆盖显式选择。
2. 账号显式 `template` 且账号模板非空：从账号模板随机选择。
3. 账号显式 `template` 但账号模板为空：读取目标群区域的通用模板。
4. 账号没有持久化评论配置行，或持久化行的 `comment_mode_configured=false`：有效方案默认为 `template`，并按第 3 条读取区域通用模板。

“是否显式配置”由独立的持久化 `comment_mode_configured` 表达，不能用模板数组是否为空反推生成方案。版本化迁移把现有已持久化 `generated|template` 行标记为显式选择；新建配置仅在写请求明确携带 `commentMode` 时把该状态置为 true。缺行或未显式写方案的读模型改为模板默认。新实现移除选群前的 `empty_template` 早退，把模板缺失判断移动到已知 `group_url` 之后；该显式状态也随既有 Cloud 内部 sync-read 快照传播，避免拆分进程丢失方案权威。

若目标无区域、区域无通用模板或解析后列表为空，记录稳定的 `missing_group_region|regional_template_missing` 非提交原因；不得回退 generated、其它区域或任意模板。选出的通用模板继续经过与账号模板相同的正文校验、审批、联系方式分离注入和平台确认。

### 6. 当前群目标通过版本化迁移一次性设为全局

Cloud 版本化迁移在一个事务内：

1. 记录迁移前目标总数、global/restricted/unscoped 数量和 scope 映射数量。
2. 锁定现存目标，将其 `account_scope_mode='global'` 并更新 scope 审计字段；旧标签映射保留为休眠兼容数据，使共享同一 PostgreSQL、尚未获授权升级的 OL 旧代码继续按升级前资格工作。
3. 回读断言所有迁移目标为 global、兼容映射逐行未变，且 membership 计数及目标 `enabled/priority/join_gating/region/park/direction` 未改变。新代码的 global 资格只看范围模式，绝不读取休眠映射；运营之后显式保存 global/restricted 时仍按正常写路径清理或替换映射。

迁移只作用于执行时已经存在的目标；迁移后的新导入仍默认 restricted/unscoped，除非请求显式选择 global。部署前按项目规范备份数据库；事务失败自动回滚，部署验收失败则用备份/回滚版本恢复，不能在未知行范围上继续。

## Risks / Trade-offs

- [全局目标显著扩大候选池] → 仍要求每账号显式自动加群开关/时段/配额、投影新鲜、群启用和一群一账号锁；迁移前后输出数量对账。
- [旧 Console 与新 API 并存时写丢 global] → 旧的 labels-only 写请求明确解释为 restricted，部署 Cloud 与 Console 作为同一 DEV 变更串行切换；API 返回数据库真态。
- [区域模板配置存在但目标区域为空/拼写漂移] → 配置只接受现有 facet 区域；运行时严格按目标行查找并给出具名 no-op，不跨区域猜测。
- [把模板缺失判断后移会多一次目标查询] → 只在本来要执行的 Facebook 评论尝试中按 canonical group URL 单行读取，频率远低于浏览热路径；不加缓存和失效机制。
- [DEV 与未升级 OL 共享群目录] → 数据迁移保留旧标签映射供 OL 旧代码兼容使用；新 DEV 以范围模式为权威并忽略这些映射。OL 仍须单独授权升级，不能借 DEV 交付改动 OL 运行时。

## Migration Plan

1. 先合入兼容读写：Cloud 能读 `account_scope_mode` 和 `comment_mode_configured`、Console 能展示三态、区域模板 API/运行时及内部 sync-read 已就绪；严格测试后再执行数据迁移。
2. 在 DEV 部署前运行目标检查和数据库备份；由版本化 schema migration 增列/建表、把执行时现存目标设为 global，并把历史账号评论配置行标记为已有显式方案。
3. 重启文档指定的 AIDCP 服务，核验 migration ledger、目标/映射/membership 对账、Panel API、Console 静态资源和健康检查。
4. 用只读查询验证任意已分组与未分组 Facebook 账号都能看到 global 候选计数；不执行真实加群/评论，除非另有真实账号写验收授权。
5. 若任一断言失败，停止后续写入，回滚应用版本并按备份恢复数据库；不得继续到 OL。

## Open Questions

无。本文把“全局分组”解释为所有 Facebook 账号（含未分组账号）均可加入，并把“未设置评论方案”解释为没有显式账号正文方案；显式生成方案始终优先，不会被区域模板覆盖。
