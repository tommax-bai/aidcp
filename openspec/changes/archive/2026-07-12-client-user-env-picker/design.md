# Design: client-user-env-picker

## 现状（带文件:行）

- 归属存储 `aidcp-cloud/src/client-auth/client-user-store.ts`：表 `client_env_scope` 主键 `(user_id, env_key)`（`client-user-store.ts:44`），`env_key` 有独立索引（`:46`）但**非唯一** → 同一 `env_key` 可挂到多个 `user_id`，一环境多分**数据层早已支持**。
- `env_key = profileId`（AdsPower 分身 id）。edge 自动归属实锤：`aidcp-edge/src/electron/main.cjs:2521` 上报 `{ envKey: env.profileId, label: env.name, platform: env.platform }`。
- 管理侧读法只有 `getScope(userId)`（`client-user-store.ts:306`，= 吃 userId 的 scoped `listEnvScope`）；**没有跨用户的全局环境视图**。
- panel 端点 `aidcp-cloud/src/panel/panel-server.ts:359-475`：GET 列客户 / POST 建 / PATCH / rotate-key / GET/PUT scope，全部受**内部** JWT。
- console 抽屉 `aidcp-console/src/pages/ClientUsersPage.tsx:482-638`：手填 `envKey` + label + platform 逐条 `addRow`，保存 = 整批替换（`useSetClientUserScope` → PUT scope）。

## 关键决策

### D1. 候选池来源 = `client_env_scope` 的 distinct env_key（不引 accounts、不引在线边端）

**理由**：环境是 AdsPower 分身，活在客户机上，云端只在「客户登录态自动归属」或「后台手动归属」时才知道某 env_key 存在——两条都落 `client_env_scope`。`accounts` 表按 `accountId`（社媒登录后才有）键、无 profileId 字段（`panel-store.ts:29` `PanelAccount` 无 profileId），**不是干净的 env_key 源**；在线边端的 `edgeId=ads-<profileId>` 是瞬态、不 durable。故候选池 = `SELECT DISTINCT env_key FROM client_env_scope`，即「系统已知的全部环境」。云端从未见过的新环境仍可用**手填兜底**登记（保留现有 addRow 输入）。

按 YAGNI 不做「全平台 AdsPower 分身枚举」：那需要边端主动上报全量花名册 + 云端持久注册表，超出本次诉求；候选池覆盖「任一客户带进来过的环境」已满足运营重分配场景。

### D2. 新读法只接内部面板端点，绝不接客户鉴权服务（守 N2）

`listAllEnvironments()` 是**跨用户聚合**（返回每个 env 的客户清单），与 N2「客户可达读只有吃 userId 的 scoped 方法」直接冲突——**必须只在受内部 JWT 的 panel 端点消费，绝不注入 client-auth-server**。红线注释写死在方法与端点上。客户令牌到不了 panel（另一密钥、验签即 bad_signature），故不泄漏。

### D3. 待分配 / 已分配 = 相对**当前端用户**的成员关系（不是全局分配态）

抽屉是「给当前这个端用户配环境」的场景，故筛选语义相对当前用户最直觉：
- **待分配**：候选池里 `env_key ∉ 当前用户当前归属集`（可加入）——默认视图。
- **已分配**：`env_key ∈ 当前用户当前归属集`。

「多人」标识是**全局**属性（该 env 被 ≥2 个客户归属），与筛选正交：待分配视图里的 env 若已属于别的客户，照样打「多人」（悬浮列出客户名），让运营看清共享面。筛选按**打开抽屉时的服务端归属快照**判定，编辑草稿（勾选/移除）不改变行的所属分区，避免行编辑中途消失。

### D4. 保存仍走既有整批替换（PUT scope），只动当前用户的行

一环境多分不需要新写路径：`setScope` 只 `DELETE ... WHERE user_id=$1` 再插当前用户的集合（`client-user-store.ts:328`），天然不碰别的用户的归属行——加入一个「已属于别人」的 env 只是给当前用户多插一行，别人的行不动。故多分安全、无需改 `setScope`。

## 契约

### cloud 新增
- store：`listAllEnvironments(): Promise<ClientEnvironmentView[]>`，`ClientEnvironmentView = { envKey, label, platform, assignees: {userId,name}[], assigneeCount }`。缺表 fail-closed 空数组。SQL 按 env_key GROUP BY，label/platform 取任一非空代表值，assignees 由 `client_users` join 得名。
- panel：`GET /api/client-environments`（内部 JWT）→ `{ environments: ClientEnvironmentView[] }`；未注入 `clientUsers` → 503。

### console 新增/改
- 类型 `ClientEnvironmentView` + `ClientEnvAssignee`；查询 `useClientEnvironments()`（GET /api/client-environments）。
- 抽屉：段控筛选「待分配 / 已分配」（默认待分配）+ 勾选加入 + 「多人」Tag（Tooltip 列客户名）+ 保留手填兜底。
- 显示名「客户端用户」→「端用户」（导航 + 卡片标题 + QueryError 文案）。

## 失败模式与对策
- **N2 回归**（把全局读接进客户服务）：只在 panel 端点消费，方法/端点注释红线 + 保留客户侧 13 用例隔离断言。
- **多分误伤别人的行**：`setScope` 只动当前 user_id；加断言「给 A 加入 B 已有的 env 后，B 的归属集不变」。
- **筛选中途行消失**：分区按打开时快照判定，不随草稿变。
- **缺表首启**：`listAllEnvironments` 缺表回落空数组，页面空态而非白屏。
