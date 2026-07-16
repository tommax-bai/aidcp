## Why

视频号 interaction 代码已经具备合成合同与 fail-closed 骨架，但真实运行仍被三处断点阻塞：首次登录前拿不到 finder identity 却强制要求预配账号 ID，Cloud 已保存的账号级 runtime controls 没有下发到 Edge，评论/私信请求仍使用未经真实授权会话验证的猜测格式。若不闭合这些断点，客户端会把可恢复的首次授权显示成配置错误，运营开关与 Edge 实际能力会漂移，并可能向平台发送结构错误的请求。

## What Changes

- 将视频号的 Cloud 逻辑账号作用域与首次登录后绑定的 finder identity 分离：多环境 Edge 以稳定 `envKey` 建立账号作用域，首次授权绑定真实 finder identity，之后任何身份漂移继续 fail-closed。
- 在 Edge 客户端明确展示首次登录、身份绑定、账号不匹配与重新授权引导，不再要求用户预先知道内部 finder ID，也不把 Cloud 请求受理显示为授权成功。
- 复用 Cloud `interaction_runtime_controls` 作为账号级唯一真值，在 `welcome` 下发版本化 Edge runtime controls；缺失、读取失败、旧 Cloud 或 scope 不匹配时 Edge 全部能力保持关闭。
- 按真实授权视频号助手会话的脱敏抓包证据校准评论读取/回复与私信读取/发送的 endpoint、method、query/body、必要非秘密 headers 及响应判断；任何尚未由证据覆盖的写能力保持关闭。
- 为身份 bootstrap、开关版本/作用域、协议兼容、请求序列化与敏感信息不落盘补充 Edge/Cloud 合同测试和只读/门禁验收证据。

## Capabilities

### New Capabilities

- `wechat-channels-real-runtime`: 视频号首次身份绑定、账号级 Edge 控制下发、真实会话请求描述与证据门禁。

### Modified Capabilities

- `platform-runtime-abstraction`: 视频号环境允许以稳定环境作用域先握手，再绑定独立平台 identity，且平台校验仍以 `accounts.platform` 为准。
- `edge-companion-ui`: 视频号首次授权、身份绑定/不匹配和账号级能力状态必须提供可执行且诚实的用户引导。
- `client-customer-auth`: 客户环境读取必须通过 `envKey` 解析权威 interaction 账号绑定，并返回与该账号下发控制一致的真态。
- `console-panel-api`: 账号级 runtime controls 更新后必须成为 Edge 下发快照的唯一真值，并维持 CAS、审计和 fail-closed 行为。

## Impact

- Edge：`src/wechat-channels/**`、WS `WelcomePayload`、`EdgeClient` 握手消费、Electron InteractionWorkspace 与相关测试。
- Cloud：WS protocol/handler、`InteractionStore` runtime controls provider、internal/customer API 与装配测试；不新增写开关的隐式默认值。
- Control repo：`docs/protocol.md`、视频号 interaction 合同/fixtures、真实机器验收记录及旧变更剩余任务的证据同步。
- 部署：Cloud runtime 变化只部署到 `dev`；Edge 默认只提交/推送，不构建桌面安装包。真实评论/私信写仍要求单独给出一次性可丢弃目标。
