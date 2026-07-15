## Why

真机事故（2026-07-15）：运营 `/comment --join` 让 FB 账号在新群评论，成功加群 + 搜索 + 开帖、人也审批通过了，但提交失败 `submit_failed:editor_not_found`，运营看到「打开正文后没等审批完就返回了首页」。跨仓核查 + 对抗复核确认：FB 定向评论路径 `runFacebookTargetedTaskBody` **全程不握任何边端租约**，而同一浏览器会话并发跑着自治 browse+like 闭环——审批阻塞的那段时间里，那条浏览闭环的 `page.scroll`/返回命令（无 taskId）在边缘「无租约占用」时被放行，把页面导回首页；审批一通过再去发评论，目标帖已不在页 → 执行端按目标帖唯一身份收窄评论框、诚实回 `editor_not_found`。小红书早已用 keep-open 租约根治此问题（`comment-search-command` 已规定），Facebook 这条手动/排期定向评论路径漏了这一步。

注：这与刚归档的 `comment-approval-target-hold` 是**两个不同的洞**——那个保护的是 RoleDispatcher 浏览闭环**内部就地触发**的评论（经 CommentApprovalGate、云端 `commentInflight` 扣自己的浏览命令）；本路径由 CommentScheduler 独立驱动、不碰 RoleDispatcher，两个子系统云端互相够不到，只能靠**边端租约**在更底层把无标识浏览命令挡掉。

## What Changes

- FB 定向评论路径（`runFacebookTargetedTaskBody`，覆盖手动 `/comment` / `--join` 与自动排期两条触发）把「搜索 → 开帖 → 撰写 → 飞书人审 → 提交」整段包进**一个持续持有的边端 keep-open 租约**（`kind:'comment_prepare'`，`leaseMs` 覆盖搜索+读+人审超时+提交最坏耗时），**贯穿人审等待窗口不释放边端**——镜像小红书 `comment-search-command` 的做法。
- **必配（否则死锁）**：给 FB 三条评论命令（`search.execute` / `note.open` / `interaction.comment`）透传该租约的 `taskId`。因为边缘的 FB 命令入口已按 `canExecute(payload.taskId)` 无差别门控（`aidcp-edge/src/main.ts:873`）：持租约期无标识命令一律被挡——**评论自己的命令若不带 taskId 会被自己设的租约一起挡死**。透传后：评论命令（带匹配 taskId）放行、自治浏览闭环命令（无 taskId）被挡 → 页面钉死在目标帖。
- `priority` 由 `manualOverride` 派生：手动操作员命令 = `'human'`、自动排期 = `'automatic'`（与小红书同口径）。
- 诚实边界不变：租约只负责「把浏览器钉在目标帖上」；未授权 / 超时 / 被拒照样不发（AC-PUB 保持）；不评错帖、不重复评论、发布前就地核对身份等红线全不动。被抢占 / 拿不到租约 → 诚实非提交终态（不打去重、可重试），绝不静默假成功。
- **边缘不改**：taskId 门控与租约接线是既有通道（`edge-task-coordinator.canExecute` + `main.ts` FB 命令入口），本 change 纯 cloud-only（两文件）。

## Capabilities

### New Capabilities
<!-- 无新增能力：扩展既有 FB 评论能力 + 复用既有边端租约机制。 -->

### Modified Capabilities
- `facebook-scheduled-comment`: 新增要求——FB 定向评论（手动与排期两路）MUST 在一个持续持有的边端 keep-open 租约内完成「搜索 → 开帖 → 撰写 → 人审 → 提交」全段、贯穿人审不释放边端、且 MUST 给每条 FB 评论命令透传该租约 taskId（否则自锁死锁）。

## Impact

- **代码（cloud-only，`aidcp-cloud`）**：`src/comment-agent/comment-scheduler.ts`（`runFacebookTargetedTaskBody` 包 `edgeTaskLeases.withLease`、派生 priority、租约获取失败/被抢占诚实终态）、`src/comment-agent/facebook-edge-steps.ts`（`FacebookEdgeStepsDeps.taskId` + 三条 envelope payload 挂 taskId）。**边缘 `aidcp-edge` 无改动**（`main.ts:873` FB 命令入口已按 `payload.taskId` 门控、`canExecute` 既有）。
- **热点约束**：`comment-scheduler.ts` 属租约/命令映射片区，与近期 `lease-strict-preemption`（已归档）同族——集成串行、合入前 rebase + 复跑闸。
- **安全红线**：AC-PUB（未授权绝不发评论）必须保持；被抢占 / 租约失败绝不静默假成功。
- **测试**：新增 scheduler 单测覆盖「keep-open 租约包住搜索→人审→提交」「FB 命令带 taskId」「租约获取失败 / 提交被抢占 → 诚实非提交终态」。真机灰度项归 backlog 簇 48/58（手动 /comment）。
