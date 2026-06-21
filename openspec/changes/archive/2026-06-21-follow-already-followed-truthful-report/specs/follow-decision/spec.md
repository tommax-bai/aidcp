## ADDED Requirements

### Requirement: 关注执行结果如实上报（already_followed 是良性成功而非失败）

关注（follow）的执行结果 SHALL 如实反映**真实平台状态**。当目标作者**已处于已关注状态**（按钮文案为「已关注 / 互关」，或状态标记如 `aria-pressed="true"`）时，边缘 MUST 将该结果上报为**良性 no-op 成功**——`reportActionCompleted({ action:'follow', ok:true, reason:'already_followed' })`，且日志 MUST NOT 写「关注失败」。仅当**真实点击了关注按钮并成功**时，边缘 SHALL 上报 `{ action:'follow', ok:true }` 且 MUST NOT 携带 `reason`（以与 no-op 区分）。

真正的失败——**找不到关注按钮**或**执行抛异常**——SHALL 仍上报 `ok:false`（带相应 reason）。MUST NOT 为消除假失败而把真失败一律报成成功（那将构成红线「假成功」）。

#### Scenario: 已关注作者报为良性成功而非失败
- **WHEN** 关注按钮文案为「已关注」或「互关」（或带已关注状态标记），目标状态本就达成
- **THEN** 边缘上报 `{ action:'follow', ok:true, reason:'already_followed' }`，日志为「✓ 已关注（无需重复关注）」一类成功表述，MUST NOT 出现「关注失败」

#### Scenario: 真实新关注成功不带 reason
- **WHEN** 关注按钮处于未关注态、边缘点击成功
- **THEN** 边缘上报 `{ action:'follow', ok:true }`（不带 `reason`），以与 already_followed 的 no-op 区分

#### Scenario: 真失败仍如实报 false
- **WHEN** 关注按钮在已知选择器集合下均找不到（no-btn），或执行过程抛异常
- **THEN** 边缘上报 `{ action:'follow', ok:false, reason }`（如 `btn_no-btn` 或异常 message），MUST NOT 报为成功

### Requirement: already_followed 的 no-op 不计入关注配额

关注配额（follow budget）SHALL 仅在**真实发生新关注点击**时扣减。云端 MUST NOT 在指令下发时无条件扣减关注配额；MUST NOT 因 `already_followed` 的 no-op 或真失败而扣减。配额扣减 SHALL 依据边缘 `action.completed` 真实回执——当且仅当 `action==='follow' && ok===true && reason!=='already_followed'` 时扣减一个 follow 配额。

#### Scenario: 已关注 no-op 不烧配额
- **WHEN** 云端发出 follow 指令，边缘回执 `{ action:'follow', ok:true, reason:'already_followed' }`
- **THEN** 该会话的 follow 配额 MUST NOT 被扣减（剩余配额不变）

#### Scenario: 真实新关注扣一个配额
- **WHEN** 边缘回执 `{ action:'follow', ok:true }`（真实新关注、不带 reason）
- **THEN** 该会话的 follow 配额扣减 1

#### Scenario: 关注真失败不扣配额
- **WHEN** 边缘回执 `{ action:'follow', ok:false, reason }`
- **THEN** 该会话的 follow 配额 MUST NOT 被扣减
