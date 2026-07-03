## Context

Phase 1（`content-schedule-auto-publish`，云端 `21ab431`+`397fd9e` 已部署、`AIDCP_CONTENT_SCHEDULE_AUTO=true` 已开闸）落了：三态周历（活跃 + 可自动位，自动 ⊆ 活跃云端强制）、每账号发帖开关 / 日上限、每分钟心跳的 `ContentScheduler`（fail-closed 掩码、错峰、幂等、风控 normal 闸、发帖全局串行、fire-and-forget、原子日上限 = 已发 + 在途）。

评论现状：只有飞书 `/comment` 命令式一条路——`CommentScheduler.triggerManual(accountId, opts)` 返回**触发回执**（`comment-scheduler.ts:87`），内含 persona 闸、边端在线检查、`running` 单飞（`:82 isRunning`）、接管边端 → 有界任务（搜索词 → 首屏甄选 → 撰写 → 去 AI 味 → **任务内联等飞书人审**（超时不发）→ 边端发布 → 入互动表）→ finally 恢复浏览 → **异步补结果卡**（`:205 postResultCard`）。互动表已账号感知（`pg-risk-store.ts:161,171`）但缺按账号当日计数方法。`RiskController.canDo(action)` 通用（`risk-controller.ts:60`）。手动 `/comment` 刻意跳配额（人是刹车）。

调度器多动作背板已预留：每账号 `inFlight` 单飞集合、错峰种子含动作维度（`offsetMinute(accountId, day, action)`）；但 tick 循环写死 `'post'` 一个动作、幂等键 `lastFired` 只按 accountId。

约束：无迁移器（DDL 幂等自愈）；退役 `default` 拒；MUST NOT 静默假成功；评论人审铁红线（未接线 / 超时 / 拒绝一律不发）；风控最终态单写（本变更只读 `canDo` / 计数）；协议 v2 不动。

## Goals / Non-Goals

**Goals:**
- 排期时段内按账号错峰自动发起评论任务，复用整条命令式评论管线（人审 / 单飞 / 结果卡全现成）。
- 每账号「自动评论」开关 + 日上限，fail-closed（未配 = 不自动）。
- 自动路径过 `canDo('comment')` 配额闸（区别于手动跳配额）。
- 诚实空槽：无强相关目标 → 0 产出、结果卡如实回报。

**Non-Goals:**
- 不做有界翻页（独立后续变更 `comment-bounded-pagination`，有真机探针前置）。
- 不做群评自动化（Phase 3，前置未满足）。
- 不做评论的每账号时段覆盖 UI、不加协议消息、不动三态周历。

## Decisions

### D1. 调度器动作循环 + 幂等键升维

tick 内对 `['post','comment']` 逐动作判定：各自 enabled / cap / 错峰分钟；幂等键从「accountId → 小时格」改为「`accountId|action` → 小时格」（否则发帖触发会把同小时的评论槽也吞掉——Phase 1 单动作时无此问题，多动作必修）。每账号每 tick 至多 fire 一个动作（`inFlight` 单飞背板 + fire 后 break 该账号的动作循环），避免同账号同分钟双动作抢边端。

- **为何 post 在前**：发帖纯云端、不接管边端；若同账号同小时两动作都命中（哈希撞车），发帖先走、评论顺延到它自己的错峰分钟或下一活跃小时——影响最小。

### D2. 评论动作三闸（替代发帖的全局串行）

评论不需要发帖那种全局串行（`publishAccountRef` 是发帖生成段的全局槽；评论任务按账号接管各自边端、互不共享可变槽）。评论专属闸：

1. **单飞**：`isCommentBusy(accountId)`（= `commentScheduler.isRunning`）在跑不重触发；调度器自己的 `inFlight` 再兜一层。
2. **原子日上限（无需新台账）**：cap 判定 = `countInteractionsTodayForAccount(accountId,'comment')` +（在跑 ? 1 : 0）。**论证**：评论管线是「任务内联等审」模型——撰写后在任务内阻塞等飞书 approved（超时不发），任务单飞、发完即写互动表；不存在「多张草稿排队待审」的窗口。重启时任务随进程死、审批信号无人等待不会发送，无孤儿。故「已发 + 在跑」即原子，早前对抗评审设想的「评论 pending 台账」在此模型下不必要。
3. **`canDo('comment')` 配额闸**：手动 `/comment` 跳配额是因为人逐条掌控；自动路径无人在场，MUST 过风控配额，被拒回黄卡如实说明、本槽不触发。

### D3. server 接线：triggerComment 包装 + 结果卡不重复

`deps.triggerComment(accountId)` 在 server 侧实现：先 `canDo('comment')`（拒 → 黄卡「配额拒绝、本槽未触发」）；过则调 `commentScheduler.triggerManual(accountId)`——**触发回执**非 ok（边端离线 / 未绑人设 / 已在跑）也回黄卡如实说明；任务**终态**结果卡由评论链自己的 `postResultCard` 补，包装层 MUST NOT 重复发终态卡（只发「未能触发」类回执卡）。fire-and-forget 天然成立（`triggerManual` 触发回执快、任务异步跑）。

### D4. 数据与面板：与发帖字段严格同构

侧表自愈 `ADD COLUMN IF NOT EXISTS comment_enabled BOOLEAN NOT NULL DEFAULT false` / `comment_daily_cap INTEGER NOT NULL DEFAULT 0`；patch 校验、DTO、`effectiveScheduleFor`、面板 PUT、console 列全部镜像发帖字段的形态（布尔 / 0..50 整数、非法整块拒、写后回读真态、未配 = 不自动）。文档迁移 `0029_content_schedule_comments.sql`。

### D5. 文案诚实（防「格子 = 会发」误读）

console「自动评论」列与提示 MUST 表述为「该时段**尝试**自动评论：自行搜索目标、可能 0 产出、每条需飞书人审」；结果卡对 `no_strong_candidate` 如实报「未找到强相关目标、本次不评」。首屏甄选命中率有限是已知现状，翻页增强属后续变更。

## Risks / Trade-offs

- **[自动评论挤占浏览会话]** 评论任务接管边端会暂停自动浏览。→ **Mitigation**：错峰（每动作每活跃小时至多一次）+ 日上限 + 任务有界 + finally 恢复浏览；运营经日上限控制频度。
- **[首屏命中率低 → 空槽卡多]** 无翻页时 `no_strong_candidate` 概率高，结果卡可能常报「未找到目标」。→ **Mitigation**：文案讲清是诚实空槽非故障；`comment-bounded-pagination` 作为独立增强跟进。
- **[同账号双动作同小时撞车]** 哈希偶发同分钟。→ **Mitigation**：动作循环 post 在前 + 每 tick 每账号至多一动作 + 各动作独立幂等键（评论槽不被吞、顺延自身分钟）。
- **[并发 session 热点文件交织]** `server.ts` / `panel/*` 仍被并发方高频改。→ **Mitigation**：热点脏则隔离 worktree 编写、`git archive` 干净树部署；worktree 提交显式列文件。
- **[归档顺序]** 本 delta 以未归档 Phase 1 的 spec 为 base。→ **Mitigation**：归档序固定「先 `content-schedule-auto-publish` 后本变更」，proposal 已明示。

## Migration Plan

- DDL：两列自愈补列（幂等），无回填（默认 false/0 = 不自动 = 零回归）；文档 `0029`。
- 回滚：纯新增、默认关——撤代码即回 Phase 1 行为；列留空无副作用。
- 部署：cloud 测试全绿后按安全序列（工作树脏则 `git archive`）；console build 后 rsync（不 `--delete`）。部署后无需开关——`AIDCP_CONTENT_SCHEDULE_AUTO` 已开，评论是否自动完全由每账号开关（默认关）决定。

## Open Questions

- 评论错峰是否需要与发帖强制隔开最小间距（如同小时内 ≥10 分钟）？（默认：不做——哈希天然大概率岔开，同小时同账号双动作已由「每 tick 一动作」限制为串行,YAGNI。）
- 空槽卡是否需要「连续 N 次空槽自动降频」？（默认：本变更不做，留缝；运营先用日上限手控。）
