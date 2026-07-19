## Why

视频号启动会先用本地加密会话做 API-only 校验，但当该会话失效、AdsPower profile 又被其他邮箱或设备占用时，Edge 把明确的启动拒绝压成 `INTERACTION_INTERNAL_ERROR`，授权状态停在 `authenticating`，客户只能看到永久“鉴权中”。系统需要保留 API-only 快路径，同时把浏览器占用诚实呈现为可恢复的人工阻塞状态。

## What Changes

- 保持并明确视频号启动的浏览器无关快路径：本地加密会话通过身份校验和所有已启用只读探针后，直接进入 API-only 正常运行，浏览器保持关闭。
- AdsPower provider 将稳定的 “profile is being used by … and is not allowed to open” 拒绝分类为结构化的 profile 占用错误，并只携带脱敏后的占用方提示。
- 视频号授权协调器在 profile 被占用时退出 `authenticating`，进入 `reauth_required`，上报 `browserState=unavailable` 和稳定原因码 `INTERACTION_BROWSER_PROFILE_IN_USE`；不得把占用冒充仍在鉴权或鉴权成功。
- Cloud 接受、持久化并原样投影新的授权原因码；Edge 客户工作区显示“浏览器环境被占用”、历史可读与写操作暂停，并提供显式重试入口。占用方只允许在 Edge 安全日志中以脱敏提示出现，不进入 Cloud 或客户 API。
- 同步 Edge/Cloud 协议类型、校验、fixture 与 `docs/protocol.md`，增加占用、脱敏和解除占用后重试成功的回归测试。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `pluggable-browser-provider`: AdsPower profile 占用拒绝必须结构化分类，并且占用方只能以脱敏提示向上游传播。
- `wechat-channels-interaction`: API-only 校验成功不启动浏览器；补授权浏览器被占用时必须进入明确、可重试且 fail-closed 的授权状态并投影到客户工作区。

## Impact

- Edge：`src/cdp/browser-provider.ts`、视频号 sidecar/授权状态机、互动协议校验、Electron 客户工作区与聚焦测试。
- Cloud：互动协议镜像、授权状态解析/持久化/客户 API 投影与契约测试；不新增数据库迁移。
- Control：OpenSpec delta、`docs/protocol.md` 与冻结 fixture/契约说明。
- 安全边界：不记录原始 Cookie、请求上下文或未脱敏邮箱；profile 占用期间所有写能力继续关闭，且不自动强制抢占或关闭其他设备上的浏览器。
