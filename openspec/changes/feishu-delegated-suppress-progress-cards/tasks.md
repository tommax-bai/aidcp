# Tasks

## 1. aidcp-cloud — 委托层不发进度卡、结果归属下沉

- [x] 1.1 新增 `delegatedPublishOutcomeReceipt` 纯函数（发帖 failed/有缺口 partially → 结果卡；发帖 completed/waiting_approval / 评论 / 候选管理 → null）+ 单测 <!-- aidcp-cloud f654850 -->
- [x] 1.2 worker `onTaskUpdated`：从推送进度卡改为只兜「发帖类终态失败」结果卡；评论 / 发帖成功 / 等待人审均不发 <!-- aidcp-cloud f654850 -->
- [x] 1.3 `CommandResult.silent` + ws-receiver 静默受理（不发卡，只留已读表情）+ auto-queue 回执改静默 <!-- aidcp-cloud f654850 -->
- [x] 1.4 回归：`npm run typecheck` + `npm run test:acceptance`（AC-PUB / AC-RISK 绿）+ 全量 `npm test`（2256 pass）全绿 <!-- aidcp-cloud f654850 -->

## 2. aidcp（中控）— spec delta

- [x] 2.1 `user-delegated-tasks` 通知需求 RENAMED + MODIFIED（委托层不发进度卡、结果归属下沉、发帖失败兜底、静默受理）
- [x] 2.2 `openspec validate feishu-delegated-suppress-progress-cards --strict` 通过

## 3. 部署

- [x] 3.1 部署 cloud `dev` 并 healthcheck（active / NRestarts=0 / 8787 / 8090 / PG / 飞书长连接均绿；backup `cloud.bak.20260715-212946.tar.gz`；dev 已在 f5b6fc9，本次仅 5 文件增量）<!-- aidcp-cloud f654850 2026-07-15 deployed dev -->
