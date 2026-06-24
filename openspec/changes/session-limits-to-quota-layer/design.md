## Context

把「单场会话上限」从人设 / 写死常量搬进安全限额层，复刻 change `safety-quota-config`（下称 D）的成熟范式（落库 + 热加载 + 绝不 brick），并守住「风控状态单写」「不触协议」两条红线。本 change 只是**配置读取**：调度器 / 监测体侧多读一个按账号的提供者，不经状态机、不经协议。

### 现状坐实（文件:行，并发改动多、动手前复核行号）

- **单场时长（现按账号、来自人设、已惰性热加载）**：
  - `src/orchestrator/role-dispatcher.ts:252` `maxDurationMs()` = `(this.resolveSoul().session_limits?.max_duration_min ?? 10) * 60_000`；`:256` `progress()` 用它算疲劳乘子；`resolveSoul()`（:244）按 `this.currentAccountId` 经 `getSoul` 取值口解析人设。
  - `src/agents/session-monitor-role.ts:118` `effectiveMaxDurationMs()` = `this.maxDurationMsOverride ?? (this.soul.session_limits?.max_duration_min ?? 10)*60_000`；调度器构造它时**已不传死值**（:403 注释），让它经 `this.soul` 惰性解析。
  - 当前真生效值：`src/soul/soul.yaml:36` `session_limits.max_duration_min: 10`（默认账号）。
- **单场互动预算（现写死、三档无关）**：`src/orchestrator/role-dispatcher.ts:484` `static freshBudget()` 返回 `{ likes:10, collects:5, follows:3, searches:5, comments:2, comment_likes:3 }`；`:211` `this.budget` 用它初始化，`:548` `restartSession()` reset 用它；`:490` `sessionLikeCounts()` 用 `freshBudget()` 作 `init` 算「已发生 = init − 剩余」的比率闸；`:594-599` 按动作扣减 `this.budget`。
- **死配置**：`session_limits` 里 `max_likes` / `max_searches` / `max_collects` / `cooldown` 全仓只解析、运行时无处读取（`grep -rn "session_limits" src/` 仅 `max_duration_min` 被读）。
- **v1 兼容路径的按档单场上限**：`src/risk/session-budget.ts:18` `SESSION_LIMITS`（const、未导出，conservative 15min/30 动作、normal 30/60、aggressive 60/120）由 `SessionBudget` 类用于 v1 plan/select 路径——**非现役事件驱动闭环**，本 change 不动它，仅作回落数字的参考来源。
- **D 范式参照**：`src/config/quota-config-store.ts`（先写库成功再刷镜像、缺值回落、同步只读 provider、永不抛）；`src/config/quota-config-facade.ts`（getCatalog / setQuota 校验 + 非乐观回真态）；`src/panel/panel-server.ts` `/api/quotas` GET/PUT（JWT，`verified.payload.sub` 作 `updatedBy`）；`src/server.ts` 与其余 config store 同 try/catch init。

## Goals / Non-Goals

**Goals:**

- 单场时长 + 单场互动预算落库、管理后台**按账号**可改、运行时**每次现读**（热加载、无需重启）。
- 绝不 brick：缺表 / 缺行 / 非法值 → 回落写死默认（时长 10min + 现 `freshBudget` 数字）；空表与现状逐位一致（严格零回归）。
- 把 `session_limits` 从人设里彻底清理掉（迁走全部读点后再删，杜绝「能改却无效」误导）。
- 守红线：不触风控状态单写、不触协议。

**Non-Goals:**

- **不引入档位（tier）维度**：用户已拍板按账号配置，不按 conservative/normal/aggressive 分档（与 D 正交：D 是按档配滑动窗配额，本 change 是按账号配单场窗口）。
- **不动 v1 `SessionBudget` / `session-budget.ts`**（plan/select 兼容路径，非现役闭环）。
- **不引入单场总动作上限（`max_actions`）**：现役闭环只有逐项预算、无总动作硬顶；引入总顶是新行为、违反零回归。仅搬现有的「时长 + 六项逐项预算」。
- 不动 `tempo` 降速旋钮（CLAUDE.md §2 已知缺口，正交）。

## Decisions

### 决策 1：配置维度 = 按账号（非按档位）

- **选择**：表主键 `account_id`，一账号一行；提供者按 `accountId` 取值。
- **理由**：① 用户 2026-06-24 拍板「仍按账号」；② 单场时长**现状本就按账号**（经人设 `resolveSoul(currentAccountId)` 解析），按账号搬是语义**不变**、最小惊讶；③ 调度器已持 `currentAccountId` 且 `resolveSoul` 已按它解析，提供者复用同一账号口、无需新引入档位访问（按档位反而要把 `quotaLevel` 现读链接进调度器，徒增耦合）。
- **取舍 vs 按档位（D 的形态）**：按档位能让 conservative/aggressive 自动有梯度，但① 与现状语义冲突（现状单场时长不随档位变）；② 单场互动预算项含 `searches`（非风控动作）、缺 `view`/`publish`，与 D 的 `(tier, action)` 行集不同构，强行复用 `quota_config` 反而别扭。**按账号 + 独立表**最贴现状、最小耦合。

### 决策 2：独立表 `session_config`（不复用 / 不扩 `quota_config`）

```sql
CREATE TABLE IF NOT EXISTS session_config (
  account_id           TEXT PRIMARY KEY,
  max_duration_min     INTEGER NOT NULL,
  budget_likes         INTEGER NOT NULL,
  budget_collects      INTEGER NOT NULL,
  budget_follows       INTEGER NOT NULL,
  budget_searches      INTEGER NOT NULL,
  budget_comments      INTEGER NOT NULL,
  budget_comment_likes INTEGER NOT NULL,
  updated_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_by           TEXT
);
```

- **理由**：单场预算的项集（`likes`/`collects`/`follows`/`searches`/`comments`/`comment_likes` 六项）与 `quota_config` 的 `RISK_ACTIONS`（七项、含 `view`/`publish`、无 `searches`）**不同构**——`searches` 不是风控动作。给 `quota_config` 加 `per_session` 列会对 `view`/`publish` 行造无用列、且无处放 `searches`。**独立宽表**（一账号一行、列即各预算项）最honest、零歧义、回落最简单。
- **取舍 vs 窄表 `(account_id, item, value)`**：窄表更「可扩展」，但① 会把「分钟」与「计数」两种语义塞进一个 `value` 列（时长是分钟、其余是次数），是坏味；② 预算项集是稳定的现役 `freshBudget` 形态，YAGNI 不需要窄表的可扩展性。建表幂等（`CREATE TABLE IF NOT EXISTS`，store 内 `SESSION_CONFIG_SCHEMA_SQL` 与迁移同源，复刻 D）。表初始**不预填行**：缺行即回落写死默认 → 全新部署 / 迁移刚跑完都安全。

### 决策 3：按账号提供者注入（热加载、不触状态单写）

```ts
// 缺行 / 非法值由 store 内部逐项回落写死默认，永不抛
export interface SessionLimitProvider {
  sessionDurationMsFor(accountId: string): number;
  sessionBudgetFor(accountId: string): SessionBudget; // { likes, collects, follows, searches, comments, comment_likes }
}
```

- `SessionConfigStore` 实现它：读 `account_id` 内存镜像行 → 时长 = `max_duration_min * 60_000`（缺行 / 非整 / 负 → 回落 `DEFAULT_SESSION_DURATION_MIN=10`）；预算 = 六列（任一列缺 / 非法 → 该项回落 `DEFAULT_SESSION_BUDGET` 对应值）。**逐项回落、永不抛**。
- **注入路径**：`RoleDispatcherOptions` 加可选 `sessionLimitProvider?`；`maxDurationMs()` 改 `this.sessionLimitProvider?.sessionDurationMsFor(this.currentAccountId) ?? DEFAULT_SESSION_DURATION_MS`；`freshBudget()`（改为实例方法或带 accountId 入参）改 `this.sessionLimitProvider?.sessionBudgetFor(this.currentAccountId) ?? DEFAULT_SESSION_BUDGET`。**保留惰性热加载**：每次现读内存镜像，`PUT` 写库成功即刷镜像 → 下一次会话 reset / 下一次 `progress()` 立即看到新值。
- **会话监测体**：`session-monitor-role.ts` `effectiveMaxDurationMs()` 去掉对 `this.soul.session_limits` 的直读，改经调度器传入的统一解析口（注入 `getMaxDurationMs: () => this.maxDurationMs()` thunk，保单一解析路径），缺省仍回落 10min。
- **比率闸一致性（关键）**：`sessionLikeCounts()` 现用 `freshBudget()` 重算 `init`。改后**会话内的 init 必须与 reset 时所用的同一份预算**——故在 `restartSession()` / 构造时把当次预算快照存 `this.budgetInit`，`sessionLikeCounts()` 用 `this.budgetInit`（而非再调提供者，避免会话中途运营改预算导致 `init − 剩余` 算出负 / 漂移）。
- **红线**：提供者只读、不写、不碰 `state` / `quotaLevel` / `applySignal` / `setQuotaLevel` / `risk_state`。单场上限编辑只动 `session_config` 表。

### 决策 4：never-brick 回落 = 当前真生效值（严格零回归）

三层兜底，任一层失败退到下一层、永不抛：

1. 提供者缺失（没注入）→ `maxDurationMs()` / `freshBudget()` 用写死默认（`DEFAULT_SESSION_DURATION_MS` = 10min、`DEFAULT_SESSION_BUDGET` = `{likes:10,collects:5,follows:3,searches:5,comments:2,comment_likes:3}`），与当前行为逐位一致。
2. 提供者在、但账号缺行 / 字段非法 → 逐项回落同一组写死默认。
3. store `init`（建表 / 载镜像）失败 → 装配处吞错、不注入提供者（退化到第 1 层），云端照常起、闭环照常用写死默认。

- **零回归基线 = 平铺现值**（用户拍板）：所有账号缺配置时都回落 10min + 现 `freshBudget` 数字（**不是** v1 `SESSION_LIMITS` 的 15/30/60 梯度），保证空表行为与现状逐位一致。梯度由运营按账号在后台配。
- 写死默认作为导出常量集中一处（供回落 + 校验上限 `SESSION_LIMIT_MAX` 复用），替代散落的内联 `?? 10` 与 `freshBudget` 字面量。

### 决策 5：人设清理（碰已部署的 F `account-persona-config`，最后做、有序删）

- **顺序铁律**：先把单场时长两处读点（dispatcher + session-monitor）全部改读新提供者、`grep -rn "session_limits" src/` 确认无残留运行时读取，**才**删 `session_limits`。这是唯一有「删了会 brick」风险的一步。
- 删点：`src/soul/types.ts` 去 `session_limits` 字段；`src/soul/loader.ts` 去 `parseSessionLimits` 及其调用；`src/soul/soul.yaml` 删该段。
- `/persona` 页若展示 / 可编辑 `session_limits`，隐藏该区（去掉「能改却无效」误导）。
- **迁移影响**：若此前有账号经 `/persona` 设过非 10 的 `max_duration_min`，删后将回落 10min（默认账号 soul.yaml 本就是 10、单租户下无差异）；运营在新「单场上限」编辑区按账号重设即可。属一次性配置迁移，非数据丢失。

### 决策 6：面板 API + console（复刻 D 范式，APPEND）

- `GET /api/session-limits`（JWT）：回显 `accountId → { maxDurationMin, likes, collects, follows, searches, comments, commentLikes, updatedAt, updatedBy }`，库缺行以写死默认合成（运营看到的即当前真生效）。
- `PUT /api/session-limits`（JWT，`verified.payload.sub` 作 `updatedBy`）：校验（有限非负整数 + `<= SESSION_LIMIT_MAX` + 时长 `>= 1`）→ 写库 → 刷镜像 → 回真态；任一字段非法整块 4xx 拒、绝不部分落库 / 假成功；未注入 503。
- console：在 `/quotas` 页加「单场上限」编辑区（按账号一行：时长 + 六项预算），保存前前端同样校验（即时反馈），**服务端校验为准**，保存后回显刷新（非乐观）。账号来源 = `accounts-master-data` 的账号列表（单租户下即 `default` 一行）。

## Risks / Trade-offs

- **[删 `session_limits` 后仍有残留读点 → 运行时 brick]** → 删前 `grep -rn "session_limits" src/` 必须零运行时读取；先合「改读提供者」的提交、`npm run typecheck` 绿、再合删除提交；单测覆盖「provider 缺失回落 10min」。
- **[比率闸 init 漂移]**（会话中途运营改预算，`init − 剩余` 算出负）→ 决策 3 用会话开始时快照 `this.budgetInit`，会话内不重读提供者；新值下场会话生效。
- **[per-account UI 在单租户下账号源单薄]** → 账号列表取 `accounts-master-data`，单租户即 `default` 一行；与 stream C / `multi-account-node-support` 的多账号底座对齐，不预造多账号 UI（YAGNI）。
- **[并发会话抢同一批文件]**（同机重度并发：`server.ts` / `panel-server.ts` / `panel/types.ts` / console `types/api.ts` / `queries.ts`）→ 一律 **APPEND**（不与他流抢同处）；只 `git add` 自己的具体文件、绝不 `-A`；共享文件用 git plumbing 只暂存自己的 hunk（见 memory `precise-git-add-concurrent-sessions`）。迁移取 `0015`（避开 `0012` 预留 B）。
- **[ECS 部署 = 全量 master 快照]** → 部署前 `rsync --dry-run` 摸范围；部署后 grep ECS 文件内容 + 看启动日志确认新码生效；同机 isales 绝不碰。

## Migration Plan

1. 合「新增表 + store + provider + facade + 接管 dispatcher/monitor 读点」提交（此时 `session_limits` 仍在、但已无运行时读点）；cloud `npm run typecheck` + `test:acceptance`（AC-RISK 红线）+ 全量 `npm test` 绿。
2. `grep -rn "session_limits" src/` 确认仅剩定义 / 解析、无运行时读取 → 合「删 `session_limits`（types/loader/yaml）+ 面板/console」提交。
3. console build/typecheck 绿。
4. 按 §5 安全序列部署 ECS（先备份 → `rsync --dry-run` → rsync → restart → healthcheck：8787 / PG `select 1` / 迁移 `0015` 已建表 / 面板 8090）；与并发会话错峰。
5. 真机校准：后台改某账号单场时长 / 某项预算 → 下场会话即按新值（热加载无重启）；空账号回落 10min + freshBudget；`/persona` 不再出现 `session_limits`。
6. 回滚：失败即回滚到备份；表为空 / 未注入提供者时闭环照常用写死默认（never-brick 保证回滚安全）。

## Open Questions

- 无阻塞性未决项。两个 user-facing 决策已拍板（维度=按账号、空表回落=平铺现值）。账号列表 UI 源（`accounts-master-data` vs 仅 `default`）在 console 实装时按现有 `/persona` 页的账号选择形态对齐即可，不阻塞 cloud 侧。
