# wechat-send-failure-semantics Specification

## Purpose
TBD - created by archiving change wechat-send-failure-semantics. Update Purpose after archive.
## Requirements
### Requirement: 视频号回复结果必须先按派发事实分类

Edge SHALL 以可信的请求派发证据作为 `failed` 与 `ambiguous` 的第一判据，而不是只按错误类别分类。能够证明平台写请求未离开 Edge 进程时 MUST 返回 `status='failed'`；请求可能已经派发但没有可信平台结果时 MUST 在有界回查后返回 `confirmed` 或 `ambiguous`，MUST NOT 盲目重发。

#### Scenario: 请求构造失败是确定未发送

- **WHEN** 视频号回复在平台请求序列化、端点解析或其他写调用前置阶段失败，错误证据为 `requestDispatched=false`
- **THEN** Edge durable 保存并回传 `status='failed'`、`verification='not_verified'`，MUST NOT 调用评论列表或私信历史进行发送回查，MUST NOT 显示为“待核验”

#### Scenario: 未知异常不能证明未派发

- **WHEN** 平台写调用抛出无法提供可信派发事实的未知异常
- **THEN** Edge MUST 保守视为可能已派发，执行有界回查；未得到唯一命中时返回 `status='ambiguous'`，MUST NOT 以 failed 放开自动重投

### Requirement: 平台明确拒绝与派发后不确定必须分流

Edge SHALL 将平台明确返回的认证失效、挑战、限流、权限拒绝或业务拒绝记为 `failed`；超时、连接中断、成功响应或 ack 无法解析等无法证明写入结果的派发后异常 MUST 先回查，只有唯一平台记录可升级为 `confirmed`，否则保持 `ambiguous`。

#### Scenario: 平台明确拒绝不进入待核验

- **WHEN** 已派发请求收到可解析且明确的拒绝响应
- **THEN** Edge 回传 `status='failed'` 与对应安全错误类别，不执行发送历史回查，Cloud MUST NOT 记录一次成功互动

#### Scenario: 派发后响应不可解析仍待核验

- **WHEN** 请求可能已抵达平台，但响应或 ack 无法形成可信结果
- **THEN** Edge 执行现有有界回查；唯一命中时返回 `confirmed`，未命中、非唯一或回查失败时返回 `ambiguous`，且平台写调用数保持一次

### Requirement: 失败语义修正不得扩展协议或写授权

本变更 SHALL 复用现有 `wechat_channels.inbox.reply.result` 的 `confirmed | failed | ambiguous`、durable outbox 与 exact Cloud ack，MUST NOT 新增 message type 或 payload 字段。尚未获得真实捕获证据的写端点与账号写开关 MUST 继续关闭，测试结果 MUST NOT 被表述为真实账号发送成功。

#### Scenario: 新旧 peer 契约保持不变

- **WHEN** 修正后的 Edge 向现有 Cloud 回传确定未派发的 `failed` 或派发后不确定的 `ambiguous`
- **THEN** Cloud 按既有 schema 和 attempt/job 状态机持久化并 exact ack，无需能力协商或数据库迁移

#### Scenario: 本地回归不冒充真实写验收

- **WHEN** 单元、协议、acceptance 或 mock 测试全部通过但没有批准的真实写目标与平台证据
- **THEN** 变更记录 MUST 明确真实评论/私信写入未执行，MUST NOT 启用未捕获写端点或宣称真机发送成功

