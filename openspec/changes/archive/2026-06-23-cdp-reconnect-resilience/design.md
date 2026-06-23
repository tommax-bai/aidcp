## Context

边缘端通过原生 WebSocket 连本机 Chrome DevTools（CDP）驱动小红书浏览。整场会话只挂**一条**连到某个 page target 的 WS（`session.ts:44-47`）。该 WS 意外关闭时，`CdpClient` 仅 `failAllPending` + 置 `connected=false`（`client.ts:105-108`），此后 `send()` 直接 reject（`client.ts:115-117`）；浏览循环各 handler 对 `cdp.send` **零 try/catch**，异常冒泡到 `main.ts` 仅打印——整段会话静默死。真机校准多次复现（间歇、与开 note 时段相关）。

关键约束（已逐条核对代码）：
- `CdpClient` 实例被约 10 个消费者**按引用**持有（`main.ts:180,205,239,243,245,247,301` 把同一 `session.cdp` 喂给 scroller/modalCtrl/overlayMonitor/notificationMonitor/fileInputSetter/publishDispatcher/BrowseSession）。
- 边↔Chrome 的 CDP WS 与边↔云 8787 会话 WS 是**两条物理无关连接**；CDP 断开期间云端 `sessionId` 不变、云端无感。
- 云端 `edge.hello → restartSession()` 会**无条件** `freshBudget()`（互动额度满血）+ 清 `searchedKeywords` + `sessionContext.reset()` + 重置 `sessionStartedAt`（`role-dispatcher.ts:386,446-471`）。
- 云端 idle 看门狗：`idleNudgeMs=130_000` 发盲 nudge、`idleEndMs=240_000` `triggerEnd`（`session-monitor-role.ts:62-63,127-139`）；`lastActivityAt` 由边缘上报（page.cards/note.detail/action.completed/notification.*）刷新。
- 协议层**没有** edge→cloud 终止消息类型；`session.end` 仅 cloud→edge，云端入站 switch 无该 case（`handler.ts:134-270`，落 default 退 `unsupported_type`）。
- 反检测前置脚本 `Page.addScriptToEvaluateOnNewDocument` 绑在那条 WS 的 CDP session 上（`stealth-injector.ts:269`），换 WS 即失效。

## Goals / Non-Goals

**Goals:**
- CDP WS 意外关闭 → 有界退避重连：重发现当前小红书页 target（域名硬过滤）→ 重连 → 重 enable 域 + 重注入反检测 → 续跑浏览循环，而非结束会话。
- 重连内化进同一 `CdpClient` 实例（保实例、换内层 WS），所有按引用持有者零改动随之复活。
- 对云端透明续跑：绝不重发 `edge.hello`、绝不触发会话/预算重置；重连总时长有**运行时硬上限** ≪ 130s，不被看门狗误杀。
- 诚实失败：重连耗尽 → 停止上报 + 退出循环，云端 240s idle 看门狗兜底终止；绝不假成功、不空转占会话假装在跑。

**Non-Goals（YAGNI / 明确不做）:**
- 浏览器级 endpoint + `Target.attachToTarget({flatten})` 重构（`send` 带 sessionId）——留作扩展缝，本变更走页级重连止血。
- 心跳/保活——回环断连确定性触发 `close`（已监听 `client.ts:105`），命令级 10s 超时已兜底（`client.ts:121-124`），纯增复杂度。
- `setAutoAttach` 自动附着子 worker/iframe/OOPIF；多 target 常驻订阅（`setDiscoverTargets` 常开）；`targetCrashed` 崩溃/断连双语义（对本系统都是一次 WS close，走同一重连）。
- 协议改动 / epoch 字段；动作级幂等重放；把重连次数上报为风控软信号；**主动 edge→cloud 终止信号**（需协议三处同步，列为未来扩展）。
- 「上层持续回写精确页 URL」状态层——重发现用 `/json` 的 target `url` 字段 + 域名硬过滤即可（`targets.ts:13,41-53`），不引入跨组件状态同步。

## Decisions

**D1. 重连内化进 `CdpClient`（保实例换内层 WS），不让 BrowseSession 重建 client。**
重建 client 须重新穿线 ~10 个持有者，漏一个即拿死引用；尤其 `WatcherSupervisor` 下 overlay/notification 监测体因 `sticky` 容错会永远轮询死的旧 client、永不翻转（captcha/未读上报全失灵）。内化后所有按引用持有者零改动随实例复活。
- 备选（否决）：BrowseSession 监听 close 后重建并重新注入全部依赖——改动面大、易漏引用。

**D2. 有界退避状态机 + 运行时硬上限计时器。**
`base=500ms / max=8000ms / maxAttempts=5`，纯退避 sleep 之和 ≈15.5s。但 `connect()`+`onReconnected`(多次 enable+inject 往返)+`/json` HTTP 各有真实耗时，故**不靠纸面相加**——加一个**总时长硬上限计时器**（如 ≤90s，到点强制 `unrecoverable`），保证即使单步变慢也绝不撞 130s 看门狗。
- 区分**主动 close vs 意外 close**：`close()` 置 `intentionalClose=true`，仅意外 close 触发重连。

**D3. 对云端透明续跑——绝不重发 hello。**
CDP 断连云端无感（两条无关连接）。走 `edge.hello → restartSession` 会把毫秒级 Chrome 抖动放大成「互动额度满血复活 + 可重刷同批笔记 + 风控水位（账号级持久滑窗）与会话预算脱节」，直接违红线。`welcome` 不带 epoch（`handler.ts:273-287`），只要边缘不重发 hello，云端零改动透明续跑。协调铁律 = **CDP 重连绝不触碰边-云 WS**。

**D4. 诚实失败走云端 idle 看门狗兜底（不碰协议）。**
重连耗尽 → 停止一切上报 + 退浏览循环（复用现成本地终止：`browse-session.ts:293` 合成 `session.end` local-stop，加 `reason:'cdp_unrecoverable'` 变体）→ 云端 240s idle 看门狗 `triggerEnd` 自然收尾。
- 备选（否决，对抗评审 A1）：边缘**主动**发终止信号告知云端。核对代码：edge→cloud **无终止消息类型**，硬发会被云端当未知消息退回（`handler.ts:265-269`）。主动信号需新增协议类型 + 三处同步，违「不碰协议」承诺——**列为未来扩展**，本变更默认走看门狗兜底（≤240s 占用一条会话，不违任何红线）。

**D5. 续跑「连接」而非「业务进度」。**
丢弃断连瞬间 in-flight 命令、**不重放**（坐标/锚点可能失效，盲放是「静默假成功」温床）；断连时正在执行的动作如实回报 `ok=false`/`no_target` 交云端决策。重连成功后：先判当前真实 URL（用 `/json` 的 target url）→ **先过 `waitWhileBlocked()` 浮层闸门**（对抗评审 B2：重连可能落在登录/验证码浮层上，域名过滤通过但页面被盖住；与冷启动 `browse-session.ts:401` 入口同口径）→ 按当前页重报 `page.cards`/`note.detail` 让云端重判。重报 page.cards 同时自然刷新云端 `lastActivityAt`。

**D6. in-flight 命令竞态用带标记错误类型区分。**
重连态下 `send` 抛**带标记的 `CdpDisconnectedError`**（而非现 `client.ts:116` 泛化 `Error('CDP 未连接')`）；BrowseSession 在 `executeCommand` 外层薄包裹**仅对该类型**走「等重连（有界）→ 丢弃命令 → 重报快照」，其他业务异常仍按现有失败语义走（对抗评审 B3：别把定位失败误当连接问题空等重连）。

**D7. 主动 close 抢占重连退避循环。**
退避循环每次 `await sleep` 后、`connect` 前检查 `intentionalClose`/取消标志，命中即终止重连、不再建新 WS（对抗评审 B4：重连退避中途上层 `close()`，否则会在已决定终止后又建一条新连接）。

**D8. re-enable + re-inject 抽成单一函数，首次 attach 与重连共用。**
`Runtime.enable` / `Page.enable` / `Input.enable`（`main.ts:98` 重连后须补，否则坐标点击失效）+ `injectStealth`（`stealth-injector.ts:269`）。重注入**幂等无叠加**：addScriptToEvaluateOnNewDocument 注册随旧 WS 死亡消失，新 WS 是全新单次注册（对抗评审 D 澄清）。

## Risks / Trade-offs

- [重连落在登录/验证码浮层上被误当「健康」] → 续跑前先过 `waitWhileBlocked()`（D5/B2），与冷启动同口径；写进 spec scenario。
- [in-flight 命令副作用已部分发生（如 note 已打开）] → 不重放、靠 D5 按当前真实 URL 重报纠正（在详情页就重报 note.detail）；`noteOpenedAt` 清零保守重计 dwell（多停留，不假成功）。
- [重连总时长撞 130s 看门狗] → D2 运行时硬上限计时器，不靠纸面相加。
- [重连频繁吃掉浏览节奏] → 当前 YAGNI；若真机出现高频重连，再考虑把重连计入节奏/风控软信号。
- [诚实失败靠看门狗兜底，云端多占一条会话 ≤240s] → 可接受，不违红线；主动终止信号待协议扩展再做。
- [attach 到错误 tab（about:blank/残留空白页）] → 域名硬过滤 `xiaohongshu.com`，不落 `pages[0]`（`targets.ts:41-53`）。

## Migration Plan

仅 edge、纯增量、缺省关闭（`CdpClientOptions.reconnect` 不传即零行为变化、单测纯净）。装配处（`main.ts` / `attachToPage`）显式开启即生效。无数据/协议迁移；回滚 = 装配处不传 reconnect 配置。

## Open Questions

- 运行时硬上限取值（暂定 ≤90s，留足重连又远离 130s）——实装时按真机重连真实耗时微调。
- 多个小红书 page target 并存（异常态）时的选择启发——当前取域名匹配的首个；若真机出现多 xhs tab 再加 title/url 启发（扩展缝）。
