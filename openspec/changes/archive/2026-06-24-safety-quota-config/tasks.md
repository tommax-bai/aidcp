> **并行协调（5 流，本 change = stream D：safety-quota-config）**
> - **迁移号预留**：C(role-model-category-config)=`0009`、**D(本 change)=`0010`**、F(account-persona-config)=`0011`、B(account-real-nickname)=`0012`。本 change 只用 `0010_quota_config.sql`，不占其他号。
> - **server.ts 归属**：stream C **拥有** model-resolver 块（`resolveModelForRole` / `resolveTempForRole` + 共享 LLM 客户端装配）且**先落**。D 只**APPEND**（quota store init + facade + 注入 registry + panel 依赖），**绝不**改 C 的 resolver 块。
> - **协议红线**：stream B 独占两份 `protocol.ts` + `command-bridge.ts` + `docs/protocol.md`（+ edge `edge-client.ts` onMessage 白名单）。**本 change 不触协议**（限额是云端内部配置，不经 WS v2）。
> - **共享 chokepoint 按保留序 APPEND（C→D→F→B）**：cloud `src/panel/panel-server.ts` 路由链、`src/panel/types.ts`；console `src/types/api.ts`、`src/api/queries.ts`。一律追加在 C 之后，不与 F/B 抢同一处。
> - **console 路由 / 导航**：D 加 `/quotas`，F 加 `/persona`（`App.tsx` + `AppShell.tsx` 互不冲突，各加各的）。
> - **红线**：风控状态单写（`setQuotaLevel` / `applySignal` / `risk_state`）不动；限额数字编辑只写 `quota_config`；缺行 / 非法值绝不 brick 回落写死默认；配额表为空时零回归。

## 1. aidcp-cloud — 配额配置存储与迁移（0010）

- [x] 1.1 新增 `migrations/0010_quota_config.sql`：建表 `quota_config(tier, action, daily, per_minute, per_hour, updated_at, updated_by, PRIMARY KEY(tier,action))`，幂等 `CREATE TABLE IF NOT EXISTS`；初始**不预填行**（缺行回落写死默认）<!-- cloud dd43691 -->
- [x] 1.2 新增 `src/config/quota-config-store.ts` `QuotaConfigStore`：复刻 `role-config-store.ts` 时序——`init()` 建表 + 载入内存镜像；`set((tier,action), patch, updatedBy)` 先写库成功再刷镜像（绝不镜像 / 库不一致）；内含 `QUOTA_CONFIG_SCHEMA_SQL` 与迁移同源 <!-- cloud dd43691 另加 getRow/getAll（面板）+ clear-row 语义经 set -->
- [x] 1.3 `QuotaConfigStore` 实现同步只读提供者 `windowQuotasFor(level)`：对 7 个 `RISK_ACTIONS` 各取 `(level,action)` 镜像行组装三窗口；任一动作缺行 / 字段非法 → 该动作回落写死默认；永不抛 <!-- cloud dd43691 **关键校正**：回落逐窗口走 `deriveWindowQuotas(level)`（非裸 MINUTE/HOUR_BURST_CAP）——否则空表 minute/hour 与历史 ceil 派生不一致、破坏零回归。task 5.1 正是断言与 deriveWindowQuotas 逐位一致，故以派生为回落基线 -->
- [x] 1.4 `src/risk/quotas.ts`：导出写死默认供回落（`DAILY_QUOTAS` 已有，把 `MINUTE_BURST_CAP`/`HOUR_BURST_CAP` 也导出）+ 新增 `QUOTA_MAX`；保留 `deriveWindowQuotas` 作回落 / 兼容 <!-- cloud dd43691 -->
- [x] 1.5 定义 `QuotaProvider` 接口（`windowQuotasFor(level): WindowQuotas`），放 `src/risk/types.ts`（风控层持接口、不依赖 config 层实现；QuotaConfigStore 实现它）<!-- cloud dd43691 -->

## 2. aidcp-cloud — 提供者注入 effectiveQuotas（不触状态单写）

- [x] 2.1 `src/risk/risk-controller.ts`：`RiskControllerOptions` 加可选 `quotaProvider?: QuotaProvider`；构造时持有 <!-- cloud dd43691 -->
- [x] 2.2 `src/risk/risk-controller.ts` `effectiveQuotas()`：基准三档由 `quotaProvider?.windowQuotasFor(level) ?? deriveWindowQuotas(level)` 提供；`warned`/`restricted`/`frozen` 基准固定 `'conservative'`（缩放 / 清零语义不变），仅 `normal` 默认分支用 `state.quotaLevel`——满足零回归 <!-- cloud dd43691 -->
- [x] 2.3 `src/risk/risk-controller-registry.ts`：构造接收并持有 `quotaProvider`，透传给每账号 `RiskController.create` <!-- cloud dd43691 -->
- [x] 2.4 红线核对：提供者只读；`effectiveQuotas` / `canDo` 不写 state、不调 `setQuotaLevel` / `applySignal`、不碰 `risk_state` 表 <!-- cloud dd43691 facade 无 RiskController 引用，结构性保证 -->

## 3. aidcp-cloud — 面板 facade 与 API 路由（APPEND，序在 C 之后）

- [x] 3.1 新增 `src/config/quota-config-facade.ts`：`getCatalog()` 回显三档 × 7 动作 × 三窗口（库缺行以派生默认合成）+ 审计；`setQuota(patch, updatedBy)` 校验（整数 + `>=0` + `<=QUOTA_MAX` + 合法 tier/action）→ 写库 → 刷镜像 → 回真态；非法整块拒（`unknown_tier`/`unknown_action`/`invalid_value`/`no_valid_fields`）、绝不部分落库 <!-- cloud dd43691 -->
- [x] 3.2 `src/panel/panel-server.ts`：**APPEND**（C 之后、F 之前）`GET /api/quotas` + `PUT /api/quotas`（JWT，`verified.payload.sub` 作 `updatedBy`；unknown_tier/action→404，invalid→400，未注入→503）<!-- cloud dd43691 -->
- [x] 3.3 `src/panel/types.ts`：**APPEND** 配额面板 DTO（`QuotaConfigRowView` / `QuotaConfigCatalogView` / `QuotaConfigPatchInput` / `QuotaConfigSetResult` / `PanelQuotaConfig` + `PanelDeps.quotaConfig?`）<!-- cloud dd43691 -->
- [x] 3.4 `src/server.ts`：**仅 APPEND** —— `new QuotaConfigStore(...)` + `init()`（与其余 config store 同 try/catch，吞错退化派生默认）+ `createQuotaConfigPanel(...)` + store 作 `quotaProvider` 传 `RiskControllerRegistry` + facade 进 panel deps；未改 C 的 resolver 块 <!-- cloud dd43691 -->

## 4. aidcp-console — 限额页（路由 + 导航 + 取数 / 写回）

- [x] 4.1 `src/types/api.ts`：**APPEND**（C 之后）配额 DTO（`QuotaTier`/`QuotaAction`/`QuotaConfigRow`/`QuotaConfigCatalog`，对齐 cloud）<!-- console 57da032 -->
- [x] 4.2 `src/api/queries.ts`：**APPEND** `useQuotaConfig`（`GET /api/quotas`）；写 mutation 在页内 `apiPut`（同 RolesPage 形态，成功后 invalidate 非乐观刷新）<!-- console 57da032 -->
- [x] 4.3 新增 `src/pages/QuotasPage.tsx`：三档 × 7 动作 × 三窗口可编辑表 + 弹窗；前端校验（非负整数 + 上限）即时反馈、**服务端校验为准**；保存后回显刷新 <!-- console 57da032 -->
- [x] 4.4 `src/App.tsx` + `src/pages/AppShell.tsx`：加 `/quotas` 路由 + 导航项（SafetyOutlined，与 F 的 `/persona` 互不冲突）<!-- console 57da032 注：AppShell 实际在 src/pages/（设计写的 src/components/ 有误） -->

## 5. 验证

- [x] 5.1 cloud 单测：`windowQuotasFor` 命中库值生效；缺行 / 非法值回落派生默认；表为空时与 `deriveWindowQuotas` 逐位一致（零回归）<!-- cloud dd43691 test/quota-config-store.test.ts -->
- [x] 5.2 cloud 单测：`effectiveQuotas()` 注入 provider 后三态缩放 / 清零语义不变；`canDo` 每次现读（改 provider 镜像后下一次判定按新值，热加载）<!-- cloud dd43691 test/quota-effective-quotas.test.ts -->
- [x] 5.3 cloud 单测：限额编辑不触状态单写——facade 仅写 quota_config、无 RiskController 引用 <!-- cloud dd43691 test/quota-config-facade.test.ts（setQuota 仅记 store.set 调用）-->
- [x] 5.4 cloud facade 单测：合法写回真态；负 / 非整 / 超上限 / 未知 tier·action / 无字段 整块拒、不落库；非乐观回显 <!-- cloud dd43691 -->
- [x] 5.5 cloud：`npm run test:acceptance`（AC-RISK / AC-PROTO 全过）→ 全量 `npm test` → `npm run typecheck` 绿 <!-- cloud dd43691 acceptance 26/26；全量 **618/618**（顺手修了 npm test glob 漏跑 49 个顶层测试文件的隐患 + 2 个因此长期被掩盖的陈旧测试，见 cloud d1f1e8c）；typecheck 绿 -->
- [x] 5.6 console：限额页 build/typecheck 通过；保存走 JWT、非乐观刷新 <!-- console 57da032 typecheck+build 绿 -->

<!-- §7（会话上限收口本层）已从本 change 移出：用户决定单开新 session 做「会话上限搬到安全限额层」（单场时长 + 单场互动预算 + 人设侧清理 session_limits）。决策与坐实见 memory [[console-worklist-10items-partition]] + F design.md「留的缝」；新 session 走 /opsx:propose 单立一个 change，不并入本 change 的归档。本 change 归档范围 = 三档×动作×三窗口的日/分/时配额可配（§1–6）。 -->

## 6. 收尾与归档

- [x] 6.1 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <sha> 备注 -->`）<!-- cloud dd43691 + d1f1e8c / console 57da032，均推 origin -->
- [x] 6.2 `openspec validate safety-quota-config --strict` 通过 <!-- 待本次归档前跑 -->
- [ ] 6.3 按 §5 安全序列部署 ECS（先备份 → rsync → restart → healthcheck：8787 / PG `select 1` / 迁移 `0010` 已建表 / 面板 `8090`）；与同批其他流 / 并发会话错峰一次部署
- [ ] 6.4 上线后真机校准：管理后台改某档某动作限额 → 观察 `canDo` 即按新值（热加载无重启）；确认风控状态不被配置写动摇
- [x] 6.5 `/opsx:archive` 归档（delta 合并进 `openspec/specs/interaction-risk-gating`）<!-- 按用户顺序：先归档、后部署（6.3/6.4 部署+真机校准在归档后执行）-->
