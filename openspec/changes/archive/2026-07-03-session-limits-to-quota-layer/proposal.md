## Why

「单场会话上限」回答的是「这账号一场能做多少、多猛才安全」——本质是**限额 / 风控**，不是「这账号是谁」（人设）。但现状里它被错放在人设与写死常量两处：单场时长来自 `soul.session_limits.max_duration_min`（人设，默认 10min），单场互动预算来自 `RoleDispatcher.freshBudget()`（写死常量，三档无关）。人设侧 `max_likes` / `max_searches` / `max_collects` / `cooldown` 更是**解析了却运行时无处读取的死配置**——运营在 `/persona` 页「能改却无效」，是误导。

需求（用户 2026-06-24 拍板）：把单场时长 + 单场互动预算从人设 / 写死常量搬进**安全限额层**（与 change `safety-quota-config` 同源治理：管理后台可改 + 热加载 + 绝不 brick），并把 `session_limits` 从人设里清理掉。配置维度 = **按账号**（沿用单场时长现有的按账号语义），缺配置时**逐位回落当前真生效值（严格零回归）**。

## What Changes

- **cloud**：新增按账号的单场会话上限配置存储（迁移 `0015_session_config.sql`，表 `session_config`，主键 `account_id`），持有可编辑的**单场时长**（`max_duration_min`）与**单场互动预算**（`likes` / `collects` / `follows` / `searches` / `comments` / `comment_likes` 六项，对齐现 `freshBudget()` 形态）。复刻 `safety-quota-config` 的存储时序：先写库成功再刷内存镜像；缺行 / 非法值回落写死默认。
- **cloud**：定义按账号的单场上限提供者（同步读内存镜像）：`sessionDurationMsFor(accountId)` / `sessionBudgetFor(accountId)`，注入浏览闭环调度器与会话监测体。
- **cloud**：单场时长接管——浏览闭环的时长解析与会话监测体的到点判定改为按当前账号读提供者（保留**惰性热加载**形态：每次现读，后台改完即生效、无需重启），缺值回落写死默认 10min。
- **cloud**：单场互动预算接管——`freshBudget()` 改为按当前账号从提供者读，保留会话启动 / 重置时的 reset 语义与「已发生计数 = 初始预算 − 当前剩余」的比率闸来源一致性。
- **cloud**：面板 API 层新增 JWT 守卫的 `GET /api/session-limits`（回显当前生效值 + 审计字段，库缺行以写死默认合成）与 `PUT /api/session-limits`（**非乐观写**：先校验、写库成功才回显真态；任一字段非法整块拒、绝不部分落库 / 假成功）。
- **cloud（人设清理，BREAKING 配置面）**：从人设移除 `session_limits`——`src/soul/types.ts` 去字段、`src/soul/loader.ts` 去 `parseSessionLimits`、`src/soul/soul.yaml` 删该段。**前置条件**：现役仅 `max_duration_min` 一处被读，须全部改读新提供者、`grep` 确认无残留 `session_limits` 读取后才删（这是唯一有「删了会 brick」风险的一步）。
- **console**：`/quotas` 页新增「单场上限」编辑区（按账号：时长 + 六项互动预算），非乐观写；`/persona` 页若展示 / 可编辑 `session_limits` 则隐藏（去掉「能改却无效」字段）。
- **不动协议**：单场会话上限是云端内部配置，不经 WebSocket 协议 v2；不动两份 `protocol.ts` / `command-bridge.ts` / `docs/protocol.md`。
- **不动风控状态单写路径**：`setQuotaLevel` / `applySignal` / 状态机 / `risk_state` 表均不改；新配置只读、只写自己的表。

## Capabilities

### New Capabilities
<!-- 无新增 capability；单场会话上限属安全限额治理，delta 并入既有 interaction-risk-gating -->

### Modified Capabilities
- `interaction-risk-gating`: 新增三条要求——(1)「单场会话上限（时长 + 互动预算）可配置、管理后台按账号可改、运行时每次现读（热加载）、缺行 / 非法值绝不 brick 回落写死默认、空表逐位零回归」；(2)「单场上限的存储与编辑绝不触碰风控状态单写路径」；(3)「单场上限不再来自人设——`session_limits` 从人设移除，运行时唯一来源是安全限额层提供者（缺值回落写死默认）」。

## Impact

- **cloud（aidcp-cloud）**：
  - 新增 `migrations/0015_session_config.sql`（表 `session_config`，主键 `account_id`）。
  - 新增 `src/config/session-config-store.ts`（`SessionConfigStore`，复刻 `quota-config-store.ts` 时序与回落不变量；实现按账号提供者接口）。
  - 新增 `src/config/session-config-facade.ts`（面板取数 / 校验 / 写回，复刻 `quota-config-facade.ts`）。
  - `src/orchestrator/role-dispatcher.ts`：`maxDurationMs()` 与 `freshBudget()` 改读注入的提供者（按 `currentAccountId`），保留 reset / 比率闸语义；构造期加可选提供者依赖。
  - `src/agents/session-monitor-role.ts`：`effectiveMaxDurationMs()` 改经调度器统一解析口（或注入的提供者）按账号读，去掉对 `soul.session_limits` 的直接读取。
  - `src/risk/session-budget.ts`：`SESSION_LIMITS` 写死值可作为回落参考来源（v1 兼容路径不动），但本 change 的运行时回落基线 = **当前真生效值**（时长 10min + 现 `freshBudget` 数字），新增导出写死默认常量供回落与校验上限（`SESSION_LIMIT_MAX`）。
  - `src/soul/types.ts` / `src/soul/loader.ts` / `src/soul/soul.yaml`：移除 `session_limits`（迁走全部读点后）。
  - `src/server.ts`：**仅 APPEND** session config store init + facade 装配 + 注入调度器 + panel 依赖（与其余 config store 同 try/catch，吞错退化写死默认）。
  - `src/panel/panel-server.ts` / `src/panel/types.ts`：**APPEND** `/api/session-limits` GET/PUT 路由 + 面板 DTO。
- **console（aidcp-console）**：
  - `src/types/api.ts` / `src/api/queries.ts`：**APPEND** 单场上限 DTO + 取数 / 写回 hook。
  - `src/pages/QuotasPage.tsx`：加「单场上限」编辑区（按账号：时长 + 六项预算）。
  - `src/pages/PersonaPage.tsx`（或等价）：隐藏 `session_limits` 字段。
- **协议 / docs**：无改动（不触协议红线）。
- **迁移号**：取 `0015`（现有最高 `0014_publish_post_url`；`0012` 仍预留 stream B `account-real-nickname`；动前 `ls ../aidcp-cloud/migrations/` 复核）。
- **红线 / 保留**：风控状态单写（`setQuotaLevel` / `applySignal` / `risk_state`）不动；缺行 / 非法值绝不 brick；空表逐位零回归；删 `session_limits` 前确认无残留读点。
