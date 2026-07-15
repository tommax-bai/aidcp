## ADDED Requirements

### Requirement: 客户互动 API 必须逐请求验证 enabled user 与 env ownership

customer-auth SHALL 暴露冻结的 interaction list/detail/draft/approve/send/regenerate/ignore/escalate/sync/auth-reopen 路径。每次请求 MUST 在客户 JWT 验签后回库复核 user enabled 与 `envKey` ownership；thread/message/job 还 MUST 属于同一 env/account。跨环境资源与不存在资源 MUST 返回同一 404，不可枚举。

#### Scenario: 有 token 但无环境归属仍不可读
- **WHEN** enabled 客户携有效 token 请求未归属 env 的互动列表
- **THEN** 返回不可枚举 404，MUST NOT 返回 item 数量、accountId 或最后同步时间

#### Scenario: 归属被移除即时生效
- **WHEN** 管理员移除客户对 env 的归属后其 token 尚未过期
- **THEN** 客户下一次 interaction 请求即被拒，无需等待 token 过期

### Requirement: Customer API 路径和 envelope 必须与共享 schema 一致

客户 API SHALL 实现：`GET /environments/:envKey/interactions`、`GET /environments/:envKey/interactions/:threadId`、`PUT /environments/:envKey/replies/:jobId/draft`、三个 reply POST（approve/send/regenerate）、message ignore/escalate、interaction sync 与 auth/reopen。成功/错误 envelope、分页 cursor、枚举与字段 MUST 通过 `docs/contracts/wechat-channels-interaction/v1/schemas/customer-auth-api.schema.json`。

#### Scenario: 列表回包携 scope 和真态
- **WHEN** 客户读取当前环境互动列表
- **THEN** 响应 data 明确回带 `envKey/accountId/platform/items/nextCursor` 且 meta 含 requestId/asOf，renderer 可拒绝错 env 回包

#### Scenario: 2xx send 不等于平台 confirmed
- **WHEN** send endpoint 成功把 job 从 approved 转 queued
- **THEN** 响应返回 job 真态 queued，MUST NOT 返回 sent 或让客户端解释为平台成功

### Requirement: 客户写操作必须使用 CAS 与幂等 header

job draft/approve/send/regenerate/ignore/escalate MUST 携 `expectedVersion`；版本或状态不符 MUST 409 并返回当前 version/state，不执行部分副作用。send/sync/auth-reopen MUST 要求 `Idempotency-Key` header，重复 key MUST 返回既有请求真态。

#### Scenario: 重复点击发送只有一个 attempt
- **WHEN** 客户端以相同 idempotency key 重试 send
- **THEN** Cloud 返回既有 job/attempt 状态，MUST NOT 创建第二 attempt

#### Scenario: 迟到编辑不能覆盖新批准
- **WHEN** 客户用旧 expectedVersion 修改已被另一客户端批准的 job
- **THEN** 服务端返回 version conflict 和当前真态，批准/文本保持不变

### Requirement: 登录失效时历史可读但写 fail closed

只要客户仍有 env ownership，已同步历史 MAY 继续读取；当 auth 非 active、identity mismatch 或 challenge 时，所有 reply/send 写 MUST 返回稳定阻断码，并可通过 auth/reopen 请求原 Edge sidecar。auth/reopen accepted 只表示请求已受理，MUST NOT 表示登录完成。

#### Scenario: Cookie 失效后仍能查看历史
- **WHEN** 当前环境 auth=reauth_required 且客户读取已同步 thread
- **THEN** API 返回历史与 auth 阻断状态，但 approve/send 按门禁拒绝

#### Scenario: Reopen 成功响应不冒充已登录
- **WHEN** Cloud 已接受 auth/reopen 并下发 Edge
- **THEN** API 返回 accepted/requestId，UI 等待后续 auth.status active，MUST NOT立即显示同步正常
