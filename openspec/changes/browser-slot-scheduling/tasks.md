# Tasks

> **⚡ 2026-08-06 事实源已翻转（`invert-split-fact-source` cutover，用户裁定不等在飞 change）**：
> `aidcp-cloud` 的 `src/` + `migrations/` 已冻结（task-preflight 会拦任何 cloud 侧源码改动），
> `sync-split-repos --apply` 已退役。**本 change 剩余的「cloud 侧」任务改为直接落对应派生仓**
> （aidcp-api / aidcp-automation / aidcp-content；逐文件属主查 `aidcp-cloud/boundaries/module-ownership.json`，
> 常见：`src/comm/**`、`src/orchestrator/**` → automation，`src/panel/**`、`src/client-auth/**` → api）。
> 已写但未推的 cloud src 改动请在派生仓重落，**勿再推 cloud**（推了会让全 fleet 任务准入变红）。
> 新迁移直接落属主仓 `migrations/`，编号取三仓并集的下一号。跨仓测试（整图/跨属主）落 cloud `test/`
> （它现在是纯集成测试仓，test/ 不冻结）。协议红线不变：edge ↔ aidcp-automation 两份 `src/comm/protocol.ts` 逐字一致。


> 落地顺序：0（量数）→ 1（边缘核心：释放/重建/闸）→ 2（边缘外壳：槽位池/串行队列）→ 3（云端）→ 4（验收）。
>
> **实装中的一处设计修正**（2026-07-14，见 `design.md` §3）：原计划「把 19 个持有者全部改成访问器、待机时置空」。
> 代码审计后改为**保住浏览器连接对象的身份、换掉它的内层**（socket + target + 重连配置）——既有的断线重连
> 已经证明这条路可行，19 个持有者与 7 处事件订阅全程无感。安全性质没丢：连接对象在浏览器缺席时**本来就会
> 响亮报错**。改动面从 ~18 个文件降到 4 个。

## 0. 量数（决定后面的常数）

- [x] 0.1 单环境内存估值改为运营实测口径 **700MB**（旧值 1GB 是没量过的设计缺省，偏保守会白白少开 2–3 个环境）。可用 `AIDCP_PER_ENV_MB` 覆盖。<!-- aidcp-edge 7226f01 仍需真机复核稳态常驻内存 -->
- [ ] 0.2 实测**单次浏览的墙钟耗时**。这是 1:2 是否长期安全的分水岭：**若中位数 > 95 秒**（= 3600/38 小时浏览配额），小时窗永远触不到顶、冷待机不再按小时释放槽位，1:2 失效。**未做——真机项，已登记 backlog。**
- [ ] 0.3 dev 上取证：排期评论 / 加群 / 联系评论的真实失败率与失败原因分布（`cdp_unhealthy` / `edge_offline` / `browser_wake_failed` 各占多少）。**未做——需 dev 部署后观察。**

## 1. aidcp-edge — 核心：待机即释放、唤醒即重建

- [x] 1.1 浏览器层单一持有者。**实装取「保住连接对象身份」路线**：`CdpClient` 实例即那个单一持有点，其 socket / target / 重连配置可整体换代。审计确认 19 个构造期持有者 + 7 处事件订阅在此路线下全部自动正确。<!-- aidcp-edge ea0c979 -->
- [x] 1.2 进入待机 = 释放浏览器层。`CdpClient.detach()`：断 WS、进入「浏览器缺席」态、**绝不触发重连**（浏览器是我们自己关的）。释放后任何页面命令**响亮失败**。<!-- aidcp-edge ea0c979 -->
- [x] 1.3 唤醒 = 原地重建。`CdpClient.reattach()` + `reattachSession()`：重开浏览器 → 重新附着 → 重启用 CDP 域 + 重注入反检测 → 重新确认登录态与身份（**当作新的一代浏览器，不假设还登着**）→ 重挂监测体。幂等。失败即诚实回退待机（可再唤醒）。<!-- aidcp-edge ea0c979 -->
- [x] 1.4 `core-lifecycle.ts` 新增 `wake` 意图（原地重建，**不走 finalize、不退出进程**）。<!-- aidcp-edge ea0c979 -->
- [x] 1.5 统一浏览器闸 `ensureBrowserAwake()`：不在 → 请求唤醒 → 有界等待（**180s**，`AIDCP_WAKE_DEADLINE_MS` 可配，必须 < 云端 240s 空转看门狗）→ 就绪继续 / 否则诚实失败。<!-- aidcp-edge ea0c979 -->
- [x] 1.6 接上任务受理与发布这两个漏网入口（`onEdgeTaskCommand` / `onPublishCommand` 此前**完全没有**待机守卫）。<!-- aidcp-edge ea0c979 -->
- [x] 1.7 `cdp_unhealthy` 与「停泊缺席」分离。协调器新增 `browserAbsent` / `requestWake`；停泊走唤醒路径，唤不醒回**独立**的 `browser_wake_failed`。<!-- aidcp-edge ea0c979 -->
- [x] 1.8 释放 ⊥ 在跑租约。`EdgeTaskCoordinator.hasActiveLease()`；冷待机据此拒绝进入（绝不把浏览器从正在执行的任务底下抽走）。<!-- aidcp-edge ea0c979 -->
- [x] 1.9 待机排空改用**非终态**的 `stopAndWait()`（`closeAndWait()` 的 closing 是终态、唤醒后再也起不来）。<!-- aidcp-edge ea0c979 -->
- [x] 1.10 向云端如实上报**已启动核心**的「在线但浏览器缺席」：`hello` 携初始 `browserState`，同一连接内以 `browser.status` 上报 `absent ↔ ready` 变化；该能力服务真实冷待机，不作为首次排队预启动核心的理由。旧 Edge 缺字段时保持兼容。<!-- aidcp-edge b5b9192; edge-client 51/51; acceptance 39/39; typecheck pass; full suite passes with the pre-existing manual-environment-nickname-ipc baseline failure excluded -->
- [x] 1.11 单测：释放后页面命令响亮失败且不触发重连；重建保住实例身份与订阅、并换掉重连配置；重建失败回缺席态；停泊走唤醒 / 唤醒失败回 `browser_wake_failed` / 真故障仍回 `cdp_unhealthy` / 唤醒中重复请求不重复唤醒 / 租约互斥。<!-- aidcp-edge ea0c979 -->

## 2. aidcp-edge — 外壳：槽位池 + 串行启动队列

- [x] 2.1 唤醒不再 `stopAndRestart`：改为下发 `lifecycle.wake` 原地重建；核心不在（IPC 不可用）才退回冷启。待机态**只在核心回报 `lifecycle.woken` 后才解除**（绝不在下发那一刻乐观标成已醒）。<!-- aidcp-edge ea0c979 -->
- [x] 2.2 槽位池：上限 = ⌊可用内存 ÷ 700MB⌋（`AIDCP_BROWSER_SLOTS` 可覆盖，至少 1）。槽位只由冷待机自然释放，**不抢占、不踢人**。<!-- aidcp-edge 7226f01 -->
- [x] 2.3 串行启动队列 `createSerialLaunchQueue`：**起完一个再起下一个**（等到浏览器起来 + 云端连上，或诚实失败）。<!-- aidcp-edge 7226f01 -->
- [x] 2.4 内存准入闸搬进队列，**全路径覆盖、无法绕过**（旧版只长在「全部启动」按钮上；单启 / 唤醒 / 崩溃重起全部绕过）。<!-- aidcp-edge 7226f01 -->
- [x] 2.5 队列优先级：手动 > 带任务的唤醒 > 普通续场恢复；同级 FIFO。<!-- aidcp-edge 7226f01 -->
- [x] 2.6 排队等待计入死线：轮到它时已超死线即**立刻诚实失败**，绝不再启动一个没人等的浏览器（它会白占槽位）。<!-- aidcp-edge 7226f01 -->
- [x] 2.7 拆掉零抖动唤醒羊群：到点的唤醒**投进串行队列**逐个放行（用户已否决抖动方案）。<!-- aidcp-edge 7226f01 -->
- [x] 2.9 1:2 上限：账号数 > 2 × 槽位时诚实告警「部分账号可能长期排不到槽位」。<!-- aidcp-edge 7226f01 -->
- [x] 2.11 **两个上限进客户端设置页**（原本只有 `AIDCP_BROWSER_SLOTS` / `AIDCP_PER_ENV_MB` 两个环境变量——分发出去的安装包里运营根本改不了）。设置抽屉新增「浏览器并发」卡：并发浏览器数 + 最大账号数，留空 = 自动。优先级 **界面 > 环境变量 > 按内存自动推**；0 / 空 = 自动而非「上限 0」。算法权威只在主进程一处（渲染层只显示、不重算——两处各算一遍必然漂移）。账号上限允许设到 1:2 之上，但诚实告警「部分账号可能长期排不到槽位」。改完即刻生效，不需重启核心。<!-- aidcp-edge ede64c4 -->
- [x] 2.10 单测：队列串行性（并发下峰值并发 = 1）；优先级 + FIFO；一个失败不阻塞其余；超死线不启动；槽位上限 / 1:2 / 700MB 估值。<!-- aidcp-edge 7226f01 -->
- [x] 2.12 **修「可用内存」读数错误——本 change 险些把整台机器锁死的真机 bug**。内存闸原来拿 `os.freemem()` 当可用内存，而它只数**完全空闲**的物理页；macOS / Linux 都把绝大部分闲置内存拿去做文件缓存（inactive / page cache），这些页随时可回收却不计入。真机复现：16GB MacBook、系统自报可用 48%，`os.freemem()` 只报 221MB < 单环境 700MB → **每一条开浏览器路径全被拦死**，客户端报「本机可用内存不足（需约 700MB，仅剩 418MB）」、一个浏览器都开不起来（手动设并发数也救不回：槽位闸与内存闸是两道独立的闸）。**这个错读数一直都在，但只有在本 change 把内存闸从「只在全部启动查、可 force 越过」收成「全路径必经、无绕过口」之后才真的咬人**——一个一直算错、但一直可以跳过的数，变成了硬砖。修：按平台读真实可用量（linux 取 `/proc/meminfo` 的 `MemAvailable`；darwin 取 `vm_stat` 的 free + inactive + speculative；其它平台回落 `os.freemem()`——探测失败只许偏保守，绝不假装内存充裕），留 512MB 系统余量（`AIDCP_MEM_RESERVE_MB` 可调），3s TTL 缓存（准入闸每次开浏览器都要问）。槽位推算与准入闸共用同一个读数，设置卡如实显示它——界面用来自证的数，必须就是闸真正用的那个数。同机复测：4431MB 可用 → 6 槽位 / 12 账号。<!-- aidcp-edge 3eb29b0 -->
- [x] 2.13 **抢不到槽位改成排队等，不再丢弃**（用户提出：「内存占满再启动应该排队，只有达到最大挂载账号数才拒绝」）。旧版启动被闸拦下就**直接丢弃请求**，环境永久停在「未启动（槽位不足）」，后来有账号进冷待机把槽位让出来也没人去取——**等于把 1:2 废掉了**：挂 12 个账号 6 个槽位，点全部启动，有 6 个账号一天都跑不了。改成按**「有没有人在死线上等这个结果」**分流（判据落在 `fleet.cjs` 的 `slotRefusalPolicy`，可单测）：① 没人等（点启动 / 全部启动 / 崩溃恢复 / 到点普通唤醒）→ 进**等槽位队列**，任一环境进冷待机或退出让出槽位即**立刻放行队头**（另有 15s 重扫兜住「别的进程放开内存」这类无事件变化）；② 有人等（云端派任务来唤醒 / 手动任务）→ **当场诚实失败**，绝不排队（云端 45s 就 acquire 超时，等半小时后开浏览器 = 给没人要的结果开机器，还挤掉真正在等的账号）。FIFO 严格：队头过不了闸就整队停住、不许后来者插队（否则先到的被反复挤掉、饿死）。排队态如实呈现「排队等槽位 · 前面还有 k 个」，待机中的环境保持待机态不改写成 idle。**硬拒绝挪到该在的地方**：新建环境时挂满「最大挂载账号数」→ 诚实拒绝并指明去设置里调高（槽位满 = 「现在轮不到你」，账号满 = 「这台机器不该再多带一个」）。「全部启动」不再整批拦阻——12 个账号 6 个槽位的正确结果是「起 6 个、排 6 个」，不是「一个都不起」。<!-- aidcp-edge 1878f90 -->
- [x] 2.14 **「槽位被占」不再是失败原因——连带修掉三个把账号做成砖的 bug**（用户第二次纠偏：「有人等也应该是超过了上限才失败吧」）。2.13 按「有没有人在死线上等」分流（task/manual → 当场判失败）是错的：那是把**「有人在等」**误当成**「所以这次该失败」**，两者毫无因果关系。更糟的是那个「失败」是假的——外壳槽位拒绝时**一个字节都不回核心**（`wakeSettle` 要到发出 wake 命令之后才赋值），核心在浏览器闸上**干等满 180s** 唤醒死线，云端 acquire 早已超时走人；同时 ① 核心的唤醒闩 `coldStandbyWakeRequested` 置位后**从不复位**（该账号在本进程生命周期内再不请求唤醒）② `wakeColdStandby` 清掉待机定时器、失败路径**不还**（再无自唤醒路径）③ 环境不进等槽位队列（槽位空出来也没人叫它）——**净效果：先把调用方吊死三分钟，再对着空气宣布失败，顺手把这个账号做成一块砖**。现改为：**任何**槽位/内存拒绝一律进 FIFO 等槽位队列，谁都不判失败；**调用方的死线只决定「什么时候回话」，绝不决定「要不要把浏览器开起来」**——协调器把云端真实 `acquireTimeoutMs`（扣 5s 往返余量；云端在 push 前就 arm 了计时器，只准早答不准迟答）经核心传到外壳，外壳到点用私有 IPC `lifecycle.wake_denied`（父子进程消息，**非 WS 协议**，不触发五处同步）告诉核心「这次没轮到」→ 核心立刻诚实作答（云端已按可恢复处理：归还小时格 + 格内重试 ≤5 次），**但环境仍留在队列里、浏览器照常起**（撤销唤醒是双输：本次没做成、重试还得再付一次冷启；起好的浏览器正是下次重试要命中的）。剩余预算低于冷启地板（30s）→ **t=0 当场作答**，绝不让调用方空等。FIFO **严格无优先级车道**（带死线的唤醒是连续到达的，让它们插队 = 1:2 里多挂的那一半永远排不上、饿死）。唤醒失败后重挂自唤醒定时器（退避 1/2/5min）+ 复位唤醒闩。<!-- aidcp-edge 809e15d -->
- [x] 2.15 **容量语义纠偏**：把「最多挂载账号数」改成「启动排队上限」，环境创建不再受容量限制；浏览器并发只限制同时执行数；内存自动推算只在 Edge 客户端启动时读取一次，任务启动热路径不得再次采样。补 UI、主进程准入与回归测试。<!-- aidcp-edge b822d75; acceptance 25/25; full 1838/1838; typecheck pass; OpenSpec strict pass -->
- [x] 2.16 **客户端排队文案收口**：`waiting_resource` 在主状态与环境栏统一显示「排队中」，不再显示「等待浏览器资源」；补回归测试。<!-- aidcp-edge 47f2559; focused 20/20; acceptance 26/26; full 2028/2028; typecheck pass; OpenSpec strict pass -->
- [x] 2.17 **首次未绑定环境槽位满时保持排队**：不启动核心、不预取账号绑定，直接保留 FIFO 资格、清除失败投影，客户端主状态与环境栏只显示「排队中」；槽位释放后再真实启动浏览器并建立账号绑定。<!-- 原实现 aidcp-edge 265ade1；本次由 2.23 收窄 -->
- [x] 2.18 **终端退避文案区分容量与故障**：`start_queue_full` 显示「启动排队已满」，只有实际执行过浏览器唤醒且失败时才显示「唤醒失败」；不改变退避时序、槽位准入或前端状态，并补回归测试。<!-- aidcp-edge 000689f; focused 30/30; lifecycle 9/9; node --check and typecheck pass; OpenSpec strict pass -->
- [x] 2.19 **客户端批量状态文案简化**：启动、排队、待槽位、未加入、完成、关闭与失败统一为「状态 + 计数」短分段，保留受理/终态与失败原因的真实边界；补精确文案回归。<!-- aidcp-edge 7e8b9bb; focused 97/97; node --check; typecheck pass; OpenSpec strict pass -->
- [x] 2.20 **槽位释放到实际启动之间保持 FIFO 权威**：队头资格保留到启动 / 唤醒真正通过槽位准入，任何后来任务不得趁空位绕过队头；首次排队只显示位次与引擎未连接，不冒充已确认身份、已连 Cloud 或已开工。<!-- aidcp-edge c036ec2; 本次由 2.23 收窄控制面部分 -->
- [x] 2.21 **客户端排队分组按权威位次排序**：环境栏「排队中」组按有效 `queuePosition` 升序展示；未知位次稳定置后，不再沿用与 `#1…#N` 冲突的花名册顺序。补视图模型回归测试。<!-- aidcp-edge ffc3004; focused 100/100, full suite exit 0, node --check and typecheck pass; ff-only pushed to master -->
- [x] 2.22 **修复当天环境目标统一改动触发的幽灵槽位回归**：连接回执核对本次 spawn 时冻结的认证目标，不因令牌刷新窗口重新读取易变会话状态而误杀同目标核心；OS 进程 `exit` 后立即归还执行槽位并推进 FIFO，`close` 只负责末尾日志归因且有界兜底，杜绝进程已消失但客户端永久显示 4/4。<!-- aidcp-edge d6dde80; focused 43/43; post-rebase full 3067 passed, 1 gated skip; node --check and typecheck pass; OpenSpec strict pass; no installer built or installed -->
- [x] 2.23 **取消首次排队预启动控制核心**：自动启动和手动“打开浏览器”在槽位不足时都只登记外壳 FIFO，不 spawn 核心、不连接 Cloud；槽位放行后再完整启动核心与浏览器。启动排队已满同样不得创建控制核心。真实运行后进入冷待机的保留核心行为不变。补源码契约与 FIFO 回归测试。<!-- aidcp-edge d9821d8; focused 202/202; three JS syntax checks and typecheck pass; OpenSpec strict pass; no installer built or installed -->
- [x] 2.24 **启动排队输入上限从 64 提升到 256**：浏览器并发上限仍保持 64；主进程分别归一两个设置，设置页与回归契约同步，避免扩大排队容量时误放宽真实浏览器并发。<!-- aidcp-edge abd1f44; focused 33/33; acceptance 39/39; full 3071 passed + 1 gated skip; three JS syntax checks and typecheck pass; no installer built or installed -->
- [x] 2.25 **重复“打开浏览器”不得把已启用的启动队列降级为手动浏览器模式**：环境已由“开始自动化”进入启动/槽位 FIFO、核心尚未创建时，再次打开浏览器只复用原资格，不得把 `automationIntent='enabled'` 覆盖为 `stopped`；锁定“核心与引擎在线 + 浏览器冷待机 → 待机中而非离线”，并保留真正手动打开时自动化关闭的语义。<!-- aidcp-edge 0a36370; focused 208/208, acceptance 39/39, two CJS syntax checks and typecheck pass; OpenSpec strict pass; no installer built or installed -->
- [ ] 2.8 **手动任务策略未实装**：插队首 → 起浏览器 → 执行 → 完成后关闭归还槽位。队列已支持 `kind:'manual'` 优先级，但「跑完就关」这一段还没接（现在手动任务唤醒后走的是 1.9「重判待机」的通用逻辑）。
- [ ] 1.9-b **「任务完成后重判待机」未单独实装**：目前依赖云端下一次的待机提示来重新停泊，而不是任务一结束就立刻判。行为正确（不会漏关），但会多占一小会儿槽位。

## 3. aidcp-cloud — 不再往关着的浏览器上盲发

- [x] 3.3 受理超时容得下一次唤醒：默认 45s → **200s**（边缘 180s 唤醒死线 + 余量）。旧值会在边缘**正在正常唤醒**的过程中先超时、把任务判失败，而浏览器一分钟后才起来、无人认领。<!-- aidcp-cloud 87f53b9 -->
- [x] 3.4 排期任务失败不烧名额：`lastFired` 改为**触发真正开始之后**才记；未开始（`started:false`）则归还小时格并打开**有界的小时内重试窗**（5 次，任意分钟）。<!-- aidcp-cloud e78d18e -->
- [x] 3.4-b 「根本没开始」从**任务结果**回流（关键）：接管边端失败发生在触发回执回了 ok **之后**，那时小时格早被记为已消耗。评论管线跑完发现 `not_started` → `ContentScheduler.reportNotStarted()` 归还名额。<!-- aidcp-cloud 87f53b9 -->
- [x] 3.5 `browser_wake_failed` 作为**独立的**租约失败码，绝不折进 `edge_unhealthy`（前者可恢复、后者是控制面故障；混为一谈会让运维去查一个根本没坏的连接）。结果卡如实说「浏览器待机、未能唤醒（可恢复，稍后自动重试）」。<!-- aidcp-cloud 87f53b9 -->
- [x] 3.6 单测：未开始归还名额并可在小时内重试；重试有界（用尽后诚实放弃、整格只回**一张**卡）；真开跑 / 抛异常都不归还（宁可少发绝不重发）。<!-- aidcp-cloud e78d18e -->
- [x] 3.4-c **修异步终态回流重置预算的线上回归**：触发入口先返回已开跑时，不得清掉同小时已有重试预算；稍后 `reportNotStarted()` 必须继续递减，首次 + 5 次后放弃。<!-- aidcp-cloud fd32fcf: same-cell retry budget retained until terminal outcome -->
- [x] 3.5-b **自动未开始结果卡去噪**：排期调度器已接管重试/放弃通知时，中间 `not_started` 不逐次发卡；预算用尽只由 `onCellAbandoned` 发一张，手动结果卡保持不变。<!-- aidcp-cloud fd32fcf: handled signal gates only automatic intermediate cards; missing/failed abandonment notifier falls back to the final immediate card -->
- [x] 3.6-b 补异步终态回流、预算递减、整格单卡和手动卡不受影响的回归测试。<!-- aidcp-cloud fd32fcf; focused 131/131; acceptance 65/65; full 2807 with 2799 pass + 8 gated skips; typecheck pass -->
- [x] 3.1 / 3.2 **区分引擎在线与浏览器就绪 + 两段式浏览会话激活**：真实冷待机 `absent` 时保留 transport/任务路由，但不启动浏览角色与 `SessionMonitorRole`；`ready` 后才开场，活动会话转 `absent` 时拆看门狗；重复状态幂等。首次本地排队不建立 transport。<!-- aidcp-cloud 8990d48 -->

## 4. 验收与部署

- [x] 4.1 edge：`test:acceptance` 19/19、`test` 1224/1224、`typecheck` 全过。<!-- aidcp-edge ede64c4 -->
- [x] 4.2 cloud：`test:acceptance` 50/50、`test` 1933/1933、`typecheck` 全过（安全红线 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 全绿）。<!-- aidcp-cloud 87f53b9 -->
- [x] 4.3 **cloud 已在 dev 生效**（无需本 session 再 rsync）。探 ECS 时发现并发 session 于 15:49 已把其工作树 rsync 上去，**其中已包含本 change 落在 master 的全部云端提交**，服务 15:50:58 重启（晚于文件落地）。逐文件核对指纹：`MAX_RETRIES_PER_CELL`×3、`browser_wake_failed`（`edge-task-lease-client.ts`×4 / `protocol.ts`×2）、`onScheduledTaskNotStarted`×3。healthcheck：`active (running)`、8787 + 8090 监听、飞书长连接已建立、「PG 锚点缓存已就绪」、`NRestarts=0`、isales 未受影响。**故意不再从 `origin/master` 覆盖 rsync**——那会顶掉该 session 尚未入库的 panel 工作（`src/panel/downloads-manifest.ts` 在机器上但不在 git 里），等于把他们正在 dev 上测的东西悄悄回滚。**本 change 无依赖变更**，不需要全量 `npm ci`。<!-- 2026-07-14 deployed (dev) -->
- [ ] 4.4 真机验收项登记 `docs/real-machine-acceptance-backlog.md`：
  - 停泊 → 唤醒 → 执行 → 重判待机一整圈，**云端连接全程不断**（这是本方案相对「杀进程重启」的核心可观测差别）。
  - 唤醒后登录态与身份被**重新确认**（而非沿用释放前缓存）。
  - **AdsPower 每次启动的调试端口都变**——唤醒后的第一次瞬断必须能正常重连，而不是被误判成「进程已死 = 终局」触发整进程回收。（这是本 change 最尖锐的坑，桩测已覆盖逻辑，但真机必验。）
  - 10 个环境串行启动的真实耗时（预期 10–15 分钟）与内存峰值；单环境稳态常驻内存（校准 700MB）。
  - 上海零点日额齐放时，羊群被串行队列拆开、无并发冷启。
  - 停泊账号收到排期任务 → 被唤醒 → 任务**真正执行**（旧行为是回一句假的 `cdp_unhealthy`）。
  - 单次浏览墙钟耗时（0.2 的分水岭数据）。
- [x] 4.5 edge 桌面安装包**未打**（CLAUDE.md §6：需用户明确要求才出包）。
- [x] 4.7 运行 Cloud 聚焦测试、acceptance、全量测试、typecheck 与 `openspec validate browser-slot-scheduling --strict`；提交推送并从干净 master 部署 dev，核验服务、连接与日志。<!-- 2026-07-22: aidcp-cloud fd32fcf ff-only pushed to master. dev backup `/opt/aidcp/backups/cloud.bak.20260722-141939.tar.gz`; deployed two runtime files from clean master with matching sha256; cloud active/NRestarts=0, 8787/8088/8090/8091 listening, health ok, PG select 1, Feishu WS onReady, isales services active. Tmax/工程师大白 remained offline after restart, so no live comment retry was fabricated. -->

## 5. 后续（多 agent 对抗性评审 2026-07-14 挖出，按价值排序；每条独立成 change，不塞进本 change）

> **必须先说破的结论**：2.14 让失败变得诚实、可恢复了，但**它不会让 12 个账号在 6 个槽位上真跑起来**。真正的病不在「怎么判失败」，在**槽位根本不轮转**。下面第 1 条才是那个杠杆。

- [ ] 5.1 **供给侧：让待机提示覆盖「这账号接下来达到 Cloud 单一 5 分钟门槛、没有活可干」的所有情形**（纯云端，零协议改动，零边缘改动，不驱逐任何人）。今天 `aidcp-cloud/src/comm/browser-standby.ts` 的待机提示**只看浏览配额耗尽**（`RiskController.explain('view')`）；于是**活跃时段窗口关闭、周掩码关闭、日会话上限已满、账号 frozen、互动配额耗尽而浏览配额还有**——全都不产生提示，浏览器就那么开着、占 700MB、好几个小时什么都不干。协议里 `UiBrowserStandbyPayload.source` **早就声明了 `'session'` 这个来源、全仓无人产出**。复用现成的进入待机闸与唤醒链路即可，放出的「槽位·小时」比任何抢占方案多一个数量级。**这一条大概率把整个争用问题变成非问题。**
- [x] 5.2 **明确不做“首次排队控制核心”**：用户确认该方案把简单排队扩张为「核心在线 + 浏览器缺席 + 可唤醒 + 可关闭」的额外运行态，属于过度设计并已造成幽灵槽位。被槽位拒绝的首次启动环境保持本地排队与 Cloud 离线；轮到后再完整启动。排期只能在账号真实上线后评估，这是容量约束的诚实结果，不再用隐藏核心兜底。
- [ ] 5.3 **cloud：`browser_wake_failed` 在发布链路被误报成「边缘离线」**（`publish-dispatcher.ts` 落进 `offline_requeued`）——边缘明明在线、浏览器只是停泊排队。运维据此去查一个根本没断的连接。加一档 `wake_failed_requeued`。
- [ ] 5.4 **cloud：`edge-task-lease-client.ts` 的 `onReleased` 只硬匹配两个 reason**，新增任何终态 reason 都会让云端干等到 acquire 超时。改成一张 reason→code 全表（结构性的漏，顺手根治）。
- [ ] 5.5 **暂停态环境白占 700MB**（浏览器开着、零工作、云端连接都断了）。回收它不涉及驱逐，但「暂停」的界面白纸黑字承诺「浏览器保持打开」——需要一个默认关闭的设置项 + 运营确认，不能偷偷改语义。
- [x] 5.6 **待机被拒不得把健康环境打成 paused**（`core-lifecycle.ts` 的 `enterStandby()` 返回 false → `currentState='paused'` + `onCloseFailed()` → 外壳写 `coreParked/session:'paused'` → 一个只是「此刻不能待机」的环境变成永久占 700MB 的砖，且从此被排除出等槽位队列）。AdsPower 的 close 无 OS 级杀，这条路生产可达。 <!-- 已由 change admit-browser-standby-on-live-facts 接管并完成（aidcp-edge 00fda89）。`enterStandby()` 改回具名分类结果（reason + browserIntact）：三条无害拒绝发生在任何拆除动作之前 ⇒ 浏览器完好、外壳原样不动；两条真失败发生在 session.detach() 之后 ⇒ 如实标真态未确认。待机被拒不再复用 close_failed 那条回执，两支都不动运营意图。此处不要再做第二遍。 -->
- [x] 5.7 **冷待机期间收到浏览命令 → 今天静默丢弃、零回执**（`src/main.ts` 三处），云端角色干等到看门狗。应回诚实的 `action.completed{ok:false}`，动作名须走那张 21 条映射表归一（CLAUDE.md §2 第 5 处）。 <!-- 2026-08-05 取证：本条描述已过期——`handleBrowserAbsentCommand` 现在请求唤醒并回 `action.completed{ok:false, reason:'browser_absent_wake_requested'}`，动作名已走 nativeActionNameForCommand 归一。**唯一残留**是同一函数里 `operation_unclassified` 那一支（只 console.warn、零回执，真机可见「未登记的命令 / 已拒绝」）。该分支属活跃 change align-cloud-edge-operation-registries，已转交，不在此处也不在 admit-browser-standby-on-live-facts 里做。 -->
- [ ] 5.8 **明确不做：需求驱动的「让位 / 槽位借调」**（请一个 resting 账号提前进冷待机腾槽位）。四位独立评审判它致命且**全部在代码里坐实**：① `session==='resting'` 标签来自 stdout 正则、滞后且粘滞，而核心的进入待机路径**没有「浏览循环是否在跑」的闸**——会真的把正在跑的会话停掉（**踩「绝不驱逐 running」红线**）；② 冷待机中的环境自己就被标成 `resting`，选中它 = 零槽位释放，调度器却以为让了位（幻影供体）；③ 让位直接调进入待机、**绕过唯一那道安全闸**（暂停 / 验证码浮层 / 稿件待审 / 未登录的 skip 链），能把运营手指底下正在过验证码的浏览器杀掉；④ 合格供体占空比仅约 3%（休息中位 60s，而设计要求剩余 ≥45s），6 持有者下「此刻有合格供体」约 15% —— 为一个 85% 时间是 no-op 的机制付一整套新的槽位所有权语义。**方向也错**：真正长期占死槽位的是 5.1 的 idle 与 5.5 的 paused，释放它们根本不涉及驱逐。

## 6. 视频号临时浏览器通道

- [x] 6.1 补齐 OpenSpec：公共执行槽位与容量 1/FIFO 的机器级临时浏览器通道分池；视频号 API-only 运行态与人设不适用写入契约。
- [x] 6.2 Edge 外壳实现通用临时通道租约、结构化排队位次、代际取消与退出兜底；公共槽位计数排除临时/API-only 环境，资源分池不放宽既有提供方限频约束。<!-- aidcp-edge 3fd5320: machine-level capacity-1 FIFO, generation guards, exit/timeout fallback, split capacity projection -->
- [x] 6.3 视频号启动与重新鉴权接入临时通道：全部环境顺序初始化；会话有效不打开浏览器；会话失效才开 sidecar，确认关闭后释放；补结构化 API/Cloud 运行证据与状态投影。<!-- aidcp-edge 3fd5320: leased sidecar, stored-session browser skip, current-process API/Cloud ACK proof -->
- [x] 6.4 视频号声明 `personaApplicable=false`：不应用 personaBound、不显示入口、不运行 gate/自动弹窗；过期 IPC 调用返回不适用并补回归测试。<!-- aidcp-edge 3fd5320: platform capability, renderer gating, not_applicable IPC -->
- [x] 6.5 运行 Edge focused/acceptance/full/typecheck 与 Electron 生命周期回归；记录通过数和真实边界，安装包仍按用户明确授权门禁。<!-- aidcp-edge 3fd5320: post-rebase focused 162/162, acceptance 28/28, typecheck, build:dist and syntax checks passed. Pre-rebase full 2166/2166 passed; post-rebase full 2167/2169 under shared-machine load had two unrelated UI timing flakes, and both exact tests passed isolated 1/1. AIDCP_E2E remained gated; no installer built. -->
- [x] 6.6 提交 aidcp-edge 与中控 OpenSpec 证据，rebase/fast-forward 合入默认分支并推送；`openspec validate browser-slot-scheduling --strict` 通过。<!-- aidcp-edge master 3fd5320; aidcp contract 3428c56; both rebased and fast-forward pushed. -->
