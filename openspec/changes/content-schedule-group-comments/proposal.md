## Why

内容排期已覆盖定时发帖（Phase 1）与定时评论（Phase 2，均已部署开闸）；运营需要第三种动作——定时自动发**带群组引流码的评论**（自动挑强相关笔记、写评论、把该账号的群码 verbatim 接入、人审通过后发出），把评论引流也纳入排期。此前群评自动化被 Phase 1/2 明确排除，前置是 `account-group-chat-injection` 真机验证「审=发」+ 部署 + 归档——**该前置已于 2026-07-03 满足**（并发线完成归档：边端保真定案为「正文逐字敲 + 群码整段原子插入」并有真机探针，spec 已合并）。剩余前置（一码一号硬阻断、群评日计数持久化、人审卡量结构性受限）在本变更内落齐。

本变更是「多账号内容排期」**Phase 3（收官）**；评论搜索翻页不在本变更（归 `comment-search-command` 家族 / 评论自动发布那条线）。

## What Changes

- **【调度器第三动作】** 动作循环扩为发帖 + 评论 + **群评**：群评沿用命令式评论机器（`triggerManual(accountId,{injectGroup:true})`，缺码 fail-closed / 人审内联 / 结果卡自带全现成，comment-agent 零改动）；单飞与评论共用（同一评论机器，天然互斥）；错峰分钟按群评动作独立哈希；幂等键（账号 × 群评 × 小时格）；每账号每 tick 至多一动作不变。
- **【群评日上限 = 每日自动尝试上限（持久、方向保守）】** 新极薄表 `group_comment_attempts`（账号 + 时刻），**触发回执 ok（任务真开跑）即记一条**；按「尝试」而非「发出」计数——被人审拒 / 无强相关目标也占额度，宁少勿多（协同 spam 敏感动作取保守方向）；重启不清零、绝不超发。**硬上限 0..10**（区别于发帖/评论的 0..50，越界整块拒），UI 建议 ≤3。
- **【一码一号硬阻断（开启即校验，非软告警）】** 开启某账号自动群评时：该账号无群码 → 具名拒 `no_group_code`；该账号群码与任一其它账号 verbatim 相同 → 具名拒 `shared_group_code`。绝不静默降级、绝不仅告警放行。触发时缺码 fail-closed 仍在（纵深防御）。
- **【自动路径配额】** 群评自动触发 MUST 过 `canDo('comment')`（与 Phase 2 评论同构；手动 `/comment group:on` 仍跳配额、人是刹车），被拒黄卡如实说明。
- **【放宽「仅命令式」spec（正式 MODIFIED）】** `group-chat-injection` 的「仅命令式路径注入」条款重写：**浏览闭环 composer 永不注入 = 硬不变量保留**；注入 MAY 由内容排期调度器触发，但 MUST 仍经同一命令式评论任务机器 + 人审 + 排期刹车（尝试型日上限 / 错峰 / 一码一号硬阻断）。
- **【每账号排期两列 + 群码徽标】** `group_comment_enabled` 默认 false / `group_comment_daily_cap` 默认 0（自愈加列，fail-closed 同构）；catalog 派生 `hasGroupCode`（Phase 1 注记归本期）。console 账号表加「自动群评」开关 + 日上限列；无码账号开关禁用 + 红徽标「未配群码」；开启被拒的诚实文案（「该群码已配到其它账号——一码一号是防关联封号的硬要求」）。
- **【人审卡量结构性受限（不另造节流器）】** 群评卡量上界 = Σ(各账号 cap ≤10、建议 ≤3) × 错峰打散 × 单飞串行，设计里论证结构性满足、专门聚合节流器按 YAGNI 不做。

> 非 BREAKING：两列默认关 / 0，未配置时调度器行为与 Phase 2 逐位一致；手动 `/comment group:on` 一字不变。

## Capabilities

### Modified Capabilities
- `content-schedule`: 动作维度扩为「发帖 + 评论 + 群评」——重写覆盖条款（群评从排除改为纳入但带独占刹车、翻页缺口声明保留）；新增群评动作 requirement（尝试型持久日上限、一码一号硬阻断纳入开启路径、单飞共用评论机器、自动路径配额、诚实黄卡）。
- `group-chat-injection`: 重写「仅命令式路径注入」条款——浏览闭环永不注入保留为硬不变量；排期调度器触发放行但 MUST 经同一命令式机器 + 人审 + 排期刹车。
- `console-write-operations`: 内容排期写通道新增群评两字段；`groupCommentEnabled=true` 的开启校验（`no_group_code` / `shared_group_code` 具名拒、绝不部分落库）。

## Impact

- **aidcp-cloud**：`config/content-schedule-store.ts`（两列自愈 + `group_comment_attempts` 表 + 开启校验跨查 `accounts.group_chat_info` + 计数 / 记录方法 + DTO / effective 扩展 + cap 硬上限 10）；`orchestrator/content-scheduler.ts`（第三动作 + deps `triggerGroupComment` / `groupAttemptsTodayCount`）；`server.ts`（`triggerGroupComment` 包装：canDo 闸 + 触发回执透传黄卡 + ok 记 attempt）；`panel/types.ts` + `panel-server.ts`（两字段）；文档迁移 `migrations/0030_content_schedule_group_comments.sql`（0029 已占）。
- **aidcp-console**：`ContentSchedulePage`（群评列 + `hasGroupCode` 徽标 + 诚实文案）+ `types/api.ts` 镜像。
- **不触及**：`comment-agent/*`（活跃 change `comment-search-command` 的地盘——群评触发入口已存在，纯调用）；协议 v2；风控最终态单写；边端（保真已落地）；浏览闭环；三态周历。
- **协同风险**：`server.ts` / `panel/*` 热点走既有 worktree 车道（`scripts/new-change` / `land-change`）；worktree 内提交显式列文件。
- **已知残余（设计明写，诚实非零）**：一码一号消除了跨账号**同码**指纹，但「多账号各自的码在同段时间高频出现」仍是行为面信号——靠小日上限（硬 ≤10、建议 ≤3）+ 错峰 + 人审逐条压制。
- **建议项（登记真机 backlog、不阻塞代码）**：运营开启任一账号自动群评前，先手动 `/comment <昵称> group:on` 真机端到端发一条，确认「审=发」在生产链路成立。
