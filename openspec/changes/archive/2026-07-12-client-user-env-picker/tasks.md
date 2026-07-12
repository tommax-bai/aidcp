# Tasks: client-user-env-picker

## 1. aidcp-cloud — 管理侧全局环境注册表

- [x] 1.1 `src/client-auth/client-user-store.ts`：新增导出类型 `ClientEnvAssignee { userId; name }` 与 `ClientEnvironmentView { envKey; label; platform; assignees: ClientEnvAssignee[]; assigneeCount }`。 <!-- aidcp-cloud 05bd239 -->
- [x] 1.2 同文件新增管理侧读法 `listAllEnvironments(): Promise<ClientEnvironmentView[]>`：GROUP BY env_key 聚合 distinct env_key、join `client_users` 得客户名、label/platform 取任一非空代表值（`array_agg … ORDER BY assigned_at DESC FILTER (WHERE … IS NOT NULL)`）；缺表（42P01）fail-closed 回落空数组。方法注释写死红线：仅供内部 panel 端点，绝不接客户鉴权服务（守 N2）。 <!-- aidcp-cloud 05bd239 -->
- [x] 1.3 `src/panel/panel-server.ts`：新增 `GET /api/client-environments`（受内部 JWT，位置紧邻 `/api/client-users` 块）→ `{ environments }`；未注入 `deps.clientUsers` → 503。 <!-- aidcp-cloud 05bd239 -->
- [x] 1.4 新增 `test/client-user-store.test.ts`：`listAllEnvironments` 映射（assigneeCount = assignees 长度 / null 回落空 / 缺表 fail-closed / 非缺表错误照抛）。真 SQL 聚合 + 多分「只动当前 user」= 真机核（见 3.3）。N2 隔离由现有 `client-auth-server.test.ts` 结构性保证（假 store 不实现该方法、client-auth-server 只调 scoped 方法）。 <!-- aidcp-cloud 05bd239 4 用例绿 -->
- [x] 1.5 `npm run typecheck` + `npm test`（1866 绿，+4）+ `test:acceptance`（47 绿，AC-* 全过、N2 不回归）。 <!-- aidcp-cloud 05bd239 -->

## 2. aidcp-console — 端用户改名 + 环境选择列表

- [x] 2.1 `src/types/api.ts`：新增 `ClientEnvAssignee` 与 `ClientEnvironmentView`（镜像 cloud）。 <!-- aidcp-console 6a6fe92 -->
- [x] 2.2 `src/api/queries.ts`：新增 `useClientEnvironments(enabled)`（GET /api/client-environments），query key `['client-environments']`；`useSetClientUserScope` 成功后一并失效之。 <!-- aidcp-console 6a6fe92 -->
- [x] 2.3 `src/pages/ClientUsersPage.tsx` 环境归属抽屉重做：段控筛选「待分配 / 已分配」（默认待分配，相对当前端用户）+ 勾选加入（rowSelection 多选，`effectiveSelected` 对账）+ 「多人」Tag（assigneeCount≥2，Tooltip 列客户名）+ 保留手填兜底；保存走整批替换。**评审修 critical**：rows 改由 `scope.data` 单一 effect 驱动（原第二个 reset effect 也 setRows → 暖缓存重开同客户时竞态清空草稿 → 保存静默清空归属）。 <!-- aidcp-console 6a6fe92 -->
- [x] 2.4 改名「客户端用户」→「端用户」：`src/routes.tsx` navLabel + Card 标题 + QueryError 文案 + 空态文案（路由路径 / 组件名 / 接口不动）。 <!-- aidcp-console 6a6fe92 -->
- [x] 2.5 `src/pages/ClientUsersPage.test.tsx`：`assigneeCell` 多人/单客户/空 三分支用例（纯渲染不 flaky）；抽屉交互（勾选加入 / 筛选）portal 重、归真机。 <!-- aidcp-console 6a6fe92 10 用例绿 -->
- [x] 2.6 `npm run typecheck` + `npx vitest run`（101 绿 +1 skip）+ `npm run build`（OK）。 <!-- aidcp-console 6a6fe92 -->

## 3. 集成 / 部署 / 收尾

- [x] 3.1 cloud + console land master（fetch 核对 in-sync → 显式 add 提交 → push）。 <!-- aidcp-cloud 05bd239 / aidcp-console 6a6fe92 -->
- [x] 3.2 部署 dev：cloud 安全序列（备份 cloud.bak.20260712-102550 → rsync 改动 src → restart → healthcheck：service active / 8787+8090+8091 监听 / 飞书长连接 / `GET /api/client-environments` 经 nginx 返 401=已接线）；console（备份 → rsync 不 --delete → 剪旧 asset+备份留 10 → 验证新 JS 200 + 端用户/client-environments 已进包）。 <!-- 2026-07-12 deployed -->
- [x] 3.3 真机 SQL 已验证：dev PG 用 BEGIN…ROLLBACK 事务塞临时数据跑真 `listAllEnvironments` SQL——`env-shared`→2 assignees（多人）、`env-solo`→1、label/platform 取非空代表值、`{userId,name}` 形状对、回滚 0 残留。GUI 侧真机项登记 backlog 簇 61。 <!-- 2026-07-12 -->
- [x] 3.4 `openspec validate client-user-env-picker --strict`（valid）→ archive（delta 纯 ADDED，合入 `client-customer-auth` spec）。 <!-- 2026-07-12 archived -->
- [ ] 3.5 GUI/交互真机项：backlog 簇 61.7–61.10。
