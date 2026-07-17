## Context

视频号互动链路由 Cloud 创建 attempt 并通过 WS 定向下发，Edge 在本地持久 claim 后调用平台写接口，再以既有 `confirmed | failed | ambiguous` 结果回传。Edge 的 `WechatChannelsError` 已携带 `requestDispatched`，用于表示请求是否可能离开进程；但 `WechatReplySender` 当前只按 `category` 决定终态，且响应 parser 产生的 `schema_changed` 默认带有本地前置错误的 `requestDispatched=false`。因此序列化前与响应解析后的错误证据没有完整分流。

这会混淆两个风险完全不同的事实：序列化前失败可以证明平台没有收到写请求；请求派发后超时、断连或响应不可解析则无法证明平台是否已写入。前者长期占据 ambiguous 会阻断后续人工修复，后者若当作 failed 重试则可能重复回复。

## Goals / Non-Goals

**Goals:**

- 让“是否可能已经派发”成为发送结果分类的第一判据。
- 保留平台明确拒绝为 `failed`，保留派发后不可判定为 bounded verify 后的 `confirmed | ambiguous`。
- 证明确定未派发的失败不会触发平台历史/评论回查，也不会被显示为待核验。
- 不改变现有协议 payload、数据库枚举和 Cloud 风险记账边界。

**Non-Goals:**

- 不捕获、猜测或启用尚无真实证据的视频号写端点。
- 不新增自动重试、人工清除 ambiguous 或结果覆盖接口。
- 不做真实账号写入、桌面安装包构建或 ol 发布。
- 不改变 `RiskController` 只有 Cloud 能写最终账号风险状态的约束。

## Decisions

### 1. 以派发证据优先于错误类别

Edge 按以下顺序分类：

| 派发证据 | 平台证据 | 结果 |
| --- | --- | --- |
| `requestDispatched=false` | 无平台调用 | `failed`，不回查 |
| `requestDispatched=true` | 平台明确拒绝（认证、挑战、限流、权限或业务拒绝） | `failed`，不回查 |
| `requestDispatched=true` 或无法证明未派发 | 平台 ack 或唯一历史命中 | `confirmed` |
| `requestDispatched=true` 或无法证明未派发 | 超时、断连、响应/ack 解析失败且回查未唯一命中 | `ambiguous` |

未知异常继续保守转换为“可能已派发”，因为仅凭 JavaScript 异常类型不能证明网络栈没有发送请求。相比把 `schema_changed` 永久定义成 failed/ambiguous，这一判据能正确区分请求构造失败与成功响应形状变化。

### 2. 复用 Edge-local 证据，不扩协议

`requestDispatched` 只参与 Edge 内部分类，不加入 `interaction.reply.result`。Cloud 已能消费 `failed` 与 `ambiguous`，数据库状态机和 result exact-ack 不需要变化。这样避免为实现细节扩展 WS v2 message type 或 payload，也不引入新旧 peer 协商问题。

### 3. 只有可能写入平台的结果才做 bounded verify

API client SHALL 在请求/响应两段分别捕获错误：请求构造或序列化失败保留 `requestDispatched=false`；收到平台响应后才发生的 parser 错误必须升级为 `requestDispatched=true`。确定未派发和平台明确拒绝都直接完成 durable result；只有可能写入但结果未知时才执行现有评论/DM 回查。回查仍要求唯一匹配，未命中或回查自身失败保持 `ambiguous`，不得盲重发。

### 4. 测试承重边界而非只测错误名称

Edge 单测至少覆盖同一 `schema_changed` 类别在 `requestDispatched=false` 与 `true` 下产生不同结果，断言真实 API client 的响应 parser 错误携已派发证据，并断言前者零回查、后者仍回查/ambiguous。保留 timeout/restart/reconcile 不重发测试。Cloud 只运行现有结果消费和协议测试，除非验证发现其状态机不能接受新的诚实 `failed` 路径。

## Risks / Trade-offs

- [上游错误错误标记 `requestDispatched=false`] → 仅允许请求构造/序列化等可证明未进入 fetch 的路径设置 false；fetch 与未知异常继续保守为 true，并用单测锁定包装器不篡改已有证据。
- [平台明确拒绝响应实际上已产生副作用] → 只把已有明确拒绝类别视为 failed；任何响应解析不可信仍走 verify/ambiguous。
- [failed 允许后续人工重试] → Cloud 继续按现有 retryability、门禁、CAS 和唯一 attempt 约束处理；本变更不新增自动重试。
- [真实写端点仍未捕获] → 写能力维持默认关闭；本变更只修诚实状态，不把未验证端点描述成可用。

## Migration Plan

1. 在隔离 Edge worktree 修改分类函数并补 focused tests。
2. 运行 Edge focused tests、acceptance、full suite 与 typecheck；不做 installer build。
3. 更新 OpenSpec 任务证据并严格校验。
4. 代码合入 `aidcp-edge/master` 后按规范发布 `dev` 运行时；真实写验证继续留在真机 backlog，未获批准不得执行。
5. 回滚只需回退 Edge 分类改动；协议和数据库无迁移。

## Open Questions

- 无实现阻断问题。真实写端点、目标和账号授权仍由 `wechat-channels-interaction-management` 的真机验收项管理，不在本变更中扩大授权。
