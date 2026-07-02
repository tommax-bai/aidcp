## 1. aidcp-cloud — 存储层与面板写路由

- [ ] 1.1 `src/alerts/alert-store.ts`：`AlertStore` 接口（`resolveByEdge` 旁）新增 `resolveById(alertId: number, at?: number): Promise<number>`；`PgAlertStore` 实现——SQL 镜像 `resolveByEdge`：`UPDATE alerts SET resolved_at=(at 给定则 to_timestamp($2/1000.0) 否则 now()) WHERE alert_id=$1 AND resolved_at IS NULL`，`return rowCount ?? 0`。**不改** `ALERTS_SCHEMA_SQL`（复用 `resolved_at`，无迁移）。
- [ ] 1.2 `src/panel/types.ts`：`PanelDeps` 新增可选 `alertStore?: Pick<AlertStore, 'resolveById'>`（顶部 `import type { AlertStore } from '../alerts/index.js'`）；加注释标红线（只写 `resolved_at`、绝不碰风控单写、绝不 `resumeEdge`、诚实回真实行数、未注入即 503）。复用既有 `AlertStore` 单例，不新造 wrapper。
- [ ] 1.3 `src/panel/panel-server.ts`：JWT 保护区内、curated 写块之后、末尾 404 之前，新增 `POST /api/alerts/:id/resolve`——`decodeURIComponent` 取 id → `Number` 校验（非整数/≤0 → 400 `{error:'bad_request',reason:'invalid_id'}`）→ `deps.alertStore` 未注入 → 503 `{error:'alerts_unavailable'}` → `const resolved = await deps.alertStore.resolveById(id)` → `sendJson(200, {resolved})`。复刻 curated `DELETE` 路由的校验+诚实回行数模式；**不加** `accountId` 越权闸（单租户，见 design D5）。
- [ ] 1.4 `src/server.ts`：`startPanelApi` 的 deps 对象（`curatedContent` 旁）加一行 `alertStore,`——直接传 `main()` 内已构造的 `alertStore` 单例（`PgAlertStore | undefined`）。init 失败为 `undefined` → 路由自然 503，绝不崩边-云闭环。（靠搜索定位，勿硬编码行号。）

## 2. aidcp-console — 前端解决按钮

- [ ] 2.1 `src/api/queries.ts`：新增共享 `useResolveAlert()`——`mutationFn:(id:number)=>apiPost<{resolved:number}>(\`/api/alerts/${id}/resolve\`)`；`onSuccess` 同时 `invalidateQueries(['alerts'])` 与 `(['dashboard','summary'])`（两页数据源不同 key）；按 `res.resolved===1` → `message.success('已解决')`、否则 → `message.info('该告警已解决或不存在')`；`onError` → `message.error('解决失败')`。镜像既有页内 `useMutation` + `apiPost` + antd `message` 写法。
- [ ] 2.2 `src/pages/MonitorPage.tsx`：告警 `List` 每个 `List.Item` 加 `actions=[<Popconfirm 二次确认后调 useResolveAlert().mutate(a.id) 的「解决」按钮>]`，`loading` 绑 `mutation.isPending`；仅加动作，不改其余只读渲染。
- [ ] 2.3 `src/pages/DashboardPage.tsx`：告警 `List` 每行同样加「解决」`Popconfirm` 按钮，走同一 `useResolveAlert()`（首页告警来自 summary，成功后 `invalidate ['dashboard','summary']` 刷新）。

## 3. aidcp-cloud — 测试（安全红线必过）

- [ ] 3.1 **AC-ALERT-1**（诚实行数）`test/alert-store.test.ts`：`resolveById` 用例——带 `at` 走 `to_timestamp`、SQL 含 `WHERE alert_id=$1 AND resolved_at IS NULL`、`params[0]=id`；fakePool `rowCount=1`（首次解决）与 `rowCount=0`（不存在/已解决）两路如实回真实数，绝不假成功。
- [ ] 3.2 **AC-ALERT-2**（路由契约）`test/panel-server.test.ts`：`POST /api/alerts/:id/resolve`——无 token→401；非整数/≤0 id→400 `invalid_id`；未注入 `alertStore`→503 `alerts_unavailable`；注入 fake 回 1→200 `{resolved:1}`、回 0→200 `{resolved:0}`（诚实透传）。
- [ ] 3.3 **AC-ALERT-3**（红线隔离，必过）：断言解决路径只 `UPDATE alerts.resolved_at`——以 spy/mock 校验绝不调 `applySignal` / `setQuotaLevel`、绝不写 `risk_state`、绝不调 `pusher.resumeEdge`（手动勾销绝不解除仍卡验证码后的 edge 暂停）。
- [ ] 3.4 **AC-ALERT-4**（共存无冲突）`test/alert-store.test.ts`：断言 `resolveById` 与 `resolveByEdge` 共用同一 `resolved_at IS NULL` 守卫（fakePool 捕获 SQL 校验）——由此保证并发/重复解决靠行锁串行、后者命中 0 行、幂等诚实、不二次解决、不抛错。
- [ ] 3.5 **AC-ALERT-5**（冷却盲区固化为已知语义）验证码协调器测：手动 by-id 解决不走 `onCleared`、不清 per-edge 冷却记录；≤ 冷却窗（约 10min）内同 edge 再现阻断仍被压制——把此行为固化为回归断言（活状况如实复现，非 bug）。
- [ ] 3.6 回归纪律：cloud 改动后先 `npm run test:acceptance` 再全量 `npm test` 再 `npm run typecheck`；`AC-RISK-*` / `AC-PROTO-*` / `AC-PUB-*` 必须全绿（本改动不碰协议/发布/风控单写，应无回归）。

## 4. aidcp-console — 校验

- [ ] 4.1 console `npm run typecheck` + `npm test`（vitest）绿；前端诚实文案（`resolved===0` 出「已解决或不存在」而非成功）随 console「无 per-page 组件测试」既有约定以 code-review + 手验把关。

## 5. 部署（ECS，安全序列，绝不碰 isales）

- [ ] 5.1 cloud 按 §5 安全序列部署 ECS：sub-repo 测试通过 → ECS 先备份（`cloud.bak.<ts>.tar.gz` + `.env.bak.<date>`）→ `rsync`（`--exclude .env --exclude node_modules --exclude .git`）→ `systemctl restart aidcp-cloud.service` → healthcheck（`active (running)` + 8787 监听 + 飞书长连接 + PG `select 1`）→ 失败即回滚。
- [ ] 5.2 console build → 发到 `/opt/aidcp/console`（`rsync` **绝不** `--delete`），Nginx 8088 serve + 反代 `/api`；执行前先做 §0 私钥 + sub-repo 检查。
- [ ] 5.3 上线验证：运营在监控页/首页对线上两条卡死告警点「解决」——block（edge `ads-k1e0awu5`）与 pacing（`edge_id` 空），确认二者掉出「未解决」列表、计数归位。

## 6. 收尾

- [ ] 6.1 `openspec validate alert-resolution-by-id --strict` 绿。
- [ ] 6.2 全部 task `[x]`、附 commit-sha / 部署注记后 `archive`（delta 合并进 `openspec/specs/alert-manual-resolution/`）。
