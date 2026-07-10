# Tasks — pacing-fallback-hardening

> 协议改动：热点文件（两份 `protocol.ts`、cloud `command-bridge.ts` 动作映射、`role-dispatcher.ts` `EdgeCommand.action` 并集）单写者串行。集成时发现并发 change `feed-refresh-on-depth` 已先落地 master（其 tasks.md 勾选滞后于代码），故无实时撞车——本 change 在其之上 +1 消息类型（71→72）。
> 回归纪律：两仓 `npm run test:acceptance`（`AC-PROTO-*` 不漂移）→ 全量 `npm test` → `npm run typecheck` 全绿；两份 `protocol.ts` 逐字一致。

<!-- cloud 7381c3f / edge 10f5f9b landed master；cloud 2026-07-10 deployed dev -->

## 1. 协议消息类型（四处同步之一：两端 protocol.ts 逐字一致）

- [x] 1.1 aidcp-cloud `src/comm/protocol.ts`：`MessageType` 加 `| 'pacing.update'` <!-- cloud 7381c3f -->
- [x] 1.2 aidcp-cloud `src/comm/protocol.ts`：加 `PacingUpdatePayload { tempo: number }`（就近 `PacingSnapshotPayload`） <!-- cloud 7381c3f -->
- [x] 1.3 aidcp-cloud `src/comm/protocol.ts`：`PayloadMap` 加 `'pacing.update': PacingUpdatePayload;` <!-- cloud 7381c3f -->
- [x] 1.4 aidcp-cloud `src/comm/protocol.ts`：移除 `PacingDefaultsPayload` + `SessionBudgetPayload.pacing?`（保留说明注释） <!-- cloud 7381c3f -->
- [x] 1.5 aidcp-edge `src/comm/protocol.ts`：与 1.1–1.4 逐字一致镜像 <!-- edge 10f5f9b -->
- [x] 1.6 两仓 `npm run typecheck` 通过、两份 protocol.ts 不漂移（`diff` 仅剩预存无关差异） <!-- 两仓 typecheck 绿 -->

## 2. aidcp-cloud — 中途档位推送 + 清死代码

- [x] 2.1 `role-dispatcher.ts`：`EdgeCommand.action` 加 `'pacing_update'` <!-- cloud 7381c3f -->
- [x] 2.2 `command-bridge.ts`：`case 'pacing_update' → createEnvelope('pacing.update', ...)` <!-- cloud 7381c3f -->
- [x] 2.3 `role-dispatcher.ts`：import `tempoForStatus`；`lastPushedTempo` 构造期基线（try/catch 回落 1.0） <!-- cloud 7381c3f -->
- [x] 2.4 `role-dispatcher.ts` `sendCommand` 顶端 `maybePushTempo()`：tempo 变化经 `rawSendCommand` 直发 `pacing_update`、去抖、不递归、不占配额/不过软暂停闸 <!-- cloud 7381c3f -->
- [x] 2.5 `handler.ts`：`onSessionBudgetRequest` 去 `pacing` 字段 + 去 import <!-- cloud 7381c3f -->
- [x] 2.6 `risk/pacing.ts`：删 `buildPacingDefaults` + `PacingDefaults`（`DWELL_FLOOR_MS`/`tempoForStatus` 保留） <!-- cloud 7381c3f -->
- [x] 2.7 `risk/index.ts`：经 `export * from './pacing.js'` 自动去导出（无需单独改） <!-- cloud 7381c3f -->

## 3. aidcp-edge — 白名单 / 应用 / 停留兜底叠 tempo（含红队修）

- [x] 3.1 `edge-client.ts`：`onMessage` 白名单加 `pacing.update` 放行到 `browseHandler`（防静默丢弃） <!-- edge 10f5f9b -->
- [x] 3.2 `browse-session.ts` `onCloudCommand` **顶端**直接应用 `pacing.update` 并返回——绝不入队/唤醒/复活已停会话（红队 Finding 1 自残红线）；`isWakeCommand` 亦排除；`main.ts` 令其穿透任务租约闸（红队 Finding 2） <!-- edge 10f5f9b -->
- [x] 3.3 `browse-session.ts`：`applyTempoUpdate(tempo)` 只更 `this.tempo`、不动 `lastActionEndAt`；加 `MAX_TEMPO` 上限防呆（红队 Finding 3） <!-- edge 10f5f9b -->
- [x] 3.4 `browse-session.ts` `ensureDetailDwell`：缺 `dwellMs` 采样兜底 × `this.tempo`（云端已下发 `dwellMs` 不叠、防 double-count） <!-- edge 10f5f9b -->
- [x] 3.5 移除对 `PacingDefaultsPayload` 的引用；`DEFAULT_DWELL_FLOOR_MS` 注释去 `buildPacingDefaults` 提法 <!-- edge 10f5f9b -->

## 4. aidcp（本仓）— 协议文档（四处同步之四）

- [x] 4.1 `docs/protocol.md`：消息类型计数由过期 61 校正为真值 72（含 feed.refresh + pacing.update），注明以两端 protocol.ts 为准 <!-- 本仓 docs -->
- [x] 4.2 `docs/protocol.md` §2 表新增 `feed.refresh` + `pacing.update` 行 <!-- 本仓 docs -->

## 5. 测试（克制：关键行为少数用例）

- [x] 5.1 cloud dispatcher（`test/integration/pacing-tempo-push.test.ts`）：normal 不推；升 warned 推 `pacing_update{1.3}` 先于实际命令；同档去抖；command-bridge 产出 `pacing.update` 带 tempo <!-- cloud 7381c3f -->
- [x] 5.2 cloud `handler-pacing.test.ts`：`session.budget` 回执无 `pacing`、其余字段不变 <!-- cloud 7381c3f -->
- [x] 5.3 cloud `protocol-contract.test.ts`：`ALL_MESSAGE_TYPES` 加 `pacing.update`、`AC-PROTO` 计数 72、round-trip <!-- cloud 7381c3f -->
- [x] 5.4 edge `pacing-min-interval.test.ts`：升档放大最小间隔且不重置锚点；兜底停留随 tempo 放大 / 给定 dwellMs 不放大；停机不复活仍应用；越界 tempo 忽略 <!-- edge 10f5f9b -->
- [x] 5.5 edge `edge-client.test.ts`：`pacing.update` 路由到 `browseHandler`（防静默丢弃） <!-- edge 10f5f9b -->
- [x] 5.6 两仓 `test:acceptance` → 全量 `test`（cloud 1746 / edge 877）→ `typecheck` 全绿；两份 protocol.ts 一致 <!-- 两仓全绿 -->

## 6. 集成 / 部署 / 真机验收

- [x] 6.1 两仓 land（fetch+rebase master、跑闸）→ ff push master（cloud 7381c3f / edge 10f5f9b） <!-- land-change --yes -->
- [x] 6.2 本仓 docs（4.x）+ openspec change 提交、push（additive，走 main 临时 worktree） <!-- 见 archive 提交 -->
- [x] 6.3 部署 dev（备份 cloud.bak.20260710-181314 + .env.bak → rsync 快照 → restart → healthcheck 全过：active/8787/8090/飞书长连接/pacing.update live/无错） <!-- 2026-07-10 deployed dev；edge 客户端无 ECS 部署 -->
- [x] 6.4 真机验收项登记 `docs/real-machine-acceptance-backlog.md`（升档 latent、难触发，记待核） <!-- 见 backlog 簇 -->
- [x] 6.5 tasks.md 勾选回写 + validate --strict → archive <!-- 本次 -->
