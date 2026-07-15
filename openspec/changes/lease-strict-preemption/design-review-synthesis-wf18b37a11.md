<!-- 自动保存：设计评审 workflow wf_18b37a11-416 的总装配方案（synthesis agent 原样输出）。
     注意：本文档 P0-a 写「等 browser-slot 归档」为启动硬门，那是依据 tasks.md 旧注生成；
     2026-07-15 已用 git 实证确认 browser-slot 协调器改动已在本分支地基、逐字节等同 master、无活跃 worktree 在改——
     该闸【已清】，以 handoff-section-5-preemption-core.md §0/§3 为准。其余分批/holes/锚点结论有效。-->

I have full context now (ground map + holes + complete tasks.md §5–13 + §12 real-machine items). Here is the final assembly plan.

---

# 最终实装方案 — lease-strict-preemption 抢占核心（§5-8 edge + §6 协议 + §7 cloud + §8 静默丢弃 + §10 spec）

## 0. 前置结论（动手前必须成立的硬门，非本方案能自解）

**P0-a 排它写者门（start-blocker，外部依赖）**：§5 推进边界（tasks:75）已由 fleet 定序——协调器 `edge-task-coordinator.ts` 与装配入口 `main.ts` 正被活跃 change `browser-slot-scheduling` 重改（master 已到 `809e15d`，本 worktree 分叉于 `84267f2`、当前 HEAD `35d3aec`）。**在 `browser-slot-scheduling` 落定/归档前，绝不同时大改协调器**。动手第一步 = 等它归档 → 本 worktree rebase 到最新 master → 消化 §1-4 与 slot 改动交叉 → 才独占实装。这不是可绕过项。

**P0-b 用户禁区门（start-blocker，需协调）**：main.ts 的「FB 租约闸节奏豁免段」在**本 worktree committed 态里根本不存在**（实测 35d3aec / master / 全部 codex 分支：唯一的 `env.type !== 'pacing.update'` 穿透只在 XHS handler `main.ts:1145`）。用户正把它 graft 进 FB handler（镜像 XHS），是未提交的并行工作。**rebase 到用户分支后，禁区行号会重新长出且不可预测**——所有 main.ts 落点必须在用户豁免段合并后、按内容特征重新定位（见 §2）。

**P0-c 协议先行不变量**：§5 边缘 emit 新原因而 §7 云端不认 = 烧稿（第 4 节血教训同型）。落地序**焊死**为：先 §6 协议（inert 安全）→ 再 cloud「认而不烧」→ 最后 edge「真 emit + 真抢占」与 cloud「主动抢占」co-deploy。据此分三批（§1）。

---

## 1. 分批实装序列（commit 粒度 + deploy 原子性）

### 批 1 — 协议 + docs + 往返断言（edge+cloud，可独立部署，inert 安全，必须最先落）

| commit | 内容 | 文件:行 |
|---|---|---|
| 1a | 6.1 新增 3 原因 + 6.2 新增「已派发提交」布尔位，**两份 protocol.ts 逐字同改** | edge `src/comm/protocol.ts` EdgeTaskReleasedPayload.reason:1296 / PublishCommandResultPayload:910；cloud `src/comm/protocol.ts` :1289 / :903 |
| 1b | 6.3 docs 同步：**先回填既有缺口 `browser_wake_failed`**（doc 只列 5 个、代码已 6 个）再加 3 新原因 = 9 个；补 publish.command.result 的布尔位字段文档；**头部计数保持 76 不变**（§6 不新增 MessageType，「含头部消息计数」是 no-op） | `docs/protocol.md` :141 表行 / :773-774 示例 / :19 计数 |
| 1c | 6.4+11.9 往返断言：**两仓各加 AC-PROTO-14（3 原因裸值）+ AC-PROTO-15（布尔位字段存活）** | edge/cloud `test/acceptance/protocol-contract.test.ts:34` 区（ALL_MESSAGE_TYPES 穷举在此文件、非 protocol.ts；计数仍 76） |

**测试**：两仓 `typecheck` + `test:acceptance`。**可单独部署**（新联合成员无人 emit、布尔位无人读 = inert 无害）。满足「先 6」。

### 批 2 — cloud「认而不烧」（修今日既存 bug，edge 抢占 emit 前落地即安全）

关键洞察：§7 大半修的是**今天就在烧稿**的路径（task_lease_mismatch 边缘已 emit / post_validate_failed / 暂停期投递 0 / edge.post 三态塌成 false），与抢占无关，先落只会让 cloud 更宽容、不引入新险。

| commit | 内容 | 落点 |
|---|---|---|
| 2a | **7.1 第四终局 + command-sequencer `preempted` outcome（HOLE-1）**：在 command-sequencer 的 `ok:false` 分支（:240→:258）与 catch（:219→:238）识别抢占原因串（preempted_by_task / task_lease_mismatch / window_busy / yield_timeout）→ 产出**独立 `preempted` outcome，绝不并入 failed_before_submit**；publish-dispatcher 在 :380 之前加分支：`preempted` → 保持 pending、不写 failed、不 recordSeqFailure、FB 素材归还、保留授权签名、事件驱动重投 | cloud `src/publish-agent/command-sequencer.ts:238/258/265` + `publish-dispatcher.ts:380-409` |
| 2b | **6.2 消费（HOLE-2）**：command-sequencer 的 `cmd.kind==='submit_publish' && !result.ok` 分支（:258）读布尔位——dispatched=true → outcome=`submitted_unconfirmed` 落 dispatcher :371（转 submitted、不失败、不熔断、不重试）；dispatched=false 才 failed_before_submit。**修今天 post_validate_failed 被烧成 failed** | command-sequencer.ts:258/265 |
| 2c | **7.1「已开始」下移（HOLE-13）**：`sequenceStarted`（:343）判据锁成「**首条产生平台副作用的命令真正 sent>0 之后**」——navigate 类无写步骤不计、投递 0 不算「已开始」，保证暂停期/navigate 前抢占走 :388-401 零副作用回待审 | publish-dispatcher.ts:343 |
| 2d | **7.3 硬暂停闸**：下发前加 isEdgePaused 闸；投递数为零按零副作用回待审、不 reject 烧 failed。机制横跨两文件须一并理解 | publish-dispatcher.ts:321-344 + ws-server.ts:212-222 bypassPause 白名单 + command-sequencer.ts:308-312 |
| 2e | **7.4 task_lease_mismatch 接线**：云端全仓 0 命中 → 加识别，归入 `preempted` 语义（边缘 main.ts:727/811 今天已 emit） | cloud `src/comm/handler.ts`（新增分支） |
| 2f | **7.6 edge.post 三态升级（HOLE-8）**：`edge.post()` 从 `Promise<boolean>` 升为三态（confirmed / submitted_unconfirmed / not_dispatched，沿用 §3.2 已在线的 `submitted_unconfirmed` reason）；去重账本写入门（comment-scheduler:1351）改为「提交已派发（confirmed∪submitted_unconfirmed）」而非 `ok===true`；补集判据 isEdgeTaskAcquireFailure(:1523) 对「提交点之后」不得判 not_started | cloud `comment-agent/edge-steps.ts:292/150/311` + `comment-task-runner.ts:59` + `comment-scheduler.ts:1344/1351/1365-1373/1523` |

**测试**：cloud `test:acceptance` + `test` + `typecheck`。**可单独部署**：这些只让 cloud 更宽容今天的烧稿；唯一新 emit（preempted_by_task）edge 侧尚未产生，那些分支休眠；task_lease_mismatch/post_validate_failed/edge.post 三态严格改善今天的烧稿。preempted 保持 pending 的重投触发器在无人抢占时不触发。

### 批 3 — edge 抢占真 emit + 协调器 + main.ts + cloud 主动抢占（**必须与批 2 同在线，内部多 commit、整体 co-deploy**）

> 本批是「抢占上线」的不可分单元。批 2 必须已在生产。edge emit 与 cloud 主动抢占同一次 rsync 部署，避免 8.1↔7.8、5.3↔7.1/7.4/7.5 的单边窗口。

**edge 协调器（不碰 main.ts）**：
- 3a **5.6**：DEFAULT_ACQUIRE_TIMEOUT_MS 边云一致（edge `edge-task-coordinator.ts:63`=45s vs cloud 200s），或对缺 acquireTimeoutMs 的申请诚实拒绝。先落，小。
- 3b **5.2 页面写者注册表**：单一浏览闸泛化成注册表（每写者提供 取消/有界让位/是否在提交窗口）。**HOLE-4 强制项：canExecute（:207-212）在「有在途发布写者登记」时也返回 false**，不只保留 active/quiescing/queue/browseBlocked——否则 post-validation 期新浏览命令仍会导航发布页。接口 `EdgeTaskBrowseGate:8-16`。
- 3c **5.4 抢占**：drain 入口守卫（:293-294 `if(this.active||this.quiescing)return`）改为允许严格高档打断；复用 pickNext 档位比较（:259-271，priorityDelta:265，同档 FIFO=到达序）；acquire（:109-144）比较来者与在跑者 priority；窗口占用时立刻回「窗口占用中+剩余预算」不空等；quiesce+授予序列 :305-346。
- 3d **5.9**：resumeBrowseIfIdle（:372-381）让位于在途发布写；**5.2 的 canExecute 与 5.9 的 resumeBrowseIfIdle 都必须读同一在途发布写者登记**（HOLE-4）。
- 3e **5.5 让位超时→控制面故障（HOLE-3/HOLE-11 强制项）**：timeout 时刻**重读提交窗口标志+剩余预算**——标志=set → 走 5.4「窗口占用中+剩余预算」把剩余等出来、**绝不判故障**；只有「标志=clear 却仍在写」判控制面故障→整队诚实拒绝→退运营重启（10.4）。**禁用「quiesce 抛出即故障」的算术边界代替语义判据**。

**edge 提交窗口标志 + 六处（不碰 main.ts，纯 flow 文件）**：
- 3f **5.1 六处提交窗口标志（HOLE-9 强制置位语义）**：置真在「**按下事件真正发出的那一刻**」，center 查找类失败保持 false，与 6.2 布尔位同一时机、**语义与 5.1 窗口标志相反（窗口标志 SET 在点击前、6.2 位 SET 在点击后），MUST NOT 复用同一标志**：
  - XHS 发布 `publish-command-handlers.ts` runSubmit@892，SET 在 942/943（点击 try 成功后、pollBounded 之前），窗口≈15s
  - FB 发布 `facebook/publish-executor.ts` submit@488，SET 在 498 dispatchClick 后、waitUntil 前，窗口≈20s（**统一上界**）
  - XHS 评论 `browse-session.ts` executeComment@2391，最后取消点 2496，SET 在 2496 后 2511 前，窗口≈4s
  - FB 评论 `facebook/comment-executor.ts` submitComment@459，最后取消点 530，SET 在 530 后 536 回车前，窗口≈20s
  - **FB 加群 `facebook/join-executor.ts` joinGroup@613（evalJson@677，真 click 在 GROUP_JOIN_CLICK_JS@592）—— 与 5.10(b) 同批原子交付（HOLE-3）**：(a) 给 joinGroup/onJoin 穿 checkpoint 让 observeUntilReady(≤30s) 观察前缀可抢占；(b) observePostClickUntilSettled(≤45s) 拆成窗口内短确认(≤~18.5s)+其余可抢占，受保护窗口收窄到 click+短确认≤20s。**5.10(b) 从「顺手项」提为与 5.1 加群窗口同一 blocking 交付，不可一 blocking 一 deferrable**。
  - **通知巡视两处 `browse-session.ts` browseNotificationComments 分类点击@3019 / viewNotificationCategory 分类点击@3068**：点击即消费未读、无回滚游标 → **窗口内 MUST 拒绝抢占、MUST NOT 在段内加 §4 checkpoint**（加=中途租约到期抛出→已消费未上报的一整波未读永久丢失）。此处窗口标志与 §4 语义互斥、§4 刻意缺席。

**edge main.ts（**均需先与用户协调**；禁区见 §2）**：
- 3g **5.8 删遗留整页发布处理器** `main.ts` onPublishCommand:596-659（真闭合 659，非 tasks 写的 639）。**删除前 MUST 实证核对 cloud command-bridge/dispatcher 确无 `publish.request` 出口**（否则删=静默丢一条真发布命令、零回执、云端干等超时）。删 ~64 行会把下方 FB/XHS handler 与禁区整体上移 → 删后按内容重定位一切。
- 3h **5.3 发布执行流注册为第二写者 + 真取消**：onPublishAtomCommand 外层 735-800、游离 IIFE 754-799。登记覆盖**整个 dispatch()（含 post-validation）**（HOLE-4）；注入取消 signal（今天 main.ts dispatch 只传 payload、不传 takeover ⇒ runSubmit 三处 checkpoint 恒 no-op，符合「铺管不注入」，此批才翻真）。**是 publish handler、与 browse/pacing 禁区结构隔离**。
- 3i **8.1 三处静默丢弃补诚实回执**（HOLE-2/HOLE-12/HOLE-13）：
  - XHS browse warn 1145-1150 → 补 `preempted_by_task ok:false`，**保留 1142-1145 pacing.update 穿透**（非禁区，改 body 不改条件）
  - **FB comment-only warn 879-884 与 FB browse warn 1075-1080 = 禁区本身**（一旦用户豁免 graft 进来）：见 §2，须排在用户豁免合并后、按内容定位、对**全部三处**保留 `env.type!=='pacing.update'` 穿透
  - browse-session.ts quiesceForTask 让位清队 964-966（`this.commandQueue=[]`）→ 对被清命令补回执
- 3j **8.2 巡视合成终态回执（HOLE-10 强制注入点）**：合成 `notification_back_home ok:false, reason:preempted_by_task`（照抄断连模板 browse-session.ts:1360/1368），**只在「任何在飞巡视操作已 settle（waitDrained 返回）且确认本会话正处于巡视 excursion」时发一次**，绑到 quiesce 成功/抢占授予收尾处——**不是 quiesce 清队那一刻**（在飞巡视还在跑、还会发数据事件 → 假终态）、**不是 per-command catch**（这三条无 checkpoint、到不了）、**动作名固定合成名 notification_back_home、绝不用 cmd.type**（:1346 通用路径用 cmd.type='notification.open'，云端 excursion_resumer 不认）。

**cloud 主动抢占语义**：
- 3k **7.5 活跃租约中断通道（HOLE-7 强制形态）**：收到被抢占/让位超时/排队超时释放 → **让在飞的那条 publish.command 就地 reject**，交 runSequence 按 submitted(238/258) 归类，**绝不 unwind 掉 executePublishSequence**（否则 catch 处拿不到 submitted 状态无从安全判别 → 提交后被抢的已发帖被重投双发）。7.1「保持待审重投」只允许 outcome==='failed_before_submit' 且原因为抢占；`submitted_unconfirmed`（含提交后被抢）一律走 371-379 submitted 终态、绝不重投。落点 edge-task-lease-client.ts:210-244（onReleased 今天对活跃租约只 active.delete）/ 173-189（withLease 无外部中断入口）。
- 3l **7.8 兜底滚动原因级短路（HOLE-12）**：「被抢占」插在 noRecoverScroll 名单判断**之前**（真实位置 role-dispatcher.ts:**2269-2278** 名单 + **2279-2282** 触发，tasks 写的 2149-2162 错位 ~120 行）——open_note/refresh/profile_open 不在名单，补诚实回执会立刻触发恢复滚动滚到抢占方页面。**必须与 edge 8.1 同 deploy**。
- 3m **7.7 巡视租约被撤 + 空闲停表**：撤租约接既有失败出口（beginNotificationTask:569-622，今天只覆盖 acquire 失败:588-592/616-618）；独占租约期会话空闲时钟停表（净新增，session-monitor-role.ts:211 checkIdle/153 pauseClock，注意 pauseClock 今天明确不冻 idle 看门狗；阈值现为 idleEnd≈1h/idleNudge≈2min，**勿沿用旧 240s**）。
- 3n **7.9 FB 评论走租约**：三条命令（facebook-edge-steps.ts search.execute:168/note.open:204/interaction.comment:233）补 taskId，纳入租约门控，否则租约在跑时被边缘静默丢弃。
- 3o **7.2 抢占计数+退避**（阈值建议 3，停自动重投+通知运营）、**7.10 验证码受理超时 20s→45s**（captcha-assist.ts:349-368，覆盖最长 20s 窗口+停手+让位+往返；同事件多次提交改续租）、**7.11 抢占原因进加群瞬态白名单+人工加群档位一路传下去**。
- 3p **9.1 优先级口径**：发布派发处不按触发路径给档、硬定自动档；人工档只留手动评论/手动加群/客户端内审批即时动作。

**spec + 收口**：
- 3q **10.1 delta 改写（HOLE-5）**：MODIFIED #1 的 header 从「任务优先级严格生效…」**改回主 spec:62 原名「任务优先级与同级 FIFO 可预测」**（对照 MODIFIED #2:31 与主 spec:38 逐字一致），或补 `## RENAMED Requirements(FROM/TO)`；重定义两条既有回归 Scenario（人工评论先于排期发布:66-68、恢复任务不强杀已提交动作:74-76）。**openspec validate --strict 通过掩盖此洞，只在 archive 期暴露**。
- 3r **10.2** 四条新 requirement（清场协议/有界让位与超时升级/被抢占第四终局/巡视窗口保护）、**10.4** 写明控制面回收=人工重启客户端非自愈。
- 3s **11.2-11.8 测试** + **11.8 参数一致性断言扩项（HOLE-3）**：断言云端受理预算 **且边缘等停预算** ≥ 最长提交窗口(20s)+取消停手+让位+往返。

**测试/部署**：edge `test:acceptance`→`test`→`typecheck`，cloud 同。co-deploy dev。

---

## 2. main.ts 禁区边界 + 我的每个编辑点

**禁区定义**：main.ts「FB 租约闸节奏豁免段」。**committed 态不存在**；用户未提交、将 graft 进 FB handler，镜像 XHS `main.ts:1142-1145`（`if (env.type !== 'pacing.update' && !taskCoordinator.canExecute(...))`）。**rebase 到用户分支后按内容特征定位，绝不认行号**：条件行 `env.type !== 'pacing.update'` + 提示文案 `Facebook 命令被任务租约抑制` + `if(!canExecute)` 结构。禁区行 = 那个 `if` 的**条件行**，绝不触碰。

| 编辑点 | 当前锚点 | 是否禁区 | 需否先协调 |
|---|---|---|---|
| 5.2 协调器 wiring 改注册表 | 519-543（闸字面量 520-523） | 否（构造区，在 handler 之上） | **是**（main.ts） |
| 5.3 onPublishAtomCommand 注册写者+注入取消 | 735-800（IIFE 754-799） | 否（publish handler，结构隔离） | **是**（main.ts） |
| 5.8 删遗留 onPublishCommand | 596-659 | 否（publish handler） | **是**+删前实证云端无 publish.request 发送方 |
| 8.1 XHS browse 补回执 | 1145-1150 | 否（改 body 非条件，与 XHS 豁免 1142-1145 相邻但不重叠） | **是** |
| **8.1 FB comment-only 补回执** | **879-884** | **是（用户豁免落此 handler）** | **是，且必须排在用户豁免合并之后**，按内容定位，保留 pacing.update 穿透 |
| **8.1 FB browse 补回执** | **1075-1080** | **是（同上）** | **是，同上** |

**已落地不再碰**：2.5 两处 quiesceForTask 调用（FB 1088-1092 / XHS 1157-1161，均带 catch），tasks 明标非豁免段。

**冲突性质**：8.1 FB 两处是「同一个 `if` 块，我改 body（warn→补回执）而用户改条件（加 pacing 穿透）」的 main.ts 单写者三方冲突，typecheck 抓不到——丢 pacing 穿透→独占窗口内升档命令被当页面写抑制、边缘永停旧档；丢补回执→回静默丢弃、看门狗杀会话。**必须串行、内容定位、三处都保留 `env.type!=='pacing.update'`**（不只 XHS）。

---

## 3. 正确锚点表（覆盖 tasks.md 全部漂移）

**edge `src/execution/edge-task-coordinator.ts`**（整体 +5）：EdgeTaskBrowseGate 接口 tasks:8-11→**8-16**（quiesceForTask timeoutMs? 在 14）；PRIORITY 档位映射→**55-59**；DEFAULT_ACQUIRE_TIMEOUT_MS=45_000 tasks:58→**63**；acquire()→**109-144**；canExecute()→**207-212**；pickNext 档位比较 tasks:254-266→**259-271**（priorityDelta:265）；drain 入口守卫 tasks:288-289→**293-294**；drain quiesce+授予 tasks:300-308→quiesce **305-321**+授予 **322-346**；resumeBrowseIfIdle→**372-381**；rejectQueuedForQuiesceTimeout→**402-419**。

**edge `src/main.ts`**（早段 +17、晚段 +23；5.8 删除后再整体上移、须内容重定位）：EdgeTaskCoordinator wiring tasks:502-506→**519-543**；遗留 onPublishCommand tasks:579-639→**596-659**；onPublishAtomCommand tasks:737-782→**735-800**（IIFE 754-799，canExecute 736，touch 753）；FB comment-only warn tasks:862-867→**879-884**（handler 872-887）；FB browse warn tasks:1058-1063→**1075-1080**（handler 1068-1085）；XHS browse warn tasks:1122-1127→**1145-1150**（handler 1131-1155，pacing 豁免 1142-1145）；FB 会话 quiesceForTask tasks:1069→**1088-1092**；XHS 会话 quiesceForTask tasks:1133→**1157-1161**。**禁区无行号锚点**（内容定位）。

**edge flow 文件（5.1 六处）**：XHS 发布 tasks:725→`publish-command-handlers.ts` runSubmit@**892**（点击 923/933-935，最后取消点 922/932，CHECK **947**，pollBounded 948-961 timeout 15s@957，6.2 位置在 942/943）；FB 发布 tasks:435→`facebook/publish-executor.ts` submit()@**488**（dispatchClick **498**，waitUntil 499=20s，方法内无 checkpoint）；XHS 评论 tasks:2366→`browse-session.ts` executeComment@**2391**（提交点击 **2511**，最后取消点 2496）；FB 评论 tasks:518→`facebook/comment-executor.ts` submitComment@**459**（Enter **536**，最后取消点 530，禁区 545-558）；FB 加群 tasks:677→**准确**（`join-executor.ts` evalJson@677，真 click 在 GROUP_JOIN_CLICK_JS@592，joinGroup@613）；通知巡视 tasks:2862/2911→`browse-session.ts` browseNotificationComments 分类点击@**3019** / viewNotificationCategory 分类点击@**3068**。断连终态模板 1360/1368；TaskTakeoverError 通用分支 1344-1346（用 cmd.type，勿复用于巡视）；让位清队 tasks:887-889→quiesceForTask **964-966**。

**edge 协议/白名单**：EdgeTaskReleasedPayload.reason edge**:1296**/cloud**:1289**（准确）；PublishCommandResultPayload edge**:910**/cloud**:903**（tasks 无锚，补此）；protocol-contract.test.ts ALL_MESSAGE_TYPES**:34**（计数 76）；edge-client.ts onMessage acquire/release**:566**（浏览白名单 511-554）；边缘 task_lease_mismatch emit main.ts**:727/:811**。

**cloud（路径漂移：tasks 写 src/publish/ 与 src/scheduler/ 均不存在）**：`src/publish-agent/publish-dispatcher.ts` sequenceStarted **331/343**、失败终局 366-409、熔断 99-142、7.3 加闸 321-344；**`src/publish-agent/command-sequencer.ts`（tasks 完全未列，HOLE-1）** 分类 238/258、submitted=true 仅 :265、sent<=0 reject 308-312、capture_postId 266-269；`src/publish-agent/publish-log-store.ts` updateStatus:281/markRejected:285-289/updatePostId:298-302；`src/comm/ws-server.ts` bypassPause 212-218、pausedEdges 222、isEdgePaused 252-264；`src/comm/handler.ts` task_lease_mismatch **0 命中**（需新增）；`src/comm/edge-task-lease-client.ts` onReleased **210-244**/withLease 173-189/DEFAULT_ACQUIRE_TIMEOUT_MS 值 200s@**80**；`src/orchestrator/role-dispatcher.ts` noRecoverScroll tasks:2149-2162→**2269-2278+2279-2282**、RETRIABLE_INTERACTION_REASONS 2244-2245（comment 不在）、beginNotificationTask 569-622、pauseClock 调用 view_quota:1404/patrol:2062；`src/comment-agent/comment-scheduler.ts` keep-open 1271-1290、失败分档 **1365-1373**（定向路径 1194-1196）、onScheduledTaskNotStarted 1380-1391、isEdgeTaskAcquireFailure 1523-1525、edge.post 门 1344/1351；`src/comment-agent/facebook-edge-steps.ts` 三命令无 taskId 168/204/233（pushToEdges:135）；`src/agents/session-monitor-role.ts` checkIdle:211/215、pauseClock:153-156。

**控制仓**：主 spec `openspec/specs/edge-task-execution-coordination/spec.md` Requirement header **:62**、禁令句 :64、冲突 Scenario :66-68/:74-76、MODIFIED#2 目标 :38；delta `changes/lease-strict-preemption/specs/.../spec.md` MODIFIED#1 改名 :3（HOLE-5）、MODIFIED#2 :31（正确对照）；`docs/protocol.md` :19 计数 / :141 表行 / :773-774 示例。

---

## 4. Holes 逐条处置

**全部 13 条 ACCEPT，无驳回**（每条均已在 worktree/cloud 坐实到文件:行，无过度设计）。分类：

**Blocker（必须先纳入方案设计，否则整批白做；在批内解决、非外部前置）**：
- **HOLE-1（blocker）** command-sequencer 未上改动清单 → 被抢占发布仍烧成不可逆 failed。**接受为方案核心**：批 2a 把 command-sequencer.ts 列为热点、产出独立 `preempted` outcome。这是「§7 被抢占≠失败」能否达成的判决点。
- **HOLE-7（high，等价 blocker）** 7.5 中断必须经序列器 submitted 门、不得 unwind executePublishSequence，否则提交后被抢的已发帖被重投双发。**接受**：批 3k 固化「就地 reject 在飞命令」形态；7.1 重投只限 failed_before_submit+抢占原因。
- **HOLE-2（high）** 6.2 布尔位无消费点 → protocol 加字段 inert。**接受**：批 2b 在 command-sequencer:258 消费。

**可实装中处理（已并入对应批，非动手前置）**：
- **HOLE-3 / HOLE-11（high/medium，同源合并）** 5.5 缺窗口豁免 + FB 加群 46.5s + 5.10(b) 掉队。**接受**：批 3e 让 5.5 timeout 重读窗口标志；批 3f 把 5.10(b) 提为与 5.1 加群窗口同一 blocking 原子交付；批 3s 参数一致性断言纳入边缘等停预算。
- **HOLE-4（medium）** 5.9/5.2 假成功两缝：canExecute 须在有在途发布写者时返 false；CHECK 仍 URL-absent=success。**接受（部分带真机依赖）**：批 3b/3d 让 canExecute+resumeBrowseIfIdle 都读在途发布写者登记（主修，blocking）；CHECK 收紧成「submit 已派发且见正证据」为保守默认，URL 缺失单独不判成功——**能否完全移除 URL 原语依赖新真机项**（见 §5）。
- **HOLE-6（high）** 6.4/11.9 只焊原因串、漏 6.2 布尔位。**接受**：批 1c 加 AC-PROTO-15。
- **HOLE-8（high）** 7.6 edge.post boolean 塌三态 → 重复评论。**接受**：批 2f 升三态、去重门改 dispatched。
- **HOLE-9（medium）** 6.2 置位语义未定（早=假成功、晚=假失败）。**接受**：批 3f 固化「按下事件真正发出那刻」置真、XHS+FB 两处都置、与 5.1 窗口标志语义相反不复用。
- **HOLE-10（medium）** 8.2 无注入点。**接受**：批 3j 固化「在飞 settle 后+确认在巡视 excursion 才发一次、合成名 notification_back_home」。
- **HOLE-12（medium）** 8.1↔7.8 次序 → 单边上线新增上下文污染。**接受**：批 3 把 §8 与 7.8 co-deploy。
- **HOLE-13（low）** 7.1「已开始」下移若首命令是 navigate 仍烧零副作用。**接受**：批 2c 锁「首条产生平台副作用 sent>0 之后」。
- **HOLE-5（low）** spec delta MODIFIED#1 改名 → 归档旧禁令存活自相矛盾。**接受**：批 3q header 改回或补 RENAMED。归档期才暴露、务必修。

---

## 5. 真机项（§12）动手前确认 vs 留 backlog

**严格「阻塞设计、动手前必须确认」的：无。** 每个不确定项，方案都已内建保守默认（被抢占发布整条序列重跑并接受可能留孤儿图；巡视整个 excursion MUST 拒绝抢占，无论导航是否消费未读；CHECK 收紧为正证据门）。故都不阻塞开始写代码。

**但必须在 archive / spec 定稿前解决（gate spec 措辞或安全移除某原语，不 gate 编码）**：
- **12.1（A，10 秒）** 小红书上传后缩略图前缀指向本机还是平台。→ 只 gate spec 措辞：指向平台则「抢占留孤儿图无回收」必须写进 10.2 清场协议 requirement 显式承认。设计已接受两种答案，不 gate 编码。**先做、结论回填 spec。**
- **12.2（B）** 脏发布页导航离开是否弹「离开此页/保存草稿」框冻住浏览器。→ §3 清场协议已 landed（含对话框处理），故降级为**部署门验证**，由 12.6（F 端到端）覆盖。若真冻结则整个抢占不安全——**必须在批 3 部署 dev 后、真机 F 验证通过前不算完成**。不 gate 编码。
- **新增真机项（HOLE-4 引出，并入 A 簇）** 小红书是否在导航前稳定给出发布成功文案。→ gate「CHECK 能否完全移除 URL 缺失原语」：不给则保守正证据门保留、spec 显式承认残余假成功。**先做、结论决定 CHECK 最终形态与 spec 措辞。**

**留 backlog（纯部署后验证，不影响设计与编码）**：12.3（C 巡视可抢占段是否为空——保守设计已覆盖两种答案）、12.4（D 草稿箱）、12.5（E 话题实体）、12.6（F 端到端，兼验 B）、12.7（G FB 评论不再静默丢弃）、12.8（H 逃生梯）。全部按 CLAUDE.md 归并入 `docs/real-machine-acceptance-backlog.md`。

---

**一句话总结（说人话）**：这批活的核心是「让高优先级的操作能打断正在跑的低优先级操作，而被打断的那一方不能被冤枉成失败、更不能因此重复发帖」。方案分三步走——先改协议（安全、无副作用），再让云端学会「看到‘被抢占’不烧稿」（顺带修好几个今天就在烧稿的老 bug），最后才让边缘真正开始抢占、和云端一起同步上线。最大的雷有两个：一是评审发现有个关键的云端翻译层（command-sequencer）没被列进改动清单，不补它整批都白做（已纳入）；二是 main.ts 里有一段用户正在改的代码是禁区，我有两个补回执的点正好落在那上面，必须等用户改完、按内容而不是行号去找、且保留他加的豁免逻辑。动手的两个硬前提：等另一个并行 change（browser-slot-scheduling）先归档再 rebase，以及和用户对齐 main.ts 禁区的最终边界。