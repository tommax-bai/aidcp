# Tasks

## 1. aidcp-cloud — 精确旧命令直接排队

- [x] 1.1 `DelegatedTaskService.createFromText`：`source==='legacy_command'` 时自动确认入队（`awaiting_confirmation → queued`），返回 `autoQueued`；自然语言仍返回 `autoQueued=false`、停在 `awaiting_confirmation` <!-- aidcp-cloud 821ecef -->
- [x] 1.2 server `delegate` 出口：`autoQueued` → 「已直接排队」任务进度卡；否则维持结构化确认卡 <!-- aidcp-cloud 821ecef -->
- [x] 1.3 单测：`/publish`、`/comment` 直接 `queued` + `approvalMode='review'` 不变；自然语言仍 `awaiting_confirmation` <!-- aidcp-cloud 821ecef -->
- [x] 1.4 回归：`npm run typecheck` + `npm run test:acceptance`（含 AC-PUB / AC-RISK）+ 全量 `npm test`（2225 pass）全绿 <!-- aidcp-cloud 821ecef -->

## 2. aidcp（中控）— spec delta

- [x] 2.1 `feishu-command-ingestion` 需求改名 + MODIFIED（写命令直接排队、自然语言仍先确认）
- [x] 2.2 `openspec validate feishu-legacy-write-direct-queue --strict` 通过

## 3. 部署

- [x] 3.1 部署 cloud `dev` 并 healthcheck（active / 8787 / 8090 / PG / 飞书长连接均绿；backup `cloud.bak.20260715-204854.tar.gz`）<!-- aidcp-cloud 821ecef 2026-07-15 deployed dev -->
