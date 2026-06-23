## Why

安全限额（每账号每动作的滑动窗配额）是风控闸 `RiskController.canDo(action)` 的核心阈值，但当前数字全是写死常量：`aidcp-cloud/src/risk/quotas.ts` 里的 `DAILY_QUOTAS`（三档 conservative / normal / aggressive 的每日上限）、`MINUTE_BURST_CAP`、`HOUR_BURST_CAP`。要调一个限额（如把 `comment_like` 每日 6 调成 4）必须改代码、重新部署。运营无法在管理后台按真机表现实时收紧 / 放宽限额。

需求（用户已拍板）：把安全限额**数字**做成管理后台可改，且**每日数字与分钟 / 小时突发上限都可改**（不再让突发上限从每日值派生）。要求复刻角色配置（`console-role-model-config`）的成熟范式——配置落库、热加载（改完无需重启）、绝不 brick（缺行 / 非法值回落写死默认）。

红线（必须守住）：风控**终态**（`normal→warned→restricted→frozen` 与档位 `quotaLevel`）是云端单写路径（`RiskController` 经 `setQuotaLevel` / `applySignal` → `PgRiskStore` 落库）。本 change 只改**配额数字这一份配置读取**，**绝不**让数字编辑走 `setQuotaLevel` / `applySignal`（那是状态单写通道，会污染风控状态机）。

## What Changes

- **cloud**：新增配额配置存储 `QuotaConfigStore`（迁移 `0010_quota_config.sql`，表 `quota_config`），按 `(tier, action)` 持有可编辑的 `daily` / `per_minute` / `per_hour` 三个数字。复刻 `RoleConfigStore` 时序：先写库成功再刷内存镜像；缺行 / 非法值回落写死默认（`quotas.ts` 的 `DAILY_QUOTAS` / `MINUTE_BURST_CAP` / `HOUR_BURST_CAP`）。
- **cloud**：把一个**配额提供者**（quota provider，同步读内存镜像）注入 `RiskController`（经 `RiskControllerOptions` → `RiskControllerRegistry` 透传到每账号 controller）。`effectiveQuotas()` 改为**每次** `canDo` 经提供者读取**当前生效数字**（命中即热加载、无需重启）；提供者缺失 / 缺值时回落 `quotas.ts` 写死默认。`warned`/`restricted`/`frozen` 的缩放 / 清零语义不变，只是基准三档数字来自提供者。
- **cloud**：突发上限不再从每日值派生——`quota_config` 直接持有 `per_minute` / `per_hour`，提供者按 `(tier, action)` 直接给出三窗口数字（写死默认仍用 `quotas.ts` 的 `MINUTE_BURST_CAP` / `HOUR_BURST_CAP` 兜底）。
- **cloud**：面板 API 层新增 JWT 守卫的 `GET /api/quotas`（回显当前生效三档 × 全动作 × 三窗口 + 审计字段）与 `PUT /api/quotas`（**非乐观写**：先校验、写库成功才回显真态；任一字段非法整块拒、绝不落库假成功）。校验 = 有限非负整数 + 合理上限（防误填天文数字）。
- **console**：新增 `/quotas` 页面（路由 + 导航），三档 × 全动作 × 三窗口的可编辑表格，保存前校验、保存后用服务端回显刷新（非乐观）。
- **不动协议**：配额是云端内部配置，**不经 WebSocket 协议 v2**；不动 `protocol.ts` / `command-bridge.ts` / `docs/protocol.md`（协议红线归 stream B 独占）。
- **不动风控状态单写路径**：`setQuotaLevel` / `applySignal` / 状态机 / `risk_state` 表均不改。

## Capabilities

### New Capabilities
<!-- 无新增 capability；delta 落在既有 interaction-risk-gating -->

### Modified Capabilities
- `interaction-risk-gating`: 新增三条要求——(1)「安全限额数字可配置、管理后台按档位可改（每日 + 分钟 / 小时突发）、`canDo` 每次读最新、缺行 / 非法值绝不 brick 回落写死默认」；(2)「限额数字编辑绝不触碰风控状态单写路径」；(3)「管理后台限额页 + JWT 守卫的非乐观写」。

## Impact

- **cloud（aidcp-cloud）**：
  - 新增 `migrations/0010_quota_config.sql`（表 `quota_config`）。
  - 新增 `src/config/quota-config-store.ts`（`QuotaConfigStore`，复刻 `role-config-store.ts` 时序与回落不变量）。
  - 新增 `src/config/quota-config-facade.ts`（面板取数 / 写回 + 校验，复刻 `role-config-facade.ts`）。
  - `src/risk/risk-controller.ts`：`RiskControllerOptions` 加可选 quota provider；`effectiveQuotas()` 经提供者读三窗口数字（回落写死默认）。
  - `src/risk/risk-controller-registry.ts`：构造每账号 controller 时透传 provider。
  - `src/risk/quotas.ts`：导出写死默认供回落（`DAILY_QUOTAS` / `MINUTE_BURST_CAP` / `HOUR_BURST_CAP` 已有），新增「按 provider 数字组装 `WindowQuotas`」的纯函数；保留 `deriveWindowQuotas` 供回落 / 兼容。
  - `src/server.ts`：**仅 APPEND** quota store init + facade 装配 + 注入 registry + panel 依赖（**绝不**改 stream C 的 `resolveModelForRole` / `resolveTempForRole` resolver 块）。
  - `src/panel/panel-server.ts`：APPEND `/api/quotas` GET/PUT 路由（保留序 C→D→F→B，本 change 为 D，在 C 之后）。
  - `src/panel/types.ts`：APPEND 配额面板 DTO（保留序 C→D→F→B）。
- **console（aidcp-console）**：
  - `src/types/api.ts`：APPEND 配额 DTO（保留序 C→D→F→B）。
  - `src/api/queries.ts`：APPEND `useQuotaConfig` / `useUpdateQuotaConfig`（保留序 C→D→F→B）。
  - 新增 `src/pages/QuotasPage.tsx`（限额编辑表格）。
  - `src/App.tsx` + `src/components/AppShell.tsx`（或等价导航壳）：加 `/quotas` 路由 + 导航项（D 加 `/quotas`，F 加 `/persona`，互不冲突）。
- **协议 / docs**：无改动（不触协议红线）。
- **迁移号**：预留 `0010`（C=0009 / D=0010 / F=0011 / B=0012；本 change 为 D）。
- **红线 / 保留**：风控状态单写（`setQuotaLevel` / `applySignal` / `risk_state`）不动；缺行 / 非法值绝不 brick；`canDo` 拒绝路径与「被拒不假成功 / 不扣 budget」语义不变。
