## Why

用户反馈「管理后台数据看板，数据没有在更新」。ECS 诊断厘清了真相：

- **看板前端是健康的**：`useDashboardSummary` 每 15s 轮询、每次读实时 PG、无缓存层；`GET /api/dashboard/summary` 每请求都是新查询。
- **问题在上游没有新数据**：`risk_counters` 全表历史仅约 8 行、且全部是 2026-06-19；06-20/21/22 三天为空。今天有边缘 17:18 连上、17:20 只滚动一次、17:22 因 idle 240s 被看门狗结束会话——**零互动产生**，自然没有新计数可显示。
- 另外「浏览量」tile 与「点赞率」分母**结构性恒为 0**：`view` 从不进 `interaction.occurred` allow-list（`handler.ts`），所以这两格永远空。

当前 UI **不暴露「数据截至几点」、也不暴露「是否有边缘在线」**，导致「当前无新活动」被运营误读成「看板坏了 / 界面卡住」。本 change 只做**前端可读性**：让运营一眼看出数据是实时拉取的、只是当前没有新活动，而非界面冻结。

## What Changes

- **cloud（面板 API）**：`GET /api/dashboard/summary` 响应附一个服务端生成的 `asOf` 时间戳，供 console 渲染「数据截至 …」。
- **console**：看板页显示「最后更新时间 + 自动刷新中」徽标；当在线边缘数为 0 时显示「系统当前未在浏览，故无新数据」提示；为看板查询降低 `refetchInterval` 或加 `refetchOnWindowFocus` 覆盖（只调既有 `useDashboardSummary` 块，不新增 hook）。

**明确不做（OUT OF SCOPE）**：

- 把 `view` 加进互动 allow-list（高频、且走 `RiskController.record` / `canDo` 风控红线路径，需单独决策）。
- 修「浏览闭环为何这几天几乎不产生互动」——那是运行态排查，属另一条独立工作，不在本前端可读性 change 内。

## Capabilities

### New Capabilities
<!-- 无新增 capability -->

### Modified Capabilities
- `console-panel-api`：新增一条要求——总览接口暴露数据新鲜度（`asOf`），后台据此呈现「数据截至」与边缘在线状态，使「无新活动」与「界面冻结」可被运营区分。

## Impact

- **cloud（aidcp-cloud）**：`src/panel/panel-server.ts`（`/api/dashboard/summary` 增 `asOf`）；`src/panel/types.ts`（总览 DTO 增 `asOf` 字段）。
- **console（aidcp-console）**：`src/pages/DashboardPage.tsx`（新鲜度徽标 + 边缘在线/无活动提示）；`src/api/queries.ts`（**仅**调 `useDashboardSummary` 既有块的轮询参数）；`src/types/api.ts`（镜像 `asOf` 字段）；可选 `src/main.tsx`（聚焦刷新策略）。
- **协调（写进 tasks）**：`queries.ts` 是跨流共享文件——本流只调既有 `useDashboardSummary` 块、不新增 hook，避免与其它流冲突；**绝不碰** `handler.ts` 的 `view` allow-list。
- **红线**：诚实呈现——「无新数据」如实标示为无活动 / 边缘离线，绝不伪造活跃感。
