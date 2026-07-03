> **协调与红线（动手前必读）**
> - **迁移号**：取 `0015_session_config.sql`（现有最高 `0014_publish_post_url`；`0012` 仍预留 stream B `account-real-nickname`）。**动前 `ls ../aidcp-cloud/migrations/` 复核**，与并发会话错峰。
> - **不触协议**：单场上限是云端内部配置，不经 WS v2。两份 `protocol.ts` / `command-bridge.ts` / `docs/protocol.md` / edge `edge-client.ts` 白名单一律不动。
> - **不触风控状态单写**：`setQuotaLevel` / `applySignal` / 状态机 / `risk_state` 不动；提供者只读，新配置只写 `session_config`。
> - **共享 chokepoint 一律 APPEND**：cloud `server.ts` / `panel-server.ts` / `panel/types.ts`；console `types/api.ts` / `queries.ts`。只 `git add` 自己的具体文件、**绝不 `-A`**；与他流共享文件用 git plumbing 只暂存自己的 hunk（见 memory `precise-git-add-concurrent-sessions`）。
> - **删 `session_limits` 是唯一会 brick 的步骤**：必须等全部运行时读点迁走、`grep` 确认无残留、typecheck 绿之后才删（见 §4，最后做）。
> - **零回归基线 = 平铺现值**：空表 / 缺行回落 时长 10min + 现 `freshBudget` 数字（**不是** v1 `SESSION_LIMITS` 15/30/60 梯度）。

## 1. aidcp-cloud — 单场上限配置存储与迁移（0015）

- [x] 1.1 新增 `migrations/0015_session_config.sql`：建表 `session_config(account_id PK, max_duration_min, budget_likes, budget_collects, budget_follows, budget_searches, budget_comments, budget_comment_likes, updated_at, updated_by)`，幂等 `CREATE TABLE IF NOT EXISTS`；初始**不预填行**（缺行回落写死默认）<!-- aidcp-cloud 497d1bc -->
- [x] 1.2 在集中常量处（如 `src/risk/session-budget.ts` 或新 `src/config/session-limit-defaults.ts`）导出写死默认：`DEFAULT_SESSION_DURATION_MIN=10`、`DEFAULT_SESSION_BUDGET={likes:10,collects:5,follows:3,searches:5,comments:2,comment_likes:3}`、校验上限 `SESSION_LIMIT_MAX`；保留 v1 `SESSION_LIMITS` 不动（兼容路径）<!-- aidcp-cloud 497d1bc 新建 src/risk/session-limits.ts（安全限额层，与 quotas.ts 同层）；v1 session-budget.ts SESSION_LIMITS 未动 -->
- [x] 1.3 定义 `SessionLimitProvider` 接口（`sessionDurationMsFor(accountId): number` / `sessionBudgetFor(accountId): SessionBudgetShape`），放风控 / 共享类型层（持接口、不依赖 config 实现）<!-- aidcp-cloud 497d1bc 在 src/risk/session-limits.ts，从 risk/index.ts 导出 -->
- [x] 1.4 新增 `src/config/session-config-store.ts` `SessionConfigStore`：复刻 `quota-config-store.ts` 时序——`init()` 建表（内含 `SESSION_CONFIG_SCHEMA_SQL` 与迁移同源）+ 载入内存镜像；`set(accountId, patch, updatedBy)` 先写库成功再刷镜像；`getRow/getAll`（面板用）<!-- aidcp-cloud 497d1bc -->
- [x] 1.5 `SessionConfigStore` 实现 `SessionLimitProvider`：按 `accountId` 取镜像行组装；缺行 / 字段非有限非负整数（时长还需 `>=1`）→ 逐项回落写死默认；永不抛<!-- aidcp-cloud 497d1bc -->

## 2. aidcp-cloud — 接管运行时读点（按账号、热加载、不触状态单写）

- [x] 2.1 `src/orchestrator/role-dispatcher.ts`：`RoleDispatcherOptions` 加可选 `sessionLimitProvider?`；构造时持有 <!-- aidcp-cloud a015253 -->
- [x] 2.2 `role-dispatcher.ts` `maxDurationMs()`：改 `this.sessionLimitProvider?.sessionDurationMsFor(this.currentAccountId) ?? DEFAULT_SESSION_DURATION_MS`（保留惰性现读形态，`progress()` 不变） <!-- aidcp-cloud a015253 -->
- [x] 2.3 `role-dispatcher.ts` `freshBudget()`：改为按当前账号从提供者读（缺则回落 `DEFAULT_SESSION_BUDGET`）；`this.budget` 初始化、`restartSession()` reset 用它 <!-- aidcp-cloud a015253 freshBudget 改实例方法；budget 字段 lazy（!:），构造期 + startSession + restartSession 三处刷新 -->
- [x] 2.4 `role-dispatcher.ts` 比率闸一致性：会话开始 / reset 时把当次预算快照存 `this.budgetInit`；`sessionLikeCounts()` 用 `this.budgetInit`（不再现读提供者），杜绝会话中途改预算致 `init−剩余` 漂移 <!-- aidcp-cloud a015253 -->
- [x] 2.5 `src/agents/session-monitor-role.ts` `effectiveMaxDurationMs()`：去掉对 `this.soul.session_limits` 的直读，改经调度器注入的统一解析口（`getMaxDurationMs: () => this.maxDurationMs()` thunk），缺省回落 10min；调度器构造 `SessionMonitorRole` 处接线（约 :405） <!-- aidcp-cloud a015253 接线点现 :442；缺省回落 DEFAULT_SESSION_DURATION_MS -->
- [x] 2.6 红线核对：提供者只读；`maxDurationMs` / `freshBudget` / 监测体不写 state、不调 `setQuotaLevel` / `applySignal`、不碰 `risk_state`、不经协议 <!-- aidcp-cloud a015253 结构性核对通过；AC-RISK/AC-PROTO 26/26 绿 -->

> §2 备注：committed cloud a015253；committed 树隔离 worktree 校验 typecheck 全绿（无并发 WIP），full test 718/718、acceptance 26/26。

## 3. aidcp-cloud — 面板 facade 与 API 路由（APPEND）

- [x] 3.1 新增 `src/config/session-config-facade.ts`：`getCatalog()` 回显按账号的时长 + 六项预算（库缺行以写死默认合成）+ 审计；`setQuota/set(patch, updatedBy)` 校验（整数 + `>=0` + `<=SESSION_LIMIT_MAX` + 时长 `>=1`）→ 写库 → 刷镜像 → 回真态；非法整块拒、绝不部分落库 <!-- aidcp-cloud a015253 方法名 set；getCatalog 经提供者口取「显示=真生效」，default 账号恒列 -->
- [x] 3.2 `src/panel/panel-server.ts`：**APPEND** `GET /api/session-limits` + `PUT /api/session-limits`（JWT，`verified.payload.sub` 作 `updatedBy`；invalid→4xx，未注入→503） <!-- aidcp-cloud a015253 invalid_value/no_valid_fields→400；bad_request→400 -->
- [x] 3.3 `src/panel/types.ts`：**APPEND** 单场上限面板 DTO（`SessionLimitRowView` / `SessionLimitCatalogView` / `SessionLimitPatchInput` / `SessionLimitSetResult` / `PanelSessionLimits` + `PanelDeps.sessionLimits?`） <!-- aidcp-cloud a015253 -->
- [x] 3.4 `src/server.ts`：**仅 APPEND** —— `new SessionConfigStore(...)` + `init()`（与其余 config store 同 try/catch，吞错退化写死默认）+ `createSessionLimitPanel(...)` + store 作 `sessionLimitProvider` 传 `RoleDispatcher` 装配处 + facade 进 panel deps；未改他流既有块 <!-- aidcp-cloud a015253 server.ts/panel-server.ts/panel-types.ts 与并发 text-provider WIP 交织，已 surgical 重建「仅本 change 改动」入 commit、未裹挟他流 -->

## 4. aidcp-cloud — 人设清理（最后做，唯一会 brick 的步骤）

- [x] 4.1 `grep -rn "session_limits" src/` 确认运行时**已无读点**（仅余 §1–3 完成后的定义 / 解析），typecheck 绿 <!-- aidcp-cloud a015253 §2 迁走两读点后 grep 仅余 panel-server 错误串 + 迁移注释，无运行时读点 -->
- [x] 4.2 `src/soul/types.ts`：移除 `Soul.session_limits` 字段（及 `SessionLimits` 类型，如无他用） <!-- aidcp-cloud a015253 仅删字段；SessionLimits 类型保留（browse_patterns.session 仍用，parseSession） -->
- [x] 4.3 `src/soul/loader.ts`：移除 `parseSessionLimits` 及其调用（`session_limits` 不再解析） <!-- aidcp-cloud a015253 parseSession（browse_patterns.session）保留 -->
- [x] 4.4 `src/soul/soul.yaml`：删除 `session_limits` 段 <!-- aidcp-cloud a015253 -->
- [x] 4.5 删后回归：`grep -rn "session_limits" src/` 零结果；`npm run typecheck` 绿；提供者缺失 / 空表回落 10min + freshBudget 的单测覆盖删除后路径 <!-- aidcp-cloud a015253 committed 树 typecheck 全绿；test/session-effective-limits.test.ts 覆盖 provider 缺失回落 10min + 默认预算零回归；soul.test.ts 验 loader 不再解析该字段 -->

## 5. aidcp-console — 单场上限编辑区 + 人设页清理

- [x] 5.1 `src/types/api.ts`：**APPEND** 单场上限 DTO（账号 + 时长 + 六项预算，对齐 cloud） <!-- aidcp-console e74a76c SessionInteractionBudget/SessionLimitRow/SessionLimitCatalog -->
- [x] 5.2 `src/api/queries.ts`：**APPEND** `useSessionLimits`（`GET /api/session-limits`）；写走页内 `apiPut`（成功后 invalidate 非乐观刷新，同 RolesPage/QuotasPage 形态） <!-- aidcp-console e74a76c -->
- [x] 5.3 `src/pages/QuotasPage.tsx`：加「单场上限」编辑区（按账号一行：时长 + 六项预算）+ 弹窗；前端校验（非负整数 + 上限 + 时长≥1）即时反馈、**服务端校验为准**；保存后回显刷新；账号源对齐现有账号选择形态（单租户即 `default`） <!-- aidcp-console e74a76c 第二个 Card「单场会话上限」+ 独立编辑 Modal -->
- [x] 5.4 `src/pages/PersonaPage.tsx`（或等价）：隐藏 / 移除 `session_limits` 编辑区（去掉「能改却无效」字段） <!-- aidcp-console e74a76c PersonaPage 为 YAML 文本编辑器，无离散 session_limits 字段；更新文档注释指明已迁出到单场上限页 -->

## 6. 验证

- [x] 6.1 cloud 单测：`sessionDurationMsFor` / `sessionBudgetFor` 命中库值生效；账号缺行 / 字段非法逐项回落写死默认；空表与写死默认逐位一致（零回归） <!-- aidcp-cloud a015253 test/session-config-store.test.ts（fake pool，8 例） -->
- [x] 6.2 cloud 单测：`maxDurationMs()` / `freshBudget()` 注入提供者后按账号现读（改镜像后下一次读按新值，热加载）；`sessionLikeCounts()` 用会话初始快照、中途改预算不漂移 <!-- aidcp-cloud a015253 test/session-effective-limits.test.ts（monitor getMaxDurationMs + dispatcher 小预算耗尽 vs 默认零回归）；store 热加载在 store 测覆盖 -->
- [x] 6.3 cloud 单测：单场上限编辑不触状态单写——facade 仅写 `session_config`、无 `RiskController` 引用、不经协议 <!-- aidcp-cloud a015253 facade 测 setCalls 仅触该账号；facade 无 RiskController import（结构性） -->
- [x] 6.4 cloud facade 单测：合法写回真态；负 / 非整 / 超上限 / 时长<1 / 未知账号字段 整块拒、不落库；非乐观回显 <!-- aidcp-cloud a015253 test/session-config-facade.test.ts（8 例，含空 accountId/时长<1/预算 0 合法） -->
- [x] 6.5 cloud 单测：删 `session_limits` 后，soul 加载不含该字段、loader 不解析；提供者缺失回落 10min（删除后路径不 brick） <!-- aidcp-cloud a015253 soul.test.ts + session-effective-limits.test.ts -->
- [x] 6.6 cloud：`npm run test:acceptance`（AC-RISK / AC-PROTO 全过）→ 全量 `npm test` → `npm run typecheck` 绿 <!-- aidcp-cloud a015253 acceptance 26/26、full test 718/718；typecheck：committed 树隔离 worktree 全绿（worktree 内 publish-agent + text-provider 并发 WIP 报错非本 change） -->
- [x] 6.7 console：单场上限编辑 + 人设页清理 build/typecheck 通过；保存走 JWT、非乐观刷新 <!-- aidcp-console e74a76c tsc --noEmit 绿 + vite build 通过 -->

## 7. 收尾、部署与归档

- [x] 7.1 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <sha> 备注 -->`） <!-- aidcp（本提交）；cloud a015253 / console e74a76c / §1 storage 497d1bc -->
- [x] 7.2 `openspec validate session-limits-to-quota-layer --strict` 通过 <!-- 2026-06-26 "Change is valid" -->
- [x] 7.3 按 §5 安全序列部署 ECS（先备份 → `rsync --dry-run` 摸范围 → rsync → restart → healthcheck：8787 / PG `select 1` / 迁移 `0015` 已建表 / 面板 8090）；部署后 grep ECS 文件内容 + 看启动日志确认新码生效；与并发会话错峰 <!-- 2026-06-26 deployed：部署 origin/master f1e0883（先隔离 worktree 校验 typecheck 全绿 + acceptance 26/26 才发）；clean-master rsync（pristine worktree，排除本地并发 WIP）；备份 cloud.bak.20260626-100038.tar.gz + .env.bak；restart 后启动日志「…安全限额 + 单场上限存储已就绪（…session_config）」实测出现；PG session_config 表已建（0 行→全回落默认=零回归）；ECS grep 确认 panel-server 2 个 /api/session-limits handler + server.ts sessionLimits dep + facade 85 行；8787/8090 监听 + 飞书长连接已建 + isales 80/8000 未碰。dry-run 校验：内容级 0 diff（并发会话已先发同 master）+ 删除项仅 stale .zip/旧测试（故 real rsync 去 --delete 避并发竞态） -->
- [ ] 7.4 真机校准：后台改某账号单场时长 / 某项预算 → 下场会话即按新值（热加载无重启）；空账号回落 10min + freshBudget；`/persona` 不再出现 `session_limits` <!-- GATED：部署前置闸已满足（7.3 已于 2026-06-26 部署，cloud f1e0883），现仅待真机执行（勿提前勾选） -->
- [ ] 7.5 `/opsx:archive` 归档（delta 合并进 `openspec/specs/interaction-risk-gating`） <!-- 待 7.3/7.4 后归档 -->
