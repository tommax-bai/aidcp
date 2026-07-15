## ADDED Requirements

### Requirement: 视频号平台标识与能力必须诚实声明

系统 SHALL 使用精确 `PlatformId='wechat_channels'`，并 SHALL 继续把每个视频号账号绑定为一个 `envKey + accountId` 环境。平台能力 SHALL 分别声明 `identity`、`overlay`、`auth.browser_sidecar`、`interaction.comment.read`、`interaction.comment.reply`、`interaction.dm.read`、`interaction.dm.send_text`、`interaction.dm.send_image`；browse/like/collect/follow/publish/patrol MUST 显式 unsupported。账号状态上报的 capability 布尔值 MUST 表达 build support、feature flag、active auth、identity match 与 endpoint probe 同时成立后的有效能力，MUST NOT 把“代码可能支持”冒充“当前可用”。

#### Scenario: 视频号环境按精确平台启动
- **WHEN** 一个环境被标注为 `wechat_channels` 并启动
- **THEN** Edge 与 Cloud 均以 `wechat_channels` 路由该账号，MUST NOT 回落 `xiaohongshu` 或 `facebook`

#### Scenario: 未通过发送探针时不声明写能力
- **WHEN** 当前账号评论读取正常但评论发送 probe/feature flag 未通过
- **THEN** `commentsRead` MAY 为 true，但 `commentsReply` MUST 为 false，系统 MUST NOT 下发发送命令

#### Scenario: 图片私信在 v1 诚实禁用
- **WHEN** 任意 v1 视频号账号上报能力
- **THEN** `dmSendImage` MUST 为 false，任何图片 send 请求 MUST 返回 unsupported 而非转成文本或伪成功

### Requirement: 浏览器仅作为鉴权 sidecar

Edge SHALL 维护 `uninitialized → browser_login_required → browser_opening → qr_waiting → identity_verifying → session_active → browser_closing → api_only_running` 的本地鉴权主链；`api_only_running` MAY 进入 `reauth_required`、`challenge_required` 或 `degraded`。只有登录确认、身份匹配、本地密文保存和至少一个已启用只读 probe 成功后，浏览器才 MAY 关闭。关闭浏览器 MUST NOT 停止 Edge 核心、Cloud WebSocket、connector timer 或本地会话。

#### Scenario: 浏览器关闭后继续同步
- **WHEN** 账号进入 `api_only_running` 且浏览器正常关闭
- **THEN** Edge 核心与 WS 保持在线，已启用的评论/DM connector 继续工作，UI 将 browser closed 表达为正常副状态

#### Scenario: 普通网络错误不频繁拉起浏览器
- **WHEN** connector 遇到短暂网络超时但没有 auth/challenge/identity 信号
- **THEN** 鉴权状态进入或保持 `degraded` 并有限退避，MUST NOT 自动反复打开浏览器

#### Scenario: auth reopen 只在原环境执行
- **WHEN** Cloud 下发 `interaction.auth.reopen` 给某 `envKey + accountId`
- **THEN** Edge 只在该环境绑定的 browser profile 拉起 sidecar，并通过后续 `interaction.auth.status` 如实上报阶段

### Requirement: 会话凭证必须留在所属 Edge 并防串号

Cookie/session/二维码/浏览器调试地址 MUST NOT 出现在 Cloud DB、WS payload、普通日志、crash report、metrics、renderer 或 fixtures。Edge 本地密文 SHALL 绑定 `envKey + accountId + finderIdentity + browserProfileId`；每个环境 MUST 使用独立 cookie jar、timer 与 in-flight namespace。每次恢复会话和发送前 MUST 校验稳定身份；身份不符时 MUST 停止同步和发送并上报 `WECHAT_IDENTITY_MISMATCH`。

#### Scenario: 登录到错误账号时 fail closed
- **WHEN** 会话恢复后的身份 probe 与环境绑定 identity 不一致
- **THEN** Edge 禁止读写、清除当前 effective capabilities、上报 identity mismatch，MUST NOT 把观察到的账号内容写入目标环境

#### Scenario: 清除登录信息立即停写
- **WHEN** 用户对当前环境执行清除登录信息
- **THEN** Edge 停止新发送、删除本地密文并进入 login required，Cloud 只保留业务队列而不把任务标记成功

### Requirement: 私有接口必须由安全 adapter 隔离

所有创作者助手私有端点调用 SHALL 收口在 Edge `WechatChannelsApiClient`，默认启用 TLS 验证、超时、响应大小上限、有限重试和逐端点 schema 校验。未知字段 MAY 容忍，关键字段缺失 MUST 分类为 `schema_changed` 并关闭对应 capability。第三方响应/错误 MUST 经稳定 error category/code 脱敏，MUST NOT 作为官方 API 或原文直接透传。

#### Scenario: schema 漂移关闭单一能力
- **WHEN** DM history 的关键字段缺失而 comment schema 仍正常
- **THEN** Edge 关闭 `dmRead/dmSend*` 并上报 `WECHAT_SCHEMA_CHANGED`，评论能力 MAY 保持，MUST NOT 崩溃或吞掉错误当成功

#### Scenario: 读能力不自动开放写能力
- **WHEN** 评论列表 probe 成功但评论发送未做受控验证
- **THEN** 读取 MAY 开启，评论写 MUST 继续关闭

### Requirement: WS v2 互动扩展必须完整协商并原子接线

系统 SHALL 在 WS v2 新增 `interaction.auth.status`、`interaction.sync.batch`、`interaction.sync.ack`、`interaction.reply.result`、`interaction.sync.request`、`interaction.reply.send`、`interaction.auth.reopen` 七个类型，使目标 `MessageType` 总数为 83。两份 protocol 定义、Cloud handler/mapping、Edge active-command routing、`docs/protocol.md` 与共享 schema/fixtures MUST 同步。新 Edge SHALL 在 `hello.capabilities` 声明 `interaction_inbox_v1`，新 Cloud SHALL 在 `welcome.capabilities` 回显；只有双方确认后才交换新类型。

#### Scenario: 新 Cloud 不向旧 Edge 派 interaction 命令
- **WHEN** Edge hello 不含 `interaction_inbox_v1`
- **THEN** Cloud 不下发 sync/send/reopen，旧 Edge 连接与既有功能保持可用

#### Scenario: 新 Edge 遇旧 Cloud 不重试风暴
- **WHEN** welcome 未回显 `interaction_inbox_v1`
- **THEN** 新 Edge 不启动新 batch/status 上报，呈现 integration unavailable/degraded，MUST NOT 循环发送未知 type

#### Scenario: active-command routing 漏项使验收失败
- **WHEN** protocol 枚举包含 `interaction.reply.send` 但 Edge 主动命令入口未放行
- **THEN** 契约/acceptance MUST 失败，MUST NOT 以 typecheck 通过视为接线完成

### Requirement: Edge 同步 checkpoint 必须等 Cloud 显式 ack

一个 `interaction.sync.batch` SHALL 只覆盖一个 account/env/channel/scope。Cloud MUST 以相同 envelope `id` 回 `interaction.sync.ack`；Edge 只有在 ack status 为 `accepted|duplicate` 且 `cursorAfter` 逐字匹配时才提交 checkpoint。`rejected`、断连、超时或 cursor 不匹配 MUST 保持旧 checkpoint。

#### Scenario: 重复 batch 不重复副作用
- **WHEN** Edge 因 ack 丢失重发同一 `batchId`
- **THEN** Cloud 返回 `duplicate` 与原 cursor 真态，MUST NOT 重复创建 message/job，Edge MAY 安全提交 checkpoint

#### Scenario: 部分持久化失败不推进 cursor
- **WHEN** batch 中任一 thread/message 校验或事务写失败
- **THEN** Cloud 回 `rejected` 或连接错误且整批回滚，Edge 保持 `cursorBefore`

### Requirement: Edge 发送必须幂等并诚实处理歧义

Edge SHALL 持久保存 `idempotencyKey` 与已执行结果；重复 `interaction.reply.send` MUST 返回既有结果而不再次调用平台。只有平台 ack 或历史/评论回查确认才可返回 `confirmed`；网络超时、连接中断和响应解析失败 MUST 返回 `ambiguous` 并先回查，MUST NOT 盲目重发。

#### Scenario: 重复发送命令只调用一次平台
- **WHEN** 同一 `attemptId + idempotencyKey` 因 WS 重连重复到达
- **THEN** Edge 复用持久结果并回 `interaction.reply.result`，平台写接口最多调用一次

#### Scenario: 超时不冒充失败或成功
- **WHEN** 平台提交请求已发出但响应超时且回查尚无结论
- **THEN** Edge 返回 `status='ambiguous'`、`verification='not_verified'`，MUST NOT 返回 confirmed 或触发自动重试
