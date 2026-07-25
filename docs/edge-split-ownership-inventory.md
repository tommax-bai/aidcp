# Edge 拆仓 · 主进程归属台账（tasks 0.C.2 / 0.C.3 / 0.C.5 产出）

> 2026-07-25 生成。对象 = `aidcp-edge` `master` @ `cf10b0c`，`src/electron/main.cjs` 7396 行。
> 本文是 change `split-classic-client-edge-host` 第 0 节的产出：**逐通道、逐行段、逐传输定归属**。
> 只读盘点，未改任何代码。

---

## 0. 结论先行

**盘完了，而且盘出了一件顺序上的事。**

- **82 条运行时通道全部有主，零遗漏、零重复、零归属冲突。** 独立复核链路自己重新抽了一遍源码
  （不是复用盘点结果），得到同样的 82，与渲染层预加载暴露的 82 个调用名**一一对应**、既无「渲染层
  调得到但主进程没实现」也无「主进程实现了但没人调」。行段覆盖 7396 行**无空洞**。
- **但归属比预期难得多：82 条里有 30 条必须切开**，不是 10 条。对抗校验推翻了 20 条原判为「纯产品侧」
  的通道——它们的 HTTP 调用确实是产品侧的，可是它们都要先把环境 id 翻译成环境键，而那张翻译表在引擎侧。
- **最要紧的一条不是归属，是顺序**：今天**引擎事实是靠正则解析日志文本得到的**。在这层被换掉之前，
  任何一条状态类通道都无法干净归属。详见 §1——它构成 0.C 自己的前置。

---

## 1. 先决问题：产品状态今天是「猜」出来的，不是「报」出来的

这是本次盘点最重要的发现，它改变 0.C 内部的做事顺序。

**现状**：外壳并不是从引擎那里**收到**结构化事实，而是**从引擎的日志文本里猜**出来的。两处：

1. 一张 22 条规则的中文正则表，把核心的输出行匹配成活动流条目（"命令: page.scroll"、"✓ 点赞成功"、
   "浏览循环结束"…）。**这个文件自己的文件头就写着**：它是一处「无保障的手工耦合」，解析器的测试
   只测它自己、从不执行发出端，所以**核心里改一句日志措辞，测试照样全绿，而活动条目会静默消失**。
2. 状态徽标的推断：靠 `包含('已连接云端')` → 云端已连接、`包含('风控拒绝') 或 包含('⚠')` → 风险告警、
   正则 `/SunBrowser (\d+) is not ready/` → 内核准备流程、`包含('[browser-parking] control-ready')`
   → 浏览器就绪。**「浏览器控制是否就绪」这一条尤其要命**：每一次向核心写浏览器控制指令，都以
   「有没有在日志里见过那句话」为闸门。

**为什么这挡住了拆仓**：

- 这两处正则表里**硬编码了云边协议的命令名**（`page.scroll` / `note.open` / `interaction.comment` /
  `group.join` / `captcha.assist.capture` 等 23 条）。也就是说，**协议词汇今天活在产品界面的展示层里**。
  照原样搬进 Classic，等于让协议改一个消息名就随机弄坏产品 UI，而且 CLAUDE.md §2 的协议同步铁律
  完全覆盖不到这个位置。
- 原始日志行还**逐字**进了产品界面：核心的崩溃栈、发布诊断埋点、租约抑制说明、指纹浏览器报错，
  全部原样显示在每环境日志面板里。
- 所以：`status:update`、`ui:activity` 这两条推送通道，在引擎改成发结构化事件之前，**哪边都不能干净地拿走**。

**结论：0.C 内部要先做「让引擎发结构化事实」，再做「切文件」。** 顺序反了，切出来的两边会用一条
正则表连着，而那条连接线没有任何机械手段能保护。

---

## 2. 82 条通道台账

盘点口径：81 个注册调用点 → **82 条运行时通道**（其中一个调用点在循环里注册两条）。
「订正」= 对抗校验推翻了初判，理由随行给出。

归属分布（订正后）：**Classic 38 · Host 14 · 须切开 30**。

| 行 | 通道 | 归属 | 到得了执行侧？ | 说明 |
| --- | --- | --- | --- | --- |
| 5662 | `status:get` | Classic | 不到 | Read-only projection of shell/runtime state; no transport to the Core. Payload composition depends on Host-published runtime axes (statusOf is split-r |
| 5663 | `edge:pause` | Host | 进程间通道 | pauseEdge sends lifecycle.pause_and_exit via child.send (Node IPC), with SIGTERM as the honest fallback when IPC delivery fails. |
| 5668 | `edge:resume` | Host | 进程间通道 | resumeEdge sends lifecycle.resume via child.send when a Core exists; otherwise it wakes cold standby or enqueues a fresh Core start. |
| 5673 | `edge:close` | Host | 进程间通道 | stopAutomation sends lifecycle.close via child.send and falls back to SIGTERM; with no child it only converges local intent and does a read-only AdsPo |
| 5678 | `browser:close` | Host | 进程间通道 | closeBrowserExecutor sends lifecycle.standby via child.send; the Core stays connected. Measured fact: standby over Node IPC => lifecycle. |
| 5683 | `browser:open` | Host | 启动核心 | With a live Core it is a Node-IPC cold-standby wake; with no Core it spawns one (startBrowserAbsentCore for bound envs, enqueueStartFlow for first-log |
| 5740 | `auth:relogin` | Host | 信号 | stopAndRestart SIGTERMs the running Core (respawn path then starts a new one); with no child it goes straight to enqueueStartFlow. Not customer login. |
| 5745 | `settings:get` | **须切开** | 不到 | **订正**（原判 Classic）：返回体里嵌了并发槽位的实时占用/排队/临时通道，全部来自引擎侧调度器。整块判 classic 会让设置面板要么丢掉这段读数，要么让渲染层自己再算一遍——代码注释明令禁止后者。 |
| 5774 | `client-auth:login` | Classic | 不到 | Customer HTTPS login, then loads visible environments and swaps login window for main window. |
| 5783 | `client-auth:logout` | Classic | 不到 | Cloud logout best-effort plus local session invalidation and credential forgetting. |
| 5790 | `client-auth:session` | Classic | 不到 | Reads local customer session flags only. |
| 5794 | `client-auth:prefill` | Classic | 不到 | Reads locally stored login prefill (secure local state). |
| 5795 | `client-auth:prefill:clear` | Classic | 不到 | Clears locally stored login prefill. |
| 5802 | `interaction:list` | Classic | 不到 | Cloud HTTPS GET via interactionCustomerRequest; cancellable read, bypasses Core. |
| 5819 | `interaction:detail` | Classic | 不到 | Cloud HTTPS GET via interactionCustomerRequest; bypasses Core. |
| 5833 | `interaction:draft:update` | Classic | 不到 | Cloud HTTPS PUT of reply draft with expectedVersion; bypasses Core. |
| 5854 | `slow-start:set` | Classic | 不到 | Cloud HTTPS PUT keyed by envKey only. Code comment records the ruling that no engine-online gate may be added here. |
| 5868 | `slow-start:get` | Classic | 不到 | Cloud HTTPS GET; must render for environments that have never started, so it must not be routed through Host. |
| 5880 | `environment-risk:get` | Classic | 不到 | Cloud HTTPS GET of risk state; must work with the engine stopped. |
| 5890 | `environment-risk:recover` | Classic | 不到 | Cloud HTTPS POST to lift a persistent restricted state; the Cloud is the single writer, the shell only submits. |
| 5902 | `interaction:approve` | Classic | 不到 | Registered by the for-loop template at 5901; Cloud HTTPS POST .../replies/<jobId>/approve. |
| 5902 | `interaction:regenerate` | Classic | 不到 | Registered by the same for-loop template at 5901; Cloud HTTPS POST .../replies/<jobId>/regenerate. |
| 5916 | `interaction:send` | Classic | 不到 | Cloud HTTPS POST with idempotency key; the Cloud, not this process, performs the actual send. |
| 5931 | `interaction:ignore` | Classic | 不到 | Cloud HTTPS POST with expectedVersion; bypasses Core. |
| 5944 | `interaction:escalate` | Classic | 不到 | Cloud HTTPS POST with validated reason string; bypasses Core. |
| 5959 | `interaction:sync` | Classic | 不到 | Cloud HTTPS POST requesting a sync; the Cloud schedules any edge work afterwards. |
| 5975 | `interaction:test-reset` | Classic | 不到 | Cloud HTTPS POST test helper; bypasses Core. |
| 5990 | `interaction:auth:reopen` | Classic | 不到 | Cloud HTTPS POST asking Cloud to reopen auth; this process sends no command to its Core. |
| 6003 | `interaction:browser:control` | Classic | 不到 | Cloud HTTPS POST with action open/close; the sidecar is driven by Cloud afterwards, not by this handler. |
| 6021 | `interaction:browser:open-local` | **须切开** | 不到 | Customer scope enforcement (Classic) wrapped around AdsPower runtime init, kernel provisioning and Local API profile open (Host). Deliberately does no |
| 6065 | `interaction:read-controls:update` | Classic | 不到 | Cloud HTTPS PUT of read toggles with expectedVersion; bypasses Core. |
| 6079 | `interaction:notify` | Classic | 不到 | Local desktop notification only (surfaceNotification) after a customer scope check; no network call, no Core contact. |
| 6094 | `interaction:reads:cancel` | Classic | 不到 | Aborts the shell's own in-flight customer-API reads for that envKey. |
| 6100 | `settings:save` | **须切开** | 信号 | Persistence and customer scoping are Classic, but the same handler calls syncEnvHandles, which registers/destroys per-environment supervisors and SIGT |
| 6160 | `cloud:restartAll` | Host | 进程间通道 | requestCoreCloudRebind sends a request-shaped rebind message to each running Core via child.send and awaits a reply; stopped environments only get the |
| 6185 | `edge:start` | Host | 启动核心 | Sets automation intent then either wakes cold standby (Node IPC) or spawns a Core through the serial start queue (queueStartEnv). |
| 6202 | `edge:restart` | Host | 启动核心 | stopAndRestart: SIGTERM the running child (restartPending makes its exit handler start a new flow) or enqueue a start flow when none is running. Stop- |
| 6208 | `fleet:get` | **须切开** | 不到 | **订正**（原判 Classic）：返回体嵌了槽位容量/占用/排队与每环境的完整引擎投影。 |
| 6209 | `fleet:select` | **须切开** | 不到 | Classic selection persistence + titlebar tone + broadcast, but also triggers the AdsPower Local API proxy preflight for the newly selected env. |
| 6221 | `fleet:setManualNickname` | **须切开** | 标准输入 | Local roster + cloud operator-alias write (Classic) ending in syncBrowserPersonaNotice(force) which writes browser.personaNotice to the Core child's s |
| 6302 | `fleet:startAll` | Host | 启动核心 | startAllEnvs queues Core spawns for stopped envs and resumes/wakes running ones (resumeEdge/wakeColdStandby use Node IPC). Renderer envIds are only a  |
| 6303 | `fleet:stopAll` | Host | 进程间通道 | stopAllEnvs -> pauseEdge -> sendCoreLifecycle('pause_and_exit') via child.send, with SIGTERM fallback when IPC is unavailable. |
| 6304 | `fleet:closeAll` | Host | 进程间通道 | closeAllEnvs -> stopAutomation -> sendCoreLifecycle('close') via child.send, SIGTERM fallback; releases slots and start queue. |
| 6305 | `fleet:setRailCollapsed` | Classic | 不到 | Persists a UI collapse flag in local settings. |
| 6309 | `persona:preview-facebook-template` | Classic | 不到 | Pure in-process template builder for the Facebook persona form. |
| 6311 | `persona:fill-facebook-selected` | Classic | 不到 | Customer-auth HTTPS call to the cloud with the client session token; invalidates the session on expiry. |
| 6330 | `browser:openAdsDownload` | Classic | 不到 | shell.openExternal on a static URL. |
| 6334 | `browser:showDriven` | **须切开** | 标准输入 | One of the only two non-lifecycle Core commands (writeBrowserControlCommand 'browser.show'), but bounds computation and post-reply window focus are El |
| 6340 | `browser:resetParking` | Host | 标准输入 | The other non-lifecycle Core command: browser.park written to the child's stdin; no window dependency. |
| 6385 | `persona:get` | **须切开** | 不到 | **订正**（原判 Classic）：经人设 IPC 骨架把 envId 解析成 envKey，读的是引擎侧的环境注册表与「当前选中环境」。 |
| 6399 | `persona:generate` | **须切开** | 不到 | **订正**（原判 Classic）：同上：envId→envKey 解析依赖引擎侧注册表。 |
| 6426 | `persona:persist` | **须切开** | 标准输入 | **订正**（原判 Classic）：写状态里的人设已绑标志，该写入会连锁触发向核心标准输入推一条浏览器横幅指令。所以它其实到得了核心——原判 reachesCore=no 是错的。 |
| 6451 | `publish:approval` | Classic | 不到 | Cloud decision write over customer-auth HTTPS; comment states core/browser/CDP/slots deliberately do not participate. |
| 6497 | `publish:image-remove` | **须切开** | 不到 | **订正**（原判 Classic）：云端删除成功后要就地改写环境状态里的稿件预览；不改的话下一次状态广播会把删掉的图「长回来」。 |
| 6572 | `delegated-task:list` | **须切开** | 不到 | **订正**（原判 Classic）：envId→envKey 解析走引擎侧注册表；且解析函数在找不到时会回落到「当前选中环境」，跨账号误投风险。 |
| 6575 | `delegated-task:draft` | **须切开** | 不到 | **订正**（原判 Classic）：同上。 |
| 6578 | `delegated-task:action` | **须切开** | 不到 | **订正**（原判 Classic）：同上。 |
| 6590 | `publish-draft:list` | **须切开** | 不到 | **订正**（原判 Classic）：同上。 |
| 6605 | `publish-draft:get` | **须切开** | 不到 | **订正**（原判 Classic）：同上。 |
| 6611 | `publish-draft:edit` | **须切开** | 不到 | **订正**（原判 Classic）：同上。 |
| 6633 | `publish-draft:refine` | **须切开** | 不到 | **订正**（原判 Classic）：同上。 |
| 6665 | `publish-draft:refinement-get` | **须切开** | 不到 | **订正**（原判 Classic）：同上。 |
| 6680 | `publish-schedule:occupied-hours` | **须切开** | 不到 | **订正**（原判 Classic）：同上。 |
| 6685 | `environment-overview:get` | **须切开** | 不到 | **订正**（原判 Classic）：同上。 |
| 6696 | `environment-schedule:get` | **须切开** | 不到 | **订正**（原判 Classic）：同上。 |
| 6706 | `publish-queue:get` | **须切开** | 不到 | **订正**（原判 Classic）：同上。 |
| 6715 | `publish-queue:cancel` | **须切开** | 不到 | **订正**（原判 Classic）：同上。 |
| 6732 | `curated:summary` | Classic | 不到 | Cloud curated-contents count read. |
| 6735 | `curated:list` | Classic | 不到 | Cloud curated list with mode/sort/pagination validated in main. |
| 6764 | `curated:get` | Classic | 不到 | Cloud curated item read. |
| 6769 | `curated:create-post` | Classic | 不到 | Orders a rewrite/post job in the cloud; no local execution. |
| 6780 | `notify:show` | Classic | 不到 | Local desktop notification. |
| 6787 | `ads:status` | Host | 不到 | AdsPower Local API status with bundled-runtime recovery; bypasses Core entirely. |
| 6789 | `ads:listProfiles` | **须切开** | 不到 | AdsPower Local API enumeration (Host) followed by customer-scope refresh, fail-closed logout and roster narrowing (Classic). |
| 6825 | `ads:openCreate` | Classic | 不到 | **订正**（原判 Host）：对抗校验两条 lens + reconcile 三方一致：整个实现是「唤起指纹浏览器桌面应用，失败则打开下载页」，不碰本机 API、不碰运行时、不碰核心。判 host 会逼 Host 引入外壳导航能力。 |
| 6837 | `ads:templates` | Classic | 不到 | **订正**（原判 Host）：静态操作系统族列表，无引擎内容。 |
| 6861 | `ads:createEnv` | **须切开** | 不到 | AdsPower runtime + fingerprint creation (Host) interleaved with cloud provisioning intent, assignment, roster join and slow-start confirmation (Classi |
| 6997 | `ads:getEnvProxy` | **须切开** | 不到 | Customer-ownership gate (Classic) guarding an AdsPower Local API proxy-credential read (Host). |
| 7079 | `ads:parseProxyLines` | Classic | 不到 | **订正**（原判 Host）：纯字符串解析，无引擎内容。 |
| 7085 | `ads:updateEnvProxy` | **须切开** | 不到 | Classic scope gate + Host write mutex, runtime ensure, Local API proxy update and preflight-evidence invalidation. |
| 7117 | `ads:updateEnvProxies` | **须切开** | 不到 | Same gate/machine mixture as the single write, plus direct renderer progress pushes (event.sender.send) that Host may not perform. |
| 7286 | `ads:deleteEnv` | **须切开** | 不到 | **订正**（原判 Classic）：订正原「走云端 HTTPS、完全绕过核心」的判断：只有视频号那条走云端，其余平台终局直接走指纹浏览器本机删除，且删前调注册表 reconcile（会停掉该环境的核心、释放槽位）。 |

---

## 3. 五条跨边界传输的归属

原设计只提到日志流一条，交接文档提到三条。**实际是五条，而且核心侧其实有六个端点**——因为
互动类平台在启动早期就分叉进了另一套运行时，于是进程间通道有**两套各自独立手写的路由**、
实现同一批线上词汇，信号也有两个语义不同的端点。**任何 typed 化必须先把它们收成一套，
否则拆完会出现两种方言的「暂停」。**

| 传输 | 方向 | 今天承载 | 归属 | 拆后必须变成 |
| --- | --- | --- | --- | --- |
| 标准输出/错误的行流 | 引擎→产品 | 日志 + 4 种结构化前缀行 + **被正则解析出的产品状态** | **须切开** | 事实归 Host 的结构化事件流；文案与呈现归 Classic。**拆后标准输出必须降级为纯诊断，任何产品行为都不得再依赖解析它** |
| 标准输入按行 JSON | 产品→引擎 | 浏览器显示（请求-应答）/ 停放 / 人设横幅 | **须切开** | 具名的浏览器窗口操作；几何坐标由 Classic 算好当数据传入，Host 不碰窗口系统 |
| Node 进程间通道 | 双向 | 6 个生命周期动词 + 云端重绑（请求-应答）+ 两组协商 + 一批状态事件 | Host | 单一 typed 命令面（穷举联合类型 + 关联 id + 截止时间 + 每条都有终局回执） |
| 启动时环境变量 | 产品→引擎（仅一次） | **四组是操作、不是配置**（见下） | **须切开** | 一个 typed 启动描述符对象，四组操作各自成为具名参数 |
| POSIX 信号 | 产品→引擎（带外） | 停止的权威兜底 | Host | 具名的 terminate 操作：typed 停止 → 宽限 → 终止信号 → 宽限 → 强杀 |

### 3.1 启动参数里藏着四组「操作」

这四组不是设置，是操作。它们今天只能在进程创建那一刻表达，一旦错过就没有第二次机会：

1. **删除环境并擦除凭证** —— 启一个只做这一件事的一次性引擎进程，它拒绝除此之外的一切命令，
   连同类命令但 id 对不上也拒绝，做完上报一次。**一个破坏性的、一次性的、需要关联的操作，
   绝不该表达成启动时的一个字符串**——一个残留的继承值就能在错误的环境上装好一颗雷。
2. **以控制面模式启动**（不起浏览器、采用指定的云端绑定身份）—— 两个变量缺一不可，
   缺一半时引擎在运行期抛错。
3. **启动时已持有临时浏览器租约 + 一个防串号令牌** —— 那个令牌今天是环境变量里的十进制字符串，
   **解析不出整数时静默退化为 0**。防串号令牌退化成 0 意味着防串号失效。
4. **以暂停态启动** —— 这就是暂停动词的启动期拼写，与运行期的暂停是同一个意思、两套词汇、两条通道。

### 3.2 标准输入桥的静默丢弃，比预想的更严重

**已确认，且有三个各自独立的丢弃点压在同一条字节流上**：三个消费者都会收到每一行，各自按类型过滤，
认不出就 `return`——没有日志、没有回执、没有任何地方报错。所以一个拼错的或新加的消息类型会被
**丢弃三次**，而发送方只能靠自己的超时发现，**看起来像引擎慢，而不像命令不认识**。

typed 替代方案必须做到三件事：① **只有一条**带帧、带关联的通道，一个解复用器、一个缓冲区，
不是 N 个监听器抢同一条流；② 按穷举的可辨识联合校验操作名（照协议那份 `Record<MessageType,true>` 的
做法，漏一个分支就编译不过）；③ 认不出的名字要回一条**终局的、带关联的错误**并发出诊断，
**绝不 `return`**。核心在云端方向上已经这么做了（无法归类的操作记为 `operation_unclassified` 并拒绝，
而不是忽略），产品→引擎方向必须照搬这条 fail-loud 规则。

### 3.3 「暂停 = 引擎断开」今天有四个洞

拆仓后 Host 合同必须堵上，逐条：

1. **没有截止时间**：外壳只在「发送失败」时才升级到信号。一个**收下了消息然后再也不动**的引擎
   （比如生命周期分发器还没装好、启动卡在最长 5 分钟的登录等待里）**永远不会被升级**。
   合同必须规定：每个停止类操作带截止时间，**超时本身**——而不只是发送失败——触发带外终止。
2. **没有升级下限**：外壳从来不给核心发强杀信号。合同必须规定：终止信号 → 有界宽限 → 强杀，
   并且把「进程没了」当作断开的终局证据。
3. **信号处理器会自我缴械**：核心注册的是持续监听而非一次性监听，且收尾流程单入口——
   于是注册这个处理器**替换掉了系统默认的终止行为**，一旦收尾卡住，核心对之后的每一个终止信号免疫。
   最危险的一环是原生页面引擎的关停，它排在在途原生执行之后。合同必须规定收尾路径自身也有截止时间、
   并以无条件退出结尾。
4. **诚实拒绝不能被当成终止**：关闭动词在浏览器无法确证关掉时会**故意不退出**并回报关闭失败——
   这是对的、必须保留成一个独立的终局结果。但这意味着「暂停」可以合法地以「引擎仍连着」收场，
   所以合同必须写明**哪些停止动词可拒绝**（关闭：可以，浏览器必须被证明关掉了）、
   **哪些不可拒绝**（终止：永不可拒绝，必须以进程死亡结束）。

---

## 4. 由此推导出的 Host 公开面

生命周期九个动词覆盖不到的操作，逐条列出。这份清单直接替换 design.md §3 里那份「9 个动词」的草稿。

**引擎启停与状态**
- `engine.start(启动描述符)` — 一个经过校验的参数对象，取代今天散在三处、由一份 24 条删除名单守护的
  约 20 个字符串。四个操作型模式作为其字段：控制面模式（带绑定账号）、离场清理模式（带清理 id）、
  自动化初始态（暂停/运行）、浏览器租约预授（带防串号令牌）。
- `engine.pause` / `engine.resume` — 带终局回执的关联调用，取代「即发即忘 + 另行观察事件」。
- `engine.stop(模式, 截止时间)` — 三种终局结果：已停止 / 诚实拒绝（浏览器关闭未确证）/ 超时。
  调用方必须能区分**诚实拒绝**与**没响应**，今天的即发即忘做不到。
- `engine.terminate(宽限)` — 永不可拒绝，以进程死亡结束。今天这条升级只是外壳里一个尽力而为的
  异常捕获，且**全链路没有强杀下限**。
- `engine.standby` / `engine.wake` — 两者按设计都可拒绝（有活跃任务租约时拒绝待机；身份复读失败时
  拒绝唤醒），都需要 typed 的「拒绝 + 原因」。

**资源协调（机器级）**
- `browserSlot.requestWake / grantWake / denyWake` — 截止时间是承重的（必须小于云端 240 秒空闲看门狗），
  且**一条被丢掉的拒绝会让环境永久卡住**，所以必须是强制应答的协商。
- `browserLease.acquire / release / grant / deny` — 带防串号令牌。**获取超时必须随消息传递**，
  今天两侧各读一个名字不同的环境变量（核心侧默认 180 秒、外壳侧默认 7 分钟），两边对预算的认知不一致。
- `runtime.ensure` — 落地运行时、采纳或启动守护进程、确保内核版本。**它必须先于 start，
  而且必须在完全没有引擎要启动时也能成功**（管理后台的只读查询就依赖它）。

**浏览器窗口**
- `browserWindow.show(几何?) / park()` — 几何由 Classic 算好当数据传入，Host 应用并**探测真实可见性**
  后回终局回执。「命令写进去了」不等于「窗口真的动了」，现有代码刻意拒绝把受理当完成，这条要保住。
- `browserWindow.setPersonaNotice(通知)` — Host 负责渲染并在页面跳转与调试重连后重新施加；
  **Classic 保留决策与文案**（是否该提示、宽限窗口、适用性、三态），Host 不得携带产品文案。

**指纹浏览器本机 API**
- `adspower.query` / `adspower.mutate` / `adspower.proxy.updateBatch` + `.progress` 事件 —
  批量代理是长耗时、部分失败、需资源协调的操作，**逐项结果就是它的全部产品价值**，
  没有任何生命周期动词能表达。
- `browser.openForInspection` — 为人工查看打开一个分身，**明确不启动核心、不改写认证状态**。
  用 `start` 是错的动词。

**云端与批量**
- `cloud.rebind(目标, 截止时间)` — 已经是请求-应答形状，且**核心侧已经被实现了两遍**，必须收成一份。
- `fleet.admitStart` — 批量启动返回的是**准入裁决**（已排队 / 仅控制面 / 因队列满被拒），
  逐环境的 `start` 动词表达不了这三种区别，而这正是操作者看到的东西。

**事件流**
- `runtime.state`（快照 + 增量）、`runtime.event`（**只带事实，不带展示文案**）、
  `runtime.commandDiagnostic`、`runtime.kernel.progress`、`runtime.browser.ready`、`runtime.blocked`、
  `runtime.failed{原因}`、`engine.controlReady`、`offboard.cleanupComplete`。
- `api.unknownOperation(名字, 关联 id)` — 由 §3.2 强制要求。

---

## 5. 须切开的接缝：模块级共享状态

这是「按类别写的所有权表」藏起来、而「按文件/行段写的清单」才暴露出来的东西。
下面每一条都是一个**双方都在读写**的模块级状态，它们决定了哪些块看似归属清楚、实际搬不动。

| 共享状态 | 归属 | 另一侧的读写者 | 不切开会怎样 |
| --- | --- | --- | --- |
| 环境注册表 | Host | 约 20 处产品侧通道靠它把环境 id 翻成环境键 | 这些通道全部返回「需要先选环境」；且解析函数找不到时**回落到当前选中环境**，会把发布草稿编辑、队列取消打到**另一个账号**上 |
| 设置对象 | Classic | 引擎侧读它取指纹浏览器密钥、本机 API 地址、平台、并发上限 | Host 拿不到用户配的密钥与自定义地址，整条指纹浏览器链路停摆；并发上限改了要重启才生效，而这正是这段代码存在的目的 |
| 「当前选中环境」 | Classic | 引擎侧的 `selectedHandle()` 用它做回落 | 退化成「注册表里的第一个环境」——多环境用户选了第二个，人设读取、发布草稿编辑、浏览器前置**全打到第一个上** |
| 主窗口 / 托盘 | Classic | 引擎侧三处失败弹窗（内嵌运行时启动失败、内核准备失败、浏览器缺失） | 要么 Host 引入窗口与通知能力（越界），要么**弹窗在搬迁中被丢掉**——而窗口默认关到托盘，用户可能永远看不到那条失败 |
| 槽位池与容量缓存 | Host | 产品侧设置面板读它；缓存由产品侧保存设置时置空 | 设置面板丢掉实时读数，或渲染层自己再算一遍（代码注释明令禁止：两处各算一遍必然漂移） |
| **退出中标志** | **真·双owner** | 引擎侧约 20 处读它判断「这次停止是不是故意的」，产品侧关窗逻辑也读它 | **两个方向都是坏的**：归 Host，则产品侧关窗永远收不到、应用**永远退不掉**；归 Classic，则退出时每个核心的退出都被判为异常，**收尾过程中反复重启核心**并弹「已停止运行」提示 |
| 浏览器停放几何 | Classic（要读显示器） | 引擎侧的启动参数构造器调它 | 每个核心丢掉停放参数：有头浏览器窗口全部落在平台默认位置、**N 个窗口叠在同一处**，用户设的停放模式被静默忽略 |

---

## 6. 四条推送通道（此前完全无主）

盘点原本只覆盖请求-应答类通道，独立复核指出：**还有 4 条引擎→界面的推送通道谁都没认领**。
只路由那 82 条，界面会没有状态、没有名册、没有活动流、没有批量进度。

| 通道 | 归属 | 说明 |
| --- | --- | --- |
| 状态更新 | **须切开** | 整个面里最严重的混合体：产品事实（环境名、客户会话态、上次发布、人设已绑）与引擎事实（云端/会话/认证/风险徽标、循环阶段、统计、内核准备、代理运行时…）在同一个对象里。且**引擎那半几乎全部来自正则解析日志**（见 §1） |
| 活动流 | **须切开** | 事实 100% 来自引擎，但今天由那张 22 条规则的正则表产生。**正则回退表绝不能带进 Classic**——那会把核心的日志措辞和协议命令名永久焊死在产品界面上 |
| 名册更新 | **须切开** | 身份块归产品侧；槽位容量/占用/队列深度归引擎侧；且每个环境元素里又嵌了一份完整状态投影，等于把引擎事实**广播了第二遍** |
| 批量代理进度 | **须切开** | 唯一一条「回给发起方」而非广播的流。逐项写入、单飞互斥与限频归引擎侧；关联 id、进度条与操作者文案归产品侧 |

---

## 7. 对既有「实测事实」的订正

盘点时喂给各路的前提事实里，有三条经对抗校验被推翻，逐条记录以免被再次引用：

1. **「只有两条非生命周期通道能命令运行中的执行侧」——低估了，而且低估的方式很重要。**
   至少还有两条（改环境昵称、落库人设）通过「更新状态」这个函数的连锁反应写到了核心的标准输入。
   **真正的接缝不是通道清单，而是「更新状态」这个函数的扇出**——任何未来调用它的产品侧通道都会
   自动继承这条到执行侧的路径。按通道清单画边界会漏。
2. **「删除环境走云端 HTTPS、完全绕过执行侧」——两处都错。** 它用的不是那条云端封装函数；
   而且只有视频号那条路走云端，其余平台的终局直接调指纹浏览器本机删除，删前还要触发注册表 reconcile
   （会停掉该环境的核心、释放它占的槽位）。整块判产品侧的话，删一个正在跑的环境会**云端撤销 + 名册移除
   成功，但它的核心还活着、还占着浏览器槽位**。
3. **「人设落库到不了执行侧」——错。** 见第 1 条。

另有两条一致性问题（唤起指纹浏览器桌面应用 vs 打开下载页这对孪生行为被分到了两边）已在 §2 台账里订正。

---

## 8. 行段归属清单（230 块，覆盖 1-7396 行无空洞）

分布：Host 119 · Classic 65 · 须切开 46。

| 行段 | 内容 | 归属 | 切分说明 |
| --- | --- | --- | --- |
| 1-5 | Electron/Node runtime imports (app+window+tray+ipc+notification+safeStorage, child_process.spawn, path/fs/crypto) | **须切开** | classic: line 1 (app/BrowserWindow/Menu/Tray/ipcMain/nativeImage/Notification/shell/screen/safeStorage). host: line 2 (spawn — the Core child launcher). shared/duplicated in both: lines 3-5 (path, fs, crypto). |
| 6-15 | Customer-auth security primitives and startup auth restore imports | Classic |  |
| 16-43 | Browser/AdsPower engine imports: chrome-launcher, Local API client, runtime + stage + fingerprint, proxy config/reassignment, env-group creation service, Facebook account import and batch create | Host |  |
| 44-47 | Facebook selected-persona template build and cloud auto-fill request imports | Classic |  |
| 48-67 | Runtime-event/diagnostic and browser-behaviour imports: os, UI event stream + stat merge, command diagnostics, proxy runtime/preflight, browser parking, browser cold standby | Host |  |
| 68-69 | Fleet roster/capacity module import and Core bootstrap supervisor import | **须切开** | classic: the roster half of fleet.cjs (envIdForProfile, normalizeEnvironment(s), migrateEnvironments, legacyMirrorOf, environmentWithOperatorAlias, nicknameSourceForPlatform, personaApplicableForPlatform). host: the capacity/launch half (buildEnvSpawnEnv, ENV_KEYS_MUST_DROP, stagger + serial launch queues, availableMemoryBytes/usableMemoryBytes, resolveSlotCapacity/resolveSlotSettings/startQueueAd |
| 70-75 | Persona notice text, persona keyword-selection validation and tray icon path imports | Classic |  |
| 76-77 | Native Page Engine artifact verification import | Host |  |
| 78-90 | Per-instance userData redirection (AIDCP_USER_DATA_DIR) before single-instance lock | Classic |  |
| 91-95 | Process-singleton AdsPower Local API client with 1 req/s serial pacing | Host |  |
| 96-128 | Module-level mutable state: window/tray handles, self-provider login poller, persona/publish-approval/browser-show stdin correlation maps, quit flags, Ads runtime base and managed daemon handle | **须切开** | classic: mainWindow, tray, isQuitting, quitFinal, quitStopAllInFlight, ADS_DOWNLOAD_URL (lines 96-97, 112-114, 126-127). host: loginPoller (self-provider Chrome login gate, line 98), browserShowPending + BROWSER_PARKING_REPLY_PREFIX + BROWSER_SHOW_COMPLETION_TIMEOUT_MS (lines 108-111, the browser.show stdin correlation bridge), adsServiceBase + managedAdsRuntime + adsRuntimeSessionResetComplete (l |
| 129-160 | Edge log file tee (rotating userData/logs/edge.log sink for Core child stdout/stderr) | Host |  |
| 161-216 | Cloud endpoint constants and build-baked defaults (automation WS URLs, customer data-API URLs, baked default env, WS/label helpers) | **须切开** | host: CLOUD_ENV_URLS, DEFAULT_CLOUD_URL, isWsUrl, cloudKeyForUrl, readBakedDefaultCloudEnv/BAKED_DEFAULT_CLOUD_ENV (lines 167-185, 204, 206-215) — these decide the Cloud<->Edge automation endpoint injected into Core. classic: CLIENT_AUTH_ENV_URLS, normalizeClientAuthUrl, readBakedClientAuthUrl/BAKED_CLIENT_AUTH_URL (lines 171, 186-203) — customer-auth data access base. shared display copy: CLOUD_E |
| 217-258 | DEFAULT_SETTINGS schema and the live settings object | **须切开** | classic (owner of the store and these fields): devDetails, railCollapsed, selectedEnvId, clientAuthUrl, clientAuthEnabled, clientRosterExclusionOwner, clientRosterExcludedEnvIds, pendingInteractionOffboards, environments roster, legacy adsProfileId/adsProfileName/platform mirrors. host (consumes as a config projection, and owns their meaning): provider, adsApiKey, adsApiBase, cloudEnvKey/cloudUrlC |
| 259-301 | Interaction offboard record normalization and client roster exclusion normalization | Classic |  |
| 302-327 | Settings file path and loadSettings (parse, defaults merge, legacy roster migration, mirror writeback) | Classic |  |
| 328-367 | Cloud settings normalization, automation URL resolution and the display-facing cloud selection view | **须切开** | host: resolveCloudUrl (344-360) and the cloudEnvKey/cloudUrlCustom half of normalizeCloudSettings (331-333, 335-338) — automation endpoint resolution consumed when spawning Core. classic: the clientAuthUrl half of normalizeCloudSettings (334, and the clientAuthUrl clause of the custom-downgrade check) and cloudSelectionView (362-366), which exists only to render 'which cloud are we on' in the shel |
| 368-386 | Customer login gate state: login window handle, client session, cloud-allowed env/platform/control-state maps, session timer | Classic |  |
| 387-392 | Core bootstrap supervisor construction (bounded-concurrency offboard cleanup worker) | Host |  |
| 393-425 | Customer data-API base derivation (explicit URL > baked > dev/ol default > derive from cloud host), auth-enabled predicate, combined cloud target view | Classic |  |
| 426-491 | Client session and login prefill secure local storage (safeStorage seal/unseal, atomic private writes, plaintext migration, validity check) | Classic |  |
| 492-591 | Session refresh gate, bounded customer-auth HTTP client (timeouts, idempotency headers, bounded JSON parsing), and login | Classic |  |
| 592-638 | Control-plane bootstrap: cloud-authoritative envKey to accountId resolution for browser-absent start | Classic |  |
| 639-781 | Interaction/customer-auth IPC bridge core: channel constants, argument and identifier validation helpers, per-env read cancellation registry, interactionCustomerRequest with scope check, IPC error wrapper | Classic |  |
| 782-814 | Refresh of cloud-visible environments (allowed profile ids, authoritative platforms, binding/persona control states) | Classic |  |
| 815-851 | Non-authoritative assignment warning wrapper and cloud environment-provisioning intent creation | Classic |  |
| 852-875 | Add a provisioned environment to the local roster (persist, rollback on write failure, reconcile handles, broadcast) | Classic |  |
| 876-900 | Finalize created-environment assignment against cloud (idempotent complete call with bounded retry) — first half | Classic |  |
| 901-953 | finalize a newly created environment: Cloud provisioning-complete call + local roster join | Classic |  |
| 954-970 | startup validation / restore of the saved customer session | Classic |  |
| 971-982 | session-invalid teardown: clear session, drop scope, close main window, return to login | Classic |  |
| 983-1022 | bounded backfill of pre-upgrade manual environment aliases to Cloud | Classic |  |
| 1023-1040 | login window creation | Classic |  |
| 1041-1089 | proceedAfterAuth: the whole post-login startup sequence | **须切开** | CLASSIC keeps: clientAuthEnabled/hasValidSession/refreshClientSessionIfNeeded/refreshAllowedEnvironments (1043-1056), clientRosterExclusionOwner settings write (1049-1053), syncUnsyncedManualAliases + retryPendingInteractionOffboards (1058-1059), loadUiState (1060), createWindow/createTray (1078,1081), startSessionMaintenance (1087), and the Chinese ready/待配置 copy in 1064-1074. HOST takes: syncEnv |
| 1090-1105 | session maintenance timer: sliding renewal + periodic re-scope | Classic |  |
| 1106-1150 | legacy single-environment mirror + saveSettings persistence of local shell state | Classic |  |
| 1151-1167 | cold-standby and browser-slot-limit normalization written into settings | **须切开** | CLASSIC keeps: the settings object write and persistence, plus the legacy `delete settings.maxAccountLimit` migration guard (1164-1165). HOST takes: the normalization/defaulting rules for cold standby and slot/queue limits (they are the resource-coordination schema) and slotViewCache invalidation (1166), which must be triggered by a 'config changed' notification from Classic rather than by Classic |
| 1168-1181 | browser parking plan from desktop display geometry | Classic |  |
| 1182-1204 | spawn-env builders: per-environment parking cascade + self-provider env | Host |  |
| 1205-1251 | baked AdsPower runtime credentials, single api-key resolver, ads provider spawn env | Host |  |
| 1252-1267 | resolveAdsOpts: AdsPower Local API base/key resolution for read+write calls | Host |  |
| 1268-1322 | maybeRenameEnvToNickname: keep the AdsPower environment name following the real platform nickname | **须切开** | CLASSIC keeps: the manual-alias branch (1284-1298) that writes systemName into settings and calls broadcastFleet, the manual-vs-system naming policy including the post-write manual guard (1308), the idempotence/in-flight de-dup decision, and the roster/display name update (1310-1311). HOST takes: resolveAdsOpts + createAdsWriteApi.renameProfile (1302-1306) and the honest-degradation semantics of t |
| 1323-1341 | open or focus the AdsPower desktop client, else open the download page | Classic |  |
| 1342-1397 | makeStatus: the per-environment status projection template | **须切开** | HOST takes the structured fields and their invariants (notably the tri-state personaBound default null and cloudEverConnected, both of which exist to stop 'unknown' being read as 'no'). CLASSIC takes the human-facing defaults — lastMessage (1366) and presence.text (1371) — which are Chinese UI copy that the renderer should render from the structured state rather than receive pre-written from the e |
| 1398-1414 | environment registry, current UI selection, proxy-preflight controller wiring | **须切开** | HOST takes `envs` (envId -> supervisor handle, 1400), `selectedProxyPreflightTimer` (1402) and the createProxyPreflightController wiring (1404-1414), which reads the profile's proxy config through the AdsPower Local API and writes structured proxyPreflight state. CLASSIC takes `selectedEnvId` (1401) — which environment the product UI has focused — and passes it to Host as a prioritisation hint. |
| 1415-1452 | proxy preflight eligibility and debounced scheduling for the selected environment | Host |  |
| 1453-1475 | proxy failure reason text + abort-the-start on proxy failure | **须切开** | CLASSIC takes the reason->text mapping (1454-1464) and the '自动化未启动：… 请修改代理后重试。' / presence wording. HOST takes the state transition in 1466-1475: refuse the start, set edge=stopped/session=idle and record the structured failure reason; the renderer renders the sentence. |
| 1476-1563 | makeEnvHandle: the per-environment supervisor handle | Host |  |
| 1564-1568 | resolve the current handle from the selected environment id | Host |  |
| 1569-1578 | pending interaction-offboard record readers over local settings | Classic |  |
| 1579-1675 | syncEnvHandles: reconcile the supervisor registry against roster + customer scope | **须切开** | CLASSIC computes the desired set (1581-1609: provider mode, settings.environments filtered by allowedProfileIds and roster exclusions, pending-offboard entries, cascade index assignment) and owns the trailing broadcastFleet (1665) plus refreshSameAccountWarnings (1664, a product warning). It also owns seeding the account label from roster data (1649) and feeding cloud-derived personaBound control  |
| 1676-1713 | enforceOwnedAutomationEngines: stop engines whose account binding is no longer trustworthy | **须切开** | CLASSIC owns the trust predicate (1683-1688: clientAuthEnabled, hasValidSession, allowedProfileIds membership, allowedEnvironmentControlStates bindingState === 'bound') and the CONTROL_BOOTSTRAP_REASON_ZH wording (1700-1710). HOST owns the enforcement: coreBootstrapSupervisor.remove, automationIntent='stopped' with engineStopReason='binding_untrusted', clearRespawnTimer and the SIGTERM of the chil |
| 1714-1743 | fleetSnapshot: the full renderer-facing fleet projection | **须切开** | CLASSIC owns the snapshot composition for the renderer — it is a renderer contract — including railCollapsed, selectedEnvId, the cloud selection/target views and all roster/naming fields. HOST supplies the runtime half through a typed read API: slot capacity/occupied/queued and transientQueueSnapshot (1723-1730) and statusOf(handle) (1740). Today Classic cannot build this without walking Host's `e |
| 1744-1750 | broadcastFleet: push the fleet snapshot to every renderer window | Classic |  |
| 1751-1758 | lifecycle stagger queue + queueLifecycle wrapper (AdsPower ~1req/s pacing for start/stop/re-login) | Host |  |
| 1759-1783 | serial browser launch queue + transient browser sidecar lane + lease timeout constant | Host |  |
| 1784-1791 | platform capability predicates: transient-browser-lane usage, persona applicability | Host |  |
| 1792-1801 | transient browser lane occupancy snapshot (capacity/occupied/queued/owner) | Host |  |
| 1802-1812 | sendTransientMessage — best-effort Node IPC send to the Core child | Host |  |
| 1813-1847 | transient browser lease settle + queued-lease cancel (with denial message to Core) | Host |  |
| 1848-1868 | awaitTransientBrowserRelease — lease deadline, escalates to SIGTERM on the Core child | Host |  |
| 1869-1951 | enqueueTransientBrowserLane + startTransientEnvironment (lane admission, grant/deny, optional Core spawn) | Host |  |
| 1952-1997 | per-environment lifecycle generation: isCurrent / advance (cancel queues, settle leases, clear timers) / ensureEnabled | Host |  |
| 1998-2033 | browser-slot capacity resolution: per-env byte budget, startup memory snapshot, slotSettingsView / slotCapacity / maxQueuedStarts | Host |  |
| 2034-2062 | occupiedSlots / queuedStartCount / releaseStartQueue — live slot and start-queue membership accounting | Host |  |
| 2063-2088 | reserveStartQueue — start-queue admission decision | Host |  |
| 2089-2096 | showStartQueueFull — surfaces a 'start queue full' status/presence patch | Host |  |
| 2097-2126 | launch-ready budget: LAUNCH_READY_TIMEOUT_MS, awaitLaunchReady, settleLaunchReady | Host |  |
| 2127-2138 | admitBrowserSlot — browser concurrency admission gate | Host |  |
| 2139-2190 | slot-wait queue doctrine block (rescan interval, cold-start floor, timer handle) + slotWaiters FIFO membership | Host |  |
| 2191-2215 | parkForSlot — enter the wait-for-slot FIFO, arm caller deadline, report queue position | Host |  |
| 2216-2258 | denyWakeNow (lifecycle.wake_denied to Core) + armWakeDeadline / clearWakeDeadline | Host |  |
| 2259-2299 | clearSlotWaiting + drainSlotWaiters (FIFO release into wakeColdStandby/startEdge) + slot-wait rescan timer | Host |  |
| 2300-2318 | bounded respawn policy constants (backoff, healthy uptime, env-in-use terminal guard) + clearRespawnTimer | Host |  |
| 2319-2360 | ui-state.json persistence (per-env lastPublish display history): uiStateFile / loadUiState / saveUiState | **须切开** | CLASSIC: the file path, read/write, JSON shape, corrupt-file tolerance and the legacy single-env migration — Classic owns the on-disk store and the userData path. HOST: nothing on disk; instead Host accepts a saved lastPublish value when an environment is registered (Classic supplies it) and emits a lastPublish-changed event when Core reports a publish. The direct mutation of handle.status inside  |
| 2361-2377 | Windows title-bar overlay tones + applyOverlayTone (tint window chrome by risk state) | Classic |  |
| 2378-2399 | daily-usage module import + statsFromDailyUsage (Core action counters → status stats) | Host |  |
| 2400-2420 | updateStatus — merge status patch, sync persona notice to Core, tint window, persist ui-state, broadcast to all renderer windows | **须切开** | HOST: the stats merge / loopStage normalization / Object.assign into handle.status / updatedAt stamping (2402-2408), the syncBrowserPersonaNotice(handle) call at 2409 (it writes a browser.personaNotice command to the Core child's stdin), and building the statusOf(handle) projection at 2415 — after which Host emits a 'status changed' event carrying that projection. CLASSIC: subscribing to that even |
| 2421-2430 | presencePatch + clearEdgeFailurePatch — status patch shape helpers | Host |  |
| 2431-2478 | Core exit/failure attribution: exitMessage, conciseFailureLine, rememberEdgeFailureCandidate, edgeFailurePatch, abnormalExitFailurePatch | Host |  |
| 2479-2486 | broadcastActivity — fan out an activity-stream entry to all renderer windows | Classic |  |
| 2487-2517 | surfaceFailure (restore/show/focus main window + notify) and surfaceNotification (system notification) | Classic |  |
| 2518-2554 | Electron window permission policy: permission labels, allowlist, throttled denial notice, installPermissionPolicy | Classic |  |
| 2555-2600 | frameOptions (per-platform title bar) + createWindow (main window, preload, close-to-tray behaviour) | Classic |  |
| 2601-2643 | createTray(): tray icon, context menu, show/hide, customer logout, quit | Classic |  |
| 2644-2656 | writeBrowserControlCommand(): the Core stdin control-command bridge | Host |  |
| 2657-2702 | Driven-browser persona banner: grace constant, readiness, grace reset, sync-to-core | Host |  |
| 2703-2710 | sendBrowserParkingCommand(): fire-and-verify wrapper for park/show commands | Host |  |
| 2711-2725 | focusAidcpAboveDrivenBrowser(): restore/show/focus/moveTop of the AIDCP main window | Classic |  |
| 2726-2745 | handleBrowserParkingReply(): match Core's browser.show ack, then raise the app window | **须切开** | HOST keeps: JSON parse of the core reply, pending-map lookup by id with envId ownership check, clearTimeout, resolve({ok}/{ok:false,error}) from the core's own ack (line 2727-2741). CLASSIC keeps: line 2742's focusAidcpAboveDrivenBrowser() call — after Host's promise resolves ok, the Classic 'browser:showDriven' handler raises the AIDCP window above the driven browser. Host must never call the win |
| 2746-2779 | showDrivenBrowserBelowClient(): compute client-aligned bounds, then command Core to move the browser | **须切开** | CLASSIC keeps lines 2750-2763: main-window liveness check, getBounds/getDisplayMatching/clientAlignedBrowserBounds and the 'window position invalid' honesty branch. HOST keeps lines 2747-2749 and 2764-2777: the engine-readiness precondition, requestId minting, browserShowPending registration, completion timeout and the stdin write. New seam: Host exposes moveDrivenBrowser(envId, targetBounds) -> P |
| 2780-2809 | sendPersonaCommand(): correlated persona RPC written into a specific env's Core stdin (currently unreferenced) | Host |  |
| 2810-2840 | sendPublishClientCommand()/sendPublishApprovalCommand(): publish approval RPC over Core stdin (currently unreferenced) | Host |  |
| 2841-2858 | applyPublishPreviewImages(): patch the env's publish preview after a cloud image delete | **须切开** | HOST keeps ownership of the per-environment status projection including publishPreview (produced by the core event stream) and must expose a narrow, validated state-patch entry point, e.g. patchPublishPreviewImages(envId, recordId, images, contentVersion), that keeps the recordId/contentVersion staleness guards at 2851-2853. CLASSIC keeps the cloud call and the decision to patch, and calls that Ho |
| 2859-2895 | handlePersonaReply()/handlePublishApprovalReply(): demux [persona-reply] / [publish-approval-reply] off Core stdout | Host |  |
| 2896-2913 | refreshSameAccountWarnings(): fleet-wide duplicate-account detection and warning flag | Host |  |
| 2914-2924 | scheduleRespawnIfNeeded(): bounded respawn backoff after core exit/spawn error | Host |  |
| 2925-2948 | sendCoreLifecycle(): narrow lifecycle intents over Node IPC to the core child | Host |  |
| 2949-3019 | failPendingCoreRebind() + requestCoreCloudRebind(): Cloud<->Edge transport rebind request/response | Host |  |
| 3020-3060 | Cold-standby bookkeeping helpers: timer clearing, hold timer, status shape, flag snapshot | Host |  |
| 3061-3120 | applyBrowserStandbyHint(): decide standby from the cloud's wait hint, incl. min-hold re-arm | Host |  |
| 3121-3150 | enterColdStandby(): request browser close via lifecycle.standby, honest failure rollback | Host |  |
| 3151-3188 | onColdStandbyAck(): core confirmed browser closed; free the slot and re-evaluate | Host |  |
| 3189-3208 | updateColdStandbyCloudRecovery(): reflect cloud reconnect/reconnecting while standing by | Host |  |
| 3209-3244 | scheduleColdStandbyWake() + rearmWakeRetry(): wake timer and 1/2/5min failure backoff | Host |  |
| 3245-3367 | wakeColdStandby(): queue admission, proxy preflight, browser-slot admission, lifecycle.wake | Host |  |
| 3368-3416 | onColdStandbyWoken(): core rebuilt the browser in place; clear standby, start min-hold clock | Host |  |
| 3417-3448 | onColdStandbyWakeFailed(): stay asleep honestly, tell the core, re-arm retry, release the slot | Host |  |
| 3449-3500 | startBrowserAbsentCore() (first half): control-plane-only core start without taking a browser slot | Host |  |
| 3501-3511 | status projection for "core starting, browser absent / not yet queued" | **须切开** | Host keeps the structured facts (edge='starting', session='resting', browserStandby=coldStandbyStatus('scheduled',{reason:'start_queue_full'}), clearEdgeFailure) as a runtime-state event; Classic keeps the Chinese lastMessage/presence sentence construction and the BrowserWindow status:update broadcast. |
| 3512-3528 | start core without a browser slot: spawn call, rollback, control-plane-starting latch | Host |  |
| 3529-3587 | restricted offboard cleanup: grant validation + Cloud cleanup-bootstrap fetch + refusal paths | **须切开** | Classic: pendingOffboardForEnv lookup, cleanupGrant presence/expiry/edgeId matching, the clientAuthFetch customer-auth call and its 401/403/404/409/410 interpretation, cleanupManual product state and every user-facing sentence. Host: receives an already-validated opaque bootstrap {accountId, offboardId} and owns only the consequence rule — a definitive rejection stops automatic core restart, a tra |
| 3588-3598 | spawn the restricted browserless cleanup core | Host |  |
| 3599-3619 | startEdge: cancel gates, start-queue reservation, timer clearing | Host |  |
| 3620-3625 | status projection for "queued for a browser slot (n/m running)" | **须切开** | Host emits occupied/capacity/queue-position as structured state; Classic renders the '排队等待启动槽位（当前 x/y 个浏览器在跑）' message and presence line. |
| 3626-3663 | serial launch queue run body: re-check gates, admit browser slot, park or spawn | Host |  |
| 3664-3684 | spawnEdgeChild entry: signature, re-entrancy/generation gates, control-plane flags | Host |  |
| 3685-3727 | core entry path + asar cwd guard + identity-gate spawn env + duplicate-edgeId guard | Host |  |
| 3728-3749 | Native Page Engine artifact resolution and signature verification for xiaohongshu | Host |  |
| 3750-3781 | cloud URL / egress-probe / bootstrap-mode env injection into the core | Host |  |
| 3782-3813 | per-run handle reset + spawn() with stdio ['pipe','pipe','pipe','ipc'] + start-queue release | Host |  |
| 3814-3847 | post-spawn status projection: engine restart state + publish card clearing + copy | **须切开** | Host: edge='starting', session, closeScope, cloudEverConnected=false, browserStandby, proxyRuntime, respawnGaveUp, connectedCloudKey/targetCloudKey/cloudRebind reset. Classic: clearing publish + publishPreview (the client in-app publish approval cards are customer product state, not engine state) and every Chinese lastMessage/presence variant plus the renderer broadcast. |
| 3848-3859 | core stdout/stderr wiring + Node IPC message router preamble and stale-generation filter | Host |  |
| 3860-3889 | cloud rebind reply handling (lifecycle.cloud_rebound / cloud_rebind_failed) | Host |  |
| 3890-3919 | transient browser lease lane: request admission/denial and release settlement | Host |  |
| 3920-3962 | interaction runtime proof ingestion (lifecycle.interaction_runtime) | Host |  |
| 3963-4009 | cold standby ack, executor failure teardown, wake request/woken/failed, standby cloud degraded/reconnected | Host |  |
| 4010-4017 | lifecycle.task_idle -> re-run the standby decision | Host |  |
| 4018-4046 | lifecycle.paused / lifecycle.resumed handling and resume-wake | Host |  |
| 4047-4067 | offboard cleanup complete: Cloud tombstone reconciliation then kill the cleanup core | **须切开** | Classic: reconcilePendingInteractionOffboard (Cloud tombstone polling over customer-auth HTTPS and local environment removal), the cleanupManual product state and the messaging. Host: matching message.offboardId to the running use-once core and SIGTERM-ing it, plus the rule that a cleanup core is never recycled into a general core. |
| 4068-4093 | lifecycle.close_failed: unconfirmed browser close becomes a retryable failure state | Host |  |
| 4094-4115 | child 'error' handler entry: crash-isolation rationale, rebind failure, launch-queue release, flag reset | Host |  |
| 4116-4152 | stale-generation late spawn failure: do not charge the new generation, restart if intent says so | Host |  |
| 4153-4183 | current-generation spawn failure: bounded respawn decision + failure surfacing | **须切开** | Host: fleet.decideRespawn, respawnStreak/gaveUp bookkeeping, scheduleRespawnIfNeeded, and emitting a structured 'core spawn failed (streak n/max, gaveUp)' event. Classic: surfaceFailure's window restore/focus + system Notification, and the Chinese failure sentence, auth='checking' relabeling and presence text. |
| 4184-4228 | child 'close' handler entry: why 'close' not 'exit', exit bookkeeping and abnormal-exit classification | Host |  |
| 4229-4260 | exit-during-cold-standby branch (incl. cleanup-core exit -> manual handling) | Host |  |
| 4261-4306 | env-in-use terminal classification, bounded respawn decision, kernel-missing recoverable path | Host |  |
| 4307-4367 | terminal exit status projection (full Chinese message/presence decision tree) | **须切开** | Host: the classification inputs and structured fields — edge stopped/warning, session derived from stopReason/wasClosing/wasRestarting/wasPausing/wasParked, risk reset to normal, adspower auth reset to checking, overlayBlocked, respawnGaveUp, and the edgeFailure payload from abnormalExitFailurePatch (exitCode/signal). Classic: the entire nested lastMessage/presence sentence tree (envInUse, user_pa |
| 4368-4381 | abnormal-exit desktop notifications (env-occupied vs stopped/gave-up) | Classic |  |
| 4382-4400 | schedule respawn, resume-after-stop restart, and intentional restart re-enqueue | Host |  |
| 4401-4407 | tail of startEdge: Core child exit → restart-pending respawn + serialized launch-ready await | Host |  |
| 4408-4460 | self lane: local Chrome launch + platform (xiaohongshu) cookie login gate before spawning Core | Host |  |
| 4461-4490 | AdsPower runtime single-flight registries (service + per-version kernel) and settings-panel read-with-recovery | Host |  |
| 4491-4507 | stage the bundled AdsPower CLI runtime template into a writable userData dir | Host |  |
| 4508-4584 | ensureAdsService: resolve CLI entry, reset stale session daemon, start/adopt runtime, establish single base authority | Host |  |
| 4585-4609 | ensureKernelOnce: per-version browser kernel download single-flight with progress | Host |  |
| 4610-4647 | pre-launch readiness = service ensure + kernel precheck (kernel version learned reactively from Core's start error) | Host |  |
| 4648-4690 | startAdsPowerFlow: adspower lane start — readiness, generation/cancel gates, proxy preflight, spawn Core | Host |  |
| 4691-4700 | startFlowForEnv: lane dispatch by environment kind (self / transient / adspower) | Host |  |
| 4701-4732 | enqueueStartFlow: browser start-queue admission, control-only browser-absent fallback, lifecycle queue submission | Host |  |
| 4733-4768 | queueStartEnv: start intent — advance lifecycle generation, clear terminal/cancel flags, enqueue | Host |  |
| 4769-4792 | stopAndRestart: SIGTERM-then-restart, shared by settings-save / re-login / resume | Host |  |
| 4793-4799 | handleEdgeOutput: Core stdout/stderr chunk → per-line dispatch with generation guard | Host |  |
| 4800-4834 | Core stdout early intercepts: persona reply, publish-approval reply, browser-parking reply, command diagnostics | **须切开** | HOST: the prefix demux itself and the command-diagnostics path (4818-4834) — parse the whitelisted structured line, merge into per-env structured runtime state, and guarantee the raw JSON never reaches the log. Also HOST: expose one generic request/response RPC over the Core stdio bridge. CLASSIC: handlePersonaReply (4803-4806) and handlePublishApprovalReply (4807-4810), which resolve promises own |
| 4835-4863 | Core log persistence with public-IP redaction + reactive 'kernel not ready' detection | Host |  |
| 4864-4887 | parking-ready flag + persona banner re-sync + 'stopping' suppression gate + failure-candidate memory + AdsPower env-in-use terminal verdict | **须切开** | HOST: browserParkingReady / browserOpenPending flags (4864-4866); the `stopping` suppression gate (4870-4887) that forbids flipping runtime badges during an intentional shutdown; rememberEdgeFailureCandidate (4873); fleet.classifyAdsInUse (4877-4883) whose verdict the exit handler consumes as a non-restartable terminal. CLASSIC: lines 4867-4868 — resetting browserPersonaNoticeState and calling syn |
| 4888-4960 | runtime-state derivation from Core log lines: halt whitelist, cloud connect/reject/disconnect/exhausted, browse-loop session axis, risk hint, launch-ready settle | Host |  |
| 4961-5081 | ui-event projection: identity + rename, persona tri-state, proxy runtime, publish cards, counters, activity stream, loop stage, overlay-blocked, standby hint | **须切开** | HOST: the Core event parse itself (handle.uiEvents.push, 4965); the identity-established fact next.auth='logged in' (4978); proxyRuntime normalization (4992-4995); the browserStandby hint and its cold-standby scheduling (5027-5030 plus applyBrowserStandbyHint at 5080 — that is browser-slot/resource coordination); the loopStage / loopStageBrowserIndependent runtime axis (5060-5066); and the overlay |
| 5082-5135 | pauseEdge: pause = stop tasks, disconnect engine, release browser slot (lifecycle.pause_and_exit over Node IPC, SIGTERM fallback) | Host |  |
| 5136-5190 | resumeEdge: resume path incl. cold-standby wake, control-plane-only wake, and restart-after-close deferral | Host |  |
| 5191-5246 | honest close verification with no Core alive: read-only AdsPower active-profile probe | Host |  |
| 5247-5300 | stopAutomation (opening two-thirds): user close — generation advance, cancel gates, queue/slot release, externally-occupied special case, no-child close path | Host |  |
| 5301-5316 | tail of stopAutomation: stopping-status patch + lifecycle 'close' to the Core child with SIGTERM fallback | Host |  |
| 5317-5350 | closeBrowserExecutor — put the browser executor into cold standby while keeping the Core connected | Host |  |
| 5351-5355 | relogin — stop-and-restart the environment's Core under the current browser settings | Host |  |
| 5356-5394 | startAllEnvs — bounded serial start queue across the fleet (accepted / control-only / rejected) | Host |  |
| 5395-5413 | stopAllEnvs and closeAllEnvs — fleet-wide pause / stop-automation fan-out | Host |  |
| 5414-5426 | stopManagedAdsRuntime — stop the AdsPower CLI daemon this process started | Host |  |
| 5427-5456 | gracefulStopAllAndQuit — quit sequence: stop login poller, kill every Core, bounded wait for honest shutdown, stop Ads daemon, then app.quit() | **须切开** | HOST: clearing respawn/cold-standby timers, stopLoginPoller (the self-Chrome login gate poller), SIGTERM of every Core child through queueLifecycle, the bounded ~10s wait for children to exit honestly, and stopManagedAdsRuntime — exposed as a single 'shutdown all and confirm' call. CLASSIC: the quit-in-flight/isQuitting/quitFinal guards, the selectedProxyPreflightTimer cancellation (UI-selection d |
| 5457-5461 | quitApp — renderer/tray-facing quit that routes through before-quit | Classic |  |
| 5462-5481 | reconcileRunningProfiles — startup reconciliation of already-running AdsPower profiles (read-only V2 active probe) | Host |  |
| 5482-5487 | IPC routing header + resolveHandle(envId) — envId routing key with fallback to the currently selected environment | **须切开** | HOST: the envs.get(envId) lookup against the per-environment supervisor registry — Host APIs should take an explicit envId. CLASSIC: the selectedHandle() default, i.e. resolving 'no envId given' to the currently selected environment, which is renderer/product state persisted in settings. Classic resolves the default and always passes an explicit envId across the boundary. |
| 5488-5601 | lifecycleAxes — derives clientSessionState / engineLinkState / coreState / automationState / browserState (incl. transient-browser lane variant) | **须切开** | HOST: coreState, engineLinkState, cloudState (compat alias), browserState and automationState including both the persistent and transient-browser-lane branches — this is the structured runtime state Host publishes. CLASSIC: clientSessionState (clientAuthEnabled()/hasValidSession()) is customer-auth state and must be merged onto the Host-published axes in the shell, not read inside the Host project |
| 5602-5627 | lifecycleQueueProjection — queue stage and provable numeric queue position (transient / slot / launch / preparing) | Host |  |
| 5628-5661 | statusOf — composes the full per-environment status payload sent to the renderer | **须切开** | HOST: handle.status, lifecycleAxes' engine axes, lifecycleQueueProjection, and commandDiagnostics pruning — published as a structured runtime-state snapshot per envId. CLASSIC: envName, the personaApplicable/browserUsageMode product flags, targetCloudKey defaulting from the UI cloud selection, and the no-handle fallback object (which encodes clientSessionState for a signed-out shell). Classic comp |
| 5662-5662 | status:get — renderer polls the composed environment status | Classic |  |
| 5663-5739 | edge:pause / edge:resume / edge:close / browser:close / browser:open handlers — the automation lifecycle control surface | Host |  |
| 5740-5744 | auth:relogin handler — restart the engine for a fresh login | Host |  |
| 5745-5772 | settings:get — returns settings, offboard cursors, cloud selection, appVersion and live slot occupancy | Classic |  |
| 5773-5799 | client-auth:* — customer login, logout, session probe, credential prefill and prefill clear | Classic |  |
| 5800-5899 | interaction list/detail/draft-update + slow-start get/set + environment-risk get/recover — named cloud customer-API calls | Classic |  |
| 5900-5915 | interaction:approve / interaction:regenerate — templated pair of reply-action cloud calls | Classic |  |
| 5916-6002 | interaction send / ignore / escalate / sync / test-reset / auth:reopen — cloud customer-API actions | Classic |  |
| 6003-6017 | interaction:browser:control — ask Cloud to open/close the interaction sidecar browser | Classic |  |
| 6018-6064 | interaction:browser:open-local — customer-scoped manual inspection open of the WeChat Channels profile through the local AdsPower runtime | **须切开** | CLASSIC: hasValidSession/allowedProfileIds/allowedEnvironmentPlatforms scope enforcement and the 403 INTERACTION_SCOPE_MISMATCH responses (customer auth), plus the renderer-facing result shape. HOST: locating the adspower handle by profileId, ensureAdsServiceOnce (runtime init), ensureKernelOnce (kernel provisioning), adsApi.openProfileForInspection (AdsPower Local API), and setting handle.browser |
| 6065-6078 | interaction:read-controls:update — cloud PUT of comment/DM read toggles | Classic |  |
| 6079-6093 | interaction:notify — local desktop notification for new interactions | Classic |  |
| 6094-6099 | interaction:reads:cancel — abort in-flight customer-API read requests for an env | Classic |  |
| 6100-6158 | settings:save — scope-filter and persist settings, then sync the environment registry and return the refreshed view | **须切开** | CLASSIC: stripping renderer-forgeable fields (pendingInteractionOffboards, clientRosterExclusionOwner), the allowedProfileIds scope filtering of environments/adsProfileId/clientRosterExcludedEnvIds, saveSettings persistence, broadcastFleet to the renderer, and returning the settings view with saveOk/saveError. HOST: syncEnvHandles (register new env supervisors, tear down removed ones with SIGTERM, |
| 6159-6183 | cloud:restartAll — rebind every running Core to the currently selected cloud target | Host |  |
| 6184-6200 | edge:start — start automation for one environment (wake cold standby or enqueue a staggered start) | Host |  |
| 6201-6206 | 「按新设置重启」IPC:显式停+重启目标环境核心 | Host |  |
| 6207-6208 | fleet 控制面段首 + fleet:get 花名册快照 | Classic |  |
| 6209-6218 | fleet:select 选中环境(持久化+窗口染色+广播+代理预检) | **须切开** | CLASSIC: selectedEnvId persistence via saveSettings, applyOverlayTone (window chrome), broadcastFleet to renderer. HOST: scheduleSelectedProxyPreflight/ensureProxyPreflight — it reads the profile's proxy config off the AdsPower Local API and writes a proxyPreflight snapshot into runtime state; Host should expose 'selection changed -> preflight' as an API/event Classic calls. |
| 6219-6301 | fleet:setManualNickname 运营别名一致写(本地花名册+云端 alias+浏览器横幅重推) | **须切开** | CLASSIC: the whole alias transaction — validation, allowedProfileIds scope check, saveSettings/rollback, clientAuthFetch operator-alias PUT, confirmed-name reconciliation. HOST: syncEnvHandles() registry resync and the syncBrowserPersonaNotice stdin re-push after rename; Classic should emit an 'environment renamed' event that Host reacts to. |
| 6302-6304 | fleet:startAll / stopAll / closeAll 全体启停 | Host |  |
| 6305-6308 | fleet:setRailCollapsed 环境栏折叠偏好 | Classic |  |
| 6309-6329 | persona:preview-facebook-template / fill-facebook-selected(FB 人设模板+云端批量补齐) | Classic |  |
| 6330-6333 | browser:openAdsDownload 打开指纹浏览器下载页 | Classic |  |
| 6334-6339 | browser:showDriven 把被驱动浏览器抬到客户端下方/前台 | **须切开** | HOST: writeBrowserControlCommand('browser.show', {requestId, bounds}) over the child's stdin, the pending-reply table and the completion timeout (browserShowPending / handleBrowserParkingReply). CLASSIC: computing client-aligned bounds from the Electron window + display, and re-focusing the main window after the Core confirms. Boundary = Classic passes bounds in and gets a completion promise back. |
| 6340-6340 | browser:resetParking 复位浏览器停靠位置 | Host |  |
| 6341-6447 | 人设 IPC 骨架(envId→envKey 解析/失败归一/包装)+ persona:get / generate / persist | Classic |  |
| 6448-6526 | publish:approval 客户端内审批 + publish:image-remove 预览删图 | Classic |  |
| 6527-6588 | delegatedTaskRequest 客户令牌请求出口 + delegated-task:list / draft / action | Classic |  |
| 6589-6682 | publish-draft:list/get/edit/refine/refinement-get + publish-schedule:occupied-hours | Classic |  |
| 6683-6729 | environment-overview:get / environment-schedule:get / publish-queue:get / publish-queue:cancel | Classic |  |
| 6730-6779 | curated:summary / list / get / create-post 灵感库四条具名 IPC | Classic |  |
| 6780-6785 | notify:show 本地系统通知 | Classic |  |
| 6786-6787 | ads:status AdsPower 运行时只读探测 | Host |  |
| 6788-6824 | ads:listProfiles 本机分身枚举 + 按客户归属收窄 | **须切开** | HOST: readAdsWithRuntime -> adsApi.listProfiles (raw machine-local profile list). CLASSIC: session validity + refreshAllowedEnvironments, the fail-closed logout returns, allowedProfileIds/roster narrowing, physicalUserIds computation and offboardPending annotation. Host must return the unfiltered machine list to Classic, which alone decides what the logged-in customer may see. |
| 6825-6826 | ads:openCreate 唤起 AdsPower 客户端 | Host |  |
| 6827-6840 | 建号编排前置:环境分组解析器 / 建号与改代理单飞互斥 / OS 家族标签 + ads:templates | Host |  |
| 6841-6994 | ads:createEnv 程序化建指纹环境(单建/FB 批量)+ 云端配额意图与分配收尾 | **须切开** | HOST: runtime readiness, write-API construction, fingerprint/OS-family selection, group recovery, per-item creation loop and the AdsPower-facing failure receipts — i.e. 'create N local profiles with these fingerprints/proxies'. CLASSIC: createEnvironmentProvisioningIntent, finalizeCreatedEnvironmentAssignment, safeCreatedEnvironment's assignment/roster/slowStart fields and the visibilityWarning te |
| 6995-7006 | ads:getEnvProxy 读取单环境完整代理配置(含凭据) | **须切开** | CLASSIC: proxyTargetScope authorization and the 403/session-expired shaping — customer scope is Classic-owned. HOST: the AdsPower proxy-config read with runtime recovery. Classic must authorize first and then ask Host for a specific userId; Host must not reach back into customer-auth state. |
| 7007-7026 | proxyTargetScope 代理操作归属门禁 | Classic |  |
| 7027-7040 | proxyTargetActive 目标环境是否在使用中 | Host |  |
| 7041-7056 | AdsPower 代理写失败文案归一(单项/批量) | Host |  |
| 7057-7070 | 批量改代理进度:请求标识校验 + 向渲染层推进度 | Classic |  |
| 7071-7077 | invalidateProxyEvidence 代理改动后作废预检证据 | Host |  |
| 7078-7083 | ads:parseProxyLines 粘贴代理文本纯解析 | Host |  |
| 7084-7116 | ads:updateEnvProxy 改单个环境代理 | **须切开** | CLASSIC: proxyTargetScope authorization only. HOST: everything else — normalizeProxyInput, the write mutex, active-environment refusal, runtime ensure, the Local API write and proxy-evidence invalidation. |
| 7117-7193 | ads:updateEnvProxies 批量改代理(计划/逐项写/进度/部分失败回执) | **须切开** | CLASSIC: proxyTargetScope authorization and forwarding progress to the renderer. HOST: createProxyReassignmentPlan execution, the write mutex, per-item re-check of proxyTargetActive, ensureAdsServiceOnce, writeApi.updateProfileProxy per item, evidence invalidation and the partial-failure receipt. The onProgress callback must become a Host-emitted structured event that Classic relays; Host must nev |
| 7194-7228 | 待清理解绑游标本地持久化(存/更新/完成清理/轮询等待) | Classic |  |
| 7229-7246 | deletePhysicalEnvironmentAfterTombstone 云端墓碑后真删本机分身 | **须切开** | HOST: runtime readiness + writeApi.deleteProfile + the already-missing/in-use interpretation, returning a structured outcome. CLASSIC: finishLocalInteractionOffboard (pending cursor + roster removal, persistence honesty) and the user-facing cleanupPending messages. This is the one place ads:deleteEnv genuinely needs a Host capability. |
| 7247-7283 | 解绑对账轮询 + 启动后重试挂起解绑 | Classic |  |
| 7284-7326 | ads:deleteEnv 删除环境(视频号先云端解绑→墓碑→物理删) | Classic |  |
| 7327-7366 | 单实例锁 + app.whenReady 启动引导(加载设置/会话/登录门/activate) | Classic |  |
| 7367-7379 | 监督者级未捕获异常/拒绝兜底 | Classic |  |
| 7380-7393 | before-quit 退出前有界收尾(停全部核心+停托管 Ads 运行时) | **须切开** | CLASSIC: the app.on('before-quit') hook, the 'nothing running' fast path and preventDefault/quit sequencing. HOST: a shutdown() that stops all Core children and the managed AdsPower runtime and resolves; Classic awaits it and then quits. Today the fast path also inspects handle.child and managedAdsRuntime directly — that predicate must come from Host. |
| 7394-7396 | window-all-closed 阻止关窗即退出 | Classic |  |
