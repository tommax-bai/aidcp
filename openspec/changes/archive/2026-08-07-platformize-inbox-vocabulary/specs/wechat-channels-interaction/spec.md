## MODIFIED Requirements

### Requirement: 浏览器仅作为鉴权 sidecar

Edge SHALL 维护 `uninitialized → browser_login_required → browser_opening → qr_waiting → identity_verifying → session_active → browser_closing → api_only_running` 的本地鉴权主链；`api_only_running` MAY 进入 `reauth_required`、`challenge_required` 或 `degraded`。只有登录确认、身份匹配、本地密文保存和至少一个已启用只读 probe 成功后，浏览器才 MAY 关闭。关闭浏览器 MUST NOT 停止 Edge 核心、Cloud WebSocket、connector timer 或本地会话。

#### Scenario: 浏览器关闭后继续同步
- **WHEN** 账号进入 `api_only_running` 且浏览器正常关闭
- **THEN** Edge 核心与 WS 保持在线，已启用的评论/DM connector 继续工作，UI 将 browser closed 表达为正常副状态

#### Scenario: 普通网络错误不频繁拉起浏览器
- **WHEN** connector 遇到短暂网络超时但没有 auth/challenge/identity 信号
- **THEN** 鉴权状态进入或保持 `degraded` 并有限退避，MUST NOT 自动反复打开浏览器

#### Scenario: auth reopen 只在原环境执行
- **WHEN** Cloud 下发 `wechat_channels.inbox.auth.reopen` 给某 `envKey + accountId`
- **THEN** Edge 只在该环境绑定的 browser profile 拉起 sidecar，并通过后续 `wechat_channels.inbox.auth.status` 如实上报阶段

### Requirement: 已验证的视频号昵称必须回填通用账号展示名

Cloud 在完成连接账号、平台与环境 scope 校验后收到 `wechat_channels.inbox.auth.status` 时，只有 payload 同时满足 `status='active'`、identity 非空且 `identity.displayName` 去除首尾空白后非空，才 SHALL 将该展示名写入通用 `accounts.nickname`。该写入只补充展示元数据，MUST NOT 改变 `accountId`、平台、环境归属、身份路由或授权状态；昵称补充失败 MUST NOT 把已经持久化的 auth status 冒充为失败。Console 账号列表 SHALL 继续使用通用 `nickname → label → accountId` 诚实回落链，MUST NOT 增加视频号专用假名分支。

#### Scenario: active 身份状态自动回填后台昵称
- **WHEN** 已绑定视频号环境上报 scope 匹配的 active auth status，identity displayName 为 `示例视频号`
- **THEN** Cloud 持久化 auth status 并把对应 `accounts.nickname` 更新为 `示例视频号`，Console 后续读取账号列表时显示该昵称而非 envKey/accountId

#### Scenario: 未验证或空白身份不得覆盖昵称
- **WHEN** auth status 不是 active、identity 为空，或 displayName 去除首尾空白后为空
- **THEN** Cloud MAY 持久化真实 auth status，但 MUST NOT 新建、清空或覆盖 `accounts.nickname`

### Requirement: WS v2 互动扩展必须完整协商并原子接线

系统 SHALL 在 WS v2 完整接线基础 inbox 七个类型，以及 `wechat_channels.inbox.reply.result.ack`、`wechat_channels.inbox.reply.reconcile`、`wechat_channels.inbox.reply.reconcile.result`、`wechat_channels.inbox.offboard.command`、`wechat_channels.inbox.offboard.result`、`wechat_channels.inbox.offboard.ack` 六个恢复/offboard 类型，使目标 `MessageType` 总数为 91；该数字为人工维护、可能滞后，权威口径以 Cloud 与 Edge 两端 `protocol.ts` 的联合类型穷举为准。两份 protocol 定义、Cloud handler/mapping、Edge active-command routing、`docs/protocol.md` 与共享 schema/fixtures MUST 同步。基础能力用 `interaction_inbox_v1`，结果恢复用 `interaction_reply_recovery_v1`，offboard 用 `interaction_offboarding_v1`；Cloud 只回显双方支持的能力，扩展能力依赖基础能力。回显 offboard 能力时 welcome MUST 带 account-bound `interactionRecovery.offboardPending`，Edge 只有明确 false 才可恢复 connector。

#### Scenario: 新 Cloud 不向旧 Edge 派 interaction 命令
- **WHEN** Edge hello 不含 `interaction_inbox_v1`
- **THEN** Cloud 不下发 sync/send/reopen，旧 Edge 连接与既有功能保持可用

#### Scenario: 新 Edge 遇旧 Cloud 不重试风暴
- **WHEN** welcome 未回显 `interaction_inbox_v1`
- **THEN** 新 Edge 不启动新 batch/status 上报，呈现 integration unavailable/degraded，MUST NOT 循环发送未知 type

#### Scenario: active-command routing 漏项使验收失败
- **WHEN** protocol 枚举包含 `wechat_channels.inbox.reply.send` 但 Edge 主动命令入口未放行
- **THEN** 契约/acceptance MUST 失败，MUST NOT 以 typecheck 通过视为接线完成

#### Scenario: 未协商恢复能力不清 durable result
- **WHEN** 新 Edge 对接只支持基础 inbox 的旧 Cloud
- **THEN** Edge MAY 发送基础 reply.result，但 MUST 保留 result outbox，直到后续连接协商 recovery 并收到 exact ack

#### Scenario: 未协商 offboard 能力保持撤权待清理
- **WHEN** Cloud 已撤权但连接的旧 Edge 没有 `interaction_offboarding_v1`
- **THEN** Cloud 不发送未知 type、不恢复同步/写，offboard 保持 pending 且不得提前 tombstone

#### Scenario: pending 查询失败不短暂恢复 connector
- **WHEN** Cloud 回显 offboard capability 但 pending 状态读取失败或 welcome 缺少 recovery barrier
- **THEN** Edge 将其视为 offboardPending=true，保持 connector 停止，MUST NOT 在 command 到达前短暂同步或写

### Requirement: Edge 同步 checkpoint 必须等 Cloud 显式 ack

一个 `wechat_channels.inbox.sync.batch` SHALL 只覆盖一个 account/env/channel/scope。Cloud MUST 以相同 envelope `id` 回 `wechat_channels.inbox.sync.ack`；Edge 只有在 ack status 为 `accepted|duplicate` 且 `cursorAfter` 逐字匹配时才提交 checkpoint。`rejected`、断连、超时或 cursor 不匹配 MUST 保持旧 checkpoint。

#### Scenario: 重复 batch 不重复副作用
- **WHEN** Edge 因 ack 丢失重发同一 `batchId`
- **THEN** Cloud 返回 `duplicate` 与原 cursor 真态，MUST NOT 重复创建 message/job，Edge MAY 安全提交 checkpoint

#### Scenario: 部分持久化失败不推进 cursor
- **WHEN** batch 中任一 thread/message 校验或事务写失败
- **THEN** Cloud 回 `rejected` 或连接错误且整批回滚，Edge 保持 `cursorBefore`

### Requirement: Edge 发送必须幂等并诚实处理歧义

Edge SHALL 持久保存 `idempotencyKey` 与已执行结果；重复 `wechat_channels.inbox.reply.send` MUST 返回既有结果而不再次调用平台。只有平台 ack 或历史/评论回查确认才可返回 `confirmed`；网络超时、连接中断和响应解析失败 MUST 返回 `ambiguous` 并先回查，MUST NOT 盲目重发。

#### Scenario: 重复发送命令只调用一次平台
- **WHEN** 同一 `attemptId + idempotencyKey` 因 WS 重连重复到达
- **THEN** Edge 复用持久结果并回 `wechat_channels.inbox.reply.result`，平台写接口最多调用一次

#### Scenario: 超时不冒充失败或成功
- **WHEN** 平台提交请求已发出但响应超时且回查尚无结论
- **THEN** Edge 返回 `status='ambiguous'`、`verification='not_verified'`，MUST NOT 返回 confirmed 或触发自动重试

### Requirement: Edge 发送结果必须 durable 并由 Cloud exact ack

Edge SHALL 在发送 `wechat_channels.inbox.reply.result` 前将完整结果写入 durable outbox，并在启动/重连后补发。Cloud SHALL 在事务持久化 scope-matching attempt/job 后返回同 envelope id 的 ack。Edge MUST 只在 ack status=`accepted|duplicate` 且 jobId/attemptId/idempotencyKey/envKey/accountId/platform 全部逐字匹配时清除 outbox。

#### Scenario: Cloud 持久化后在 ack 前崩溃
- **WHEN** Edge 未收到 ack 并在重连后重发同一 result
- **THEN** Cloud 返回 duplicate，job/attempt/RiskController 副作用至多一次，Edge 收 exact ack 后清 outbox

#### Scenario: 错绑或 rejected ack 不清 outbox
- **WHEN** ack 的 accountId、attemptId 或 idempotencyKey 不匹配，或 status=rejected
- **THEN** Edge 保留 durable result 并停止本轮 flush，MUST NOT 把结果视为已确认

### Requirement: Attempt reconciliation 禁止 blind resend

Cloud SHALL 在启动和 Edge 重连时针对 `created|dispatched|ambiguous` 原 attempt/idempotency identity 发 `wechat_channels.inbox.reply.reconcile`。Edge SHALL 只检查 durable execution/result 或平台历史，不得调用 reply platform write。`created+not_found` MAY 明确 failed；`dispatched|ambiguous+not_found` MUST 保持 ambiguous；`result_replayed` MUST 通过正常 durable result 回传推进。

#### Scenario: Edge 本地没有 dispatched attempt
- **WHEN** reconcile 请求一个 Cloud 已 dispatched、Edge 状态中不存在的 attempt
- **THEN** Edge 回 not_found 且平台写调用数为 0，Cloud 保持 ambiguous 并禁止同 job 新 attempt

### Requirement: Edge offboard 必须 durable、scope-bound 且与普通生命周期分离

Edge SHALL durable claim scope-bound `wechat_channels.inbox.offboard.command`，先停止新同步/写并 drain 在途任务，再清除 `envKey+accountId+identity+profile` 加密 session、关闭 sidecar、durable 保存 result，并在 exact Cloud ack 前跨重启补发。普通 pause/close/standby/logout MUST NOT 执行 session clear。

#### Scenario: Edge 离线后重连补清理
- **WHEN** Cloud 已撤权并持久化 offboard，而 Edge 当时离线
- **THEN** 新 Edge 重连协商 capability 后收到同一 offboardId，按顺序清理并补发结果，期间不得恢复 connector 同步/写

#### Scenario: 清理失败可重试且不误报成功
- **WHEN** session clear 或 sidecar close 失败
- **THEN** Edge durable 回 failed，Cloud 保持 pending；重试同 offboardId 可继续清理，MUST NOT tombstone 或显示已完成
