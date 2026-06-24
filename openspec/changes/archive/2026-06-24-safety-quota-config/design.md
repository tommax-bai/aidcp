# Design — safety-quota-config

把安全限额数字做成管理后台可改，复刻角色配置范式（落库 + 热加载 + 绝不 brick），并守住「风控状态单写」红线：本 change 只是 `RiskController` 侧的**配置读取**，不经状态机、不经协议。

## 1. 现状坐实（文件:行）

- `aidcp-cloud/src/risk/quotas.ts:3` `DAILY_QUOTAS`（三档 × 7 动作的每日上限，写死）；`:33` `MINUTE_BURST_CAP`、`:43` `HOUR_BURST_CAP`（写死）。
- `aidcp-cloud/src/risk/quotas.ts:53` `deriveWindowQuotas(level)`：当前**从每日值派生**分钟（`ceil(daily/20)` 夹 `MINUTE_BURST_CAP`）/ 小时（`ceil(daily/4)` 夹 `HOUR_BURST_CAP`），三窗口打包成 `WindowQuotas`。
- `aidcp-cloud/src/risk/risk-controller.ts:62` `explain()` 每次取 `this.effectiveQuotas()`，逐窗口比对计数；`:125` `effectiveQuotas()`：`warned`→`scaleWindowQuotas(derive('conservative'),0.7)`、`restricted`→`zeroInteractionQuotas(derive('conservative'))`、`frozen`→`scale(...,0)`、其余→`deriveWindowQuotas(state.quotaLevel)`。
- 状态单写：`risk-controller.ts:105` `applySignal`、`:117` `setQuotaLevel` 经 `enqueue` 串行链 + `store.saveState`（`risk_state` 表）。**这条路径本 change 不碰。**
- 构造：`risk-controller-registry.ts:23` 每账号 `RiskController.create({ accountId, store, clock })`；`server.ts:321` `new RiskControllerRegistry(riskStore)`。
- 范式参照：`src/config/role-config-store.ts`（先写库成功再刷镜像、缺值回落 null、`getForRole` 同步读、`set` 非乐观回真态）；`role-config-facade.ts`（面板取数 / 校验 / 写回）；`panel-server.ts:366/374` `/api/roles` GET/PUT（JWT `verifyJwt` → `verified.payload.sub` 作 `updatedBy`）；`server.ts:674` `createRoleConfigPanel` 装配 + `:751` 注入 panel 依赖。

痛点：调任一限额数字都要改代码 + 重新部署，运营无法按真机表现实时收紧 / 放宽。

## 2. quota_config 表结构（迁移 0010）

按 `(tier, action)` 一行，三窗口三列。建表幂等（`CREATE TABLE IF NOT EXISTS`，与 store 内 `QUOTA_CONFIG_SCHEMA_SQL` 同源，复刻 `role_config` 做法）：

```sql
CREATE TABLE IF NOT EXISTS quota_config (
  tier        TEXT NOT NULL,   -- 'conservative' | 'normal' | 'aggressive'
  action      TEXT NOT NULL,   -- view|like|collect|comment|follow|publish|comment_like
  daily       INTEGER NOT NULL,
  per_minute  INTEGER NOT NULL,
  per_hour    INTEGER NOT NULL,
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_by  TEXT,
  PRIMARY KEY (tier, action)
);
```

设计取舍：
- **每行三窗口都存**（`daily` / `per_minute` / `per_hour`），落实用户「突发上限也可改、不再派生」的决定。`deriveWindowQuotas` 的派生只作为**写死回落**时的兜底，不再是生效主路径。
- 表初始**可空**（不预填行）：缺行即回落 `quotas.ts` 写死默认 → 全新部署、迁移刚跑完都安全。面板首屏 GET 用「库值 ?? 写死默认」合成回显，运营看到的就是当前真生效值。
- 不存账号维度：限额按**档位**（tier）配置，沿用现有「三档 × 动作」模型，与 stream C 的 nullable `account_id` 评估缝**正交**（本 change 不引入 account 维度，避免与 C 抢 seam）。

## 3. 提供者注入 effectiveQuotas（热加载，不触状态单写）

新增同步只读提供者接口（内存镜像，`canDo` 每次调，零 IO）：

```ts
// 返回某档位某动作的三窗口生效数字；缺值由 store 内部回落写死默认，永不抛
export interface QuotaProvider {
  windowQuotasFor(level: RiskQuotaLevel): WindowQuotas;
}
```

- `QuotaConfigStore` 实现 `windowQuotasFor(level)`：对 7 个动作各取 `(level, action)` 的内存镜像行 → 组装 `{ minute: {…per_minute}, hour: {…per_hour}, day: {…daily} }`；任一动作缺行 / 非法 → 该动作回落 `DAILY_QUOTAS[level][action]` / `MINUTE_BURST_CAP[action]` / `HOUR_BURST_CAP[action]`。
- 注入路径：`RiskControllerOptions` 加可选 `quotaProvider?: QuotaProvider` → `RiskControllerRegistry` 构造时持有并透传给每账号 `RiskController.create`。
- `effectiveQuotas()` 改写：基准三档不再直接 `deriveWindowQuotas(level)`，而是 `provider?.windowQuotasFor(level) ?? deriveWindowQuotas(level)`；`warned`/`restricted`/`frozen` 仍对**基准**套 `scaleWindowQuotas` / `zeroInteractionQuotas`（缩放语义不变，只是基准数字来自 provider）。**关键**：现状这三态的基准是写死实参 `deriveWindowQuotas('conservative')`（见 `risk-controller.ts:126-128`，**非** `state.quotaLevel`），改造后必须 `provider?.windowQuotasFor('conservative') ?? deriveWindowQuotas('conservative')`（实参固定 `'conservative'`）；只有 `normal` 默认分支用 `level = state.quotaLevel`。错把三态基准改成 `level` 会违反「表为空逐位一致」零回归。
- **热加载**：`canDo`→`explain`→`effectiveQuotas` 每次现读内存镜像，`PUT /api/quotas` 写库成功即刷镜像 → 下一次 `canDo` 立即看到新数字，无需重启。
- **红线**：provider 只读、不写、不碰 `state` / `quotaLevel` / `applySignal` / `setQuotaLevel`。配额数字编辑只动 `quota_config` 表，**绝不**经状态单写串行链。

## 4. 校验（非乐观写）

`QuotaConfigFacade.setQuota` 在写库前校验每个数字：
- `Number.isInteger(n)` 且 `n >= 0`（有限非负整数；0 合法 = 该动作该窗口禁止）。
- `n <= QUOTA_MAX`（合理上限，如 `100000`，防误填天文数字击穿滑动窗比较）。
- `tier ∈ RISK_QUOTA_LEVELS`、`action ∈ RISK_ACTIONS`，否则 `unknown_tier` / `unknown_action`。
- 任一字段非法 → 整块 400 拒、**绝不部分落库、绝不假成功**（复刻 role facade 的 `unknown_role`→404 / 其余→400 范式）。
- 写库成功后 store 刷镜像、facade 回显**服务端真态**（含 `updated_at` / `updated_by`），console 用回显刷新（非乐观，不本地假设成功）。

## 5. 绝不 brick 的回落链

三层兜底，任一层失败都退到下一层、永不抛、永不让风控失效：
1. provider 缺失（`RiskControllerOptions` 没注入）→ `effectiveQuotas` 用 `deriveWindowQuotas` 写死默认（与当前行为完全一致，零回归）。
2. provider 在、但某 `(tier, action)` 缺行 / 字段非法 → 该动作回落 `quotas.ts` 写死默认。
3. store `init`（建表 / load 镜像）失败 → 装配处吞错、不注入 provider（退化到第 1 层），云端照常起、风控照常用写死默认。

零回归保证：迁移刚跑完表为空时，行为与现状逐位一致。

## 6. 面板 API + console 页

- `GET /api/quotas`（JWT）：回显 `tier → action → { daily, perMinute, perHour, updatedAt, updatedBy }`，库缺行处用写死默认合成（运营看到的即当前真生效）。
- `PUT /api/quotas`（JWT，`verified.payload.sub` 作 `updatedBy`）：体携带要改的 `(tier, action, daily?, perMinute?, perHour?)`；校验通过写库 + 刷镜像 + 回显真态；否则 400 整块拒。
- console `/quotas` 页：三档 tab / 分组 × 7 动作 × 三窗口的可编辑表格；保存前前端同样校验（非负整数 + 上限）给即时反馈，但**服务端校验为准**；保存后用 `useUpdateQuotaConfig` 的回显刷新缓存。

## 7. 协调与延后缝（deferred seams）

- **不触协议**：限额是云端内部配置，不经 WebSocket v2。`protocol.ts` / `command-bridge.ts` / `docs/protocol.md` / `edge-client.ts` onMessage 白名单一律不动（协议红线归 stream B）。
- **server.ts**：只 APPEND（quota store init + facade + 注入 registry + panel 依赖）；stream C 的 resolver 块（`resolveModelForRole` / `resolveTempForRole`）先落、本 change 不碰。
- **共享链路按保留序 APPEND（C→D→F→B）**：`panel-server.ts` 路由链、`panel/types.ts`、console `types/api.ts`、`queries.ts` 一律追加在 C 之后、不与 F/B 抢同一处。
- **账号维度延后**：本 change 限额按档位、不按账号。stream C 拥有 nullable `account_id` 评估缝；若将来要「按账号覆盖限额」，可在 `quota_config` 加可空 `account_id` 列 + 提供者先查账号行回落档位行——本 change 留干净缝、不预实现（YAGNI）。
- **`tempo` 降速旋钮**（CLAUDE.md §2 已知缺口）与本 change 正交，不在范围内。
