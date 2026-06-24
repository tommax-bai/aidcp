# Design — account-persona-config

## 背景与现状（带文件:行）

- 人设是一份全局 YAML：`aidcp-cloud/src/soul/soul.yaml`，启动时 `loadSoul()` 一次性读入（`src/server.ts:473` `const soul = loadSoul();`），fail-fast 校验缺字段即抛。
- 浏览侧注入：`RoleDispatcher` 构造收 `soul`（`src/orchestrator/role-dispatcher.ts:73,189`），在 `setup()` 拍成 `commonOptions = { eventBus, soul: this.soul, llm }`（`role-dispatcher.ts:276`），逐个 agent 经构造存为 `protected readonly soul: Soul`（`src/agents/base-role.ts:25,30`）。各 agent 在 `buildPrompt` 内联读取（如 `src/agents/content-evaluator.ts:142` `const { identity, interests } = this.soul;`）。
- 发布侧注入：`PublishScheduler` 构造收同一个 `soul` 单例（`src/server.ts:613` 附近），经 `trigger.generateInput.soul` 进入发布角色。
- 账号主表 `accounts` 已有 `persona_ref` 列但**未使用**（`src/account-store.ts` `ACCOUNTS_SCHEMA_SQL`）。soul 加载器导出 `loadSoulFromValue(value)`（已解析 YAML 值 → 校验 → 强类型 Soul）与 `loadSoul(path?)`（打包默认）。
- 现存先例：`RoleConfigStore`（`src/config/role-config-store.ts`，落库 + 内存镜像 + 写库成功才刷镜像 + 永不抛回落）与 `createRoleConfigPanel`（`src/config/role-config-facade.ts`，目录 / 校验写 / 保存前校验不过即拒不落库）。本 change 全程**复刻**这两者的形态。

痛点：人设全局单份、改需重启、无法按账号、运营后台够不着。

## 决策一：按账号人设 schema（迁移 0011，FK 到 accounts）

新表 `persona_config`，按账号主键，FK 到 `accounts(account_id)`。人设本身存为一段文本（YAML 或等价序列化），由 soul 加载器解释——**不在 DB 里铺平 identity / interests 等子字段**（YAGNI：人设是整体喂给 prompt，无需结构化查询；铺平会与 soul 类型演进强耦合）。

```sql
-- migrations/0011_persona_config.sql（与 store 内 CREATE IF NOT EXISTS 同源、幂等）
CREATE TABLE IF NOT EXISTS persona_config (
  account_id  TEXT PRIMARY KEY REFERENCES accounts(account_id) ON DELETE CASCADE,
  persona     TEXT NOT NULL,            -- soul 文本（loadSoulFromValue 可解析）
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_by  TEXT
);
```

- FK + `ON DELETE CASCADE`：人设行不能孤儿存在；账号删除连带清理。
- 短期只 `default` 行被填充（与 `accounts` seed 的 `default` 对齐），但主键即 `account_id`，多账号天然就位。
- `accounts.persona_ref`：本 change 把它的语义**激活**为"是否有自定义人设"的指针 / 标记；与 stream B 共享 `account-store.ts`，B 加昵称列、F 用 `persona_ref`——加性、需协调，不互相覆盖。

## 决策二：派发时取值口替换启动快照（热加载，不重启）

现状把全局 soul 在 `setup()` 拍成 `commonOptions.soul`，agent 构造期存死。要让后台编辑即时生效，需把"取人设"从**值快照**改为**延迟解析的取值口**。

方案对比：
- A（rebuild 全部 agent）：每次编辑后重建 RoleDispatcher / 所有 agent。重、状态会丢、与会话生命周期打架。否决。
- B（base-role 改 getter，单点改）：`base-role.ts` 的 `soul` 由 `readonly` 快照字段改为 `protected get soul(): Soul`，内部调用注入的 `getSoul()` 取值口；`commonOptions` 不再带 `soul: Soul` 快照，改带 `getSoul: () => Soul`。约 11 个 agent 读 `this.soul.xxx` 的写法**一字不改**（getter 透明替换字段），零回归。**选 B**。

取值口 `getSoul()` 的实现：派发时按**当前账号**解析人设（见决策三回落链），返回强类型 `Soul`。`RoleDispatcher` 是该取值口的唯一改造方（本 change 独占 role-dispatcher soul 访问的编辑）。发布侧 `PublishScheduler` 同理：把构造期的 `soul` 单例改为构造期注入 `getSoul()`，在 `generateInput` 时取值（或在触发时解析当前账号人设传入），使发布角色也吃到最新人设。

"当前账号"来源：当前单 RoleDispatcher / 单账号现实下，账号 = `default`（或会话上下文中的 `accountId`，若已就位则用之）。多账号 per-edge 多路复用是后续（item 9），本 change 留 `getSoul(accountId?)` 形参缝，默认解析 `default`。

## 决策三：回落链（never-brick）

解析某账号人设时，按序回落，任一步失败都不 brick：
1. `PersonaStore.getForAccount(accountId)` 命中且非空 → `loadSoulFromValue(parse(text))` 校验通过 → 用之。
2. 该账号无行 / `persona` 为空 → 回落打包 `loadSoul()`（启动已成功解析的默认 soul，进程内缓存一份）。
3. 镜像里该账号文本存在但解析失败（理论上写入门已挡，防御性兜底）→ 记一条 warn，回落打包默认。

打包 `soul.yaml` 永远是最后兜底，且它在启动 fail-fast 已被验证可解析，故回落目标恒定可用。`getSoul()` **永不抛**（复刻 RoleConfigStore 回落不抛的不变量）。

## 决策四：写前校验，诚实拒绝（绝不静默假成功）

`PersonaFacade.setPersona(accountId, personaText, updatedBy)`：
1. 先用 `loadSoulFromValue(parse(personaText))` 校验。抛错 = 人设非法 → 返回 `{ ok:false, reason:'persona_invalid' }`，**不落库、不刷镜像、不返回成功**（红线：MUST NOT 静默假成功；对齐 role-config 的 `model_invalid` 形态）。
2. 校验通过 → `store.set(...)`（写库成功才刷内存镜像，复刻 RoleConfigStore 时序），返回服务端写后真态（含 `updatedBy` / `updatedAt`）。
3. 空 `personaText`：视作"清除覆盖 → 回落打包默认"，不算非法（对齐 role-config 空值 = 回落语义）。

## 决策五：人设如何到达浏览 + 发布两侧角色 prompt

- 浏览侧：`getSoul()` 注入 `commonOptions` → `base-role` getter → 各 agent `buildPrompt` 读 `this.soul`。透明、覆盖全部 ~11 个浏览 agent。
- 发布侧：`PublishScheduler` 注入 `getSoul()`，在生成输入时取当前账号人设 → 发布角色（ContentCreator / TitleCreator 等）拿到。两侧共用同一份解析结果，人设是 item 4 所指"喂给所有角色 prompt 的共享缝"。

## 决策六：面板接口与页面（JWT + 非乐观）

复刻 role-config 面板形态：
- `GET /api/persona`：列账号 + 各自人设当前生效值 + 是否覆盖 / 回落 + 审计字段。
- `GET /api/persona/:accountId`：单账号人设详情（编辑回显）。
- `PUT /api/persona/:accountId`：写人设（经 facade 校验 + 落库 + 刷镜像），返回写后真态。
- 全部受现有 `/api/*` JWT 守护；写**非乐观**（round-trip 后据真态渲染）；文案诚实（已保存 / 人设格式无效无法保存）。
- console `/persona` 页：列账号、按账号编辑、保存后 round-trip 重渲染。

## 协调约束（5 流并行）

- 迁移号 **0011** 为本流（F）预留。
- `src/server.ts`：本流**只 APPEND**（store init + facade 装配 + getSoul 注入），**绝不改 stream C 的 model-resolver 块**（C 先落地、独占该块）。
- 协议红线：本流**不碰** protocol.ts / command-bridge.ts / docs/protocol.md / edge-client.ts onMessage（属 stream B）。人设不经协议。
- 共享 chokepoint 文件按 **C→D→F→B** 顺序 APPEND：`src/panel/panel-server.ts` 路由链、`src/panel/types.ts`、console `src/types/api.ts`、`src/api/queries.ts`。本流（F）在 C、D 之后、B 之前追加自己的条目。
- console 路由 / 导航：D 加 `/quotas`，F（本流）加 `/persona`（`App.tsx` + `AppShell.tsx`）。
- `src/account-store.ts` 与 stream B 共享：B 加昵称、F 激活 `persona_ref`——加性、协调，不互删对方字段。
- `role-dispatcher.ts` 的 soul 访问改造由本流**独占**。

## 留的缝（deferred）

- `getSoul(accountId?)` 形参缝：多账号 per-edge 多路复用就位后传真 `accountId`；当前默认 `default`。
- 人设结构化编辑（分字段表单 / 校验提示）暂以整段文本编辑起步；后续可在 facade 不变的前提下增量做。
- 与 stream B 昵称的合并：账号真实昵称可作为人设 identity 的一部分来源，本期不自动联动，留协调缝。
- **`session_limits` 迁出本层 → 归 stream D（2026-06-24 用户决策）**：会话硬上限是限额 / 风控性质、非人设性质。坐实发现它在人设里大半是死配置（只有 `max_duration_min` 真在用，`max_likes`/`max_searches`/… 解析了但运行时无处读取；真正卡单场互动的是 `role-dispatcher.ts` `freshBudget()` 写死值）。决策：会话上限（单场时长 + 单场互动预算）收口到安全限额层（D `safety-quota-config`，见其 proposal「范围补充」+ tasks §7），按账号 + 三档可配；人设此后**只承载身份 / 兴趣 / 行为偏好**。本期 F 已上线、暂仍承载整份 soul（含 session_limits，仅时长生效）；待 D 实装时把 `session_limits` 从人设删除 / 隐藏、`max_duration_min` 改由 D 供给。
