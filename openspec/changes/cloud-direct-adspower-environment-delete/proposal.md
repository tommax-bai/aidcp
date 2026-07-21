## Why

当前管理后台删除环境要先创建 Cloud 删除申请，再等待匹配 Edge 客户端轮询、认领和回执；这让一次明确的管理员删除依赖客户端在线与版本，流程和页面状态都过于复杂。改为 Cloud 直接调用服务端可达的 AdsPower Local API，并且只在 AdsPower 明确删除成功后收口 AIDCP 环境状态，可以缩短链路同时保留真实成功边界。

## What Changes

- **BREAKING**：管理后台逐环境确认后，由 Cloud 在同一次请求链路直接调用 AdsPower `user/delete`；不再创建等待 Edge 的删除责任，不再依赖 Edge maintenance poll/claim/result 或客户端 outbox。
- AdsPower 返回明确成功后，Cloud 才把环境标记为 deleted、移出有效环境与账号摘要；AdsPower 不可达、未配置、鉴权失败或业务失败时保留 AIDCP 环境并返回真实失败。
- 为重试处理“AdsPower 已删但 Cloud 收口失败”的窄窗口：Cloud 仅在同一服务端 AdsPower API 通过 profile 查询明确证明 envKey 不存在时，才把重试收敛为成功；未知或查询失败不得当作已删除。
- 复用 Cloud 现有加密凭据存储保存 AdsPower API Key。管理后台设置页展示配置状态、来源与掩码，允许整段覆盖保存，但绝不回显明文。
- AdsPower API 地址由 Cloud 服务端配置（默认 Local API 地址，可用环境变量覆盖），不交给浏览器提交；API Key 在删除时按需从加密存储读取，保存后无需重启 Cloud。
- 环境页删除成功后直接提示完成并刷新；失败则显示服务端真实原因，不再出现“请求已受理 / 等待客户端删除”等文案。既有精确 envKey 确认、单环境操作、账号数据不随环境删除和软删除审计继续保留。

## Capabilities

### New Capabilities

- `admin-environment-direct-deletion`: Cloud 直调 AdsPower、成功后收口 AIDCP 环境、失败保持原记录以及幂等重试的完整管理删除契约。

### Modified Capabilities

- `adspower-environment-provisioning`: 管理后台仍是逐环境精确确认的允许来源，但远程删除执行方从 Edge 改为 Cloud，并移除远程删除对客户端 maintenance 链路的要求。
- `console-panel-api`: 环境删除端点改为返回 AdsPower 调用后的写后真态，并通过现有平台配置接口提供 AdsPower 密钥的非明文状态与加密写入。
- `model-provider-config`: 平台凭据目录增加 AdsPower API Key，设置页以掩码展示、加密保存并支持运行时热读取。

## Impact

- `aidcp-cloud`: 新增受限 AdsPower 删除客户端；重构 Panel 删除路由与环境删除存储事务；注册 AdsPower 平台凭据；移除客户鉴权 maintenance API 依赖和服务端相关调度状态。
- `aidcp-console`: 设置页增加 AdsPower API Key 项；环境删除改为直接成功/失败反馈并简化生命周期文案和类型。
- `aidcp-edge`: 远程删除不再使用 environment-maintenance poll/claim/result 与 outbox；本地桌面逐个二次确认删除仍保留。
- 运行环境：Cloud 必须能访问一台已启动的 AdsPower Local API；仅保存 API Key 不会自行创建可达的 AdsPower 服务。默认 `http://local.adspower.net:50325`，可由服务端环境变量覆盖。
