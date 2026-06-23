> **并行协调（5 流并发，本流 = F account-persona-config，worklist item 8）**：
> - **迁移号**：cloud **0011** 为本流预留（C=0009 role-model-category-config / D=0010 safety-quota-config / F=0011 本流 / B=0012 account-real-nickname）。勿占他号。
> - **server.ts 所有权**：stream C **独占** model-resolver 块（`resolveModelForRole` / `resolveTempForRole` + 共享 LLM 客户端装配）且**先落地**；本流（F）**只 APPEND** store-init / facade 装配 / `getSoul()` 注入，**绝不改 C 的 resolver 块**。
> - **协议红线**：stream B **独占** 两份 `protocol.ts` + `command-bridge.ts` + `docs/protocol.md`（+ edge `edge-client.ts` onMessage 白名单）。本流**不碰协议**——人设不经边-云协议下发。
> - **共享 chokepoint 文件按 C→D→F→B 顺序 APPEND**：cloud `src/panel/panel-server.ts` 路由链、`src/panel/types.ts`；console `src/types/api.ts`、`src/api/queries.ts`。本流在 C、D 之后、B 之前追加自己的条目，**不改他流条目**。
> - **console 路由 / 导航**：D 加 `/quotas`，本流（F）加 `/persona`（`App.tsx` + `AppShell.tsx`）。
> - **account-store.ts 与 B 共享**：B 加昵称列、F 激活 `persona_ref` 语义——**加性改动、需协调**，不互删字段。
> - **role-dispatcher.ts 的 soul 访问改造由本流独占**（其他流勿动 soul 取值口）。

## 1. aidcp-cloud — 人设存储与校验（复刻 role-config 先例）

- [ ] 1.1 新建迁移 `migrations/0011_persona_config.sql`：`persona_config(account_id TEXT PK REFERENCES accounts(account_id) ON DELETE CASCADE, persona TEXT NOT NULL, updated_at, updated_by)`（与 store 内 `CREATE TABLE IF NOT EXISTS` 同源、幂等）
- [ ] 1.2 新建 `src/config/persona-store.ts`：复刻 `role-config-store.ts` —— 落库 + 内存镜像；`getForAccount(accountId)`（缺行 / 空一律回落语义、永不抛）；`getAll()`（面板列表）；`set(accountId, personaText, updatedBy)`（**写库成功才刷镜像**，返回写后真态含审计字段）；`init()` 建表 + reload
- [ ] 1.3 新建 `src/config/persona-facade.ts`：复刻 `role-config-facade.ts` —— `setPersona` 先用 `loadSoulFromValue`（来自 `src/soul/loader.ts`）校验，**校验不过返回 `{ ok:false, reason:'persona_invalid' }`、不落库、不刷镜像、不假成功**；空人设视作清除覆盖（回落）；`getCatalog` 列账号 + 各自当前生效人设 + 来源（覆盖 / 回落）+ 审计字段
- [ ] 1.4 复用 `src/soul/loader.ts` 的 `loadSoul()` 作为打包默认回落（进程内缓存一份）；新增按账号解析人设的纯函数 `resolvePersona(accountId)`：命中镜像且可解析 → 用之；否则回落打包默认；解析失败记 warn 并回落（永不抛）

## 2. aidcp-cloud — 热加载取值口（替换启动快照，本流独占 role-dispatcher soul 改造）

- [ ] 2.1 `src/agents/base-role.ts`：把 `protected readonly soul: Soul` 快照字段改为 `protected get soul(): Soul`，内部调用注入的 `getSoul()` 取值口；构造参数由 `soul: Soul` 改为 `getSoul: () => Soul`（约 11 个 agent 读 `this.soul.xxx` 的写法**一字不改**，getter 透明替换，零回归）
- [ ] 2.2 `src/orchestrator/role-dispatcher.ts`：`commonOptions` 由 `soul: this.soul` 快照改为 `getSoul: () => resolvePersona(currentAccountId)`（派发时解析当前账号人设）；`session_limits` 等启动期读取改为按当前账号解析（默认 `default`，留 `getSoul(accountId?)` 形参缝）
- [ ] 2.3 发布侧 `PublishScheduler`：构造由 `soul` 单例改为注入 `getSoul()`，在 `generateInput` 时取当前账号人设传给发布角色（与浏览侧共用同一解析结果）

## 3. aidcp-cloud — server.ts / 面板装配（只 APPEND，C→D→F→B 顺序）

- [ ] 3.1 `src/server.ts`：**APPEND**（不改 C 的 model-resolver 块）—— 装配 `PersonaStore`（`init()` 建表 + reload；PG 不可用则不建、人设全程回落打包默认、不 brick）+ `PersonaFacade`，把 `resolvePersona` / `getSoul` 注入 `RoleDispatcher` 与 `PublishScheduler`
- [ ] 3.2 `src/panel/panel-server.ts`：按 C→D→F→B 顺序**追加**人设路由 `GET /api/persona`、`GET /api/persona/:accountId`、`PUT /api/persona/:accountId`（受现有 JWT 守护；`PUT` 经 facade、写非乐观回真态、`persona_invalid` 诚实拒绝）
- [ ] 3.3 `src/panel/types.ts`：按序**追加**人设面板类型（账号人设视图 / 写结果 / `reason` 联合含 `persona_invalid`），不改他流类型
- [ ] 3.4 `src/account-store.ts`：与 stream B 协调，激活 `persona_ref` 语义（标记账号是否有自定义人设）——**加性**，不删 B 的昵称字段

## 4. aidcp-console — 人设页（路由 + 导航 + 非乐观写）

- [ ] 4.1 `src/types/api.ts`：按 C→D→F→B 顺序**追加**人设相关类型（与 cloud `panel/types.ts` 对齐），不改他流条目
- [ ] 4.2 `src/api/queries.ts`：按序**追加** `GET /api/persona`、`GET /api/persona/:accountId`、`PUT /api/persona/:accountId` 的查询 / mutation（JWT 经现有拦截器）
- [ ] 4.3 新建 `src/pages/PersonaPage.tsx`：列账号、按账号编辑其人设、回显当前生效值与来源（覆盖 / 回落）；保存**非乐观**（round-trip 后据服务端真态重渲染）；诚实文案（已保存 / 人设格式无效无法保存）
- [ ] 4.4 `src/App.tsx` + `src/components/AppShell.tsx`：加 `/persona` 路由与导航项（与 D 的 `/quotas` 协调，不互删）

## 5. 验证

- [ ] 5.1 cloud 单测：`PersonaStore` 写库成功才刷镜像、缺行 / 空回落、`getForAccount` 永不抛
- [ ] 5.2 cloud 单测：`PersonaFacade.setPersona` —— 非法人设 `persona_invalid` 不落库 / 不刷镜像 / 不假成功；合法人设落库回真态；空人设视作清除覆盖
- [ ] 5.3 cloud 单测：`resolvePersona` 回落链（命中 → 回落打包默认 → 解析失败回落），取值口永不抛
- [ ] 5.4 cloud 单测：`base-role` getter 透明替换字段（agent `this.soul` 读法不变）；热加载——写人设后 `getSoul()` 返回新值，无需重启
- [ ] 5.5 cloud `npm run typecheck` 绿（重点：base-role 构造签名变更后约 11 个 agent 仍编译过）；`npm run test:acceptance`（AC-PROTO 两端不漂移——本流未碰协议应保持）→ `npm test` 全量
- [ ] 5.6 console `npm run typecheck` + `npm run build` 绿；`/persona` 页加载、列账号、编辑保存非乐观、非法人设诚实报错

## 6. 收尾与归档

- [ ] 6.1 按 sub-repo 分节回写本 tasks.md 进度（`<!-- <repo> <commit-sha> 备注 -->`）
- [ ] 6.2 `openspec validate account-persona-config --strict` 通过
- [ ] 6.3 cloud 改动按 §5 安全序列部署 ECS（先备份 → rsync → restart → healthcheck：迁移 0011 已应用 / `persona_config` 建表 / FK 到 accounts / PG `select 1`）；migration 0011 与 C0009 / D0010 / B0012 不冲突
- [ ] 6.4 上线后真机校准：后台改 `default` 人设 → 浏览 / 发布角色即时改用新人设（无需重启）；缺行账号回落打包默认不 brick
- [ ] 6.5 `/opsx:archive` 归档（delta 合并新建 `openspec/specs/account-persona-config`）—— 待 6.4 验证后归档
