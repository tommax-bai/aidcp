## Why

边缘端整场浏览只挂着**一条**连到某个 Chrome page target 的 CDP（DevTools）WebSocket。这条 WS 一旦被 Chrome 关闭（真机观察到的间歇性 target/连接丢失），CDP 客户端只 `failAllPending` 后置「未连接」、**无重连、无重新 attach、无心跳**，浏览循环里所有 `cdp.send` 随即抛错冒泡，**整段浏览会话静默死掉**。真机校准已多次复现：浏览中（与开 note 时段相关、间歇发生）会话提前死，无法长时间无人值守运行。已合并 spec `browse-loop-resilience`（idle 看门狗自愈、坏页兜底、不可恢复才诚实终止）尚未覆盖这一「连接层丢失」缺口。

## What Changes

- 边缘 CDP 客户端在 WS **意外关闭**时进入**有界退避重连**：重新发现当前小红书页 target（域名硬过滤）→ 重建 CDP 连接 → 重新启用所需 CDP 域并**重注入反检测脚本** → 续跑浏览循环，而不是结束会话。
- 重连**内化进同一 CDP 客户端实例**（保实例、只换内层 WS），使约 10 个按引用持有该客户端的组件（含后台监测体）零改动随之复活。
- 对云端**透明续跑**：CDP 重连**绝不**触碰边-云会话连接、**绝不重发 `edge.hello`**（避免触发云端会话/互动预算满血重置）。重连总时长有运行时硬上限，远小于云端 idle 看门狗阈值，天然不被误杀。
- **诚实失败**：重连耗尽上限 → 停止一切上报 + 退出浏览循环，由云端 240s idle 看门狗兜底干净结束会话；**绝不静默假成功、绝不空转占着会话假装在浏览**。
- 续跑语义：**丢弃**断连瞬间 in-flight 的命令（不在可能失效的坐标上盲目重放），续跑前先过现有「浮层闸门」(登录/验证码)，按当前真实页面重报结构化快照交云端重判。

## Capabilities

### New Capabilities
<!-- 无新增能力：本变更扩展既有 browse-loop-resilience 的韧性边界，不引入新概念域 -->

### Modified Capabilities
- `browse-loop-resilience`: 新增「CDP 连接丢失 MUST 有界自愈、不可恢复才诚实终止」要求——把现有「浏览闭环 MUST NOT 被永久挂起 / 不可恢复才诚实终止」的韧性边界从「页面/业务层」延伸到「CDP 连接层」。

## Impact

- **仅 aidcp-edge**：`src/cdp/client.ts`（重连状态机/区分主动 vs 意外 close/带标记错误类型）、`src/cdp/session.ts` 与 `src/cdp/targets.ts`（attach 与 target 重发现）、`src/cdp/stealth-injector.ts`（重注入复用）、`src/browse/browse-session.ts`（续跑接线 + in-flight 命令薄包裹 + 跨命令状态清理）、`src/main.ts`（装配重连配置）。
- **不碰协议 v2**：透明续跑不需要协议层标识，不动两份 `protocol.ts` / `command-bridge` / `docs/protocol.md`；edge→cloud 无终止消息类型，主动终止信号列为未来扩展（届时才需协议三处同步）。
- **不碰云端代码**：云端零改动透明续跑；`session-monitor-role` / `role-dispatcher` / `handler` 仅作协调约束的只读依据。
- **风险与红线**：保持「edge 只原样执行、不静默假成功、约束收口云端」；重连不可恢复时诚实终止，不把「已死」伪装成「健康」。
