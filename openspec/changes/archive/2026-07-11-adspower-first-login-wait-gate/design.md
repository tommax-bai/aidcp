# Design — adspower 首次登录等待门 + 诚实停手真退出

## 结论（不重写身份/启动栈）

身份读取栈本身是好的、诚实红线也守得住：`readSelfIdentity` 只在读出形态合规稳定 id 时才 `ok:true`，读不出诚实 `ok:false`，`decideHandshakeIdentity` 绝不猜、绝不回落 `default`（`self-identity.ts:99-114`）。缺陷**不在读取本身**，而在两处**接线**：

1. **启动期把「登录尚未建立」当成了「登录已完成但读不出」**——前者对全新分身首登是常态、操作者正在扫码，应等；后者才是终态。当前一次性读取不区分二者，未登录即 `halt`。
2. **`halt` 的「诚实停手」没真退出**——`process.exitCode=1` + bare return，被 IPC/stdin 常驻句柄钉死成僵尸。

## 根因链（已代码核实，见 proposal §Why）

attach → 只读一次身份（`main.ts:192`）→ 未登录 `halt`（`main.ts:194-206`：`session.close()` + `exitCode=1` + `return`）→ 进程带 IPC（`main.cjs:1116` stdio 第4路 + `main.ts:103`）+ stdin readline（`main.ts:185`）→ 事件循环钉死、**进程不退挂僵尸** → `child.on('exit')` 不触发 → 有界重起（`fleet.decideRespawn`）**从不 engage** → 无人再读随后完成的登录 → 卡死。手动「启动」空操作（僵尸 `handle.child` 在，`main.cjs:1578` early-return）；「重新登录」SIGTERM 强杀才恢复。

## 方案选择：核心内等登录门（否决壳侧门）

**选 A：核心内「等登录」门。** 门控用**可判定条件**：provider 无壳侧登录门（`adspower`）+ 启动期首读 + 判定 `halt`（**不**试图在首读时区分「登录尚未建立」vs「已登录但读不出」——身份读取只回自由文本原因、`allowNavigate=false` 下两者返回相同失败，无结构化判据；确凿登出由超时兜底）。命中即核心**不 `session.close`**、保持 CDP 附着，进入有界耐心循环，每 ~5s 用 `readSelfIdentity(allowNavigate=false)` **只就地重读**；读出形态合规真 id 即无缝续跑既有握手；超时（默认 ~5min、env 可调/可关）走**真退出**（见「必做 2」）。

**超时 = 干净停止、不自动重起。** 关键修正：超时**不能**走会触发看护重起的可重起码——`fleet.cjs:197` 的 `baseStreak` 只在 `uptimeMs≥healthyUptimeMs`(60s) 时归零，而 ~5min 等待远超 60s → 每轮 streak 归零 → 连续失败上限（`fleet.cjs:200` give-up）**永不命中** → 永不登录的节点会「起浏览器→等 5min→退→重起→再等 5min」无限循环、每轮真起一次 AdsPower 内核，违反 `edge-node-supervised-recycle`「连续失败达上限诚实放弃」。故超时以**干净停止码**退出（外壳标 stopped、操作者经「启动」再触发）。且「靠 respawn 再读一次」本就站不住：若核心内每 ~5s 就地重读都接不住已完成的登录，重起到同一附着目标也接不住。正常路径完全靠核心内等待。

**否决 B：壳侧登录门。** 壳要自己判登录态就得自己调 `browser/start` 读 cookie，直接撞 `pluggable-browser-provider`「浏览器生命周期由核心单写」硬红线（`ads-write-api.cjs` 硬抛），且壳结构上拿不到核心动态分配的 CDP 端口；退化成红线安全版又多一条 IPC 回传 + **第二个身份真相源**（cookie 启发 vs 核心 `readSelfIdentity`，易发散、软登出会假放行），还完全没碰僵尸根因。

## 两条必做（不做则触红线、bug 复活）

1. **等待期可即时中断（收窄到 IPC 生命周期命令路径）**：等待落在生命周期信号未接线的启动早窗——唯一会被搁置的是**经 IPC 堆进 `pendingLifecycleCommands`**（`main.ts:101-107`）的暂停/关闭，直到握手后 `dispatchLifecycleCommand`（`main.ts:874`）就绪才派发、最长整个超时无响应。故等待循环须**主动排空/拦截该 IPC 队列**、收到暂停/关闭即时中断收口。**无需接管 `SIGINT`/`SIGTERM`**：早窗内自定义信号处理器尚未注册（在 `main.ts:898-899` 才装），信号走 Node 默认处置＝立即终止、本就即时不被搁置；临时装卸信号处理器反是易错的多余接线。早窗中断一律以**干净停止**码退出（无运行中账号会话可暂停、adspower 浏览器外部托管不随进程退出而关），操作者经「启动/恢复」再来。
2. **收口端点真退出**：置可重起退出码 → 关闭 stdin 控制读取器 + 断开/关闭 IPC 通道（`process.disconnect` / 移除 `message` 监听）→ 必要时 `process.exit`。**绝不**沿用 bare-return——否则 IPC+stdin 再度钉死成僵尸、原 bug 原样复活。回归测试须断言带 IPC/stdin 常驻句柄的核心在停手路径上**进程确已终止**。

## 红线核对

- **绝不静默假成功**：PASS——只在读出真 id 时握手；等待只是把「诚实停手」推迟到窗口之后。且把今天「exitCode 置了却因僵尸不退」的**静默假死**转成明确的登录成功或诚实退出，比现状更强。
- **绝不回落 default**：PASS——等待与握手全程只用实读 id，超时零回落；`decideHandshakeIdentity` 对 `override='default'` 的禁用不动。
- **读不出即诚实停手**：PASS——停手语义不变，只在其前加一段有界等待。
- **自愈不自残 / 诚实下线**：**有条件 PASS**——仅当「必做 1（可即时中断）」+「必做 2（真退出）」都做到才成立；任一缺失 → 超时/关闭时再度僵尸=自残。故二者列为 must-fix、非可选。
- **协议 v2 四处同步 / 主动命令白名单**：PASS——不新增/改任何边-云消息类型与主动命令，纯核心启动 + 本地 IPC/stdin 生命周期层。
- **热点文件单写**：PASS——不碰 `protocol.ts` / `command-bridge` / `RoleName` / `risk-state-machine`。

## 与既有实现的正交点（保留、勿破坏）

- 等待/就地重读**复用** `readSelfIdentity`（`allowNavigate=false`），不复制身份读取逻辑；判定纯函数化、有界迭代计数（不依赖 `now()` 前进——与既有 hydrate 循环同款，防测试注入恒定时钟死循环，见 memory `edge-poll-helpers-iteration-bounded`）。**内层就地重读须用极小 hydrate 预算**（单次 `IN_PLACE_SCAN`/`hydrateTimeoutMs≈0`），MUST NOT 把 `readSelfIdentity` 默认 ~6s hydrate 轮询（`self-identity.ts:364-382`）嵌进 ~5s 外层循环，否则「即时」中断延迟退化到 ~6s。
- 等待门**严格限**可判定的 `adspower` + 启动期首读 + `halt`；`self`（已有壳侧门）与 `override` 路径逐字不动。
- `AIDCP_ADSPOWER_LOGIN_WAIT_MS`（或同义名）默认 ~5min、可调可关。**看护/headless 与 adspower 的现实关系**：命令行多节点启动器按 `pluggable-browser-provider` 钉回 `self`，故 adspower 当前跑在**交互式桌面外壳**（操作者在场扫码）——~5min 首登等待正当其所。已登录老号被看护/外壳重起时命中持久化登录、秒级读出、**不进等待**；仅「会话过期后重起」才可能进等待，这类无人值守上下文应注入短 `AIDCP_ADSPOWER_LOGIN_WAIT_MS`（对齐 self 的 ~45s `AIDCP_CHROME_LOGIN_TIMEOUT_MS` 注入，`main.ts:153-159`），且超时走干净停止不无限重起。
- **同源停手端点仅订正不盲改**：`main.ts:194-206` 是坐实的 exitCode 僵尸（本 change 修）；`main.ts:605-609` 是**刻意 stay-alive**（不置 exitCode、有意留活不重连）＝行为决策，默认不动；`main.ts:313` 死路径。
