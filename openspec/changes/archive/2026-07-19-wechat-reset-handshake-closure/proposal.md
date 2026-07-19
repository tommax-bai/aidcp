## Why

Cloud 重启时会先开放 Edge WebSocket 监听，稍后才初始化连接运行时。Edge 若在该窗口发送 `hello`，Cloud 会返回 `handler_error`，但双方仍可能把这条失败握手连接保留为“在线”；后续视频号测试重置因此把“写入幽灵 socket”误报成“正在重新拉取”，实际没有任何平台读取或同步证据。

## What Changes

- 收紧 Edge/Cloud 握手准入：只有成功返回并校验 `welcome` 的连接才能进入在线路由，失败握手必须关闭并重连。
- 消除 Cloud 启动竞态：连接运行时和握手依赖就绪后才开放 WebSocket 监听。
- 将传输准入与业务运行时激活拆开：无人设、调度暂停、无 browse 能力或角色初始化失败只能让业务保持受限，不能把身份/平台合法的连接升级成握手失败。
- 视频号 interaction-only 连接不构造浏览 `RoleDispatcher`、不读取人设；XHS/FB 无人设时保持在线并回传未绑定真态，由客户端弹出人设引导而不是反复重连。
- 同 `edgeId` 顶替只在新连接成功 welcome 后发生，失败候选不能提前关闭旧健康连接。
- 让视频号测试重置区分 Cloud 清空、重拉命令投递和真实同步完成；`accepted` 不再被展示为已开始或已完成。
- 复用按渠道 `syncFreshness.receivedAt` 作为完成证据；无推进时保持等待/失败真态，不伪造重新拉取。
- 增加启动窗口、错误 hello、幽灵连接不可路由、重置证据推进等回归测试。

## Capabilities

### New Capabilities

- `edge-cloud-handshake-admission`: 定义 Cloud/Edge 对成功 hello/welcome、启动就绪和在线路由登记的 fail-closed 契约。
- `wechat-test-reset-completion-honesty`: 定义视频号测试重置从 Cloud 清空到 Edge 重读完成的分阶段状态和同步证据口径。

### Modified Capabilities

- 无。

## Impact

- `aidcp-cloud`: 启动装配顺序、WebSocket hello 登记、welcome 后业务激活、同 edge 顶替及相关测试。
- `aidcp-edge`: hello/welcome 校验、自动重连、视频号互动工作区重置状态及相关测试。
- `aidcp`: 新增 OpenSpec 变更、行为契约和交付证据。
- 不修改微信平台数据，不发送回复，不增加协议消息类型，不构建 Edge 安装包；Cloud 运行时修复完成后部署到 `dev`。
