# Design — client-user-env-registry

## Context

前序 change `client-user-env-picker` 把「待分配」候选池实现为「`client_env_scope` 的 distinct env_key」。这在「至少分过一次」的前提下够用，但暴露了 bootstrap 死结：**注册表由「已分配」反推 → 无法承载未分配环境**。本 change 拆掉这个耦合。

坐实的约束（`文件:行`）：
- `client-user-store.ts` `listAllEnvironments()`：原 SQL `FROM client_env_scope s JOIN client_users u ... GROUP BY env_key` — 只出已归属环境。
- `account-store.ts:28` `accounts`：主键 = 社媒登录 userid，**无 profileId 列**，从不持久化 edge↔profile 映射 → 不能当环境全集源。
- 全库 `edge_id` 列仅 `alerts.edge_id` 一处（偶发、带 `ads-` 前缀）→ 不是完整源。
- edge 口径：`fleet.cjs:19` `envIdForProfile = ads-${profileId}`；`main.cjs:2521` attachEnv 发 `env.profileId`（**裸 id、无前缀**）；`main.cjs:310-313` 过滤 `/my-environments` 拿 `envKey` 当 `allowedProfileIds`（裸 id）。→ **env_key = 裸 profileId，不带 `ads-`**。

## Goals / Non-Goals

- **Goal**：环境能「只登记、不归属」；后台「待分配」显示未归属环境；存量环境可一次性批量入池；新环境连上即自维护入池。
- **Non-Goal**：不做 console 「批量导入」UI（一次性导入由运营/SQL 完成，非高频）；不枚举 AdsPower 全量 profile（云端无此接口，YAGNI）；不改协议、不动 accounts。

## Decisions

### D1. 独立注册表 `client_environments`（env_key 主键），而非继续从归属反推
环境全集 = `client_environments` ∪ `client_env_scope`（并集）。前者承载「已知但未分配」，后者承载「已分配」（含历史 attachEnv 落的、注册表尚无的）。并集保证两类都不漏。
- 备选（否决）：给某「占位端用户」挂全部未分配环境 → 污染租户模型、占位号可能是真登录，红线风险。独立表干净。

### D2. `registerEnvironments()` 幂等 upsert，冲突用 COALESCE 只补非空
`ON CONFLICT (env_key) DO UPDATE SET label=COALESCE(EXCLUDED.label, 原值), platform=COALESCE(...)` —— 自动登记（auto，昵称可能缺）不拿 null 覆盖导入（import）时的好名字；`source` 只在首次插入定、冲突不降级。**只登记不归属**：绝不写 `client_env_scope`，fail-closed 归属边界不破。

### D3. 自动登记挂 `onEdgeRegistered`（server.ts:1518）
握手注册完成即 `registerEnvironments([{envKey: edgeId 去 ads-, label: accountNickname, platform}], 'auto')`。仅 `ads-` 前缀的真实分身登记；`self-`/`host-` 兜底 edge 跳过（非可分配环境）。失败只 warn、不阻断握手（best-effort，池新鲜度非关键路径）。

### D4. 并集读的聚合正确性
`WITH keys AS (注册表 UNION 归属表) ... LEFT JOIN 三表 GROUP BY env_key`：`client_environments e` 对 env_key 1:1 不放大 assignees；`json_agg(...) FILTER (WHERE u.user_id IS NOT NULL)` 使未归属环境 assignees 空 → assigneeCount 0；label/platform `COALESCE(归属最新非空, max(注册表值))`。缺表（首启竞态）fail-closed 回落空数组。

### D5. N2 边界不变
`listAllEnvironments` 是跨用户聚合，**只准接内部 JWT 的 panel 端点**（`GET /api/client-environments`），绝不注入 client-auth-server。客户可达读仍只有吃 userId 的 `listEnvScope`。

## Risks

- **env_key 前缀写错** → 客户端按 `allowedProfileIds` 过滤一个都不匹配（fail-closed，看不到环境）。缓解：导入 / 自动登记均用裸 id（去 `ads-`），与 edge attach/过滤口径逐字一致；真机核。
- **敏感值泄漏**：AdsPower 导出含 Cookie/账号密码/2FA。缓解：导入**只取 env_key/名字/平台**，凭据一律不入库、不落文件（项目红线）。
- **真 SQL 聚合桩验不了**：store 测试是手写假 pool。缓解：dev 真库直查已核（11 导入 assigneeCount 全 0、已归属 k1ejvb06 并入 count 1）；真机 GUI 核归入 backlog。
