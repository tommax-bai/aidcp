## Why

真机上同时暴露的两个 bug，根因是同一类错误：**把「我还不知道」当成「我知道，答案是否」**。两者共用同一个触发器——冷待机唤醒。

**① 冷待机关浏览器时把浏览循环撕断。** 外壳打「浏览器已关闭进入冷待机」13 秒后，日志出现 `CdpDisconnectedError: CDP 未连接` 的「浏览会话异常」。`enterStandby()` 调 `browse.close()`（只是**请求**停止、不等）后立刻杀浏览器；若循环恰好停在启动段——那段既不看停止标志、也不在断连处理域内——它醒来后照样摸页面，打在死 CDP 上。而 `waitForVisibleCards` 把断连 `catch {}` 吞成「卡片还没渲染好」，对着死浏览器空转满 12s 墙钟预算（`initialScanTimeoutMs`），才由 `reportVisibleCards` 真正抛出。**12s 静默把「设备没了」读成了「内容还没来」**，13 秒的缺口正是这么来的。

**② 已设置人设的账号被反复误弹人设向导**（工程师大白；弹出后面板显示「已设置」）。云端**只在为真时**下发 `personaBound`，于是边缘侧「云端说没有」和「云端还没说」压成同一个 `false`，只能靠一个 6 秒宽限去猜。而宽限期的重置代码是**死代码**——`personaUnboundSince` 的两处清理都写在只有「未绑」才走得到的分支里，账号一旦已绑，调用方早已 return。于是首次会话记下的时间戳永不被清，之后**每一次核心重启**（冷待机唤醒是最常见的一条，它会把绑定标志归零）都发现 `elapsed >> 6s` → 跳过宽限 → 在快照到达前的亚秒空窗里弹窗；快照随后到达把面板翻成「已设置」，却没有任何代码去关那个已经弹开的窗。**这是确定性的，不是偶发竞态**——所以「修了几次还复发」：三次修复都在给那个错误推断打补丁，没有一次消灭它。

（对症的那次修复 `210f386` 其实存在，但只活在 `release/20260712-ol-recut`，从未 forward-port 回 `master`——用户跑的正是 master 包，所以从来没拿到它。）

## What Changes

- **关浏览器前必须先把浏览循环排空**：`close()` 之外提供有界的 `closeAndWait()`（复用既有的原子操作排空原语），冷待机与退出/回收路径改用它；排空超时诚实告警后照常关（有界是刚性要求，否则一个卡住的动作就能把冷待机本身挂死）。
- **启动段纳入停止判定与断连处理域**：每个 await 之后复核停止请求；断连走有界重连或诚实终止，绝不再冒成「浏览会话异常」。
- **轮询辅助不再吞断连**：`CdpDisconnectedError` 立刻上抛，不再被读成「内容还没来」。
- **在途巡视命令被待机撕断时仍发诚实回执**（`ok:false`），否则云端 `excursionActive` 永真、看门狗随后杀整会话。
- **人设绑定态改为三态**：云端 `true` / `false` **都下发**，字段缺省 = 未知。云端是人设状态的唯一权威写方，它有资格诚实地说「这个账号没有人设」。
- **这个零 I/O 的 bit 从重快照里摘出来先发**（原本排在 5 个 PG/fs 往返之后），绑定/解绑后即时重推。
- **弹窗只由权威的 `false` 触发**；整套宽限期机制删除——它是那个错误推断的载体。

## Capabilities

### New Capabilities

### Modified Capabilities
- `browse-loop-resilience`: 关浏览器前的排空契约 + 启动段的停止/断连守卫 + 轮询辅助不吞断连。
- `edge-companion-ui`: `personaBound` 三态语义（true/false/未知），弹窗只由权威 false 触发。

## Impact

- `aidcp-edge`: `src/browse/browse-session.ts`、`src/browse/edge-browse-session.ts`、`src/facebook/facebook-session.ts`、`src/main.ts`、`src/comm/protocol.ts`（注释契约）、`src/flows/ui-event-lines.ts`、`src/electron/main.cjs`、`src/electron/persona-notice.cjs`、`src/electron/renderer/renderer.js`
- `aidcp-cloud`: `src/comm/ui-snapshot.ts`、`src/config/persona-facade.ts`、`src/server.ts`、`src/comm/protocol.ts`（注释契约）
- 向后兼容：旧边缘只读 `personaBound === true`，新云端下发的 `false` 被它忽略，行为与今天一致（无回归）。
- 协议消息类型数不变（`personaBound` 是 `UiSnapshotPayload` 既有可选字段），`AC-PROTO-02` 的 74 不动。
