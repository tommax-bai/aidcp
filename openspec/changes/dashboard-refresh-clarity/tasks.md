# Tasks — dashboard-refresh-clarity（看板可读性，worklist item 1 = A 流）

> **并发协调（5 流并行，本流 = A「看板」）：**
> - **本流不需要数据库迁移**（A 无 schema 改动）。预留迁移号台账（勿占用）：C(role-model-category-config)=0009、D(safety-quota-config)=0010、F(account-persona-config)=0011、B(account-real-nickname)=0012。
> - **共享拥塞文件按保留顺序追加（C→D→F→B），本流 A 不在该顺序内**：`cloud src/panel/panel-server.ts` 路由链、`src/panel/types.ts`、`console src/types/api.ts`、`src/api/queries.ts`。本流对这些文件**只做最小、就地、与他流不冲突的局部改动**（总览 DTO 的 `asOf`、总览路由响应、总览查询块），不重排路由链、不动其他流的 store-init / 依赖接线。
> - **`cloud src/server.ts`**：C 流独占 model-resolver 块（`resolveModelForRole`/`resolveTempForRole` + 共享 LLM 客户端接线）且先落地。**本流 A 不碰 `server.ts`**。
> - **PROTOCOL v2 红线**：B 流独占两份 `protocol.ts` + `command-bridge.ts` + `docs/protocol.md`（及 `edge-client.ts` onMessage 白名单）。**本流 A 不碰任何协议文件**——本 change 纯属面板 API + 前端，无边-云协议改动。
> - **`console src/api/queries.ts` 是跨流共享文件**：本流**只调既有 `useDashboardSummary` 块**（约第 42 行起的轮询参数），**不新增任何 hook**，避免与他流冲突。
> - **红线**：诚实呈现——「无新数据」如实标为无活动 / 边缘离线；**绝不碰** `aidcp-edge`/`aidcp-cloud` 的 `handler.ts` 互动 allow-list（不把 `view` 加进采集口径，那是高频 + 风控红线路径的单独决策）。

## 1. aidcp-cloud — 总览接口暴露数据新鲜度

- [x] 1.1 `src/panel/types.ts`：总览 DTO（`DashboardSummary`）确认含服务端生成的 `asOf: number`（数据新鲜度时间戳）字段；缺则就地新增，**不重排其他字段**。 <!-- aidcp-cloud 88a1b91 原 DTO 不存在（响应为路由内联对象），按「缺则就地新增」补 DashboardSummary interface（asOf/edgesOnline/totals/…），未重排他流字段 -->
- [x] 1.2 `src/panel/panel-server.ts` `GET /api/dashboard/summary` 路由：响应体确认带 `asOf`（取该次查询的服务器当前时刻，如 `Date.now()`）与如实的 `edgesOnline`（`onlineEdgeCount()`，死连接不计）；**沿用既有索引查询，MUST NOT 引入全表扫描 / 重聚合**；不重排路由链、不动他流接线。 <!-- aidcp-cloud 88a1b91 asOf/edgesOnline 在 master 已存在（panel MVP 即带）；本流将响应体收口为 DashboardSummary 类型使契约有编译期保证；沿用既有查询、零新查询 -->
- [x] 1.3 确认未触碰任何 `handler.ts` 互动 allow-list、未触碰 `protocol.ts`/`command-bridge.ts`/`server.ts`。 <!-- aidcp-cloud 88a1b91 diff 仅 panel/types.ts + panel-server.ts + test/panel-server.test.ts；未触 handler.ts/protocol.ts/command-bridge.ts/server.ts -->

## 2. aidcp-console — 总览页呈现新鲜度与边缘在线状态

- [x] 2.1 `src/types/api.ts`：`DashboardSummary` 镜像 `asOf: number` 字段（与 cloud DTO 一致）；缺则就地新增，**不动他流字段**。 <!-- aidcp-console 零改动：src/types/api.ts 的 DashboardSummary 在 master 已含 asOf:number，与 cloud DTO 一致，未动共享文件 -->
- [x] 2.2 `src/api/queries.ts`：**仅**在既有 `useDashboardSummary` 块内调轮询参数——可下调 `refetchInterval`（如 15s→10s）并按需加 `refetchOnWindowFocus: true` 覆盖（覆盖 `main.tsx` 的全局 `false`）；**MUST NOT 新增任何 hook**、不动其他查询块。 <!-- aidcp-console d65d093 仅 useDashboardSummary 块：refetchInterval 15s→10s + refetchOnWindowFocus:true（块级覆盖），零新 hook -->
- [x] 2.3 `src/pages/DashboardPage.tsx`：呈现「数据截至 `{asOf 格式化}` / 自动刷新中」新鲜度标识（每轮刷新后 `asOf` 推进 → 证明界面在更新）。 <!-- aidcp-console d65d093 健康行 Card 增「数据截至 {本地化时间} + 自动刷新中 Tag」，data 就绪时渲染 -->
- [x] 2.4 `src/pages/DashboardPage.tsx`：当 `edgesOnline === 0` 时呈现「系统当前未在浏览，故无新数据」一类提示，把「无新计数」如实归因为无边缘在浏览；**诚实呈现，绝不伪造活跃感**。 <!-- aidcp-console d65d093 edgesOnline===0 → info Alert 归因提示；有边缘在线时不渲染（测试断言缺席） -->
- [x] 2.5（可选）`src/main.tsx`：若 2.2 选择全局聚焦刷新策略而非块级覆盖，再在此处调整；否则不动。 <!-- 按设计不做：2.2 采用块级覆盖，main.tsx 不动（任务自身约定此情形不动） -->

## 3. 验证

- [x] 3.1 cloud：`npm run typecheck` 绿；定向确认 `GET /api/dashboard/summary` 响应含 `asOf` 且为服务端时刻、`edgesOnline` 来自活态登记。 <!-- aidcp-cloud 88a1b91 typecheck 绿；test/panel-server.test.ts 新增断言 asOf 为服务端时刻（落在请求前后时间窗）；rebase 后全量 1121 绿 + acceptance 27 绿 -->
- [x] 3.2 console：`npm run build`/`typecheck` 绿；本地或预览确认总览页显示新鲜度标识、`edgesOnline=0` 时显示无活动提示、轮询后 `asOf` 推进。 <!-- aidcp-console d65d093 build/typecheck 绿；新增 DashboardPage.test.tsx（3 测试：新鲜度渲染/零边缘提示/有边缘时缺席）。真浏览器「轮询 asOf 推进」= 真机项 → docs/real-machine-acceptance-backlog.md 簇5 -->
- [x] 3.3 回归：未引入新协议（无 AC-PROTO 影响）、未改互动采集口径、总览接口无全表扫描。 <!-- 零协议改动（AC-PROTO 全过）、未改互动采集口径、无新查询/全表扫描 -->

## 4. 收尾与归档

- [x] 4.1 按 sub-repo 分节回写本 tasks.md 进度（commit-sha + 偏离说明）。 <!-- 2026-07-03 本次回写；实装经 fleet agent 于隔离 worktree 完成、scripts/land-change 串行集成（rebase→全量绿→ff push） -->
- [x] 4.2 `openspec validate dashboard-refresh-clarity --strict` 通过。 <!-- 2026-07-03 valid -->
- [ ] 4.3 cloud 改动（若有）按 §5 安全序列部署 ECS；console 静态产物按 console 发布流上线。
- [ ] 4.4 上线后让运营核对：看板能一眼区分「无新活动」与「界面冻结」（新鲜度标识推进 + 无边缘在线提示）。
- [ ] 4.5 `/opsx:archive` 归档（delta 合并进 `openspec/specs/console-panel-api`）。
