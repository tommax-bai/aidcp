## Why

内容排期 Phase 1（`content-schedule-auto-publish`，已部署开闸）只做了定时自动**发帖**；运营同样需要账号在排期时段里自动**发评论**（自动挑一篇强相关笔记、写一条评论、人审通过后发出），今天评论只有飞书 `/comment` 手动一条路。评论管线本身已完整且带人审、单飞、结果卡——缺的只是「定时触发来源 + 每账号评论开关/日上限 + 自动路径的配额闸」。

本变更是「多账号内容排期」**Phase 2，只加评论**；发带群组的评论仍不做（Phase 3，前置未满足：`account-group-chat-injection` 真机验证「审=发」+ 部署 + 归档、一码一号升级硬阻断、以 MODIFIED delta 放宽其「仅命令式」spec）。

## What Changes

- **【调度器动作循环】** 内容调度器 tick 从「只判发帖」扩为按动作循环（发帖 + 评论）：各动作独立的开关 / 日上限 / 错峰分钟（错峰种子已含动作维度）/ 幂等键（幂等键从「按账号」修为「按账号 × 动作 × 小时格」）。每账号每 tick 至多一动作（单飞背板已有）；「自动 ⊆ 活跃」与风控 normal 闸沿用（账号级统一判）。
- **【评论动作专属闸】** 评论不需要发帖那种全局串行（各账号接管各自边端），改用三道：① `isCommentBusy(accountId)` 单飞（评论任务在跑不重触发）；② **原子日上限** = 今日已发评论数（互动表按账号当日计数，新增查询方法）+（在跑 ? 1 : 0）——评论管线是「任务内联等审」模型，任务单飞 + 发完即入库，无需新的在途台账（设计里写明论证）；③ **`canDo('comment')` 配额闸**——手动 `/comment` 刻意跳配额（人是刹车），自动路径无人在场 MUST 过配额，被拒回黄色卡如实说明、不触发。
- **【复用评论管线 + 结果卡免费】** 排期触发直接调用现有命令式评论入口（persona 闸 / 边端在线检查 / 接管边端 / 有界任务 / 人审 / finally 恢复浏览 / 结果卡全部现成）；可能诚实产出 0 条（首屏无强相关目标 → `no_strong_candidate`），结果卡如实回报。
- **【每账号排期加评论字段】** 排期侧表自愈加两列 `comment_enabled`（默认 false）/ `comment_daily_cap`（默认 0），fail-closed 与发帖同构；面板 PUT / DTO / console 账号表各加「自动评论」开关 + 日上限两列。
- **【文案诚实】** UI 表述为「该时段尝试自动评论：自行搜索目标、可能 0 产出、每条需飞书人审」，MUST NOT 表述为「发 N 条评论」。
- **【范围裁剪】** 有界翻页**不在本变更**：它是搜索甄选链的保真属性（同样惠及手动 `/comment`），且有真机探针前置（搜索结果页滚动加载行为未经核实），留作独立后续变更 `comment-bounded-pagination`；本变更先用今天的首屏甄选（命中率低 = 诚实空槽多，如实回卡，不算坏账）。三态周历不变（白点 = 允许自动内容，做什么由每账号表勾选）。

> 非 BREAKING：新列默认关 / 0、调度器无评论配置时行为与今天逐位一致；手动 `/comment` 一字不变、不受时段限制。

## Capabilities

### Modified Capabilities
- `content-schedule`: 动作维度从「仅发帖」扩为「发帖 + 评论」——重写「本能力仅覆盖发帖」条款（评论纳入、群评仍排除并保留其前置声明）；新增评论动作的排期行为要求（动作循环与每动作幂等、评论三闸：单飞 + 原子日上限 + `canDo('comment')` 配额、诚实空槽与结果卡、手动不受限、文案诚实）。
- `console-write-operations`: 内容排期写通道新增 `commentEnabled` / `commentDailyCap` 两字段，校验与发帖字段同构（布尔 / 0..50 整数、非法整块拒、写后回读真态）。

## Impact

- **aidcp-cloud**：`config/content-schedule-store.ts`（自愈 `ADD COLUMN IF NOT EXISTS` 两列 + patch 校验 + DTO + `effectiveScheduleFor` 扩展）；`orchestrator/content-scheduler.ts`（动作循环 + 幂等键改 `(account, action, 小时格)` + 评论闸 deps）；`risk/pg-risk-store.ts`（新增 `countInteractionsTodayForAccount(accountId, action)`，interactions 表已账号感知）；`server.ts`（`triggerComment` 接线：`canDo('comment')` 闸 + 黄卡 + 调 `commentScheduler.triggerManual`；触发回执异常回卡；终态结果卡由评论链自补、不重复发）；`panel/types.ts` + `panel-server.ts`（patch 两字段）；文档迁移 `migrations/0029_content_schedule_comments.sql`（0028 已占）。
- **aidcp-console**：`ContentSchedulePage` 账号表加「自动评论」开关 + 日上限列；`types/api.ts` 镜像两字段；诚实文案。
- **不触及**：协议 v2（评论任务走既有信封）；`RiskController` 最终态单写（只读 `canDo` / 计数）；发布链；群评（不加开关、不接线）；三态周历与浏览掩码。
- **协同风险**：云端仓有并发 session 活跃改动（prompts / evaluator 一带）；本变更主要文件（content-schedule-store / content-scheduler / ContentSchedulePage）为本线独有、交织面小；`server.ts` / `panel/*` 仍是热点——落地时若工作树脏则走隔离 worktree 编写 + `git archive` 干净树部署（成熟套路）；worktree 内提交必须显式列文件（gitignore 尾斜杠不匹配软链的教训）。
- **openspec 顺序**：本变更对 `content-schedule` 的 delta 以 Phase 1（`content-schedule-auto-publish`，未归档）的 spec 为 base——**归档必须先 Phase 1 后本变更**，使 MODIFIED 有据可依。
