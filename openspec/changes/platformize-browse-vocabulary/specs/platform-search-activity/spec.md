## MODIFIED Requirements

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
