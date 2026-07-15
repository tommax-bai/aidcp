## Context

FB 定向评论路径 `runFacebookTargetedTaskBody`（`comment-scheduler.ts:719-938`，人审阻塞在 `:901` `approveFacebookComment`，提交在 `:917`）全程不握边端租约。同一 FB 浏览器会话并发跑自治 browse+like 闭环（RoleDispatcher 驱动）。边端 FB 命令入口 `main.ts:866-881` 按 `canExecute((env.payload).taskId)` 无差别门控：`canExecute(undefined)` 在**空闲**（无 active 租约）时放行（`edge-task-coordinator.ts:311` `return !taskId`）、在**持租约**时挡掉（`:305` `return !!taskId && active.taskId===taskId`）。故今天审批期浏览闭环的无标识 `page.scroll`/返回被放行、`ensureFeed` 导航回 HOME、目标帖离页 → 提交时 own-identity 收窄评论框失败 `editor_not_found`。

小红书 `runXhsTargetedTaskBody` 已把 搜索→pick→读→撰写→人审→发布 整段包进 `withLease({kind:'comment_prepare', leaseMs:KEEP_OPEN=4min})`（`comment-scheduler.ts:1287-1360`），`edgeFor(lease.taskId)` 让每条命令带 taskId → 持锁期浏览闭环无标识命令被挡、页面钉死。spec 在 `comment-search-command`。

## Goals / Non-Goals

**Goals:**
- FB 定向评论（手动 + 排期）镜像 XHS：keep-open 租约包住全段、贯穿人审不释放边端、每条 FB 命令透传 taskId。
- 诚实边界不破：AC-PUB、就地核对身份、不重复评论全保留；租约失败 / 被抢占走诚实非提交。

**Non-Goals:**
- 不改边缘（taskId 门控与 canExecute 既有；`main.ts:873` 已读 `payload.taskId`）。
- 不动 XHS 路径、不动 RoleDispatcher 浏览闭环、不动刚归档的 `comment-approval-target-hold`（两个正交的洞）。
- 不引入新协议消息、不改 FB 执行端逻辑。

## Decisions

### D1：租约边界 = 从 `buildFacebookEdgeSteps` 到提交整段（含 search）
**选择**：把 `runFacebookTargetedTaskBody` 现在 `802-937`（建 steps → search → pick → open → compose → validate → contact → shadow → approve → submit → audit）整段移进 `withLease` 回调，steps 用 `lease.taskId` 构建。cloud-only 前置（config / 配额闸 / 连接检查，`731-800`）留在租约外。
**理由**：审批期钉住页面要求 open 与 approve 与 submit 在**同一连续租约**内；把 search 也纳入与 XHS 一致、且省去「search 在租约外被浏览闭环打断」的边角。shadow 分支在回调内 early-return（租约随之释放），holds 短、无害。
**备选（弃）**：只包 open→submit——search 在租约外仍可能被浏览闭环干扰，且与 XHS 不一致。

### D2：`priority` 由 `manualOverride` 派生
**选择**：`const priority = options.manualOverride ? 'human' : 'automatic'`。
**理由**：`manualOverride` 已是「手动操作员命令」的既有信号（`:787` 据它跳过配额闸）；手动 = human、排期 = automatic，与 XHS 的 `options?.priority ?? 'human'` 同口径。无需新增参数穿透所有调用点。

### D3：taskId 透传到三条 envelope，边缘不改
**选择**：`FacebookEdgeStepsDeps` 加 `taskId?: string`；`search.execute`/`note.open`/`interaction.comment` 三条 payload 各挂 `...(deps.taskId ? { taskId: deps.taskId } : {})`。
**理由**：边端 `main.ts:871-873` 已从 `env.payload.taskId` 取值门控——payload 挂上即生效，边缘零改动。可选形态保持无租约旧测试构造零回归。

### D4：租约失败 / 被抢占 = 诚实非提交
**选择**：① 租约获取超时（`EdgeTaskLeaseError('acquire_timeout')`）在 body 内 catch → audit 诚实非提交终态（不打去重、可重试），不落到外层 wrapper 的泛化 `exception`。② 提交被抢占：FB 边端对失配 taskId 命令**静默丢弃**（`main.ts:873` warn+return 无回执）→ 云端 `submitComment` 超时 → 现有 `reallySubmitted=false` 路径已诚实（不打去重、可重试）。若边端回执带 preemption reason，现有 `reason!==ok && !=verification_ambiguous` 分支同样不打去重、诚实。
**理由**：符合 lease-strict-preemption「被抢占≠假成功」；FB 边端不发失配命令的显式 preempted 回执（与 XHS 略异），但超时即诚实非提交，无 AC-PUB 风险。

## Risks / Trade-offs

- **[持锁却不透传 taskId → 自锁死锁]** → D3 强制三条命令都挂 taskId；单测断言每条 envelope 带 taskId；spec Scenario 4 red-line 反例锁死。
- **[shadow 路径也持锁、短暂挡住浏览闭环]** → shadow 只读、~10s 内 early-return 释放；可接受（shadow 本就该独占读、不被浏览闭环滚走）。若判定过重，可后续把 shadow 排除在租约外（本 change 先求正确一致）。
- **[排期评论频繁申请租约增加边端往返]** → 与 XHS 排期同代价；租约获取在浏览闭环不持锁时快速授予（浏览命令无标识、不占租约）。
- **[热点文件 comment-scheduler.ts]** → 与 lease 族串行集成、合入前 rebase + 复跑闸。
- **[被抢占报 timeout 而非 preempted]** → FB 边端不发失配命令回执，语义略糙但诚实（非提交、可重试）；手动 /comment 罕发，操作员可重跑。登记为已知残留。

## Migration Plan

1. `aidcp-cloud` worktree 实装（cloud-only 两文件）。
2. `npm run test:acceptance`（AC-PUB / FB 评论闸全过）→ `npm test` → `npm run typecheck`。
3. 合入前 rebase 最新 master、跑闸；ff-push。
4. 默认部署 dev（clean snapshot rsync → restart → healthcheck）。
5. 真机灰度：运营 `/comment <目标> --join`，观察审批期停在目标帖、审后原地发出、并发浏览闭环命令被挡（backlog 簇 48/58）。
- **回滚**：cloud-only、无协议/DB/边缘变更，回滚即还原两文件。

## Open Questions

- shadow 是否值得排除在租约外（省 dev 高频 shadow 的租约往返）——先纳入求一致，真机看 shadow 频率再定。
- 是否给 FB 边端补失配命令的显式 preempted 回执（对齐 XHS 语义）——本 change 不做（边缘不改红线），超时诚实即够；登记残留。
