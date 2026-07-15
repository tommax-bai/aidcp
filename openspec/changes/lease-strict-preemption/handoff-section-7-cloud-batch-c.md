# 交接文档 — 批 C（cloud 失败语义「被抢占 ≠ 失败」，co-deploy 另一半）

> 写于 2026-07-15。给**换 session 接手 cloud 批 C** 用。edge 批 B（抢占激活 + 对抗复核加固）**已完整落地、门禁全绿、推 `origin/lease-strict-preemption`**（见 `handoff-section-5-preemption-core.md §0.6`）。本文档自包含，含 edge→cloud 新契约 + BLOCKER + 7.x 逐条锚点 + 落地序，可直接照着开工。
>
> **本文档的 cloud 锚点写于设计评审（wf_18b37a11-416）时；cloud 仓高度活跃、锚点可能漂移 → 动手前必须先在 cloud worktree 逐条复核（像 edge 那样先跑一轮 read-only 映射 workflow 再下刀）。**

---

## 0. 一句话状态

**edge 半边全绿并激活，但绝不可单独部署 —— 它现在会向云端回 `preempted_by_task`，而当前 cloud 会把它烧成不可逆 failed + 熔断。批 C 就是让 cloud「认而不烧」，两边 co-deploy 才安全。**

假成功修复链 = 5.2+5.3+5.9+6.2（edge，已落）+ **7.1 + command-sequencer 分类（cloud，本批）**，必须整批同部署。

---

## 1. 快速定位

| 项 | 值 |
| --- | --- |
| cloud worktree | `../aidcp-cloud.wt/lease-strict-preemption`（分支同名，批 A 协议已在其中，HEAD 从 `9f0194b`） |
| cloud canonical | `../aidcp-cloud`，停 `master`（**勿切分支**） |
| edge 分支（已推） | `origin/lease-strict-preemption` HEAD `6d87e39`（批 B 全落 + 加固） |
| edge 批 B 提交 | `bc3e774`(B-2a inert) / `b9fdfa5`(B-2b 激活) / `9a9ebda`(B-2c 删遗留) / `6d87e39`(B-2d 加固) |
| 设计评审 | `wf_18b37a11-416`（cloud 锚点来源）+ edge 加固复核 `wf_1657e89b-85a` |

**动手前先跑 `scripts/task-preflight`**（四仓 canonical 须停默认分支），再确认 cloud worktree 在位。

---

## 2. edge→cloud 新契约（批 A 协议 + 批 B edge 已落，批 C 要消费）

批 C 要认的**两个渠道**的抢占信号 —— 别混：

### 2.1 `edge.task.released` 渠道（租约释放）——由 `edge-task-lease-client.onReleased` 处理（§7.5）
edge 协调器释放租约时带 `reason`，批 A 新增 3 值（协议 `EdgeTaskReleasedPayload.reason`，两份 protocol.ts byte-identical）：
- **`preempted_by_task`**：被严格高档位抢占、**且 edge 已确认写者真停**（quiesce 成功）⇒ **可重投的干净让位**（edge 不进 terminal）。
- **`window_busy`**（+ 可选 `windowRemainingMs`）：抢占撞上不可逆提交窗口 ⇒ 在跑任务不动、challenger 被拒；云端应**按剩余预算精确重排 acquire**（不空转轮询）。
- **`yield_timeout`**：写者收到取消仍不停手 = 控制面故障 ⇒ 通向「**请运营重启浏览器客户端**」人工动作（§10.4），**不是自愈**、不可重投。
- 既有 `cdp_unhealthy`（控制面丢失，良性可恢复）edge 已在发、cloud `edge-task-lease-client:212` 已识别。

### 2.2 `publish.command.result` 渠道（发布命令结果）——**BLOCKER 所在，见 §3**
- edge 被抢占的发布 dispatch 回 `{ ok:false, error:'preempted_by_task' }`（PublishCommandDispatcher.dispatch 顶层 catch 统一分类）。
- 批 A 新增 `PublishCommandResultPayload.submitDispatched?: boolean`（**已派发提交动作**）：
  - `ok:false && submitDispatched===true` ⇒ **已点未确认**（提交动作已派发、结果未知）⇒ 云端按 `submitted_unconfirmed` 处置、**绝不重投**（否则双发）。
  - `ok:false && submitDispatched 缺省/false` ⇒ **压根没点**（提交前失败）⇒ 可重投。
  - edge 已置位：XHS/FB submit 在**按下事件派发那一刻**置真（onPressDispatched）；center 查找/no_target/控件禁用等点击前失败保持假。

**批 C 必须让 command-sequencer 同时认 `error:'preempted_by_task'`（→ preempted outcome）与 `submitDispatched`（→ submitted_unconfirmed vs failed_before_submit）。**

---

## 3. 🔴 BLOCKER：command-sequencer 的 `ok:false` 分类（tasks.md 从没点名的层）

- **文件**：`src/publish-agent/command-sequencer.ts`（评审锚点 `:238 / :258` 分类、`:219` catch）→ `src/publish-agent/publish-dispatcher.ts:380`（写 failed + 熔断）。
- **问题**：被抢占的发布在边缘一律以普通命令结果 `ok:false` 浮现（edge 三出口：`main.ts` 的 dispatch 顶层 catch 回 `preempted_by_task` / 在途回收回 `[recycled]` / canExecute 假回 `task_lease_mismatch`）。command-sequencer 对任何核心步 `ok:false` 一律归 `failed_before_submit`（`submitted` 只在 `ok:true` 才翻真）→ publish-dispatcher `:380` 写**不可逆 failed + 熔断**（publish-log-store 无 failed→pending 回退）。
- **后果**：即便 §7 其余全落地，被抢占的发布仍在序列器这一层就被烧成 failed。**这是假成功修复链真正的根。**
- **修法**：
  1. command-sequencer 在 `:238-258` 的 `ok:false` 分支与 `:219` catch 里识别抢占类原因串（`preempted_by_task` / `task_lease_mismatch` / `window_busy` / `yield_timeout`），产出**独立 `preempted` outcome**，**绝不并入 `failed_before_submit`**。
  2. 同时认 `submitDispatched`：`ok:false && submitDispatched===true` → `submitted_unconfirmed`（提交后终态、不重投）；提交后被抢占（已 submitted）一律走 submitted 终态、**绝不重投**（防已发出的稿被重投双发）。
  3. publish-dispatcher `:380` 之前加分支：`outcome==='preempted'` → 保持 pending、不写 failed、不 record 熔断，交抢占方释放后**事件驱动重投**（不靠 60s 兜底盲投）。

---

## 4. §7 逐条锚点 + 修法（评审坐实，动手前 cloud 复核）

> 目录多处 tasks.md 没写，务必带 `src/publish-agent/` | `src/comment-agent/` | `src/agents/`。

- **7.1 发布第四终局**（`src/publish-agent/publish-dispatcher.ts:331-343 / :380-409 / :99-142`）：被抢占＝保持待审、不写 failed、不计熔断、FB 素材走归还而非隔离、保留授权签名，事件驱动重投。`failed` 是**不可逆终态**（`publish-log-store.ts` 无 failed→pending 回退，确认过）。**「已开始」标志下移到首条产生平台副作用的命令真正发出（sent>0）之后**（今天在拿到租约瞬间置真 → 零副作用失败被判终态 + 熔断 +1）。
  - **HIGH（§5.4）**：活跃租约中断（7.5）MUST 表现为「让在飞那条 publish.command 就地 reject」交 runSequence 按 submitted(238/258) 归类，**绝不 unwind `executePublishSequence`**；「保持待审重投」只允许 `failed_before_submit` 且原因为抢占时触发；`submitted_unconfirmed`（含提交后被抢）走 371-379 submitted 终态、绝不重投。
- **7.2 抢占计数 + 退避**：「被抢占不计熔断」拆掉了唯一那道刹车，必须补：达阈值（建议 3）→ 停自动重投 + 通知运营。
- **7.3 边缘硬暂停闸**（`publish-dispatcher.ts:321-344`；真实硬暂停机制在 `ws-server.ts:212-222` + `command-sequencer.ts:308-312`）：验证码期云端暂停向该 edge 下发页面命令，而发布命令不在豁免名单 → 投递数 0 → 序列器立即 reject → 烧 failed + 熔断。下发前加闸；投递数为零按零副作用回待审。
- **7.4 `task_lease_mismatch` 接线**（`handler.ts` 全仓 0 命中确认；edge 发送点 `main.ts:727` 与 `:811`）：今天被当普通业务失败烧稿 + 熔断。识别为抢占类、走 preempted 而非 failed。
- **7.5 活跃租约中断通道**（`edge-task-lease-client.ts:210-244(onReleased) / :173-189(withLease)`）：收到 preempted/yield_timeout/排队超时释放 → 立刻中断该任务执行体、抛可区分错误；`window_busy` 按 `windowRemainingMs` 精确重排、不空等自己的计时器。
- **7.6 评论**（`src/comment-agent/comment-scheduler.ts:1271-1290 / :1523-1525`；真正失败分档 **1365-1373**，定向路径同构 **1194-1196**）：被抢占**不得判「未开始」**；已过提交点按「已提交待确认」写去重账本；被抢占的按需评论 = **放弃本次**（含 90s 人审），不重建、不本轮重试。
  - **HIGH（§5.4）boolean 接口塌三态→重复评论**：`edge.post()`（`comment-agent/facebook-edge-steps.ts:292` / 类型 `comment-task-runner.ts:59` / `edge-steps.ts:150`）今天返回 `Promise<boolean>`，把 edge 已在线的 `submitted_unconfirmed` 三态塌成 false → post_failed → 去重账本(comment-scheduler:1351)不写 → 下次排期重触发 = 重复评论。**修：升级为携带「提交是否已派发」的三态；去重写入门改为「提交已派发(submitted_unconfirmed ∪ confirmed)」而非 `ok===true`。**
- **7.7 巡视**（`role-dispatcher.ts:569-622` 只覆盖 acquire 失败；会话空闲时钟真实在 `src/agents/session-monitor-role.ts:211(checkIdle) / :153(pauseClock)`）：租约被撤 → 走既有失败出口收敛（解软暂停、回 feed）；独占租约期间空闲时钟**停表**。
- **7.8 🔴 「被抢占」原因级短路插在兜底滚动抑制名单判断之前**（`role-dispatcher.ts:2269-2282`，noRecoverScroll 名单 2269-2278 + 兜底滚动触发 2279-2282；tasks 原写 2149-2162 约错 120 行）：名单按动作名匹配，开笔记/刷新/看主页不在名单 → 一旦 edge §8.1 补诚实回执就会触发一次恢复滚动、滚到抢占方页面。**必须在 edge §8.1（批 D）上线前先落**（单边 = 净新增兜底滚动污染，§4 血教训同型）。
- **7.9 FB 评论走租约**（`comment-agent/facebook-edge-steps.ts`：search.execute(168)/note.open(204)/interaction.comment(233) **均无 taskId**，坐实）：不纳入 = 「覆盖全部独占任务」是假话；且今天有任何租约在跑时云端下发的 FB 评论命令会在边缘被静默丢弃、云端干等超时。
- **7.10 验证码协助受理超时 20s → 45s**（`captcha-assist.ts:349-368`）：覆盖最长 20s 提交窗口 + 取消停手 + 让位 + 往返。**5.6（边缘 45s 默认 vs 云端）与本条同批坐实**——两端受理预算一致，别单改成不一致的表。同一验证码事件多次提交改为续租而非重复抢占。
- **7.11 加群档位透传**：被抢占原因补进加群瞬态白名单；人工触发的加群把档位一路传下去（今天硬写自动档 → 运营手动敲的加群会被另一条人工任务抢掉）。

---

## 5. 落地序 + 对抗复核 + co-deploy 部署序

- **落地序（红线）**：批 C 内部 **command-sequencer 分类（BLOCKER）+ 7.1 + 7.4 + 7.5 + 6.2 消费（submitDispatched）** 是假成功修复链 cloud 半边，必须成套。7.8 必须在 edge §8.1（批 D）之前落。
- **对抗复核建议**：cloud 失败语义同样安全关键（不可逆 failed + 熔断），值得一轮独立对抗复核（并发/漏洞/三态塌陷三视角），像 edge `wf_3a8e8996` / `wf_1657e89b` 那样 —— 单测全绿 ≠ 无竞态（edge 两轮各揪出 BLOCKER）。
- **co-deploy 部署序**：批 C 全绿（cloud full + typecheck）→ 与 edge `6d87e39` **一起**部署 dev（CLAUDE.md §5 安全序列：backup → rsync --exclude .env/node_modules/.git → restart → healthcheck → 失败回滚）。**edge 分支与 cloud 分支同一批上，绝不 edge 先上**。dev 验证抢占端到端（12.6 F）后再考虑 archive。
- **批 D（edge §8 静默丢弃收口）绑 §7.8 同批**：8.1 FB 两处（定向评论/浏览 handler）**就是 FB pacing 禁区本身**（用户未提交工作）——排在用户 FB pacing 豁免落地后、按内容特征定位、**动 main.ts 前与用户协调**。8.1 的 open_note/refresh/profile_open 回执绝不先于 cloud 7.8 上线。
- **批 E 收口**：§9 优先级口径（一切发布=自动档，已用户拍板）+ §10 spec delta（**先修 MODIFIED header 不匹配**，§5.4 LOW）+ §11 测试矩阵 + §12 真机项登记 backlog + §13 validate/部署/archive。

---

## 6. 动手前必做（硬前置）

1. **cloud worktree 先跑一轮 read-only 映射**（像 edge 批 B 那样）坐实 command-sequencer / publish-dispatcher / comment-scheduler / role-dispatcher / session-monitor-role / edge-task-lease-client 的**当前**锚点（本文档锚点写于评审时、cloud 活跃可能漂移）。
2. **热点文件单写者**：command-sequencer、publish-dispatcher 是本批热点，不与他人并行。
3. **红线**：failed 不可逆（写了救不回）；被抢占 ≠ 失败；submitted_unconfirmed 绝不重投；单边接线 = 烧稿/双发；台账 SHA 必须已推送、`git add` 显式列文件绝不 `-A`、不写敏感值、正文中文 code 英文、收尾给「说人话」总结。
4. **相关 memory**：`lease-preemption-cancel-points`、`lease-failure-honesty-complement`、`failure-must-be-structural`、`tasks-md-sha-must-be-pushed`、`token-cost-from-billing-not-price-table`（TokenUsageStore 连错库那条与熔断/退避无关但同仓）。

---

## 7. 恢复 session（新 session 接手第一步）

```bash
git -C /Users/baitianxing/codes/aidcp branch --show-current          # 应 main
ls -d ../aidcp-cloud.wt/lease-strict-preemption                       # cloud worktree 在位？不在则 scripts/new-change 建
openspec list | grep lease-strict                                     # 看状态
# 读：本文档 + handoff-section-5-preemption-core.md §0.6（edge 批 B 事实）+ tasks.md §7 + design-review-synthesis-wf18b37a11.md
# 先做 §6 硬前置（cloud 锚点映射）→ 按 §3 BLOCKER 起步 → §4 逐条 → §5 co-deploy
```
