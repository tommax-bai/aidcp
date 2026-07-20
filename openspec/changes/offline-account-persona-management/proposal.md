## Why

账号人设的读取、生成和保存都发生在 Cloud，但 Electron 目前把这些请求绕经正在运行的环境 core 与 WebSocket，导致停止环境只能看到“去启动”，也无法核对或调整已有人设。客户鉴权 API 已具备按 `envKey` 复核客户归属并解析持久账号绑定的能力，现在可以移除这层偶然的引擎在线依赖，同时保持账号身份与写入真态仍由 Cloud 决定。

## What Changes

- 为客户鉴权 API 增加环境级人设读取、草稿生成和确认保存能力；客户端只提交 `envKey` 与受控输入，Cloud 复核客户归属并解析真实 `accountId`，响应不暴露账号键。
- 把人设生成幂等、输入/平台校验、现有人设单写通道和首次绑定引导收口为 WebSocket 与客户 HTTP 共用的 Cloud 服务，避免两条入口语义漂移。
- 新版 Electron 在环境未启动时也可按需读取人设真态；已设置账号先展示精简的人设摘要与折叠完整定义，未设置账号直接进入现有偏好向导。
- “调整人设”复用现有选择、生成草稿、预览确认流程，并尽量从当前人设预填语言、语气、内容方向与点赞倾向；确认后整体替换，保存失败保留原人设并显示真实原因。
- 旧版 Edge 使用的 `persona.generate` / `persona.persist` WebSocket 请求继续兼容；新版人设界面无论环境是否运行都使用同一 customer-auth HTTP 路径。
- 已归属但从未成功建立账号绑定的环境以 `binding_unknown` 明示“首次启动并登录一次”，MUST NOT 从本地环境名、缓存或导入资料猜测账号身份。

## Capabilities

### New Capabilities

<!-- None. This change extends existing persona, customer-auth, and companion capabilities. -->

### Modified Capabilities

- `client-customer-auth`: 增加客户范围内、按环境解析账号的人设读取、生成和保存 API，并保持 fail-closed 归属边界。
- `persona-keyword-generation`: 人设生成与保存不再要求环境 core 在线；HTTP 与旧 WebSocket 入口共用生成幂等和写入语义。
- `account-persona-config`: 客户端可读取当前账号真实人设并经既有校验单写通道更新，未绑定状态不得把打包模板冒充成当前人设。
- `edge-companion-ui`: 人设浮层在停止环境中也能显示真态、查看摘要和调整人设，网络在途、失败与未绑定状态保持诚实。

## Impact

- `aidcp-cloud`: customer-auth 环境级路由、共享人设应用服务、现有 WebSocket handler 装配与相关单元/验收测试。
- `aidcp-edge`: 具名 preload/IPC customer-auth 桥、人设浮层状态与摘要视图、按环境隔离的读取/草稿/保存反馈及回归测试。
- `aidcp` control repo: OpenSpec delta 与验证证据。
- 不新增数据库表或迁移，不改 `persona_config` 结构，不改协议 v2 类型，不改 Console，不构建 Edge 安装包。
