> 范围：Phase 3（收官），只加定时群评。翻页归 `comment-search-command` 家族；**comment-agent/\* 零改动**（活跃 change 地盘，触发入口 `triggerManual(id,{injectGroup:true})` 已存在纯调用）。
> MODIFIED base（content-schedule / group-chat-injection / console-write-operations）均已在 openspec/specs/，归档无顺序约束。

## 1. aidcp-cloud — 数据层

- [ ] 1.1 `account_content_schedule` 自愈加列 `group_comment_enabled BOOLEAN NOT NULL DEFAULT false` / `group_comment_daily_cap INTEGER NOT NULL DEFAULT 0`；新表 `group_comment_attempts (id BIGSERIAL PRIMARY KEY, account_id TEXT NOT NULL, attempted_at TIMESTAMPTZ NOT NULL DEFAULT now())` + 按账号索引（均幂等，store `init()` 自建）
- [ ] 1.2 `ContentScheduleStore`：patch 校验（布尔 / **0..10** 整数 `GROUP_COMMENT_DAILY_CAP_MAX`，越界整块拒）、行 DTO / `effectiveScheduleFor` / catalog 扩两字段；catalog 派生 `hasGroupCode`（LEFT JOIN accounts.group_chat_info IS NOT NULL）
- [ ] 1.3 **一码一号开启硬校验**：`setAccount` 收到 `groupCommentEnabled: true` 时——无码拒 `no_group_code`、与任一其它账号群码 verbatim 相同拒 `shared_group_code`（跨查 accounts，每次开启写入重跑）；结果联合加两具名 reason
- [ ] 1.4 attempts 方法：`recordGroupCommentAttempt(accountId)` + `countGroupAttemptsToday(accountId)`（服务器本地日历日）
- [ ] 1.5 人审文档 `migrations/0030_content_schedule_group_comments.sql`（两列 + attempts 表 DDL，与 store 自愈 SQL 同源）

## 2. aidcp-cloud — 调度器第三动作

- [ ] 2.1 动作循环扩 `['post','comment','group_comment']`：群评 enabled/cap 闸、按动作独立错峰分钟与幂等键、每账号每 tick 至多一动作不变
- [ ] 2.2 群评闸：单飞共用 `isCommentBusy`（同一评论机器）；日上限 = `groupAttemptsTodayCount(accountId) >= cap` 跳过（尝试型、持久）
- [ ] 2.3 deps 扩：`triggerGroupComment?(accountId)` / `groupAttemptsTodayCount?(accountId)`（可选三件套形态，未注入=群评动作整体跳过、零回归）

## 3. aidcp-cloud — server 接线

- [ ] 3.1 `triggerGroupComment` 包装：`canDo('comment')` 拒 → 黄卡；过 → `commentScheduler.triggerManual(accountId,{injectGroup:true})`；回执非 ok（缺码 fail-closed / 离线 / 未绑人设 / 在跑）→ 黄/红卡透传；**回执 ok → `recordGroupCommentAttempt` 再返回**；终态结果卡评论链自补、不双卡；卡片名「排期群评（自动）」
- [ ] 3.2 deps 注入（条件挂 commentScheduler 存在）：`groupAttemptsTodayCount` = store 计数

## 4. aidcp-cloud — 面板 API

- [ ] 4.1 `panel-server.ts` PUT 校验两字段（布尔 / number，语义与硬校验在 store 整块拒）；patch 类型经 store import 自动扩

## 5. aidcp-console — 排期页

- [ ] 5.1 账号表加「自动群评」开关 + 日上限列（max=10）；无码账号开关禁用 + 红徽标「未配群码」（用 catalog `hasGroupCode`）
- [ ] 5.2 开启被拒诚实文案：`no_group_code` →「该账号未配群码，请先到账号页录入」；`shared_group_code` →「该群码已配到其它账号——一码一号是防关联封号的硬要求」；列提示「每日自动**尝试**上限（被拒/无目标也占额度）；每条仍需飞书人审；建议 ≤3；改码后请自查一码一号」
- [ ] 5.3 `types/api.ts` 镜像两字段 + `hasGroupCode`

## 6. 测试与回归

- [ ] 6.1 调度器单测：群评动作循环 / 幂等独立 / 单飞共用评论 / 尝试型日上限 / 三件套未注入跳过
- [ ] 6.2 store 单测：两列校验（0..10 越界拒）/ 一码一号硬校验（无码拒、同码拒、异码过、每次开启重跑）/ attempts 记录与当日计数 / fail-closed 默认
- [ ] 6.3 全量回归：`npm run test:acceptance` → `npm test` → `npm run typecheck`；console `typecheck` + `build`

## 7. 部署与收口

- [ ] 7.1 cloud 按安全序列部署（脏则 `git archive`；备份 → rsync → restart → healthcheck 含新列 / 新表自愈）；console build 后 rsync（不 `--delete`）
- [ ] 7.2 真机 backlog 登记：开启任一账号自动群评前，先手动 `/comment <昵称> group:on` 真机端到端发一条（确认生产链路「审=发」）
- [ ] 7.3 归档本 change（MODIFIED base 均已在 specs/，无顺序约束）
