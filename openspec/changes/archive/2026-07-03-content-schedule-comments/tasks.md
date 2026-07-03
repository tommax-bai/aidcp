> 范围：Phase 2，只加定时自动评论。群评排期不做（Phase 3 前置未满足）；有界翻页归独立变更 `comment-bounded-pagination`。
> 归档顺序：先 `content-schedule-auto-publish` 后本变更（MODIFIED delta 以其 spec 为 base）。

## 1. aidcp-cloud — 数据层与计数

- [x] 1.1 `account_content_schedule` 自愈加列 `comment_enabled BOOLEAN NOT NULL DEFAULT false` / `comment_daily_cap INTEGER NOT NULL DEFAULT 0`（`ADD COLUMN IF NOT EXISTS`，store `init()` 跑） <!-- aidcp-cloud 88009ea（master） -->
- [x] 1.2 `ContentScheduleStore`：patch 校验（布尔 / 0..50 整数、非法整块拒）、行 DTO、`effectiveScheduleFor` 扩两字段；未传保持原值、未配 fail-closed <!-- 88009ea -->
- [x] 1.3 `pg-risk-store` 加 `countInteractionsTodayForAccount(accountId, action)`（interactions 表按账号 + 服务器本地日历日 count；镜像 publish 侧 countPublishedTodayForAccount 语义） <!-- 88009ea -->
- [x] 1.4 人审文档 `migrations/0029_content_schedule_comments.sql`（两列 DDL，与 store 自愈 SQL 同源） <!-- 88009ea migrations/0029 -->

## 2. aidcp-cloud — 调度器动作循环

- [x] 2.1 tick 扩为动作循环 `['post','comment']`：各动作独立 enabled / cap / 错峰分钟判定；**幂等键升维为 `accountId|action` → 小时格**（发帖触发不吞评论槽）
- [x] 2.2 同账号每 tick 至多一动作（fire 后 break 动作循环；post 在前——纯云端、不接管边端） <!-- 88009ea -->
- [x] 2.3 评论动作闸：`isCommentBusy(accountId)` 单飞 + 日上限 =（今日已发 + 在跑?1:0）>= cap 跳过；发帖闸（全局串行 / postFiring / pending 台账）保持不变、不套在评论上 <!-- 88009ea；评论 cap 的「在跑?1:0」在单飞闸后恒 0，等价成立 -->
- [x] 2.4 deps 扩：`triggerComment(accountId)` / `isCommentBusy(accountId)` / `commentedTodayCount(accountId)`；`triggerPost` 语义不变 <!-- 88009ea；三件套为可选 deps，未注入=评论动作整体跳过 -->

## 3. aidcp-cloud — server 接线

- [x] 3.1 `triggerComment` 实现：先 `canDo('comment')`（拒 → 黄卡「配额拒绝、本槽未触发」）；过则 `commentScheduler.triggerManual(accountId)`；触发回执非 ok（离线 / 未绑人设 / 在跑）回黄卡如实说明；**任务终态结果卡由评论链自补，包装层不重复发** <!-- 88009ea -->
- [x] 3.2 deps 注入：`isCommentBusy` = `commentScheduler.isRunning`、`commentedTodayCount` = `riskStore.countInteractionsTodayForAccount(id,'comment')`；`commentScheduler` 未建（PG 缺）时评论动作诚实跳过并 log <!-- 88009ea：条件注入三件套（不注入=跳过）；log 由调度器 deps 缺省路径隐含 -->

## 4. aidcp-cloud — 面板 API

- [x] 4.1 `panel/types.ts` PanelContentSchedule patch / DTO 加 `commentEnabled` / `commentDailyCap`；`panel-server.ts` PUT 校验两字段（布尔 / number，语义校验在 store 整块拒） <!-- 88009ea；patch 类型经 store import 自动扩 -->

## 5. aidcp-console — 排期页

- [x] 5.1 账号表加「自动评论」开关 + 日上限两列（复用发帖列交互范式：Switch + InputNumber onBlur 提交、总开关 disabled 联动） <!-- aidcp-console (branch content-schedule-comments) 7cd5cd4 待 land；cap 草稿 key 泛化为 账号×动作 -->
- [x] 5.2 `types/api.ts` 镜像两字段；页面提示与列文案诚实：「该时段尝试自动评论：自行搜索目标、可能 0 产出、每条需飞书人审」+ 自动路径过配额说明 <!-- 7cd5cd4 待 land；typecheck+build 绿 -->

## 6. 测试与回归

- [x] 6.1 调度器单测：动作循环 / 每动作幂等互不吞 / 同 tick 至多一动作 / 评论单飞 / 评论日上限原子（已发 + 在跑）/ 发帖闸不套评论 <!-- 88009ea test/content-scheduler.test.ts 18/18 -->
- [x] 6.2 store 单测：两新列校验（非法整块拒 / 部分补丁保持原值 / fail-closed 默认） <!-- 88009ea test/content-schedule-store.test.ts 8/8 -->
- [x] 6.3 `countInteractionsTodayForAccount` 单测（pool 桩：按账号 + 当日过滤、action 过滤） <!-- 88009ea test/risk/count-interactions-today.test.ts 2/2 -->
- [x] 6.4 全量回归：`npm run test:acceptance` → `npm test` → `npm run typecheck`（AC-* 全过）；console `typecheck` + `build` <!-- 2026-07-03 land 树：cloud 全量 1150/1150 + acceptance 绿 + typecheck 干净；console typecheck+build 绿 -->

## 7. 部署（按需、安全序列）

- [x] 7.1 cloud：工作树若被并发方弄脏则 `git archive` 干净树部署；备份 → rsync（exclude .env/node_modules/.git）→ restart → healthcheck（active + 8787/8090 + 飞书长连 + PG + 新列自愈补上） <!-- 2026-07-03 deployed：主 checkout 干净直发（88009ea）；备份 cloud.bak.20260703-163123.tar.gz；ECS 近 1h 无并发部署；comment_enabled/comment_daily_cap 已自愈 -->
- [x] 7.2 console：build 后 rsync dist（**不 `--delete`**）
- [x] 7.3 验证：排期页评论列读写诚实；`AIDCP_CONTENT_SCHEDULE_AUTO` 已开、评论是否自动完全由每账号开关（默认关）决定——运营配置即生效，无需再动 env <!-- 2026-07-03：调度器已在跑（Phase 1 开闸）、评论动作随每账号开关生效；页面读写经部署后端点可用 -->
