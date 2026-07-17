## Why

视频号首次授权成功后会把加密会话交给 API-only 运行时并主动关闭 AdsPower 浏览器，这在资源和安全上是正确的，但授权仍有效时客户没有入口重新打开所属浏览器，容易把正常后台运行误解为环境停止，也无法临时查看或处理浏览器现场。

## What Changes

- 为授权有效且浏览器已关闭的视频号环境增加“打开浏览器”操作，并在浏览器已打开时提供“转入后台”操作。
- 打开操作只作用于当前客户拥有的 `envKey + accountId` 和唯一在线 Edge；Edge 打开所属 sidecar 后保持可见，直到客户转入后台或环境生命周期结束。
- 浏览器打开或关闭请求只返回“已受理”；客户端继续以 Edge 后续上报的 `interaction.auth.status.browserState` 作为成功真值，不把命令投递当执行成功。
- 保留原有首次授权、重新授权、挑战处理及身份错配 fail-closed 语义；客户账号“退出登录”与环境浏览器控制继续分离。
- 同步 Edge/Cloud 协议定义、Cloud command mapping、`docs/protocol.md` 和 Edge active-command routing，并补齐回归测试。

## Capabilities

### New Capabilities
- `wechat-channels-browser-foreground-control`: 定义视频号 API-only 状态下 env/account 作用域的浏览器打开、保持可见、受控关闭、状态真值和失败边界。

### Modified Capabilities
- `edge-companion-ui`: 视频号 workspace 在授权正常时展示明确的浏览器前台/后台控制与等待真态文案。
- `client-customer-auth`: 客户只能对自己拥有的视频号环境提交浏览器打开/关闭请求，并且 API 只报告受理状态。

## Impact

- `aidcp-edge`: 视频号 auth/sidecar 生命周期、WS 协议校验与路由、Electron preload/main IPC、互动 workspace UI 和测试。
- `aidcp-cloud`: WS 协议与 handler/pusher 路由、customer-auth API、幂等请求声明和测试。
- `aidcp`: OpenSpec 契约、任务进度和 `docs/protocol.md`。
- 不新增平台写权限，不改变评论/私信能力闸门，不构建 Edge 安装包；完成后按默认流程推送并部署 Cloud 到 `dev`，Edge 源码停在 commit/push。
