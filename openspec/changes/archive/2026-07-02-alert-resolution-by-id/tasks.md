## 1. aidcp-cloud — 存储层与面板写路由

- [x] 1.1 `src/alerts/alert-store.ts`：`AlertStore` 接口（`resolveByEdge` 旁）新增 `resolveById(alertId: number, at?: number): Promise<number>`；`PgAlertStore` 实现——SQL 镜像 `resolveByEdge`：`UPDATE alerts SET resolved_at=(at 给定则 to_timestamp($2/1000.0) 否则 now()) WHERE alert_id=$1 AND resolved_at IS NULL`，`return rowCount ?? 0`。**不改** `ALERTS_SCHEMA_SQL`（复用 `resolved_at`，无迁移）。 <!-- aidcp-cloud 7a90701 -->
- [x] 1.2 `src/panel/types.ts`：`PanelDeps` 新增可选 `alertStore?: Pick<AlertStore, 'resolveById'>`（顶部 `import type { AlertStore } from '../alerts/index.js'`）；加注释标红线（只写 `resolved_at`、绝不碰风控单写、绝不 `resumeEdge`、诚实回真实行数、未注入即 503）。复用既有 `AlertStore` 单例，不新造 wrapper。 <!-- aidcp-cloud 7a90701 -->
- [x] 1.3 `src/panel/panel-server.ts`：JWT 保护区内、末尾 404 之前，新增 `POST /api/alerts/:id/resolve`——`decodeURIComponent` 取 id → `Number` 校验（非整数/≤0 → 400 `{error:'bad_request',reason:'invalid_id'}`）→ `deps.alertStore` 未注入 → 503 `{error:'alerts_unavailable'}` → `const resolved = await deps.alertStore.resolveById(id)` → `sendJson(200, {resolved})`。复刻 curated `DELETE` 路由的校验+诚实回行数模式；**不加** `accountId` 越权闸（单租户，见 design D5）。偏离：id 校验先于存储可用性（请求形状先判，语义更正确）。 <!-- aidcp-cloud 7a90701 -->
- [x] 1.4 `src/server.ts`：`startPanelApi` 的 deps 对象（`curatedContent` 旁）加一行 `alertStore,`——直接传 `main()` 内已构造的 `alertStore` 单例（`PgAlertStore | undefined`）。init 失败为 `undefined` → 路由自然 503，绝不崩边-云闭环。 <!-- aidcp-cloud 7a90701 -->

## 2. aidcp-console — 前端解决按钮

- [x] 2.1 `src/api/queries.ts`：新增共享 `useResolveAlert()`——`mutationFn:(id:number)=>apiPost<{resolved:number}>(\`/api/alerts/${id}/resolve\`)`；`onSuccess` 同时 `invalidateQueries(['alerts'])` 与 `(['dashboard','summary'])`（两页数据源不同 key）；按 `res.resolved===1` → `message.success('已解决')`、否则 → `message.info('该告警已解决或不存在')`；`onError` → `message.error('解决失败')`。镜像既有页内 `useMutation` + `apiPost` + antd `message` 写法。 <!-- aidcp-console 1a84054 -->
- [x] 2.2 `src/pages/MonitorPage.tsx`：告警 `List` 每个 `List.Item` 加 `actions=[<Popconfirm 二次确认后调 useResolveAlert().mutate(a.id) 的「解决」按钮>]`，`loading` 绑 `isPending && variables===a.id`（per-row）；仅加动作，不改其余只读渲染。 <!-- aidcp-console 1a84054 -->
- [x] 2.3 `src/pages/DashboardPage.tsx`：告警 `List` 每行同样加「解决」`Popconfirm` 按钮，走同一 `useResolveAlert()`（首页告警来自 summary，成功后 `invalidate ['dashboard','summary']` 刷新）。 <!-- aidcp-console 1a84054 -->

## 3. aidcp-cloud — 测试（安全红线必过）

- [x] 3.1 **AC-ALERT-1**（诚实行数）`test/alert-store.test.ts`：`resolveById` 用例——带 `at` 走 `to_timestamp`、SQL 含 `WHERE alert_id=$1 AND resolved_at IS NULL`、`params[0]=id`；fakePool `rowCount=1`（首次解决）与 `rowCount=0`（不存在/已解决）两路如实回真实数，绝不假成功。 <!-- aidcp-cloud 7a90701 -->
- [x] 3.2 **AC-ALERT-2**（路由契约）`test/panel-server.test.ts`：`POST /api/alerts/:id/resolve`——无 token→401；非整数/≤0 id→400 `invalid_id`；未注入 `alertStore`→503 `alerts_unavailable`；注入 fake 回 1→200 `{resolved:1}`、回 0→200 `{resolved:0}`（诚实透传）。 <!-- aidcp-cloud 7a90701 -->
- [x] 3.3 **AC-ALERT-3**（红线隔离，必过）：断言解决路径只经 `alertStore.resolveById`——spy `riskRegistry` 校验绝不调风控 controller（不 `applySignal`/`setQuotaLevel`/写 `risk_state`）；面板 `edgeServer` dep 结构上无 resume 能力，故无从 `resumeEdge`。 <!-- aidcp-cloud 7a90701 -->
- [x] 3.4 **AC-ALERT-4**（共存无冲突）`test/alert-store.test.ts`：断言 `resolveById` 与 `resolveByEdge` 共用同一 `resolved_at IS NULL` 守卫（fakePool 捕获 SQL 校验）——由此保证并发/重复解决靠行锁串行、后者命中 0 行、幂等诚实、不二次解决、不抛错。 <!-- aidcp-cloud 7a90701 -->
- [x] 3.5 **AC-ALERT-5**（冷却盲区固化为已知语义）`test/comm/captcha-coordinator.test.ts`：手动 by-id 解决不走 `onCleared`、不清 per-edge 冷却记录；≤ 冷却窗（10min）内同 edge 再现阻断仍被压制——固化为回归断言（活状况如实复现，非 bug）。 <!-- aidcp-cloud 7a90701 -->
- [x] 3.6 回归纪律：`npm run test:acceptance`（27 绿，AC-RISK/AC-PROTO/AC-PUB 全过）→ 全量 `npm test`（1053 绿）→ `npm run typecheck`（绿）。本改动不碰协议/发布/风控单写，无回归。 <!-- aidcp-cloud 7a90701 -->

## 4. aidcp-console — 校验

- [x] 4.1 console `npm run typecheck`（绿）+ `npm test`（vitest 5 绿/1 skip）+ `npm run build`（绿）；前端诚实文案（`resolved===0` 出「已解决或不存在」而非成功）随 console「无 per-page 组件测试」既有约定以 code-review + 手验把关。 <!-- aidcp-console 1a84054 -->

## 5. 部署（ECS，安全序列，绝不碰 isales）

- [x] 5.1 cloud 已上线（`7a90701` 生效）。**偏离说明**：并发 session 的 `role-thinking-mode-config` 与本改动共用同一份工作树 `../aidcp-cloud`，其 rsync 部署把共享工作树（含本改动 + 其 WIP）一并推上 ECS，服务于 **22:00:57** 重启到位（干净启动：`AlertStore 已就绪`、8787+8090 监听、飞书长连接已建立、PG 正常）。故本改动**非**由我走 §5 序列部署，而是随并发方部署一并生效；我**未**再次部署 cloud（避免重推其 WIP、覆盖其更新工作）。已只读验证路由存活：`POST /api/alerts/2/resolve` 无 token → 401（JWT 闸 + 路由已接线、新码在跑）。 <!-- aidcp-cloud 7a90701, 2026-07-02 deployed (via concurrent shared-tree rsync), verified live -->
- [x] 5.2 console 已部署：`npm run build`（bundle `index-ChRoxtSX.js` 含 `api/alerts/` 路由）→ ECS 先备份（`console.bak.20260702-220637.tar.gz`）→ `rsync dist/`（**无** `--delete`，保 `intro.*` 非构建文件）→ Nginx 8088 验证：`index.html` 200 且引用新 bundle、`assets/index-ChRoxtSX.js` 200。「解决」按钮已上线。 <!-- aidcp-console 1a84054, 2026-07-02 deployed -->
- [x] 5.3 上线验证已完成：运营在后台点「解决」清掉两条卡死告警——alert 3（P1 block，edge `ads-k1e0awu5`）与 alert 2（P2 pacing，`edge_id` 空，此前结构上无解）均于 **22:44** `resolved_at` 置值、掉出未解决列表；未解决计数归零（DB 核实 `count(*) WHERE resolved_at IS NULL = 0`）。经真面板 API 端到端生效，未走 raw SQL。此前另加两次前端微调并部署：告警行内容包一层 `Space` 修对齐（console `3d66568`）、「解决」去 `type=link` 改带框按钮（console `bd01105`）。 <!-- 2026-07-02 operator-verified live -->

## 6. 收尾

- [x] 6.1 `openspec validate alert-resolution-by-id --strict` 绿。
- [x] 6.2 全部 task `[x]`、附 commit-sha / 部署注记后 `archive`（delta 合并进 `openspec/specs/alert-manual-resolution/`）。
