## Why

Edge 已经在本机安全能力可用时加密保存最近一次成功登录的 `name + key`，但客户令牌失效后再次启动仍停在登录门，要求用户手动提交同一份凭据。客户端应使用这份既有加密记忆完成一次有界的启动恢复，同时继续服从服务端鉴权、停用和限流结果。

## What Changes

- 客户鉴权启用时，Edge 启动先恢复仍有效的客户令牌；令牌本地过期或被服务端拒绝时，再读取当前 `userData` 下的加密凭据并自动登录一次。
- 自动登录成功后保存新令牌并继续既有客户范围校验和主界面启动流程。
- 无凭据或自动登录失败时停在登录门，不循环重试；明确的凭据拒绝清除失效记忆，网络或限流失败保留记忆供用户手动重试。
- 显式退出登录继续清除令牌与加密凭据，确保用户主动退出后下次启动不会自动登录。
- 不延长客户 JWT 时长、不新增明文凭据存储、不改变 Cloud API、WebSocket 协议或客户端内部业务界面。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `edge-client-login-gate`: 扩展启动登录门与本机加密凭据记忆契约，使无效 Token 可以在启动期触发一次安全、可停止的自动登录。

## Impact

- **aidcp-edge**：客户会话启动编排、登录请求复用逻辑及对应 Electron 测试。
- **aidcp control**：`edge-client-login-gate` 的 OpenSpec delta 与交付记录。
- **不受影响**：Cloud 客户鉴权接口、JWT TTL、客户范围权威校验、Console、协议与安装包发布流程。
