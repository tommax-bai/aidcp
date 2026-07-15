# 交接文档 — lease-strict-preemption 抢占核心（第 5–13 节）

> 写于 2026-07-15。给**换 session 接手抢占核心**用。第 1–4 节 + 5.7 + 5.10(a) 已落地，抢占核心（5.1–5.6/5.8/5.9/5.10b + §6 协议 + §7 云端 + §8 静默丢弃收口 + §10 spec + §11–13 收口）**尚未动手**。本文档自包含，含设计评审刚坐实的锚点修正与 holes，可直接照着开工。

---

## 0. 一句话状态

**Fleet 定序闸已清，抢占核心可以动手了。** 之前卡在「并行 change `browser-slot-scheduling` 正重改协调器/main.ts」——现已确认它对这两块的改动**全部落进本分支地基、与 master 逐字节一致、edge 仓无任何活跃 worktree 还在改这两块**。设计评审（workflow `wf_18b37a11-416`）已把 tasks.md 的行锚点按当前代码重新坐实、找出 1 个 BLOCKER + 若干 HIGH，并**揪出一个关键真相：tasks.md 反复警告的「main.ts FB 租约闸节奏豁免禁区段」目前根本不存在，是用户未提交的并行工作**——见 §5。

**动手前的硬前置**：① 把新发现（BLOCKER=命令序列器、禁区真相、分批约束、5.10b 提级）先并进 tasks.md；② 动 main.ts 前与用户协调（禁区尚未落地，时机敏感）。

---

## 0.5 进度更新（2026-07-15 下半场，接手看这里）

**已落地并推送（全部本地门禁全绿：edge full 1356 / cloud full 2044 / 两端 typecheck 0）：**

| 单元 | 内容 | SHA |
| --- | --- | --- |
| 批 A 协议地基 | 6.1（3 释放原因 preempted_by_task/window_busy(+windowRemainingMs)/yield_timeout）+ 6.2（PublishCommandResultPayload.submitDispatched）+ 6.3 docs + 6.4/11.9 AC-PROTO-14/15。inert 未接线 | edge `9bc6c6b` / cloud `9f0194b` / 控制仓 `098a394`+台账 |
| 批 B-1 协调器抢占核心 | 5.2 EdgeTaskPageWriterProbe（inCommitWindow/commitWindowRemainingMs/publishInFlight/cancelPublish 全可选）+ 5.4 drainOrPreempt 三态 + 5.5 yield_timeout 控制面故障 + 5.9 publishInFlight 让位。**探针门控休眠**（main.ts 未 wire writers → 与今日逐字同行为） | edge `52d2a78` |
| 批 B-1 加固 | 对抗性复核 `wf_3a8e8996` 揪出并修：**BLOCKER**（cancel-before-declare：preemptedPending，被抢占 preempted_by_task 只在 quiesce 确认写者停后才发，cancel 抛出→yield_timeout，防云端重投未停发布=双发）+ **HIGH #1**（yield_timeout 后 browse 保持冻结）+ **HIGH #A**（canExecute active 分支也认 publishInFlight）+ LOW（quiesceAllWriters sync-throw 安全）。coordinator 27 单测 | edge `1f67249` |
| 批 B-1b 提交窗口守卫 | `src/execution/commit-window.ts` `CommitWindowGuard`（时基兜底自动过期 + 世代守卫）+ `combineCommitWindows`。5 单测。**未接线**（5.1 六站 enter/exit + main.ts wire） | edge `a062cbd` |

**cloud worktree 已建**：`../aidcp-cloud.wt/lease-strict-preemption`（分支同名，从 master `1cfddb5`）。批 A 的 cloud protocol.ts 已在其中。

**下一步＝把休眠的抢占引擎接线激活（5.1 + 5.3 + main.ts wiring）。已坐实的接线方案（省下重新推导）：**

- **publishInFlight 探针** ＝ `() => inFlightPublishes.size > 0`（main.ts:373 现成的 Map，发布 dispatch 期间有 entry，含后置校验窗口）。
- **cancelPublish 探针** ＝ 把 `inFlightPublishes` 的 failer 从「只发失败回执」升级为**真取消**：给每条发布 dispatch 建一个 takeover（AbortController + Checkpoint，见 `src/execution/takeover.ts`），`onPublishAtomCommand`（main.ts:735-800）把它传给 `publishDispatcher.dispatch(env.payload, takeoverCtx)`（dispatch 已收 takeover 第二参、见 publish-command-handlers.ts:300），cancelPublish(ms) = 触发 takeover + 有界等 dispatch settle。
- **inCommitWindow/commitWindowRemainingMs 探针** ＝ `combineCommitWindows([publishGuard, browseGuard])`。**publishGuard** 归 PublishCommandDispatcher 所有（runSubmit 的不可逆点击 publish-command-handlers.ts:923/933 处 enter/dispose；FB submit publish-executor.ts:498 处），**browseGuard** 归 browse session 所有（XHS 评论提交 browse-session.ts:2511、通知分类 3019/3068、FB 评论 Enter comment-executor.ts:536、FB 加群 join-executor.ts:592）。两个 guard 由各自 owner 暴露给 main.ts 聚合。
- **notifyPublishSettled** ＝ `onPublishAtomCommand` 的 finally（inFlightPublishes.delete 之后）调 `taskCoordinator.notifyPublishSettled()`——**复核 finding C：此钩当前零调用者，5.3 必须接上，否则发布 dispatch 结束后浏览永久冻结**。
- **6.2 submitDispatched 置位** ＝ XHS 在 publish-command-handlers.ts:942（点击 try 成功后、pollBounded 前）、FB 在 publish-executor.ts:498（dispatchClick 后）置真；center 查找类失败保持 false；**MUST NOT 复用 5.1 提交窗口标志**（语义/时机相反）。回执带上 submitDispatched。
- **5.9 收紧假成功 CHECK** ＝ publish-command-handlers.ts:947 的 CHECK 去掉 `|| !location.href.includes('/publish/publish')`，改正证据优先（只认成功文案/落地 URL）。
- **5.1 六站清单 + 窗口预算**（handoff §5.3 修正锚点已核）：XHS 发布提交 ~15s、FB 发布提交 ~20s、XHS 评论提交 ~4s、FB 评论回车 ~20s、FB 加群「点击+短确认≤~18.5s」（+ **5.10b 同批**把点击后 46.5s 观察轮询拆成窗口内短确认+可中断尾巴）、通知分类栏目 ~15-20s（无回滚→窗口内 MUST 拒抢占）。统一上界取 FB 评论 20s。
- **落地序**（红线）：5.1（六站 enter/exit + 两 guard 暴露，inert）**先** → 5.3 + main.ts wire writers（此刻抢占**真激活**，须五站窗口都已 enter/exit，否则窗口内会被强杀）→ 一起构成假成功修复链的 edge 半边，**须与批 C（cloud，含 command-sequencer BLOCKER）co-deploy**。
- **禁区仍在**：8.1 FB 两处（main.ts:879-884 / 1075-1080）＝用户未提交的 FB pacing 豁免段，动前协调、按内容特征定位、保留 `env.type!=='pacing.update'` 穿透。5.3/5.8 的 main.ts 发布 handler 区与禁区结构隔离，安全。

**剩余**：5.1+5.3+main.ts wiring + 5.6 + 5.8 + 6.2-edge + 收紧 CHECK（批 B 尾）→ 批 C cloud（command-sequencer preempted 分类 BLOCKER + 7.x）→ 批 D §8 → 批 E spec/测试/部署/archive。

---

## 0.6 进度更新（2026-07-15 尾场，edge 批 B 已完整落地 + 对抗复核加固）

**edge 抢占核心全部落地并激活，门禁全绿（edge full 1363 / typecheck 0 / acceptance 21），已推 `origin/lease-strict-preemption`：**

| 提交 | 内容 |
| --- | --- |
| `bc3e774` B-2a | 5.1 六站提交窗口 enter/dispose + 5.10b 加群短确认拆分 + 6.2 边缘 submitDispatched；main.ts 创建/注入 publishGuard·browseGuard，**未 wire writers（inert）** |
| `b9fdfa5` B-2b | main.ts wire 协调器 writers（combineCommitWindows + publishInFlight=inFlightPublishes.size>0 + cancelPublish 真取消）**= 抢占引擎激活** + notifyPublishSettled 接线 + 5.9 收紧假成功 CHECK（去 URL 判据） |
| `9a9ebda` B-2c | 5.8 删遗留整页发布处理器 onPublishCommand + 三个孤立 import |
| `6d87e39` B-2d | **对抗复核 `wf_1657e89b-85a` 加固**（下述 2 BLOCKER + 1 MEDIUM） |

**对抗复核结论（5 视角 + 逐条对抗验证，1359 单测全绿仍揪出，已全修 6d87e39）：**
- 🔴 **BLOCKER FB 发帖双发**：`publish-executor.ts` submit 全程无取消点，提交窗口打开前的 target 查找期间被抢占 → cancelPublish 的 abort 对 submit 无效（不读 signal）→ 点击照发帖子发出，协调器却因 quiesce「收敛」判 preempted_by_task 可重投 → 双发。修：submit 接 TakeoverCtx，target 查找后 / enter() 前**同步** checkpoint（无 await），catch 加 rethrowIfTakeover；dispatch submit_publish case 传 takeover。
- 🔴 **BLOCKER 加群点击前冻结**：`join-executor.ts` observeUntilReady（点击前，最长 30s）无取消点，被抢占超 30s quiesce 预算 → 误判 yield_timeout + 浏览永久冻结 + 抢占者被拒。5.10b 只做了点击后尾巴。修：observeUntilReady 接 checkpoint 每轮检查（点击前完全可取消、无窗口门控）+ enter() 前补 checkpoint。
- 🟡 **MEDIUM submitDispatched 时机**：press 已注入但 CDP 响应抛错时，旧实现在 dispatchClick 返回后才置真 → 回执 submitDispatched=false → 双发。修：`cdp-util` dispatchClick 加 onPressDispatched 回调（commitLeftClick 前触发）+ runSubmit 两分支据此置位 + **catch 的 engine_error return 补带 submitDispatched**（原漏带）。
- 驳回（不改）：join 动作名有云端归一表、两 Map 去同步不可达、遗留 handler 已删、窗口预算 ~1s 尾巴 graceful 非双发。

**下一步 = 批 C（cloud，co-deploy 另一半，绝不可让 edge 单独部署）**，cloud worktree 已建 `../aidcp-cloud.wt/lease-strict-preemption`（批 A 已在其中）。锚点见 §5.3 表 cloud 部分：**command-sequencer BLOCKER**（`src/publish-agent/command-sequencer.ts:238/258` 把 ok:false 归 failed_before_submit → 识别抢占原因串产出独立 `preempted` outcome，绝不并入 failed_before_submit）+ publish-dispatcher `:380` 前加 preempted 保 pending 分支 + 7.1-7.11。5.6（边缘 45s vs 云端）与 7.10 同批坐实。批 C 完成后 co-deploy dev → 批 D（§8，含 FB 禁区，动前协调）→ 批 E 收口。

---

## 1. 快速定位（分支 / worktree / SHA）

| 项 | 值 |
| --- | --- |
| 控制仓 | `/Users/baitianxing/codes/aidcp`，分支 `main`，HEAD `c6a2285`（与 origin/main 同步） |
| edge worktree | `/Users/baitianxing/codes/aidcp-edge.wt/lease-strict-preemption`，分支 `lease-strict-preemption`，HEAD `35d3aec` |
| edge 分叉点 | `e30c211`（从这里分出；master 现 `84267f2`，领先 8 个提交） |
| edge canonical | `/Users/baitianxing/codes/aidcp-edge`，停在 `master`（**勿切分支**） |
| cloud canonical | `/Users/baitianxing/codes/aidcp-cloud`，停在 `master`；**本 change 尚无 cloud worktree**，做 §7 时需新建 |
| 设计评审 workflow | run `wf_18b37a11-416`，transcript 见 `subagents/workflows/wf_18b37a11-416/`（journal.jsonl 有 8 个坐实/对抗 result；总装配 agent 可能仍在跑或已 stall，raw 结果比它更细） |

**各节落地 SHA（全部已推 `origin/lease-strict-preemption`、台账安全）**：
- §1 安全取消点/解死锁 = edge `0ae90c8`
- §2 让位探针不撒谎 = edge `c8e3202`
- §3 清场协议 = edge `bd9ffc0`
- §4 取消点补齐 = edge `51d060e`
- §5.7 验证码回放前复检 + §5.10(a) waitUntil 迭代帽 = edge `35d3aec`
- 控制仓台账最后一次 = `246374b`（5.7 `[x]`、5.10 `[~]`）

**门禁基线**（35d3aec）：typecheck ✅ / `test:acceptance` 19/19 ✅ / 全量 `test` **1336** ✅。

---

## 2. 已落地做了什么（一句话回顾，勿重做）

- **§1–4（edge）**：把「租约被撤走」变成一个能被沿途安全接住的取消信号——阻断浮层等待、两处停留、逐字输入、6+1 个轮询循环、云端选元素、图片下载段全部接了「接管世代号」取消点；FB 侧按写者隔离（`AsyncLocalStorage`）修了「共享标量令牌被孤儿写者清空」的真 bug；清场协议（填字段前清空+全文比对、废掉 8 字探针、关发帖弹层、离开确认框 CDP 一律 accept）。**关键边界**：发布路径**只铺了取消管道、没注入取消信号**——因为抢占能力要到 5.4 才有，单边接上=净新增烧稿路径（详见 tasks §4 开头与 memory `lease-preemption-cancel-points`）。
- **§5.7 + §5.10a（edge `35d3aec`）**：验证码落点回放前强制复检（阻断消失→not_blocked、页面变→stale_snapshot+重抓帧、绝不盲点）；`publish-executor.ts` 的 `waitUntil` 补了迭代帽（防注入恒定 now 死循环）。

---

## 3. Fleet 定序闸：已清（证据链，接手可复核）

1. browser-slot 的**全部 edge 提交**（`809e15d 7226f01 ea0c979 ede64c4 3eb29b0 1878f90`）经 `git merge-base --is-ancestor` 验证：**既在 origin/master、也在本分支分叉点 `e30c211`**。
2. 协调器 `src/execution/edge-task-coordinator.ts` 的内容哈希在「809e15d / 本分支 base / master」三处**全等**（`b569764`）。
3. 我落后 master 的 8 个提交（facebook-feed-inline C2 / presence-terminal-honesty / runtime-guidance 样式 / daily-progress）**没有一个碰协调器或 main.ts**（`git log e30c211..origin/master -- src/execution/edge-task-coordinator.ts src/main.ts` 为空）。
4. `git worktree list`（edge）里**无任何 browser-slot worktree**，无人在改协调器。
5. browser-slot 的 openspec change 账面仍 `33/48`、未归档——但那是**云端 + 真机验收尾巴**，其 edge 协调器代码已定稿。→ 对本 change 要动的这块，它稳定、可独占。

---

## 4. rebase 决策：推迟到最终集成

- **现在不 rebase**。抢占核心真正要动的协调器 / main.ts / 两份 protocol.ts / publish-* 在「本 base ↔ master」逐字节相同，设计评审**直接以本分支 HEAD（35d3aec）为准坐实**——那就是要下刀的真实表面，无需先 rebase。
- **冲突面 = 仅 4 个文件**（我落后的 8 提交 ∩ 我改过的文件）：`src/browse/browse-session.ts`、`src/facebook/facebook-session.ts` + 两个对应测试。C2 的 feed 内联改动与我 §1/3/4 的取消点在不同区域，冲突预期局部。
- **推迟的理由**：现在 rebase 会改写已推的 5 个提交→触发对 feature 分支的 force-push（§6 需确认）；留到最终并线一次解冲突更干净。
- **最终集成时**（全部实装完成后）：`fetch` + rebase 到最新 master → 解那 4 个文件冲突 → 跑 `test:acceptance`+全量+`typecheck` → ff 合并到 master。force-push feature 分支或直接 merge+删分支时按 §6 与用户确认。

---

## 5. 设计评审结论（wf_18b37a11-416）——动手前必读

### 5.1 🔴 BLOCKER：真正没接线的层是**命令序列器**，tasks.md 从没点名它

- **文件**：`aidcp-cloud/src/publish-agent/command-sequencer.ts:238 / :258`（分类）→ `publish-dispatcher.ts:380`（写 failed+熔断）。
- **问题**：被抢占的发布在边缘一律以**普通命令结果 `ok:false`** 形态浮现（三条出口全在 edge `main.ts`：`:780` catch 回 `dispatch_error`、`:758` 在途回收回 `[recycled]`、`:744` canExecute 假回 `task_lease_mismatch`）——不是抛出、不是 acquire 失败。云端 command-sequencer 对任何核心步 `ok:false` 一律归 `failed_before_submit`（`submitted` 只在 `:265` 的 `ok:true` 才翻真）→ publish-dispatcher `:380` 写**不可逆 failed + 熔断**（publish-log-store 无 failed→pending 回退）。
- **后果**：§7.1「被抢占≠失败」若只改 publish-dispatcher 的终局分支、不改 command-sequencer 的**分类**，被抢占的发布仍会在序列器那一层就被烧成 failed。**这是整个 §7 假成功修复链真正的根**。
- **修法**：把 command-sequencer 列为本批必改热点：① 在 `:240-258` 的 `ok:false` 分支与 `:219` catch 里识别抢占类原因串（`preempted_by_task` / `task_lease_mismatch` / 新增 `window_busy` / `yield_timeout`），产出独立 `preempted` outcome，**绝不并入 `failed_before_submit`**；② publish-dispatcher 在 `:380` 之前加分支：`outcome==='preempted'` → 保持 pending、不写 failed、不 record 熔断。

### 5.2 🚨 禁区真相：tasks.md 说的「main.ts FB 租约闸节奏豁免段」**目前不存在**

- 评审查遍 worktree(35d3aec) / master / 所有 codex 分支：**该段根本没有**。它是**用户尚未提交的并行工作**（正要把 pacing 豁免 graft 进 FB 的命令 handler）。
- 当前唯一同型存在物 = **XHS** 的 pacing 豁免 `main.ts:1145`（`env.type!=='pacing.update'` 穿透）。用户正把镜像 graft 进 **FB 两个 handler**（定向评论 `879-884`、浏览 `1075-1080`），届时禁区最可能落在 FB handler `1068-1085` 区。
- **致命交叠**：§8.1 要补诚实回执的三处里，**有两处（FB 定向评论 879-884、FB 浏览 1075-1080）就是禁区本身**——不是「与禁区相邻」。8.1 要把这俩 `if(!canExecute){warn;return}` 的 body 改成 `{warn;补回执;return}`，而用户要把同一个 `if` 的**条件**改成 `env.type!=='pacing.update' && !canExecute`——**落在同几行**，典型 main.ts 单写者三方冲突。
- **接手动作**：① §8.1 的 FB 两处补回执**必须排在用户 FB pacing 豁免落地/合并之后**；② 用**内容特征**定位（`Facebook 命令被任务租约抑制` / `if(!canExecute)` 结构），**不用 tasks 的漂移行号**；③ 对全部三处（含 FB 两处一旦长出豁免）保留 `env.type!=='pacing.update'` 穿透；④ **动 main.ts 前先与用户协调**（禁区时机敏感）。
- **好消息**：5.3（发布写者注册 `onPublishAtomCommand` 735-800）与 5.8（删遗留 `onPublishCommand` 596-659）都是**发布 handler**，与 FB/XHS 浏览 handler、任何 pacing 豁免段**结构隔离** → 这两块安全，不碰禁区。

### 5.3 锚点漂移修正表（tasks.md 行号 → 当前 35d3aec 真实位置）

> tasks.md 的 §5–8 行号写于早期基线，被 §1–4 插入的行整体下移。**edge 一律以下表为准**。

**edge — 协调器**（整体 +5）：
- 5.2 `coordinator:8-11` → 接口 `EdgeTaskBrowseGate` **8-16**（quiesceForTask 带 timeoutMs 在 :14）
- 5.6 `coordinator:58`（45s 默认）→ **:63**（`DEFAULT_ACQUIRE_TIMEOUT_MS = 45_000`）
- 5.4 `coordinator:254-266`（pickNext 优先级）→ **:259-271**（priorityDelta 在 :265）
- 5.4 `coordinator:288-289`（drain 入口守卫）→ **:293-294**
- 5.4 `coordinator:300-308`（drain 内 quiesce+授予）→ 已扩张：quiesce+硬化 catch **:305-321**，授予前复检+建租约 **:322-346**（授予本体 329-346）
- 5.9 resumeBrowseIfIdle → **:372-381**；canExecute → **:207-212**

**edge — main.ts**（早段 +17、晚段 +23/24）：
- 5.2 `:502-506`（协调器构造/browse 闸 wiring）→ **:519-543**（闸字面量 520-523）
- 5.3 `:737-782`（游离发布执行流 IIFE）→ **:754-799**（外层 handler `onPublishAtomCommand` 735-800，canExecute 闸 736、touch 753）
- 5.8 `:579-639`（遗留整页发布处理器 `onPublishCommand`）→ **:596-659**（tasks 尾 639 低估，真实闭合 659）
- 8.1 `:862-867`（FB 定向评论静默丢弃）→ **:879-884**（handler 872-887）【禁区】
- 8.1 `:1058-1063`（FB 浏览静默丢弃）→ **:1075-1080**（handler 1068-1085）【禁区】
- 8.1 `:1122-1127`（XHS 浏览静默丢弃）→ **:1145-1150**（handler 1131-1155，pacing 豁免 1142-1145）

**edge — 六处提交窗口不可逆动作**（§5.1）：
- XHS 发布提交：`publish-command-handlers.ts:725` → `runSubmit` 方法体 **892** 起，不可逆点击在 **923**（pacing）/ **933-935**（裸 mouseEvent）；15s 窗口 pollBounded 在 :957，那条假成功 CHECK 在 **:947**
- FB 发布提交：`facebook/publish-executor.ts:435` → `submit()` 方法 **488** 起，dispatchClick 在 **498**
- XHS 评论提交：`browse-session.ts:2366` → `executeComment` 方法 **2391** 起，提交点击 **2511**（最后取消点 2496）
- FB 评论回车：`facebook/comment-executor.ts:518` → `submitComment` 方法 **459** 起，Enter 在 **536**（最后取消点 530）
- FB 加群点击：`facebook/join-executor.ts:677` → **仍准**（GROUP_JOIN_CLICK_JS evalJson 在 677，底层 target.click() 在 592）
- 通知巡视分类栏目：`browse-session.ts:2862/2911` → **严重漂移**，实为 `browseNotificationComments` 分类点击 **3019** 与 `viewNotificationCategory` 分类点击 **3068**

**edge — 让位清队**（§8.1）：`browse-session.ts:887-889` → 实在 `quiesceForTask`，**:964-966**

**协议**（§6）：
- 6.1 edge `protocol.ts:1296` / cloud `:1289`（`EdgeTaskReleasedPayload.reason`）→ **均准**、两块 byte-identical
- 6.2 目标 payload = `PublishCommandResultPayload`：edge `protocol.ts:910` / cloud `:903`（tasks 无锚点，**补上**）
- 6.3 `docs/protocol.md`：头部计数 :19=76 **不变**（§6 不新增 MessageType）；:141 / :774 的 reason 示例**已过期**（缺既有的 `browser_wake_failed`）——6.3 要顺带回填这个既有缺口，合计 9 个原因值

**cloud**（§7，注意目录，tasks 多处没写目录）：
- 7.1/7.3 `publish-dispatcher.ts` → **`src/publish-agent/publish-dispatcher.ts`**（`:331-343 / :380-409 / :99-142 / :321-344` 均准）；真实硬暂停机制在 `ws-server.ts:212-222` + `command-sequencer.ts:308-312`（tasks 未指出，需补）
- 7.2/7.1 `publish-log-store.ts` → **`src/publish-agent/publish-log-store.ts`**（确认无 failed→pending 回退路径）
- 7.6 `comment-scheduler.ts` → **`src/comment-agent/comment-scheduler.ts`**（`:1271-1290 / :1523-1525` 准；真正失败分档在 **1365-1373**，定向路径同构 1194-1196）
- 7.7 `role-dispatcher.ts:569-622`（巡视失败出口）准，但只覆盖 acquire 失败；会话空闲时钟真实在 **`src/agents/session-monitor-role.ts:211`(checkIdle)/`:153`(pauseClock)**（tasks 未给）
- 7.8 `role-dispatcher.ts:2149-2162` → **正确 2269-2282**（noRecoverScroll 名单 2269-2278 + 兜底滚动触发 2279-2282，tasks 约错 120 行）
- 7.5 `edge-task-lease-client.ts:210-244`(onReleased) / `:173-189`(withLease) → 均准
- 7.4 `handler.ts` 无 `task_lease_mismatch` 处理（全仓 0 命中确认）；边缘发送点在 edge `main.ts:727` 与 `:811`
- 7.9 `comment-agent/facebook-edge-steps.ts`：search.execute(168)/note.open(204)/interaction.comment(233) **均无 taskId**，坐实

**spec**（§10.1）：主 spec = `openspec/specs/edge-task-execution-coordination/spec.md` 的 `### Requirement: 任务优先级与同级 FIFO 可预测`（:62），禁令句 :64，冲突 Scenario `恢复任务不强杀已提交动作`（:74-76）、`人工评论先于排期发布`（:66-68）。

### 5.4 其余 holes（按严重度，含修法）

**HIGH — 7.1/7.5 中断必须走序列器 submitted 门，不能 unwind**：活跃租约中断（7.5）MUST 表现为「让在飞那条 `publish.command` 就地 reject」，交给 runSequence 按 submitted(238/258) 归类；**绝不 unwind 掉 `executePublishSequence`**（否则 catch 处拿不到 submitted 状态、无从安全判别）。7.1 的「保持待审重投」分支只允许 `outcome==='failed_before_submit'` 且原因为抢占时触发；`submitted_unconfirmed`（含提交后被抢）一律走 371-379 submitted 终态、**绝不重投**（防已发出的稿被重投双发）。

**HIGH — 7.6 boolean 接口塌掉三态→重复评论**：`edge.post()`（`comment-agent/facebook-edge-steps.ts:292` / 类型 `comment-task-runner.ts:59` / `edge-steps.ts:150`）今天返回 `Promise<boolean>`，把 §3.2 已在线的 `submitted_unconfirmed` 三态塌成 false → 走 post_failed → 去重账本(comment-scheduler:1351)不写 → 下次排期重触发 = **重复评论**。修：升级为携带「提交是否已派发」的三态；去重写入门改为「提交已派发(submitted_unconfirmed ∪ confirmed)」而非 `ok===true`。

**HIGH — 5.5 + 5.1 FB 加群窗口 + 5.10(b) 必须同批**：5.10(b)（FB 加群 46.5s 观察轮询拆成「窗口内短确认 ≤~18.5s + 可中断尾巴」）现被标为可延后的「顺手项 `[ ]`」。若掉队，真实不可取消区仍是 46.5s > 30s 的 quiesce 预算 → 5.5 的等停钟会把一个**合法处于受保护窗口**的健康写者误判成控制面故障 → 假的结构性失败 + 整队拒绝 + 运营被告知「浏览器不听话请重启」。**修：把 5.10(b) 从顺手项提为与 5.1 的 FB 加群窗口同一原子交付**（5.1 设窗口就必须同批完成拆分）。

**MEDIUM — 6.2 置位语义（两个方向都会新增红线）**：「已派发提交」布尔位 MUST 在「按下事件真正发出的那一刻」置真（XHS 落在 942 点击 try 成功后、pollBounded 前；FB 落在 498 dispatchClick 后、waitUntil 前），**center 查找类失败(910/913/495/497)保持 false**。① 置早（复用 5.1 提交窗口标志，那个 SET 在点击**之前**）→ 「压根没点」的 no_target/engine_error 会带 dispatched=true → 云端判 submitted_unconfirmed → 一篇从未提交的稿被记成「已提交待确认」、既不重投也不发出 = **静默假成功、稿永久丢失**。② 置晚（dispatchClick 整体返回后）→ mousePressed 已发但 mouseReleased 抛出的窗口丢判。**MUST NOT 复用 5.1 的提交窗口标志**（语义相反、SET 时机相反）。XHS 与 FB 两处 submit 都要置。

**MEDIUM — 5.9+5.2 canExecute 也要认在途发布写者**：5.9 只把钩子卡在 resumeBrowseIfIdle 不够。发布 IIFE(main.ts:754-799)今天游离、不持协调器租约，post-validation 期协调器空闲 → canExecute(:207) 对新到浏览命令返回 true → 该命令把发布页导航走 → CHECK(:947)命中 `!location.href.includes('/publish/publish')` → ok:true → 云端 updatePostId → published（**近乎不可逆的假成功**）。修：① 5.2 泛化注册表时 canExecute 也要在「有在途发布写者登记」时返回 false；5.3 的写者登记须覆盖整个 dispatch()（含 post-validation）；② 把 CHECK 收紧成正证据优先——只认成功文案/落地帖 URL，**URL 缺失单独不得判成功**。

**MEDIUM — 8.2 巡视合成回执的注入点**：三条数据-only 巡视方法（open/browse_comments/back_home）段内无 checkpoint、永不抛 TaskTakeoverError，既到不了断连模板(1360/1368)也到不了通用接管回执。修：合成的 `notification_back_home ok:false(reason=preempted_by_task)` 只在「任何在飞巡视操作已 settle(waitDrained 返回) 且确认本会话正处于巡视 excursion」后发一次，绑到 quiesce 成功/抢占授予的收尾处；动作名固定用合成名 `notification_back_home`、**绝不用 cmd.type**（1346 那条云端 excursion_resumer 不认）。

**MEDIUM — §8 必须绑进 5+6+7 同批（8.1↔7.8 次序）**：edge §8.1 对 open_note/refresh/profile_open 补 `preempted_by_task` 诚实回执，绝不先于 cloud §7.8 的原因级短路（插在 role-dispatcher 2269-2282 名单判断之前）上线——否则每条诚实回执立刻触发一次兜底滚动、滚到抢占方页面上（§4 血教训同型的单边接线）。

**MEDIUM — 5.5 窗口豁免判据**：控制面故障判据 = 「协调器**确实向该写者下发了取消**（即它不在提交窗口/受保护禁区；5.4 对窗口占用应直接回『窗口占用中+剩余预算』、不发取消、不进等停钟）**且**有界等停(30s)真的走完」。别用「quiesce 抛出即故障」的算术边界代替语义判据（参照 memory `failure-must-be-structural`：资源暂时被占绝不判失败）。

**LOW — 7.1「已开始」标志下移判据**：锁成「首条**产生平台副作用**的命令真正发出(sent>0)之后」——navigate 类无平台写的步骤不计；投递 0（7.3 暂停期 sent<=0）不算「已开始」。否则 navigate 后、首个真正平台写前的抢占会烧 failed（零副作用被烧成不可逆 failed，正是要根治的）。

**LOW — 10.1 spec MODIFIED header 不匹配（归档期才炸）**：delta 的 MODIFIED #1 用了新 header『任务优先级严格生效，高档位任何时刻可抢占低档位』，与主 spec 现行 header『任务优先级与同级 FIFO 可预测』不匹配且无 `## RENAMED` → 归档时该 MODIFIED 找不到目标、旧禁令 requirement 原样存活 → 合并后主 spec 自相矛盾（同时含「MUST NOT 强杀」与「任何时刻可抢」）。`openspec validate --strict` 不跨查主 spec，掩盖此洞。修：MODIFIED #1 header 改回原名，或补 `## RENAMED Requirements`，并按 10.1 重定义那两条既有 Scenario 语义。

**已确认干净、无需动作**：command-bridge 动作映射（只翻译浏览闭环动作，零 publish/edge.task 引用，无需改）；cloud→edge 主动命令白名单（新原因/布尔位都是 edge→cloud 字段、附于既有消息类型，无遗漏）；action.completed.action 口径（§6 不碰动作名）；RoleName 穷举、risk-state-machine 不误碰。

---

## 6. 推荐实装分批序列

> 原则：**假成功修复链必须同批**，协议两份+docs 同步，§8 绑进抢占批。每批一个可独立 typecheck+测试+提交的单元。cloud 批开工前先建 cloud worktree。

- **批 A（协议地基，两份 protocol.ts + docs + 断言）**：6.1（3 个释放原因，两份 byte-identical 同改）+ 6.2（`PublishCommandResultPayload` 加「已派发提交」布尔位，两份同改）+ 6.3（docs/protocol.md，顺带回填 `browser_wake_failed` 既有缺口）+ 6.4/11.9（**往返断言范围扩到「原因字符串 + 发布回执布尔位」**，edge+cloud 两份 protocol-contract.test.ts 各加，如 AC-PROTO-14/15）。热点文件，单写者，**不与他人并行**。
- **批 B（edge 提交窗口 + 写者注册表 + 抢占）**：5.1（六处提交窗口标志，按 §5.3 修正锚点；FB 加群窗口**同批带 5.10b 拆分**）+ 5.2（页面写者注册表，canExecute **也认在途发布写者**）+ 5.3（发布执行流注册为第二写者，带真取消；**动 main.ts，先与用户协调**）+ 5.4（抢占：严格高档抢占、同档 FIFO、窗口占用回剩余预算）+ 5.5（等停到期→控制面故障，**带窗口豁免判据**）+ 5.6（45s/200s 对齐）+ 5.8（删遗留整页发布处理器）+ 5.9（resumeBrowseIfIdle **且** canExecute 让位于在途发布写；顺带收紧假成功 CHECK 为正证据优先）+ 6.2 的边缘置位（按下那一刻置真，不复用 5.1 标志）。
- **批 C（cloud 失败语义，含 BLOCKER）**：**command-sequencer 加 `preempted` outcome 分类**（BLOCKER，5.1 节所述）+ 7.1（第四终局，「已开始」标志下移到 sent>0）+ 7.2（抢占计数+退避）+ 7.3（边缘硬暂停闸，含 ws-server/command-sequencer 真实机制点）+ 7.4（task_lease_mismatch 接线）+ 7.5（活跃租约中断走序列器 submitted 门、不 unwind）+ 7.6（edge.post 升三态、去重账本按已派发写）+ 7.7（巡视失败出口 + 空闲时钟停表）+ 7.8（被抢占原因级短路插在兜底滚动名单之前）+ 7.9（FB 评论走租约）+ 7.10（受理超时 20s→45s）+ 7.11（加群档位透传）。
- **批 D（edge 静默丢弃收口，绑 §7.8 同批部署）**：8.1（三处补诚实回执，**FB 两处排在用户 pacing 豁免之后、按内容特征定位、保留 pacing 穿透**）+ 8.2（巡视合成终态回执，注入点按 5.4 节 MEDIUM）。**8.1 的 open_note/refresh/profile_open 回执绝不先于 cloud 7.8 上线**。
- **批 E（收口）**：§9 优先级口径（一切发布=自动档，已用户拍板）+ §10 spec delta（**先修 MODIFIED header 不匹配**）+ §11 测试矩阵 + §12 真机项登记 backlog + §13 validate/部署 dev/archive。

**批间不变量**：假成功修复链 = 5.2+5.3+5.9+6.2+7.1+**command-sequencer 分类**，跨批 B/C，**必须一起部署**才安全（任何一半单独上线都可能净新增烧稿/双发）。edge 批可先落分支、跑本地门禁；cloud 批需 cloud worktree + ECS 部署闸。

---

## 7. 动手前必须先做（硬前置）

1. **把评审新发现并进 tasks.md**（否则下个 session 又踩）：① §5 顶部串行标记把 `command-sequencer.ts` 与 main.ts 并列为热点；② 5.10(b) 从「顺手项 `[ ]`」提为与 5.1 同批；③ 记录禁区真相（禁区尚未落地=用户未提交工作，8.1 FB 两处=禁区本身）；④ 补 §5.3 锚点修正表（或直接引本文档）；⑤ 批次不变量（假成功链同批、§8↔§7.8 次序）。
2. **动 main.ts 前与用户协调**：禁区（FB pacing 豁免）是用户正在改的未提交工作，8.1 FB 两处补回执与它落在同几行——必须排在其后、且当面对齐。
3. **cloud 侧开工前建 cloud worktree**（`../aidcp-cloud.wt/lease-strict-preemption`，用手动 `git worktree add`，先跑 `scripts/task-preflight`）。
4. **真机项里阻塞设计的两项**（§12）：A（小红书上传图后缩略图地址前缀=本机 or 平台，决定可抢占段是否留孤儿图）、B（脏编辑器页导航离开是否弹确认框，决定清场协议形状）——理论上 §3.4 已无条件接管对话框，但 spec 措辞需 A/B 结论。可留 backlog，但设计文案要留口。

---

## 8. 红线 / 不变量（贯穿全程，勿违背）

- **MUST NOT 静默假成功**（也不许假失败）：核心不变量。「已派发提交 ≠ 未派发」是本批的判别键，多处 naive 实装会净新增假成功/假失败/不可逆双发（见 §5.4）。
- **单边接线=净新增烧稿路径**（§4 血教训）：取消信号只有在抢占能力同批存在时才可翻真；假成功修复链必须整批同部署。
- **「600s 黑洞」这个数是错的**：云端选元素真实上界 1×200s，勿把 selectTimeoutMs 压到 180s 以下（会把合法 thinking 选择误判成 llm_error→烧稿）。
- **failed 是不可逆终态**（publish-log-store 无 failed→pending 回退），写了就救不回。
- **协议四处同步**（CLAUDE.md §2）：两份 protocol.ts 逐字一致 + command-bridge + docs/protocol.md + cloud→edge 白名单。本次 command-bridge/白名单**经确认无需改**，但两份 protocol.ts + docs 必须同步，且新增裸值要手写往返断言焊住（typecheck 抓不到）。
- **main.ts 禁区**：FB 租约闸 pacing 豁免段（用户占用，尚未提交）——绝不碰、按内容特征定位、动前协调。
- **canonical 停默认分支**：edge/cloud canonical 停 master，控制仓停 main，功能开发只在 linked worktree（CLAUDE.md §7）。
- **台账 SHA 必须已推送**、`git add` 显式列文件绝不 `-A`、不写敏感值、正文中文 code 英文、每次对话收尾给「说人话」总结。
- **相关 memory**：`lease-preemption-cancel-points`、`lease-failure-honesty-complement`、`failure-must-be-structural`、`edge-poll-helpers-iteration-bounded`、`note-open-miss-livelock`、`tasks-md-sha-must-be-pushed`、`concurrent-session-shares-subrepo-worktree`。

---

## 9. 如何恢复 session（接手第一步）

```bash
# 1. 认清位置
git -C /Users/baitianxing/codes/aidcp branch --show-current          # 应为 main
git -C /Users/baitianxing/codes/aidcp-edge.wt/lease-strict-preemption branch --show-current  # 应为 lease-strict-preemption，HEAD 35d3aec
openspec list | grep -E "lease-strict|browser-slot"                   # 看状态

# 2. 读计划与本交接
#    openspec/changes/lease-strict-preemption/tasks.md（权威计划）
#    openspec/changes/lease-strict-preemption/handoff-section-5-preemption-core.md（本文档）

# 3. 读设计评审 raw 结果（比总装配摘要更细）
#    subagents/workflows/wf_18b37a11-416/journal.jsonl（8 个坐实/对抗 result）

# 4. 先做 §7「动手前必须先做」，再按 §6 分批序列开工（批 A 协议地基起步）
```

**开工顺序建议**：先并 tasks.md（§7.1）→ 批 A（协议，纯 edge/cloud protocol.ts+docs，风险低、解锁其余批）→ 批 B（edge 抢占，动 main.ts 前协调）→ 建 cloud worktree → 批 C（cloud，含 BLOCKER）→ 批 D（§8 收口）→ 批 E（收口/spec/测试/部署/archive）。
