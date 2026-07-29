# wechat-sync-timestamp-honesty Specification

## Purpose
TBD - created by archiving change wechat-sync-timestamp-honesty. Update Purpose after archive.
## Requirements
### Requirement: 客户互动 API 必须投影真实分渠道同步证据

customer-auth 的 interaction list/detail 成功回包 SHALL 在 `data.syncFreshness` 返回固定的 `comment` 与 `dm` 键。每个渠道 MUST 为 `null`，或为只含有限 epoch-ms `observedAt` 与 `receivedAt` 的对象：`observedAt` SHALL 来自 Edge 成功提交批次的同名字段，`receivedAt` SHALL 来自 Cloud 提交该批次事务的服务端时间。投影 MUST 限定已授权的 account/env，MUST NOT 用 API 请求时间、`meta.asOf`、auth checkedAt、最新消息时间或当前时间补空。

#### Scenario: 从未成功同步的渠道保持 null

- **WHEN** enabled 客户读取其已归属环境，comment 已有成功批次而 dm 从未成功持久化批次
- **THEN** 回包 `syncFreshness.comment` 返回该批次的 observedAt/receivedAt，`syncFreshness.dm` 为 null

#### Scenario: 两渠道时间独立

- **WHEN** comment 与 dm 最近成功批次发生在不同时间
- **THEN** 回包分别返回各自证据，MUST NOT 用较新的渠道时间覆盖、聚合或背书另一个渠道

#### Scenario: 无环境归属不得枚举同步时间

- **WHEN** 客户请求未归属或已撤权环境的 interaction list/detail
- **THEN** 继续返回不可枚举拒绝，MUST NOT 泄漏任一渠道的 observedAt、receivedAt 或是否存在批次

### Requirement: 同步证据必须在无内容变化时仍诚实推进且不得回退

Cloud SHALL 以已提交的 interaction sync batch 作为成功证据。同 batchId、scope、cursor 与内容再次到达时，若新的 `observedAt` 严格晚于已存 observedAt，系统 MUST 将其视为一次内容未变化的新平台观察，只推进该 batch 的 observedAt/receivedAt 与对应 scope 的成功时间，不重复创建 thread/message/job；若 observedAt 相等或更早，MUST 视为网络重放并保持证据时间不变。按渠道投影 MUST 选择 observedAt 最新的已接受证据，旧包不得让时间倒退。

#### Scenario: 空批次的新观察推进时间

- **WHEN** Edge 在后续轮次再次读到相同 cursor 且 threads/messages 均为空，以相同 batchId 但更晚 observedAt 提交
- **THEN** Cloud 不重复业务写，但该渠道 syncFreshness 推进到新 observedAt 和本次事务 receivedAt

#### Scenario: 丢 ack 后重放不伪造新鲜度

- **WHEN** Edge 因 ack 丢失重放同一 batchId 与相同 observedAt
- **THEN** Cloud 返回幂等 duplicate，syncFreshness 保持原 observedAt/receivedAt，不把重放到达时间显示成新同步

#### Scenario: 延迟旧观察不让时间倒退

- **WHEN** 已有较新 observedAt 后又收到同 scope 的较旧观察
- **THEN** Cloud 保持较新证据，客户回包时间不回退

### Requirement: meta.asOf 不得被解释为同步时间

customer API `meta.asOf` SHALL 继续只表示本次响应快照/分页边界。Electron InteractionWorkspace MUST NOT 将它显示为互动“数据时间”，也 MUST NOT 仅凭 `meta.asOf` 存在、HTTP list/detail 成功、auth active、read capability=true 或 items 为空宣称“同步正常”。新客户端收到缺失或非法 `syncFreshness` 时 MUST 按 unknown/fail-closed 展示。

#### Scenario: API 可读但从未同步

- **WHEN** list 请求成功且 meta.asOf 为当前时间、读取三层门禁均通过，但目标渠道 syncFreshness 为 null
- **THEN** 客户端显示该渠道“尚未成功同步/状态待确认”，MUST NOT 显示“同步正常”、数据刚更新或真实空结果

#### Scenario: 旧 Cloud 未返回新字段

- **WHEN** 新客户端在兼容窗口读到没有 syncFreshness 的合法旧回包
- **THEN** 客户端保持历史内容可读但同步状态为待确认，MUST NOT 回退使用 meta.asOf

### Requirement: 互动 workspace 必须按真实证据展示空态与最近时间

InteractionWorkspace SHALL 将 stored read intent、Edge application status、effective capability、Cloud connectivity 与目标渠道 syncFreshness 联合判定。门禁通过且证据存在时，页面 SHALL 展示该渠道最近 observedAt；Cloud 离线时 SHALL 保留并标明“上次成功”时间。只有目标渠道有成功证据且 items 为空时，页面才可显示“当前没有评论互动/私信会话”。综合视图 MUST 分别表达 comment 与 dm，不能以任一渠道的证据替代另一个。

#### Scenario: 历史数据停滞不被页面刷新洗新

- **WHEN** 渠道最后 observedAt 已停滞一段时间，但用户或自动轮询多次成功读取 customer API
- **THEN** 页面持续显示原最近同步时间，MUST NOT 随每次 meta.asOf 推进成当前时间

#### Scenario: Cloud 离线保留上次成功边界

- **WHEN** 页面已有 syncFreshness 后 Cloud 读取失败
- **THEN** 历史列表继续可读并显示“使用上次成功数据”及原 observedAt，MUST NOT 清空时间或冒充刚同步

#### Scenario: 一个渠道有证据另一个没有

- **WHEN** comment 有成功证据而 dm 为 null
- **THEN** comment 可显示最近同步/真实空态，dm 显示尚未成功同步，综合状态不写成“评论/私信同步正常”

#### Scenario: 设备时间明显超前

- **WHEN** observedAt 比同证据 receivedAt 晚超过五分钟
- **THEN** 客户端显示设备时间待校准并保留 Cloud 接收时间作为辅助证据，MUST NOT 把未来 observedAt 展示为正常新鲜度

### Requirement: 局部刷新受理与完成必须分开

用户点击局部刷新后，HTTP 2xx/`status=accepted` SHALL 只显示请求已受理。客户端 MUST 记录目标渠道点击前的 `receivedAt` 基线；只有后续 env-scoped list/detail 回包中该渠道 receivedAt 严格推进，才可显示本次同步已有成功结果。超时、Cloud 离线、迟到的其他环境回包或未推进证据 MUST NOT 映射为完成。

#### Scenario: 请求受理但 Edge 尚未回包

- **WHEN** sync API 返回 accepted，而后续 list 仍返回原 receivedAt
- **THEN** 页面显示“已受理，尚未确认同步完成”，MUST NOT 显示本次刷新成功

#### Scenario: 空结果同步仍能确认完成

- **WHEN** Edge 完成一次内容未变化或空结果读取，Cloud 将目标渠道 receivedAt 推进
- **THEN** 后续读回可显示本次同步已有成功结果，同时 items 仍可为空

#### Scenario: 环境 A 的完成证据不结束环境 B 的等待

- **WHEN** 用户从 A 切到 B 后 A 的 syncFreshness 迟到回包
- **THEN** B 的等待状态、最近时间与空态均不使用 A 的证据
