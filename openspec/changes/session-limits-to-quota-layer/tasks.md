> **协调与红线（动手前必读）**
> - **迁移号**：取 `0015_session_config.sql`（现有最高 `0014_publish_post_url`；`0012` 仍预留 stream B `account-real-nickname`）。**动前 `ls ../aidcp-cloud/migrations/` 复核**，与并发会话错峰。
> - **不触协议**：单场上限是云端内部配置，不经 WS v2。两份 `protocol.ts` / `command-bridge.ts` / `docs/protocol.md` / edge `edge-client.ts` 白名单一律不动。
> - **不触风控状态单写**：`setQuotaLevel` / `applySignal` / 状态机 / `risk_state` 不动；提供者只读，新配置只写 `session_config`。
> - **共享 chokepoint 一律 APPEND**：cloud `server.ts` / `panel-server.ts` / `panel/types.ts`；console `types/api.ts` / `queries.ts`。只 `git add` 自己的具体文件、**绝不 `-A`**；与他流共享文件用 git plumbing 只暂存自己的 hunk（见 memory `precise-git-add-concurrent-sessions`）。
> - **删 `session_limits` 是唯一会 brick 的步骤**：必须等全部运行时读点迁走、`grep` 确认无残留、typecheck 绿之后才删（见 §4，最后做）。
> - **零回归基线 = 平铺现值**：空表 / 缺行回落 时长 10min + 现 `freshBudget` 数字（**不是** v1 `SESSION_LIMITS` 15/30/60 梯度）。

## 1. aidcp-cloud — 单场上限配置存储与迁移（0015）

- [ ] 1.1 新增 `migrations/0015_session_config.sql`：建表 `session_config(account_id PK, max_duration_min, budget_likes, budget_collects, budget_follows, budget_searches, budget_comments, budget_comment_likes, updated_at, updated_by)`，幂等 `CREATE TABLE IF NOT EXISTS`；初始**不预填行**（缺行回落写死默认）
- [ ] 1.2 在集中常量处（如 `src/risk/session-budget.ts` 或新 `src/config/session-limit-defaults.ts`）导出写死默认：`DEFAULT_SESSION_DURATION_MIN=10`、`DEFAULT_SESSION_BUDGET={likes:10,collects:5,follows:3,searches:5,comments:2,comment_likes:3}`、校验上限 `SESSION_LIMIT_MAX`；保留 v1 `SESSION_LIMITS` 不动（兼容路径）
- [ ] 1.3 定义 `SessionLimitProvider` 接口（`sessionDurationMsFor(accountId): number` / `sessionBudgetFor(accountId): SessionBudgetShape`），放风控 / 共享类型层（持接口、不依赖 config 实现）
- [ ] 1.4 新增 `src/config/session-config-store.ts` `SessionConfigStore`：复刻 `quota-config-store.ts` 时序——`init()` 建表（内含 `SESSION_CONFIG_SCHEMA_SQL` 与迁移同源）+ 载入内存镜像；`set(accountId, patch, updatedBy)` 先写库成功再刷镜像；`getRow/getAll`（面板用）
- [ ] 1.5 `SessionConfigStore` 实现 `SessionLimitProvider`：按 `accountId` 取镜像行组装；缺行 / 字段非有限非负整数（时长还需 `>=1`）→ 逐项回落写死默认；永不抛

## 2. aidcp-cloud — 接管运行时读点（按账号、热加载、不触状态单写）

- [ ] 2.1 `src/orchestrator/role-dispatcher.ts`：`RoleDispatcherOptions` 加可选 `sessionLimitProvider?`；构造时持有
- [ ] 2.2 `role-dispatcher.ts` `maxDurationMs()`：改 `this.sessionLimitProvider?.sessionDurationMsFor(this.currentAccountId) ?? DEFAULT_SESSION_DURATION_MS`（保留惰性现读形态，`progress()` 不变）
- [ ] 2.3 `role-dispatcher.ts` `freshBudget()`：改为按当前账号从提供者读（缺则回落 `DEFAULT_SESSION_BUDGET`）；`this.budget` 初始化、`restartSession()` reset 用它
- [ ] 2.4 `role-dispatcher.ts` 比率闸一致性：会话开始 / reset 时把当次预算快照存 `this.budgetInit`；`sessionLikeCounts()` 用 `this.budgetInit`（不再现读提供者），杜绝会话中途改预算致 `init−剩余` 漂移
- [ ] 2.5 `src/agents/session-monitor-role.ts` `effectiveMaxDurationMs()`：去掉对 `this.soul.session_limits` 的直读，改经调度器注入的统一解析口（`getMaxDurationMs: () => this.maxDurationMs()` thunk），缺省回落 10min；调度器构造 `SessionMonitorRole` 处接线（约 :405）
- [ ] 2.6 红线核对：提供者只读；`maxDurationMs` / `freshBudget` / 监测体不写 state、不调 `setQuotaLevel` / `applySignal`、不碰 `risk_state`、不经协议

## 3. aidcp-cloud — 面板 facade 与 API 路由（APPEND）

- [ ] 3.1 新增 `src/config/session-config-facade.ts`：`getCatalog()` 回显按账号的时长 + 六项预算（库缺行以写死默认合成）+ 审计；`setQuota/set(patch, updatedBy)` 校验（整数 + `>=0` + `<=SESSION_LIMIT_MAX` + 时长 `>=1`）→ 写库 → 刷镜像 → 回真态；非法整块拒、绝不部分落库
- [ ] 3.2 `src/panel/panel-server.ts`：**APPEND** `GET /api/session-limits` + `PUT /api/session-limits`（JWT，`verified.payload.sub` 作 `updatedBy`；invalid→4xx，未注入→503）
- [ ] 3.3 `src/panel/types.ts`：**APPEND** 单场上限面板 DTO（`SessionLimitRowView` / `SessionLimitCatalogView` / `SessionLimitPatchInput` / `SessionLimitSetResult` / `PanelSessionLimits` + `PanelDeps.sessionLimits?`）
- [ ] 3.4 `src/server.ts`：**仅 APPEND** —— `new SessionConfigStore(...)` + `init()`（与其余 config store 同 try/catch，吞错退化写死默认）+ `createSessionLimitPanel(...)` + store 作 `sessionLimitProvider` 传 `RoleDispatcher` 装配处 + facade 进 panel deps；未改他流既有块

## 4. aidcp-cloud — 人设清理（最后做，唯一会 brick 的步骤）

- [ ] 4.1 `grep -rn "session_limits" src/` 确认运行时**已无读点**（仅余 §1–3 完成后的定义 / 解析），typecheck 绿
- [ ] 4.2 `src/soul/types.ts`：移除 `Soul.session_limits` 字段（及 `SessionLimits` 类型，如无他用）
- [ ] 4.3 `src/soul/loader.ts`：移除 `parseSessionLimits` 及其调用（`session_limits` 不再解析）
- [ ] 4.4 `src/soul/soul.yaml`：删除 `session_limits` 段
- [ ] 4.5 删后回归：`grep -rn "session_limits" src/` 零结果；`npm run typecheck` 绿；提供者缺失 / 空表回落 10min + freshBudget 的单测覆盖删除后路径

## 5. aidcp-console — 单场上限编辑区 + 人设页清理

- [ ] 5.1 `src/types/api.ts`：**APPEND** 单场上限 DTO（账号 + 时长 + 六项预算，对齐 cloud）
- [ ] 5.2 `src/api/queries.ts`：**APPEND** `useSessionLimits`（`GET /api/session-limits`）；写走页内 `apiPut`（成功后 invalidate 非乐观刷新，同 RolesPage/QuotasPage 形态）
- [ ] 5.3 `src/pages/QuotasPage.tsx`：加「单场上限」编辑区（按账号一行：时长 + 六项预算）+ 弹窗；前端校验（非负整数 + 上限 + 时长≥1）即时反馈、**服务端校验为准**；保存后回显刷新；账号源对齐现有账号选择形态（单租户即 `default`）
- [ ] 5.4 `src/pages/PersonaPage.tsx`（或等价）：隐藏 / 移除 `session_limits` 编辑区（去掉「能改却无效」字段）

## 6. 验证

- [ ] 6.1 cloud 单测：`sessionDurationMsFor` / `sessionBudgetFor` 命中库值生效；账号缺行 / 字段非法逐项回落写死默认；空表与写死默认逐位一致（零回归）
- [ ] 6.2 cloud 单测：`maxDurationMs()` / `freshBudget()` 注入提供者后按账号现读（改镜像后下一次读按新值，热加载）；`sessionLikeCounts()` 用会话初始快照、中途改预算不漂移
- [ ] 6.3 cloud 单测：单场上限编辑不触状态单写——facade 仅写 `session_config`、无 `RiskController` 引用、不经协议
- [ ] 6.4 cloud facade 单测：合法写回真态；负 / 非整 / 超上限 / 时长<1 / 未知账号字段 整块拒、不落库；非乐观回显
- [ ] 6.5 cloud 单测：删 `session_limits` 后，soul 加载不含该字段、loader 不解析；提供者缺失回落 10min（删除后路径不 brick）
- [ ] 6.6 cloud：`npm run test:acceptance`（AC-RISK / AC-PROTO 全过）→ 全量 `npm test` → `npm run typecheck` 绿
- [ ] 6.7 console：单场上限编辑 + 人设页清理 build/typecheck 通过；保存走 JWT、非乐观刷新

## 7. 收尾、部署与归档

- [ ] 7.1 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <sha> 备注 -->`）
- [ ] 7.2 `openspec validate session-limits-to-quota-layer --strict` 通过
- [ ] 7.3 按 §5 安全序列部署 ECS（先备份 → `rsync --dry-run` 摸范围 → rsync → restart → healthcheck：8787 / PG `select 1` / 迁移 `0015` 已建表 / 面板 8090）；部署后 grep ECS 文件内容 + 看启动日志确认新码生效；与并发会话错峰
- [ ] 7.4 真机校准：后台改某账号单场时长 / 某项预算 → 下场会话即按新值（热加载无重启）；空账号回落 10min + freshBudget；`/persona` 不再出现 `session_limits`
- [ ] 7.5 `/opsx:archive` 归档（delta 合并进 `openspec/specs/interaction-risk-gating`）
