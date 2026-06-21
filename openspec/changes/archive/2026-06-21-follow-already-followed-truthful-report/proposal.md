## Why

边缘 `executeFollow()` 在点击前读关注按钮文案，若已是「已关注 / 互关」则返回哨兵 `{error:'already'}` 并以 `ok:false` + `reason:'already_followed'` 上报，打出 `[browse] 关注失败: already_followed`；而真正点击成功走 `ok:true`「✓ 关注成功」。**同一真实结果（作者已被关注）一条报成功、一条报失败**——这是「假失败」，违反 CLAUDE.md §2 的红线「绝不静默假成功（其推论：也绝不假失败）」。实测日志已出现该误报（作者 `红衣大叔讲AI` 页面显示已关注，日志却报关注失败）。同时，配额在指令下发时无条件扣减，一次纯 no-op 也会烧掉一个 follow 配额。

## What Changes

- **edge**：`executeFollow()` 的 already-followed 分支改为**如实的良性 no-op 成功**——`reportActionCompleted({ action:'follow', ok:true, reason:'already_followed' })`，日志改为 `[browse] ✓ 已关注（无需重复关注）`。真正「找不到按钮 / 异常」仍保持 `ok:false`（`btn_no-btn` / 异常 message）。
- **edge**：扩展 already-followed 检测，不再只看文案 `已关注 / 互关`，同时识别 `aria-pressed="true"` 等布局变体，避免漏判后去**真点一次**（造成重复关注或假失败）。
- **cloud**：`already_followed` 的 no-op **不计入 follow 配额**。`consumeBudget('follow')` 从 `profile.done` 下发时的无条件扣减，改为依据 edge 真实回执——仅当 `action.completed` 为 `follow` 且 `ok===true` 且 `reason !== 'already_followed'`（即发生了真实的新关注点击）时才扣。
- **不改协议**：复用既有 `ActionCompletedPayload.reason` 字段（`ok:true` + `reason:'already_followed'` 即可让云端区分「已达目标的 no-op」与「真实新关注」），**不新增协议字段**，从而避免 protocol v2 三处同步风险。

## Capabilities

### New Capabilities
<!-- 无新增 capability -->

### Modified Capabilities
- `follow-decision`: 新增「关注执行结果如实上报与配额」要求——`already_followed` 是已达目标状态的良性成功 / no-op，MUST NOT 报为失败；该 no-op MUST NOT 计入 follow 配额；已关注检测 SHALL 兼顾文案与 `aria-pressed` 等状态变体。

## Impact

- **edge（aidcp-edge）**：`src/browse/browse-session.ts` `executeFollow()`（按钮探测 JS + 结果分支 + 日志 + 上报）。可能涉及 `test/` 中关注相关用例。
- **cloud（aidcp-cloud）**：`src/orchestrator/role-dispatcher.ts` —— `profile.done` 处理（移除无条件 `consumeBudget('follow')`）与 `action.completed` 处理（依回执条件扣配额）。可能涉及预算相关 acceptance 用例。
- **协议 / docs**：无改动（不新增协议字段，不触 `protocol.ts` / `docs/protocol.md`）。
- **风险面**：仅改 follow 执行结果的**分类与配额计账**，不改关注**决策逻辑**（follow-decision 既有要求不变），不改浏览闭环控制流（`action.completed` 对 follow 仍 `noRecoverScroll`、由 BackToFeed 返回）。
