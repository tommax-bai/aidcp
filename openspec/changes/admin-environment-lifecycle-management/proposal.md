## Why

管理后台目前只有按账号运营的列表，以及藏在端用户归属抽屉里的环境注册表片段，无法从环境视角查看挂载账号、账号风控、分组和真实生命周期；账号页也无法区分“无环境”“环境删除中”和“仍有可执行环境”。现有本地删除还缺少跨 Cloud、Edge、AdsPower 的 HTTP 状态闭环，可能留下 Cloud 仍显示有效、AdsPower 已不存在的幽灵环境。

## What Changes

- 在管理后台「账号」分组新增独立“环境”页面，按环境展示 AdsPower 环境身份、挂载账号基本信息、账号风控、所属分组、端用户归属、Edge/AdsPower 观测状态和删除生命周期。
- 在账号页增加环境可用性摘要；只统计未删除的当前挂载环境，删除中的环境单独标记，删除最后一个环境不删除账号、不清风控、不伪造运营暂停。
- 增加内部 Panel 环境投影与异步删除申请 API。Cloud 只写 `desiredState=deleted` 并冻结新调度，AdsPower 成功或权威承载 Edge 明确回报不存在前不得显示“已删除”。
- Edge 使用客户鉴权 HTTP 主动拉取定位到本 installation 的维护责任，停止本地运行后调用既有 AdsPower `user/delete`，再以幂等 HTTP 回执写回真实结果；不新增 Cloud→Edge WebSocket 删除消息，也不把删除纳入自动化引擎命令。
- 环境注册表保留软删除审计、最后确认挂载账号和失败原因；已删除环境默认不进入有效环境数量，但可在环境页历史筛选中查看。
- 区分 AdsPower 环境名与账号显示名，并给挂载关系增加确认时间/状态，Edge 离线时显示“上次确认挂载”而非实时真态。

## Capabilities

### New Capabilities

- `admin-environment-lifecycle`: 管理侧环境资产页面、账号反向环境摘要、环境生命周期投影、删除确认与诚实状态展示。

### Modified Capabilities

- `client-customer-auth`: 增加 Edge 通过客户鉴权 HTTP 拉取环境维护责任、声明稳定 installation 身份并幂等回写 AdsPower 删除结果的收窄接口。
- `adspower-environment-provisioning`: 将管理后台逐环境二次确认产生的 Cloud 期望状态纳入允许的删除触发源，同时保持 AdsPower 写 allowlist、逐个删除和禁止陈旧本地状态自动删除。
- `console-panel-api`: 增加内部环境资产投影、删除申请/状态读取和账号环境可用性摘要，保持受内部 JWT 保护和写后真态。

## Impact

- `aidcp-cloud`: 环境注册表 additive 生命周期字段/删除申请存储、Panel 环境与账号投影、客户鉴权维护拉取/claim/result API、调度排除闸和审计。
- `aidcp-edge`: 稳定 installation 标识、HTTP 维护轮询、删除责任领取、AdsPower 删除执行、持久化结果 outbox 与启动恢复；不改 WS protocol v2。
- `aidcp-console`: `/environments` 路由与页面、账号环境摘要列、删除影响预览/二次确认及状态轮询。
- `aidcp`: OpenSpec 规格、验证证据与必要的架构说明；不构建 Edge 安装包。
