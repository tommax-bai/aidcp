# 交接：会话上限搬到安全限额层 —— /opsx:apply 进度（2026-06-24 收工，明天续）

> 给**明天续做的 session** 的交接。change = `session-limits-to-quota-layer`（已 propose + 已 push 本仓 `600d0db`）。
> 今天进入 /opsx:apply，**已完成存储层（§1）**，因 **Anthropic 侧安全分类器临时不可用**（Edit/Bash 全被挡，连只读 git status 都跑不了）+ 先前的**并发会话冲突**而收工。
> 读完本文 + propose 阶段交接 `docs/handoff-session-limits-to-quota-2026-06-24.md` + change 的 proposal/design/tasks 即可无缝续上。

## 0. 一句话现状

- change 的 36 个 task 里，**§1 存储层（task 1.1–1.5）代码已写完**，落在 **3 个隔离的新文件**（未跟踪、未提交）。
- **§2–§7 全未做**（dispatcher/monitor 接管、facade/panel、人设清理、console、测试、部署）——这些都要改**共享文件**，今天因并发会话占用 + 工具不可用没动。
- 收工时两个并发会话（publish-history、multi-account）**都已把 WIP 提交到 master**，cloud 树预计已基本干净（明天先 `git status` 复核）。

## 1. 决策（已拍板，写进 proposal/design，勿再问）

- **维度 = 按账号**（account_id 主键，非档位）。沿用单场时长现有按账号语义，最小惊讶；调度器已持 `currentAccountId` + `resolveSoul(currentAccountId)`，提供者复用同一账号口。
- **空表回落 = 平铺现值，严格零回归**：时长 10min + 现 `freshBudget` 数字 `{likes:10,collects:5,follows:3,searches:5,comments:2,comment_likes:3}`，所有账号一致（**不是** v1 `SESSION_LIMITS` 的 15/30/60 梯度）。
- **独立表 `session_config`**（不复用/不扩 `quota_config`）：预算项集含 `searches`、缺 `view`/`publish`，与 `RISK_ACTIONS` 不同构。
- 红线：不触风控状态单写（`setQuotaLevel`/`applySignal`/`risk_state`）、不触协议、删 `session_limits` 是唯一会 brick 的步骤（最后做、grep 确认无残留读点后）。

## 2. 已完成（§1，3 个新文件，均在 `../aidcp-cloud`，**未跟踪未提交**）

> ⚠️ 这 3 个文件是 **untracked**。若并发会话 `git add -A` 可能被卷走（见 memory `precise-git-add-concurrent-sessions`）。**明天第一件事：`git status` 确认它们还在**；若被别的 commit 卷走，从本文 + git 历史找回；正常则按"只 add 自己文件"提交。

1. **`migrations/0015_session_config.sql`** —— 建表 `session_config(account_id PK, max_duration_min, budget_likes, budget_collects, budget_follows, budget_searches, budget_comments, budget_comment_likes, updated_at, updated_by)`，幂等 `CREATE TABLE IF NOT EXISTS`，不预填行。（迁移号取 0015：0014 已被 `publish_post_url` 占、0012 仍留 stream B）
2. **`src/risk/session-limits.ts`** —— 安全限额层（与 `quotas.ts` 同层）。导出：
   - `SessionInteractionBudget` 类型（六项：likes/collects/follows/searches/comments/comment_likes）
   - `SESSION_BUDGET_KEYS`（穷举 + 校验/遍历用）、`SessionBudgetKey`
   - `DEFAULT_SESSION_DURATION_MIN=10`、`DEFAULT_SESSION_DURATION_MS`、`DEFAULT_SESSION_BUDGET`（Readonly）、`SESSION_LIMIT_MAX=100_000`
   - `defaultSessionBudget()`（返回**新拷贝**，因 live budget 会被扣减）
   - `SessionLimitProvider` 接口：`sessionDurationMsFor(accountId): number` / `sessionBudgetFor(accountId): SessionInteractionBudget`
3. **`src/config/session-config-store.ts`** —— `SessionConfigStore implements SessionLimitProvider`，复刻 `quota-config-store.ts`：
   - `init()` 建表（内含 `SESSION_CONFIG_SCHEMA_SQL` 与迁移同源）+ `reload()` 载镜像
   - `sessionDurationMsFor`（缺行/非法/`<1` → 回落 `DEFAULT_SESSION_DURATION_MS`）
   - `sessionBudgetFor`（逐项 `validInt(...) ?? DEFAULT_SESSION_BUDGET[key]`，返回新拷贝）
   - `getRow/getAll`（面板用）、`set(accountId, patch, updatedBy)`（先写库成功再刷镜像，UPSERT ON CONFLICT account_id）、`close()`

## 3. ⚠️ 一个待清理的尾巴（明天先处理）

- 我先前往 **`src/risk/index.ts`** 加了一行 `export * from './session-limits.js';`，但工具挂了**没撤掉**。
- 它和并发会话加的 `export * from './interaction-guard.js';` 共存在同一个 `M` 文件里。
- **风险**：若被并发会话提交（含我这行）但我的 `session-limits.ts` 未提交 → 对方从干净检出 build 失败（dangling import）。
- **明天处理（二选一）**：
  - 若决定**保留**（我的代码其实都从 `'../risk/session-limits.js'` 直接 import、不依赖 index 导出，但留着也无害）→ 确保 `session-limits.ts` 同批提交即可。
  - 若想**撤掉**：删 `src/risk/index.ts` 里 `export * from './session-limits.js';` 这一行（**只删这行**，勿动相邻 `interaction-guard`/`session-budget` 行；勿 `git checkout` 整文件——会连带撤掉并发会话的改动）。

## 4. 剩余 task（§2–§7，全改**共享文件**，按序）

> 动手前先 `git status` 确认树干净 + 对每个文件**复核当前行号**（并发改动后会漂；下面的行号是 2026-06-24 收工时所见，已对照 multi-account 提交后状态）。

### §2 接管运行时读点（`../aidcp-cloud`）
- **2.1** `src/orchestrator/role-dispatcher.ts`：`RoleDispatcherOptions` 末尾（现 `interactionGuard?` 选项在 **line 141**、紧接 `}` 在 142）**APPEND** `sessionLimitProvider?: SessionLimitProvider;` + 注释；import `SessionLimitProvider`/`defaultSessionBudget`/`DEFAULT_SESSION_DURATION_MS`/`SessionInteractionBudget` from `'../risk/session-limits.js'`（**直接从该文件 import，别走 index**）。加私有字段 + 构造赋值（构造函数现在 ~line 225 起，`interactionGuard` 赋值已在）。
- **2.2** `maxDurationMs()`（现 **line 262–264**，体为 `return (this.resolveSoul().session_limits?.max_duration_min ?? 10) * 60_000;`）改为 `return this.sessionLimitProvider?.sessionDurationMsFor(this.currentAccountId) ?? DEFAULT_SESSION_DURATION_MS;`。`progress()`（265–270）不动。
- **2.3** `freshBudget()`（收工时在 ~line 495，`private static freshBudget()`）：改为**实例方法**按当前账号读 `this.sessionLimitProvider?.sessionBudgetFor(this.currentAccountId) ?? defaultSessionBudget()`。`this.budget` 初始化（~line 221，现 `= RoleDispatcher.freshBudget()`）改为构造期 `this.budget = this.freshBudget()`（注意：字段初始化器跑在构造体前，需挪到构造体内或改 lazy；最稳：字段声明 `private budget!: SessionInteractionBudget;` + 构造体末尾 `this.budget = this.freshBudget();`）。`restartSession()`（~line 551/559）reset 用 `this.freshBudget()`。
- **2.4** 比率闸一致性：`sessionLikeCounts()`（~line 500，现 `const init = RoleDispatcher.freshBudget();`）改用会话开始/reset 时存的 `this.budgetInit` 快照（新增私有字段 `budgetInit`，在 `startSession`/`restartSession` 里 `this.budgetInit = { ...this.budget }`，**且 budget 也由它派生**：reset 时 `this.budget = this.freshBudget(); this.budgetInit = { ...this.budget };`）。杜绝会话中途运营改预算致 `init−剩余` 漂移。
- **2.5** `src/agents/session-monitor-role.ts`：`effectiveMaxDurationMs()`（收工时 **line 117–119**，`return this.maxDurationMsOverride ?? (this.soul.session_limits?.max_duration_min ?? 10) * 60_000;`）去掉 soul 读，改 `return this.maxDurationMsOverride ?? this.getMaxDurationMs?.() ?? DEFAULT_SESSION_DURATION_MS;`。`SessionMonitorRoleOptions`（line 16–34）加 `getMaxDurationMs?: () => number;`；构造（56–69）持有。调度器构造 `SessionMonitorRole` 处（收工时 ~line 405，`new SessionMonitorRole({ ...commonOptions, onSessionEnd, getRemainingBudget: () => this.budget, clock })`）补 `getMaxDurationMs: () => this.maxDurationMs()`。
- **2.6** 红线核对（结构性）：provider 只读；不写 state、不调 `setQuotaLevel`/`applySignal`、不碰 `risk_state`、不经协议。

### §3 facade + panel（APPEND，序在 D/quotas 之后）
- **3.1** 新增 `src/config/session-config-facade.ts`：复刻 `quota-config-facade.ts`。`getCatalog()` 按账号回显（时长 + 六项预算，库缺行以写死默认合成 + `overridden` + 审计）；`setQuota/set(patch, updatedBy)` 校验（`Number.isInteger`+`>=0`+`<=SESSION_LIMIT_MAX`；时长另需 `>=1`；至少带一个字段）→ `store.set` → 回真态 catalog；非法整块拒（reason: `invalid_value`/`no_valid_fields`/`unknown_account`?——按账号写一般不校验账号存在性，可省 unknown）。
- **3.2** `src/panel/panel-server.ts`：**APPEND** `GET /api/session-limits` + `PUT /api/session-limits`（JWT `verified.payload.sub` 作 updatedBy；invalid→400，未注入→503）。**插入点**：quota 路由块结束后（收工时 quota 路由在 line 509–565，PUT 在 520–565），在 565 之后、persona 块（567 起）之前 APPEND。body 解析仿 quota（tier/action 那段换成 accountId + 七个数字字段）。
- **3.3** `src/panel/types.ts`：**APPEND** DTO（`SessionLimitRowView`/`SessionLimitCatalogView`/`SessionLimitPatchInput`/`SessionLimitSetResult`/`PanelSessionLimits`）+ `PanelDeps.sessionLimits?`（PanelDeps 在 line 18–83+，`quotaConfig?` 在 83；在其后 APPEND `sessionLimits?`）。quota DTO 范例在 line 285–323。
- **3.4** `src/server.ts`：**仅 APPEND**——`new SessionConfigStore({...PG env})`（仿 quotaConfigStore，line 157–163）+ `await sessionConfigStore.init()`（加进 line 164–173 的 try/catch，吞错退化写死默认）+ import 两个新模块（仿 line 94–95）+ `createSessionLimitPanel({ store: sessionConfigStore })`（仿 line 888 `createQuotaConfigPanel`）+ 把 store 作 `sessionLimitProvider` 传进 `buildDispatcher` 的 `new RoleDispatcher({...})`（line ~619，和 getSoul/llm 同级加一行）+ facade 进 panel deps（仿 line 963 `quotaConfig: quotaConfigPanel`，加 `sessionLimits: sessionLimitPanel`）。**勿改 multi-account / 其他流的既有块。**

### §4 人设清理（最后做，唯一会 brick）
- **4.1** `grep -rn "session_limits" src/` 确认**仅余定义/解析、无运行时读点**（§2 做完后 role-dispatcher:263 + session-monitor:118 两处读点应已迁走）+ `npm run typecheck` 绿。
- **4.2** `src/soul/types.ts`：删 `Soul.session_limits`（line 89）+ `SessionLimits` 类型（若无他用）。
- **4.3** `src/soul/loader.ts`：删 `parseSessionLimits`（line 174–183 附近）及其调用（line 200 `session_limits: ...`）。
- **4.4** `src/soul/soul.yaml`：删 `session_limits:` 段（line 36–42 附近）。
- **4.5** 删后回归：`grep -rn "session_limits" src/` 零结果；`npm run typecheck` 绿。

### §5 console（`../aidcp-console`，先 `ls -d` 确认存在）
- **5.1** `src/types/api.ts`：APPEND 单场上限 DTO（对齐 cloud）。
- **5.2** `src/api/queries.ts`：APPEND `useSessionLimits`（GET）；写走页内 `apiPut` + invalidate（仿 RolesPage/QuotasPage）。
- **5.3** `src/pages/QuotasPage.tsx`：加「单场上限」编辑区（按账号一行：时长 + 六项预算）+ 弹窗；前端校验（非负整数 + 上限 + 时长≥1）；账号源对齐现有账号选择形态（单租户即 `default`）。
- **5.4** `src/pages/PersonaPage.tsx`（或等价）：隐藏/移除 `session_limits` 编辑区。

### §6 测试 / §7 收尾
- **6.1–6.5** cloud 单测：provider 命中/回落/零回归、`maxDurationMs`/`freshBudget` 热加载、比率闸快照、facade 非乐观校验、删 session_limits 后不 brick。建议新建 `test/session-config-store.test.ts`、`test/session-config-facade.test.ts`、`test/session-effective-limits.test.ts`（仿 D 的 `test/quota-*.test.ts`）。注意 `npm test` = `tsx --test 'test/**/*.test.ts'`，顶层测试会跑。
- **6.6** cloud：`npm run test:acceptance`（AC-RISK/AC-PROTO 必过）→ 全量 `npm test` → `npm run typecheck` 绿。
- **6.7** console：build/typecheck。
- **7.1** 回写本仓 `openspec/changes/session-limits-to-quota-layer/tasks.md`（按 sub-repo 分节，`<!-- <repo> <sha> 备注 -->`）。§1 的 1.1–1.5 已在 tasks.md 标 `[x]` 但注的是 `(pending commit)`，提交后补真 sha。
- **7.2** `openspec validate session-limits-to-quota-layer --strict`。
- **7.3** 部署 ECS（备份→dry-run→rsync→restart→healthcheck：8787/PG/迁移 0015/面板 8090）；同机 isales 绝不碰。
- **7.4** 真机校准（后台改某账号时长/预算→下场会话即生效热加载；空账号回落 10min+freshBudget；/persona 不再出现 session_limits）。
- **7.5** `/opsx:archive`（delta 合并进 `openspec/specs/interaction-risk-gating`）。

## 5. 并发 / git 纪律（本仓重度并发，务必守）
- 同机多会话共享工作树 + index。**只 `git add` 自己的具体文件，绝不 `git add -A`**（见 memory `precise-git-add-concurrent-sessions`；今天已见 publish-history 的 497d1bc 误卷别人测试、随后 74fbf42 收拾）。
- 我的 3 个新文件 + `risk/index.ts` 一行是今天唯一的 cloud 改动。共享文件（role-dispatcher/server/panel-server/panel-types/soul）明天若与别的会话同时改，用 git plumbing 只暂存自己 hunk（handoff propose 版 §7 有手法）。
- 提交前 `git status` 看清楚暂存了什么；提交后核对没卷走别人。

## 6. 收工时的 git 实况（cloud master）
- HEAD = `a38fb96` "fix(multi-account): gate role-subscription + watchdog to session activation"（multi-account 会话已提交）。
- 其前：`74fbf42`（chore 清理误卷测试）、`497d1bc`（publish-history per-account）。
- 我开工时 HEAD 是 `7f59fbb`，故上面 3 个 commit 都是今天并发会话产出，**不是我的**。我的 cloud 改动尚未提交（3 新文件 untracked + risk/index.ts 一行 M）。

## 7. 速查
- change 名：`session-limits-to-quota-layer`；本仓 `600d0db` 已 propose+push。
- 续做命令：`/opsx:apply session-limits-to-quota-layer`（或直接按本文 §4 干）。
- cloud 验证：`cd ../aidcp-cloud && npm run typecheck && npm run test:acceptance && npm test`。
- 今日收工主因：Anthropic 侧安全分类器（claude-opus-4-8）temporarily unavailable，Edit/Bash 全被挡（连只读 git 都过不去），非权限问题、非代码问题。
