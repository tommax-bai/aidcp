# platform-search-activity — delta (fb-search-livelock-recovery)

## ADDED Requirements

### Requirement: 发现式搜索平台准入

Cloud SHALL 维护发现式(`purpose=discovery`)搜索的平台支持集。Facebook 当前不在支持集内(Native 引擎的发现式搜索为退役路径,无 container 的 `search_execute` 一律被 `permission_gated` 拒绝):对 Facebook 账号,Cloud MUST NOT 下发发现式搜索命令。拦截 SHALL 落在搜索决策入口(评估器判定之前,不消耗模型调用),并 emit 具名跳过(原因 `platform_unsupported`)使浏览闭环继续续滚;搜索下发口 SHALL 另有同名断言式拦截作防绕过网。定向搜索(带 container,`purpose=task_targeting`)不受本要求约束。

#### Scenario: Facebook 账号触发搜索需求时被具名拦截

- **WHEN** Facebook 账号的浏览闭环触发 `search.needed`
- **THEN** Cloud 在评估器判定前直接记跳过(原因 `platform_unsupported`),不调用关键词判定模型、不下发 `facebook.search.execute`
- **AND** 浏览闭环经既有 `search.skipped` 路径继续续滚,不断流

#### Scenario: 定向评论搜索不受平台闸影响

- **WHEN** 评论任务对 Facebook 账号下发带 container 的定向搜索
- **THEN** 命令照常下发,平台准入闸不拦截

#### Scenario: 绕过评估器直达下发口时仍被拦

- **WHEN** 任何路径试图对 Facebook 账号直接下发发现式搜索命令
- **THEN** 下发口断言拦截并记录具名原因,命令不进入下行通道

## MODIFIED Requirements

### Requirement: 搜索是跨平台一级账号活动

系统 SHALL 将 Facebook 与小红书上**发起**的搜索记为账号级 `search` 风险动作:Cloud 真正把 `{platform}.search.execute` 送入下行通道(`sent=true`)即计 1 次,失败的搜索同样占用额度——搜索失败 MUST NOT 免费,否则策略层会将失败词视为「还没搜过」而无限重发。`search` SHALL 进入账号分钟、小时、Asia/Shanghai 自然日配额、当日活动统计与饱和判断,但 MUST NOT 进入需要 noteId 的 `InteractionAction`、内容互动去重或互动内容 feed。Edge 的三态终态(`results_ready`/`no_results`/`failed_after_submit`/`not_submitted`)SHALL 作为审计流如实保留,但 MUST NOT 作为额度消耗的前置条件。

#### Scenario: 发起搜索即进入账号活动但不进入内容互动账本

- **WHEN** Cloud 对一个账号成功下发一次搜索命令
- **THEN** 该账号 `search` 风险计数增加 1,并可被后续配额预闸和今日活动读取
- **AND** 系统不为该搜索创建 noteId 互动去重记录或点赞/收藏/评论 feed 项

#### Scenario: 搜索失败同样占用额度

- **WHEN** 已下发的搜索以 `ok=false`(含 `not_submitted`)终态返回
- **THEN** 发起时已记的 `search` 计数保持,不回滚、不补偿
- **AND** 终态 outcome 落审计流,供诊断区分「平台看到过」与「提交前失败」

### Requirement: 搜索事实一次性消费且回执后不重判策略

Cloud SHALL 在下发点以 `activityId` 一次性记账:每个 `activityId` 恰记 1 次 `search` 风险事实(`RiskController.record('search')` 于 `sent=true` 时驱动),MUST NOT 因回执到达时配额或风险状态已变化而销毁既成记账。终态回执 SHALL 只补写该 `activityId` 的 outcome 审计,MUST NOT 二次计数;重复或未知关联的终态 MUST NOT 产生任何计数,并 SHALL 留下可诊断信息。

#### Scenario: 同一活动终态只补审计不再计数

- **WHEN** Cloud 对已在下发点记账的 `activityId` 收到终态回执(无论成败)
- **THEN** `search` 风险计数不再变化,outcome 落审计流

#### Scenario: 重复终态不重复写审计事实

- **WHEN** Cloud 对同一 `activityId` 收到第二次终态
- **THEN** 第二次被识别为重复,不计数、不重复写事实,留下可诊断记录

### Requirement: Edge 对每条搜索命令至多回报一个诚实终态

支持 `search_activity_receipt_v1` 的 Edge SHALL 对每条 `{platform}.search.execute`(两平台各自同构名)至多回报一个 `action.completed(action='search')` 终态,回显关联、目的和范围,并用 `actuated` 区分平台是否已经观察到搜索动作:

- 结果页验证成功且存在可见结果:`ok=true, actuated=true, searchOutcome=results_ready`;
- 结果页验证成功但当前无可见结果:`ok=true, actuated=true, searchOutcome=no_results`;
- 已提交或发起导航但后置验证失败:`ok=false, actuated=true, searchOutcome=failed_after_submit`;
- 提交前失败:`ok=false, actuated=false, searchOutcome=not_submitted`。

`resultCount` 若存在 MUST 是当前页面可见且去重后的非负数量,MUST NOT 冒充平台总结果数。`page.cards` MAY 与终态共同回报,但 MUST NOT 代替终态。Cloud 侧对终态的消费为 outcome 审计(额度已在下发点消耗,见「搜索是跨平台一级账号活动」)。

#### Scenario: 已提交后页面验证失败仍如实回报

- **WHEN** Edge 已经提交搜索,但未能在限时内验证目标搜索页
- **THEN** Edge 回报 `ok=false, actuated=true, searchOutcome=failed_after_submit`
- **AND** Cloud 将该 outcome 落审计流(额度已于下发点消耗)

#### Scenario: 提交前找不到搜索控件如实回报

- **WHEN** Edge 在输入或提交前找不到可用搜索控件
- **THEN** Edge 回报 `ok=false, actuated=false, searchOutcome=not_submitted`
- **AND** Cloud 将该 outcome 落审计流,三态 MUST NOT 被压成一态

#### Scenario: 无结果是成功终态

- **WHEN** Edge 已验证到目标搜索结果页,但当前可见去重结果数为 0
- **THEN** Edge 回报 `ok=true, actuated=true, searchOutcome=no_results, resultCount=0`

### Requirement: 新搜索事实由显式能力协商启用

Edge build SHALL 声明 `search_activity_receipt_v1`,Cloud SHALL 仅对声明该能力的连接启用活动关联和终态审计消费。额度消耗在 Cloud 下发点完成,不依赖 Edge 能力等级;对未声明能力的旧 Edge,Cloud 同样按发起记账,但 MUST NOT 从 `page.cards` 或页面状态猜测 `actuated=true`、伪造终态审计。

#### Scenario: 旧 Edge 同样按发起记账

- **WHEN** 未声明 `search_activity_receipt_v1` 的旧 Edge 接收既有搜索命令
- **THEN** Cloud 在下发点已记 1 次 `search` 风险事实,不因缺终态回执而补造或删改计数

#### Scenario: 新 Edge 的能力进入协商结果

- **WHEN** Edge hello 声明 `search_activity_receipt_v1`
- **THEN** Cloud 的连接能力集合保留该能力,后续搜索使用活动关联与终态审计语义

### Requirement: 已确认搜索进入支持平台的客户端今日进展

Cloud SHALL 将按发起制记入账号 `search` 风险事实的搜索(下发点以 `activityId` 一次性记账),投影到该账号环境级客户鉴权 HTTP 今日进展,并 MAY 同步出现在兼容 `ui.push_snapshot.dailyUsage` 中。投影 SHALL 包含 day alias 以及 session、minute、hour、day 窗口中真实可得的搜索次数、有效上限、饱和状态和恢复时间;计数口径即发起制风险账本本身,MUST NOT 在账本之外用关键词尝试账或页面状态另造第二套计数。

#### Scenario: Facebook 今日搜索显示真实次数与上限

- **WHEN** Facebook 账号今日已发起 2 次搜索且当前有效 day 上限为 10
- **THEN** 客户 HTTP 今日进展的 totals 与 day window 均包含 `search=2`,day quota 包含 `search=10`

#### Scenario: 离线查看仍读取 Cloud 搜索账本

- **WHEN** 账号已有已记账搜索,但对应浏览器、自动化引擎或 Edge 当前离线
- **THEN** 客户端仍可通过环境级客户鉴权 HTTP 读取最近的 Cloud search 今日进展

#### Scenario: 发起的搜索即时进入客户端用量

- **WHEN** Cloud 已成功下发一次搜索,终态回执尚未到达或最终失败
- **THEN** 客户端 search 次数已包含该次发起,不因终态缺失或失败而回退

### Requirement: Native search admission failures SHALL retain the Cloud activity correlation
When a negotiated search command is rejected or fails before page actuation, Edge MUST emit exactly one schema-valid terminal for the original activity and MUST NOT cause Cloud to wait for a step timeout. The search quota ledger is initiation-based (charged at dispatch); the failure terminal only annotates the outcome and MUST NOT add, remove, or duplicate ledger entries.

#### Scenario: Task-lane search is rejected before submission
- **WHEN** Native search cannot be admitted before any page-side search submission
- **THEN** Edge SHALL emit `action.completed` with the original `activityId`, `purpose`, and `scope`, `ok=false`, `actuated=false`, and `searchOutcome=not_submitted`

#### Scenario: Native search results are reported with one correlated terminal
- **WHEN** Native search returns a page-card result set for a correlated search activity
- **THEN** Edge SHALL report the cards and one terminal carrying `results_ready` or `no_results` with the observed result count
