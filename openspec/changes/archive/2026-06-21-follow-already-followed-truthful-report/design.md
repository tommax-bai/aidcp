## Context

边轻云重下，关注是**原子操作只在边缘**执行（`aidcp-edge/src/browse/browse-session.ts` `executeFollow()`），云端只做决策（`FollowAgent` → `profile.done`）与配额计账（`role-dispatcher.ts`）。当前 `executeFollow()` 在点击前用一段 JS 探测关注按钮：命中文案 `已关注 / 互关` 即返回 `{error:'already'}`，与 `no-btn`、异常一同走 `ok:false` 失败通道，并打 `[browse] 关注失败: already_followed`。

问题：`already_followed` 代表**目标状态（已关注）本就达成**，是良性 no-op，却与「真的点不到按钮 / 抛异常」这类真失败混在同一条 `ok:false` 通道。这违反 CLAUDE.md §2 红线（绝不假成功，推论：绝不假失败），也让云端无法区分「已达目标」与「失败」。配额侧，`profile.done` 一旦 `followed===true` 就在指令下发处无条件 `consumeBudget('follow')`（`role-dispatcher.ts:347`），与 edge 真实结果脱钩——一次 already_followed 的 no-op 照样烧掉一个 follow 配额。

约束：`ActionCompletedPayload = { action; ok:boolean; reason? }`（edge/cloud 两份 `protocol.ts:446-450` 逐字一致）。`reason` 字段**已存在**，足以承载 no-op 标记，无需改协议。follow 的 `action.completed` 在 `role-dispatcher.ts:414` 已属 `noRecoverScroll`、返回由 `BackToFeed` 统一接管——本次改动不触碰这条控制流。

## Goals / Non-Goals

**Goals:**
- 消除「关注假失败」：already_followed 如实报为良性 no-op 成功（`ok:true` + `reason:'already_followed'`），日志不再写「关注失败」。
- 真失败仍如实：找不到按钮（`no-btn`）、执行异常仍 `ok:false`。
- 配额对齐真实平台动作：already_followed 的 no-op 不计 follow 配额，仅真实新关注点击才扣。
- already-followed 检测更稳：兼顾文案与 `aria-pressed` 等状态变体，避免漏判去真点一次。

**Non-Goals:**
- 不改关注**决策逻辑**（follow-decision 既有「只依据真实信号」要求不变）。
- 不引入云端「已关注关系投影 / 持久化 followed 集合」来事前跳过冗余关注（属更大设计，列入 Open Questions，本次不做）。
- 不新增协议字段、不改 `protocol.ts` / `docs/protocol.md`（复用既有 `reason`）。
- 不改浏览闭环控制流（follow 仍 noRecoverScroll、BackToFeed 返回）。

## Decisions

### D1：already_followed 报为 `ok:true` + `reason:'already_followed'`，而非新增协议「中性 outcome」
edge 在 already-followed 分支调用 `reportActionCompleted({ action:'follow', ok:true, reason:'already_followed' })`，日志改 `[browse] ✓ 已关注（无需重复关注）`。
- **为何**：目标状态已达成即为成功；`ok:true` 是诚实表达。`reason` 字段已能携带「这是 no-op」语义，云端据此分流即可。
- **备选（否决）**：给 `ActionCompletedPayload` 加 `outcome:'ok'|'noop'|'fail'`。否决理由——需 edge/cloud 两份 `protocol.ts` 逐字 + `docs/protocol.md` 三处同步（AC-PROTO-*），为一个 bug fix 引入协议面风险不划算；`reason` 已足够。若未来看板需要更强的 no-op 语义再单独立项。

### D2：配额计账从「下发即扣」改为「依真实回执扣」
移除 `profile.done` 分支里的 `consumeBudget('follow')`；改在 `action.completed` 处理中，当 `payload.action==='follow' && payload.ok===true && payload.reason!=='already_followed'` 时 `consumeBudget('follow')`。
- **为何**：配额应反映**真实发生的平台动作**。already_followed / 真失败都不应扣额。
- **备选（否决）**：保留下发即扣，仅在 already_followed 时回补。回补逻辑更绕、易与并发预算读写竞态；「按回执扣」单点、直观。
- **注意**：edge 必须对真实新关注上报**不带** `reason`（即 `{ action:'follow', ok:true }`），以便云端用 `reason` 区分两类成功——这是 D1/D2 的契约衔接点，需在 edge 与测试中固定。

### D3：already-followed 检测兼顾 `aria-pressed`
探测 JS 在判断 `已关注 / 互关` 文案的同时，检查 `el.getAttribute('aria-pressed') === 'true'`（或就近的已关注状态标记）；命中即视为 already。
- **为何**：纯文案判定会在按钮以不同 label / 仅状态属性呈现的布局变体下漏判，进而去真点一次（重复关注或再触假失败）。
- **范围**：保持现有 selector 列表与点击路径不变，仅扩展「是否已关注」的判定条件，避免过度改动。

## Risks / Trade-offs

- [配额语义变更：原「下发即扣」→「回执后扣」存在极短时间窗，期间 `getRemainingFollows()` 比旧逻辑略乐观] → 关注本就低频、单会话 follow 预算小（freshBudget follows:3），窗口内并发再次决策关注同一/另一作者的概率极低；且这正是「按真实动作计账」的正确语义。acceptance 用例覆盖「already_followed 不扣额」「真实关注扣额」「真失败不扣额」。
- [edge 真实新关注若误带 `reason` 会被云端当 no-op 不扣额] → 在 D2 契约处明确：真实成功路径上报不带 `reason`；加测试钉死。
- [`aria-pressed` 检测在小红书实际 DOM 上未必存在/可靠] → 作为文案判定的**叠加**条件（OR），不替换文案判定；最坏退化为现有文案行为，不会更差。
- [红线回归] → 必须确保改后真失败（no-btn / 异常）仍 `ok:false`；不可一刀切把所有 follow 都报成功（那会变成新的假成功）。acceptance 保留真失败用例。

## Migration Plan

1. edge 改 `executeFollow()`（D1 + D3）→ `npm run typecheck` → `npm run test:acceptance`（含 follow / 红线用例）→ `npm test`。
2. cloud 改 `role-dispatcher.ts`（D2）→ `npm run typecheck` → `npm run test:acceptance`（含预算用例）→ `npm test`。
3. 协议无改动，跳过三处同步校验（AC-PROTO 不受影响，仍应整体跑过）。
4. 部署按 §5 安全序列（仅 cloud 侧 role-dispatcher 改动需上 ECS；edge 本地运行）。回滚：还原两处改动即可，无数据迁移。

## Open Questions

- 是否进一步引入云端「已关注关系投影」以**事前**跳过对已关注作者的关注决策（连命令都不发）？这能省一次往返与一次 no-op，但需持久化与一致性设计，超出本 bug fix 范围——建议另立 change。
- 看板/指标层是否已把 `action.completed ok=false` 聚合为「关注失败」KPI？若是，本次将 already_followed 移出失败口径后，历史口径需对齐（不在本 change 代码范围，记录待办）。
