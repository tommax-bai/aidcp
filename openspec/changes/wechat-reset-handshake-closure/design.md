## Context

2026-07-19 dev 事故中，Cloud 在重启后先监听 8787，约一段装配流程后才赋值 `ConnectionRuntimeRegistry`。视频号 Edge 在该窗口发起 `hello` 时，`DefaultMessageHandler.onHello()` 已把 account/capabilities 写入临时 session，随后访问未就绪的 runtime 并返回 `handler_error`。`EdgeCloudServer` 对所有 hello（包括 error）都写入 `edges`，而 Edge `openAndHello()` 不校验回包类型，也把 error 当成握手完成。结果是 Cloud 可按 account/capability 解析这条连接并写入命令，Edge 却因 welcome capability 未协商而忽略 interaction 命令。

视频号测试重置进一步放大了问题：Cloud 的 `resync=accepted` 只证明 `ws.send()` 命中一个 OPEN socket；Electron 却直接显示“正在从微信平台重新拉取”。Cloud 的 `syncFreshness.receivedAt` 已能证明按渠道的新批次提交，但重置流程没有复用这条证据。

## Goals / Non-Goals

**Goals:**

- 未成功完成 hello/welcome 的连接绝不进入在线路由，也不能被 account/capability 解析命中。
- Cloud 不在握手依赖未就绪时接受 Edge 连接。
- Edge 对 error/非法 welcome fail-closed，并由既有重连/监督机制恢复。
- 测试重置把 Cloud 清空、命令投递和同步完成分开表达；完成只由目标渠道的新 `receivedAt` 证明。
- 覆盖本次真实启动竞态与错误状态文案。

**Non-Goals:**

- 不新增 WS message type 或改变 hello/welcome payload schema。
- 不修改微信私有 API、平台数据或回复发送链。
- 不实现离线重置的 Cloud 持久待办队列；本次把“联网后自动补拉”的无依据承诺改成明确要求连接恢复后重试。
- 不构建或发布 Edge 安装包。

## Decisions

### 1. 先完成 Cloud 握手依赖装配，再开放 WebSocket 监听

把 `server.start()` 移到 `ConnectionRuntimeRegistry` 构造完成之后。`EdgeCloudServer` 对象仍可提前构造并注入 sender/handler；没有监听前不会收到 hello，因此 handler 闭包引用的 runtime 在首帧前必定可用。

备选方案是在 `onHandshake` 内等待一个 ready Promise。它会让一个本应快速失败/重连的传输握手悬挂在启动过程，还保留“监听已开但服务未 ready”的模糊窗口，因此不采用。

### 2. Cloud 仅登记成功 welcome，失败 hello 回包后关闭

`EdgeCloudServer` 只有在 `reply.type === 'welcome'` 时写入 `edges` 并触发注册回调。解析失败、handler error 或配置拒绝均返回 error，且该 socket 随即关闭。在线解析继续只读 `edges`，不需要新增第二套状态。

这条防线独立于启动顺序：即使未来其他握手依赖再次失败，也不会产生可路由幽灵连接。

### 3. Edge 强校验 hello 响应

`openAndHello()` MUST 要求 response type 为 `welcome`，payload 含非空 `sessionId`；否则抛出握手拒绝错误，不能设置 `hasCompletedHello`、peer capabilities 或 runtime controls。重连路径沿用既有有界退避，初次启动沿用 supervisor 的进程失败恢复。

仅检查 `sessionId` 而不检查 type 不足以防未来 error payload 偶然出现同名字段，因此 type 与关键 payload 同时校验。

### 4. 测试重置以 syncFreshness 推进确认完成

Electron 点击重置前记录目标渠道当前 `syncFreshness.receivedAt`：

- `resync=skipped`：显示 Cloud 已清空但命令未送达，要求连接恢复后再次重置；不承诺自动补拉。
- `resync=accepted`：显示“重拉请求已发送，等待同步结果”，登记目标渠道 baseline。
- 后续 list/detail 中目标渠道 `receivedAt` 严格大于 baseline：显示该渠道重新拉取完成并清除 pending。
- 证据未推进：继续保持等待，不以 HTTP 200、`meta.asOf`、在线标志或列表空态判完成。

多个渠道连续重置时按 channel 保存 baseline，分别完成，避免后一次覆盖前一次等待状态。

## Risks / Trade-offs

- [Risk] 移动监听时机使 8787 比当前晚数秒可用。 → Edge 已有重连；Cloud 健康只有在装配完成后才应对外可用，这个延迟是正确的 readiness 语义。
- [Risk] 失败 hello 立即关闭可能暴露旧 Edge 的协议错误。 → 旧 Edge 本就无法安全协商；关闭并重连比保留不可用连接更诚实。
- [Risk] 重置收到空结果时只有 DM 保证产生空 checkpoint batch，评论 reader 的空 post 列表目前可能不产生 batch。 → UI 保持“等待同步结果”而非伪造空完成；评论空读证据完善属于后续独立 reader 契约，不在本次扩大。
- [Trade-off] 离线清空后需要连接恢复再点一次重置。 → 当前 Cloud 未持久化待执行 reset，宣称自动补拉是错误的；先修正文案，若要自动化需新增可靠 outbox。

## Migration Plan

1. 先合入 Edge 的 welcome 校验和重置状态修复；不打包，当前 unpackaged dev 客户端重启后生效。
2. 合入 Cloud 启动顺序与 hello 登记修复，部署到 `dev`。
3. 部署后确认服务只在 runtime registry 就绪后监听，失败 hello 不进入在线计数；重启视频号环境建立干净 welcome。
4. 只在用户界面确认连接恢复后重新执行测试重置；不自动触发平台读取或数据删除。
5. 回滚时可分别回滚 UI、Edge hello 校验和 Cloud 握手修复；无数据迁移。

## Open Questions

- 无。评论“平台返回零 post 时是否也发送全局空批次”另立小变更，不以本次 UI 假完成修复顺带改变 reader 批次语义。
