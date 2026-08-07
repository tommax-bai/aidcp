# platform-search-activity Specification

## Purpose
TBD - created by archiving change first-class-search-activity. Update Purpose after archive.
## Requirements
### Requirement: 搜索是跨平台一级账号活动

系统 SHALL 将 Facebook 与小红书上真实发生的搜索记为账号级 `search` 风险动作。`search` SHALL 进入账号分钟、小时、Asia/Shanghai 自然日配额、当日活动统计与饱和判断，但 MUST NOT 进入需要 noteId 的 `InteractionAction`、内容互动去重或互动内容 feed。

#### Scenario: 已执行搜索进入账号活动但不进入内容互动账本

- **WHEN** 一个账号在 Facebook 或小红书真实提交一次搜索
- **THEN** 该账号 `search` 风险计数增加 1，并可被后续配额预闸和今日活动读取
- **AND** 系统不为该搜索创建 noteId 互动去重记录或点赞/收藏/评论 feed 项

#### Scenario: 仅下发命令不计搜索事实

- **WHEN** Cloud 下发 `{platform}.search.execute`（两平台各自同构名），但 Edge 未证明平台动作已经发生
- **THEN** 系统 MUST NOT 仅凭下发成功增加账号 `search` 风险计数

### Requirement: 搜索命令标注目的、范围与活动关联

支持 `search_activity_receipt_v1` 的链路 SHALL 在 `{platform}.search.execute`（两平台各自同构名）中携带稳定 `activityId`、`purpose`（`discovery | task_targeting | operator`）和 `scope`（`global | container`）。自治概念池搜索 SHALL 标为 `discovery`，评论/任务定位搜索 SHALL 标为 `task_targeting`，人工运营命令 SHALL 标为 `operator`；容器内搜索 SHALL 标为 `container`，其余为 `global`。

字段缺失的兼容命令 MAY 由 Edge 以命令 envelope ID 作为回执关联 ID，并按“有容器即 `task_targeting/container`，否则 `discovery/global`”归一化；系统 MUST NOT 因兼容默认值把任务搜索伪装成运营授权。

#### Scenario: 自治全站搜索带出明确语义

- **WHEN** Cloud 从概念池选择关键词并向支持新能力的 Edge 下发搜索
- **THEN** 命令携带唯一 `activityId`、`purpose=discovery`、`scope=global`

#### Scenario: 评论任务容器搜索带出任务语义

- **WHEN** 评论任务需要在指定容器内定位目标内容
- **THEN** 命令携带 `purpose=task_targeting`、`scope=container`，MUST NOT 标为 `operator`

### Requirement: Edge 对每条搜索命令至多回报一个诚实终态

支持 `search_activity_receipt_v1` 的 Edge SHALL 对每条 `{platform}.search.execute`（两平台各自同构名）至多回报一个 `action.completed(action='search')` 终态，回显关联、目的和范围，并用 `actuated` 区分平台是否已经观察到搜索动作：

- 结果页验证成功且存在可见结果：`ok=true, actuated=true, searchOutcome=results_ready`；
- 结果页验证成功但当前无可见结果：`ok=true, actuated=true, searchOutcome=no_results`；
- 已提交或发起导航但后置验证失败：`ok=false, actuated=true, searchOutcome=failed_after_submit`；
- 提交前失败：`ok=false, actuated=false, searchOutcome=not_submitted`。

`resultCount` 若存在 MUST 是当前页面可见且去重后的非负数量，MUST NOT 冒充平台总结果数。`page.cards` MAY 与终态共同回报，但 MUST NOT 代替终态。

#### Scenario: 已提交后页面验证失败仍如实计数

- **WHEN** Edge 已经提交搜索，但未能在限时内验证目标搜索页
- **THEN** Edge 回报 `ok=false, actuated=true, searchOutcome=failed_after_submit`
- **AND** Cloud 仍记录一次 `search` 既成事实

#### Scenario: 提交前找不到搜索控件不计数

- **WHEN** Edge 在输入或提交前找不到可用搜索控件
- **THEN** Edge 回报 `ok=false, actuated=false, searchOutcome=not_submitted`
- **AND** Cloud 不增加 `search` 风险计数

#### Scenario: 无结果是成功终态

- **WHEN** Edge 已验证到目标搜索结果页，但当前可见去重结果数为 0
- **THEN** Edge 回报 `ok=true, actuated=true, searchOutcome=no_results, resultCount=0`

### Requirement: 搜索事实一次性消费且回执后不重判策略

Cloud SHALL 以 `activityId` 一次性消费搜索终态。首次有效终态 `actuated=true` SHALL 无条件驱动 `RiskController.record('search')`，MUST NOT 因回执到达时配额或风险状态已变化而销毁既成事实。重复或未知关联的终态 MUST NOT 重复计数，并 SHALL 留下可诊断信息。

#### Scenario: 同一活动重复回执只计一次

- **WHEN** Cloud 对同一 `activityId` 收到两次 `actuated=true` 终态
- **THEN** `search` 风险计数只增加 1，第二次被识别为重复而不再次写事实

#### Scenario: 预闸后状态变化不丢事实

- **WHEN** 搜索通过预闸并在平台发生，而账号在终态抵达前变为 restricted
- **THEN** Cloud 仍记录该次搜索，后续搜索再由新状态预闸阻止

### Requirement: 新搜索事实由显式能力协商启用

Edge build SHALL 声明 `search_activity_receipt_v1`，Cloud SHALL 仅对声明该能力的连接启用活动关联和新回执消费。未声明能力的旧 Edge MAY 沿用原搜索与概念词兼容流程，但 Cloud MUST NOT 从 `page.cards`、命令发送成功或页面状态猜测 `actuated=true`，亦 MUST NOT 伪造账号搜索计数。

#### Scenario: 旧 Edge 不被误记搜索事实

- **WHEN** 未声明 `search_activity_receipt_v1` 的旧 Edge 接收并执行既有搜索命令
- **THEN** Cloud 不因命令发送成功或收到 `page.cards` 而新增 `search` 风险事实

#### Scenario: 新 Edge 的能力进入协商结果

- **WHEN** Edge hello 声明 `search_activity_receipt_v1`
- **THEN** Cloud 的连接能力集合保留该能力，后续搜索使用活动关联与终态语义

### Requirement: 搜索默认配额与可选慢启动可配置且 never-brick

代码默认 daily 搜索配额 SHALL 为 conservative=5、normal=10、aggressive=20，独立 minute=1、hour=4，并作为 `quota_config` 缺行或非法时的 never-brick 回落。可选慢启动开启时 SHALL 同时夹逼搜索：XHS D1-2=2、D3-4=3、D5-7=5；Facebook D1-2=1、D3-4=2、D5=3、D6=4、D7=5。未开启慢启动时 MUST NOT 因账号年龄自动应用该夹逼。

#### Scenario: 配额配置缺 search 行时回落代码默认

- **WHEN** 某档位的 `quota_config` 缺少 `search` 或字段非法
- **THEN** `effectiveQuotas()` 对 search 回落该档位代码默认，不抛错、不放开无限搜索

#### Scenario: restricted 账号只保留被动浏览

- **WHEN** 账号处于将主动行为清零的 restricted 或 frozen 状态
- **THEN** search 生效配额为 0，而 view 保持既有只读浏览语义

### Requirement: 已确认搜索进入支持平台的客户端今日进展

Cloud SHALL 将已按 `actuated=true` 一次性记入账号 `search` 风险事实的搜索，投影到该账号环境级客户鉴权 HTTP 今日进展，并 MAY 同步出现在兼容 `ui.push_snapshot.dailyUsage` 中。投影 SHALL 包含 day alias 以及 session、minute、hour、day 窗口中真实可得的搜索次数、有效上限、饱和状态和恢复时间；MUST NOT 使用命令下发次数、关键词尝试账或旧 Edge 的未确认搜索补造计数。

#### Scenario: Facebook 今日搜索显示真实次数与上限

- **WHEN** Facebook 账号今日已有 2 次已确认搜索且当前有效 day 上限为 10
- **THEN** 客户 HTTP 今日进展的 totals 与 day window 均包含 `search=2`，day quota 包含 `search=10`

#### Scenario: 离线查看仍读取 Cloud 已确认搜索

- **WHEN** 账号已有已确认搜索，但对应浏览器、自动化引擎或 Edge 当前离线
- **THEN** 客户端仍可通过环境级客户鉴权 HTTP 读取最近的 Cloud 已确认 search 今日进展

#### Scenario: 未确认搜索不进入客户端用量

- **WHEN** Cloud 只下发过搜索命令，或旧 Edge 未提供可消费的 `actuated=true` 终态
- **THEN** 系统不因该下发或未知状态增加客户端 search 次数

### Requirement: 搜索进度按平台显式供给且四窗口同口径

Cloud SHALL 仅为平台注册明确支持搜索的账号供给客户端 `search` 指标。Facebook 与小红书 SHALL 供给，视频号与未知平台 SHALL 保持字段缺席；MUST NOT 用 `search=0` 代替结构性不支持或未知。minute、hour、day SHALL 来自账号风险计数窗口，session SHALL 来自当前连接运行时的 `searches` 单场统计并映射为客户端键 `search`。

#### Scenario: 小红书与 Facebook 均供给搜索

- **WHEN** Cloud 构造已知小红书或 Facebook 账号的今日进展
- **THEN** daily alias 和适用窗口保留 search 次数及配额，即使真实次数为 0

#### Scenario: 视频号与未知平台不出现搜索格

- **WHEN** Cloud 构造视频号账号或平台归属未知账号的今日进展
- **THEN** totals、quotas、saturated 与各窗口均不包含 search

#### Scenario: 单场搜索使用运行时复数键映射

- **WHEN** 当前会话统计为 `searches=1` 且单场搜索上限为 3
- **THEN** session window 投影为 `totals.search=1` 与 `quotas.search=3`，不读取 day 累计代替

### Requirement: Native search admission failures SHALL retain the Cloud activity correlation
When a negotiated search command is rejected or fails before page actuation, Edge MUST emit exactly one schema-valid terminal for the original activity and MUST NOT cause Cloud to wait for a step timeout or record a search fact.

#### Scenario: Task-lane search is rejected before submission
- **WHEN** Native search cannot be admitted before any page-side search submission
- **THEN** Edge SHALL emit `action.completed` with the original `activityId`, `purpose`, and `scope`, `ok=false`, `actuated=false`, and `searchOutcome=not_submitted`

#### Scenario: Native search results are reported with one correlated terminal
- **WHEN** Native search returns a page-card result set for a correlated search activity
- **THEN** Edge SHALL report the cards and one terminal carrying `results_ready` or `no_results` with the observed result count

### Requirement: Native Xiaohongshu AI search SHALL use verified trusted actuation
Native search MUST support the live visible AI-search textarea as well as compatible input variants, MUST verify that the intended keyword is present before submission, and MUST keep route arrival distinct from result-card readiness.

#### Scenario: Visible AI-search textarea receives a keyword
- **WHEN** Native search resolves one visible Xiaohongshu AI-search textarea for the current page
- **THEN** it SHALL focus, clear, insert, verify, and submit the keyword through trusted CDP input rather than relying on synthetic DOM keyboard events

#### Scenario: Matching AI-search route is already active
- **WHEN** the browser is already on a `search_result_ai` route whose decoded keyword matches the command
- **THEN** Native SHALL reuse that route without resubmitting the search

#### Scenario: Result cards hydrate after route arrival
- **WHEN** the matching AI-search route is confirmed before its result cards are readable
- **THEN** Native SHALL poll within a fixed budget and report only the cards actually observed at the end of that budget

