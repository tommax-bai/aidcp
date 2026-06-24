> **并行协调（5 流，本 change = stream D：safety-quota-config）**
> - **迁移号预留**：C(role-model-category-config)=`0009`、**D(本 change)=`0010`**、F(account-persona-config)=`0011`、B(account-real-nickname)=`0012`。本 change 只用 `0010_quota_config.sql`，不占其他号。
> - **server.ts 归属**：stream C **拥有** model-resolver 块（`resolveModelForRole` / `resolveTempForRole` + 共享 LLM 客户端装配）且**先落**。D 只**APPEND**（quota store init + facade + 注入 registry + panel 依赖），**绝不**改 C 的 resolver 块。
> - **协议红线**：stream B 独占两份 `protocol.ts` + `command-bridge.ts` + `docs/protocol.md`（+ edge `edge-client.ts` onMessage 白名单）。**本 change 不触协议**（限额是云端内部配置，不经 WS v2）。
> - **共享 chokepoint 按保留序 APPEND（C→D→F→B）**：cloud `src/panel/panel-server.ts` 路由链、`src/panel/types.ts`；console `src/types/api.ts`、`src/api/queries.ts`。一律追加在 C 之后，不与 F/B 抢同一处。
> - **console 路由 / 导航**：D 加 `/quotas`，F 加 `/persona`（`App.tsx` + `AppShell.tsx` 互不冲突，各加各的）。
> - **红线**：风控状态单写（`setQuotaLevel` / `applySignal` / `risk_state`）不动；限额数字编辑只写 `quota_config`；缺行 / 非法值绝不 brick 回落写死默认；配额表为空时零回归。

## 1. aidcp-cloud — 配额配置存储与迁移（0010）

- [ ] 1.1 新增 `migrations/0010_quota_config.sql`：建表 `quota_config(tier, action, daily, per_minute, per_hour, updated_at, updated_by, PRIMARY KEY(tier,action))`，幂等 `CREATE TABLE IF NOT EXISTS`；初始**不预填行**（缺行回落写死默认）
- [ ] 1.2 新增 `src/config/quota-config-store.ts` `QuotaConfigStore`：复刻 `role-config-store.ts` 时序——`init()` 建表 + 载入内存镜像；`set((tier,action), patch, updatedBy)` 先写库成功再刷镜像（绝不镜像 / 库不一致）；内含 `QUOTA_CONFIG_SCHEMA_SQL` 与迁移同源
- [ ] 1.3 `QuotaConfigStore` 实现同步只读提供者 `windowQuotasFor(level)`：对 7 个 `RISK_ACTIONS` 各取 `(level,action)` 镜像行组装 `{minute:{…per_minute},hour:{…per_hour},day:{…daily}}`；任一动作缺行 / 字段非法 → 该动作回落 `quotas.ts` 的 `DAILY_QUOTAS`/`MINUTE_BURST_CAP`/`HOUR_BURST_CAP`；永不抛
- [ ] 1.4 `src/risk/quotas.ts`：导出写死默认供回落（已有 `DAILY_QUOTAS`，把 `MINUTE_BURST_CAP`/`HOUR_BURST_CAP` 也导出）；新增「按三窗口数字组装 `WindowQuotas`」纯函数；保留 `deriveWindowQuotas` 作回落 / 兼容
- [ ] 1.5 定义 `QuotaProvider` 接口（`windowQuotasFor(level: RiskQuotaLevel): WindowQuotas`），与风控类型同源（`src/risk/types.ts` 或 store 文件导出）

## 2. aidcp-cloud — 提供者注入 effectiveQuotas（不触状态单写）

- [ ] 2.1 `src/risk/risk-controller.ts`：`RiskControllerOptions` 加可选 `quotaProvider?: QuotaProvider`；构造时持有
- [ ] 2.2 `src/risk/risk-controller.ts` `effectiveQuotas()`：基准三档由 `quotaProvider?.windowQuotasFor(level) ?? deriveWindowQuotas(level)` 提供；`warned`/`restricted`/`frozen` 仍对**基准**套 `scaleWindowQuotas`/`zeroInteractionQuotas`（缩放 / 清零语义不变）。**注意零回归红线**：现状 warned/restricted/frozen 三态的基准是写死 `deriveWindowQuotas('conservative')`（**不是** `state.quotaLevel`），故 provider 替换后这三态必须传 `windowQuotasFor('conservative')`（同样固定 `'conservative'` 实参），仅 `normal` 默认分支用 `windowQuotasFor(state.quotaLevel)`，否则破坏「表为空逐位一致」场景
- [ ] 2.3 `src/risk/risk-controller-registry.ts`：构造时接收并持有 `quotaProvider`，透传给每账号 `RiskController.create`
- [ ] 2.4 红线核对：提供者只读；`effectiveQuotas` / `canDo` 不写 state、不调 `setQuotaLevel` / `applySignal`、不碰 `risk_state` 表

## 3. aidcp-cloud — 面板 facade 与 API 路由（APPEND，序在 C 之后）

- [ ] 3.1 新增 `src/config/quota-config-facade.ts`：复刻 `role-config-facade.ts`——`getCatalog()` 回显三档 × 7 动作 × 三窗口（库缺行以写死默认合成）+ 审计字段；`setQuota(patch, updatedBy)` 校验（`Number.isInteger`+`>=0`+`<=QUOTA_MAX` + 合法 tier/action）→ 写库 → 刷镜像 → 回显真态；非法整块拒（`unknown_tier`/`unknown_action`/`invalid_value`）、绝不部分落库
- [ ] 3.2 `src/panel/panel-server.ts`：**APPEND**（在 C 的 `/api/roles` 块之后）`GET /api/quotas`（JWT，回 `getCatalog()`）与 `PUT /api/quotas`（JWT，`verified.payload.sub` 作 `updatedBy`，调 `setQuota`；非法→400、未配可用→503）
- [ ] 3.3 `src/panel/types.ts`：**APPEND** 配额面板 DTO（tier × action × {daily, perMinute, perHour, updatedAt, updatedBy}）
- [ ] 3.4 `src/server.ts`：**仅 APPEND** —— `new QuotaConfigStore(...)` + `await store.init()`（吞错则不注入、退化写死默认）+ `createQuotaConfigPanel(...)` + 把 store 作 `quotaProvider` 传 `RiskControllerRegistry` + 把 facade 加进 panel deps；**绝不**改 stream C 的 `resolveModelForRole`/`resolveTempForRole` resolver 块

## 4. aidcp-console — 限额页（路由 + 导航 + 取数 / 写回）

- [ ] 4.1 `src/types/api.ts`：**APPEND**（序在 C 之后）配额 DTO（`QuotaConfigCatalog` 等，对齐 cloud panel DTO）
- [ ] 4.2 `src/api/queries.ts`：**APPEND**（序在 C 之后）`useQuotaConfig`（`GET /api/quotas`）+ `useUpdateQuotaConfig`（`PUT /api/quotas`，成功后用回显刷新缓存，非乐观）
- [ ] 4.3 新增 `src/pages/QuotasPage.tsx`：三档 × 7 动作 × 三窗口可编辑表格；保存前前端校验（非负整数 + 上限）给即时反馈，**服务端校验为准**；保存后回显刷新
- [ ] 4.4 `src/App.tsx` + `src/components/AppShell.tsx`（或等价导航壳）：加 `/quotas` 路由 + 导航项（与 F 的 `/persona` 互不冲突）

## 5. 验证

- [ ] 5.1 cloud 单测：`windowQuotasFor` 命中库值生效；缺行 / 非法值回落写死默认；表为空时与 `deriveWindowQuotas` 写死默认逐位一致（零回归）
- [ ] 5.2 cloud 单测：`effectiveQuotas()` 注入 provider 后 `warned`/`restricted`/`frozen` 缩放 / 清零语义不变；`canDo` 每次现读（改 provider 镜像后下一次判定按新值）
- [ ] 5.3 cloud 单测：限额编辑不触状态单写——`setQuota` 后 `risk_state` 不变、`setQuotaLevel`/`applySignal` 未被调用
- [ ] 5.4 cloud facade 单测：合法写回显真态；负数 / 非整数 / 超上限 / 未知 tier·action 整块拒、不落库；非乐观回显
- [ ] 5.5 cloud：`npm run test:acceptance`（安全红线全过：`AC-RISK-*` 绝不自残、`AC-PROTO-*` 协议不漂移——本 change 不动协议应天然不影响）→ 全量 `npm test` → `npm run typecheck`
- [ ] 5.6 console：限额页 build/typecheck 通过；保存路径走 JWT、非乐观刷新

## 7. 会话上限收口本层（范围追加 2026-06-24 用户决策；详细 schema 待 apply 时设计）

> 见 proposal.md「范围补充」。把「单场会话上限」从人设（soul.session_limits）搬到安全限额层：按账号 + 三档可配、热加载、never-brick。死字段（session_limits 里除时长外的 max_likes/max_searches/… 当前无处读取）顺带清理。

- [ ] 7.1 设计单场上限的存储形态（扩 `quota_config` 还是另立 `session_config`：单场时长 by tier + 单场互动预算 by (tier,action)），与日/分/时配额同源；写死默认（`session-budget.ts` `SESSION_LIMITS` + `freshBudget()` 现值）作 never-brick 回落
- [ ] 7.2 cloud：单场时长上限接管 `max_duration_min` 来源 —— `role-dispatcher.ts` / `session-monitor-role.ts` 由读 `this.soul.session_limits` 改为读本层提供者（保留惰性解析的热加载形态）
- [ ] 7.3 cloud：单场互动预算接管 `role-dispatcher.ts` `freshBudget()` 写死值 —— 改为按当前账号 / 档位从本层读取
- [ ] 7.4 console：`/quotas` 页加单场上限编辑区（时长 + 单场互动预算），同样非乐观写
- [ ] 7.5 配套 F 清理：人设（soul / persona）停止承载 `session_limits`——删除死字段或在人设页隐藏，`max_duration_min` 改由本层供给（与 F 协调，见 F design.md「留的缝」）
- [ ] 7.6 验证：改单场上限即时生效（热加载）；缺值回落写死默认不 brick；人设页不再出现「能改却无效」的限额字段

## 6. 收尾与归档

- [ ] 6.1 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <sha> 备注 -->`）
- [ ] 6.2 `openspec validate safety-quota-config --strict` 通过
- [ ] 6.3 按 §5 安全序列部署 ECS（先备份 → rsync → restart → healthcheck：8787 / PG `select 1` / 迁移 `0010` 已建表 / 面板 `8090`）；与同批其他流协调一次部署
- [ ] 6.4 上线后真机校准：管理后台改某档某动作限额 → 观察 `canDo` 即按新值（热加载无重启）；确认风控状态不被配置写动摇
- [ ] 6.5 `/opsx:archive` 归档（delta 合并进 `openspec/specs/interaction-risk-gating`）
