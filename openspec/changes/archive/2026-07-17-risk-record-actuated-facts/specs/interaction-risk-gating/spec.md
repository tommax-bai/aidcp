## MODIFIED Requirements

### Requirement: 速率配额饱和是节奏背压、不是风控状态输入

账号威胁态（`normal` / `warned` / `restricted` / `frozen`）MUST 只由**平台可观测信号**驱动升级：验证码 → 强信号（`confirmed`）、未知阻断浮层 → 软信号（`light`）、运营手动信号（`manual_restrict` / `manual_freeze` / `operator_override_recover`）。

`RiskController.record(action)` 因**速率配额**耗尽而被 `canDo` 拒时 MUST 只返回 `false`（背压），MUST NOT 触发任何风控状态迁移——具体地：MUST NOT `applySignal`、MUST NOT 递增 `signal_count`、MUST NOT 刷新 `last_signal_at`、MUST NOT 把账号从 `normal` 推向 `warned` / `restricted`。`quota_exceeded` MUST NOT 作为风控信号种类存在于状态机升级逻辑与 `RiskSignalKind` 中。这里的速率配额包括分钟 / 小时滑动突发窗口与 Asia/Shanghai 自然日每日窗口。

**此处「只返回 `false`」限定的是本要求所禁的那一类副作用——风控状态迁移——而 MUST NOT 被解读为「因此也不许把这次动作记进计数器」。** 二者是两个不同的问题，MUST 分别作答：返回值回答**「这个动作在策略内吗」**，计数器回答**「这个动作发生过吗」**。一次已经在平台上做完的动作，其**发生**不因策略事后判定它**不该发生**而改变；记录它 MUST NOT 被当作对它的许可，拒绝记录它也 MUST NOT 被当作对它的撤销。计数器的写入规则见「互动发生后必须按账号持久计数」。

此要求**强化**「被禁账号 `record` 返回 false（绝不自残）」既有红线：返 false 不变，只去掉「撞自己配额还自升状态」的自残副作用。**同理，「记账时二次判策略、判不过就当没发生过」这个丢证据的副作用亦不在本红线保护之列**——自残指「凭空的信号把自己越限越死」；如实记下一次真实发生的动作**造不出任何假信号**，它只会让后续 `canDo` 更早拒绝（计数器只增、闸为 `count >= quota`），故在**收紧**方向上，MUST NOT 与本红线混为一谈。

#### Scenario: 配额到顶被拒不升级风控态

- **WHEN** 某 `normal` 账号的某动作在任一配额窗口（分钟 / 小时滑动窗口或自然日每日窗口）配额耗尽，`record(action)` 被调用
- **THEN** `record` 返回 `false`，该账号风控态仍为 `normal`，`signal_count` 与 `last_signal_at` 均不变

#### Scenario: 反复撞同一配额不自锁

- **WHEN** 同一账号在短时间内连续多次撞同一配额（每次 `record` 均被拒）
- **THEN** 每次都返回 `false` 且风控态**始终**停在原状态，MUST NOT 出现 `normal→warned→restricted` 的自我升级

#### Scenario: 平台真实信号仍照常升级

- **WHEN** 边缘上报验证码 / 未知阻断浮层，云端据此对账号 `applySignal({kind:'confirmed'})` / `applySignal({kind:'light'})`
- **THEN** 威胁态照常升级（如 `normal`→`restricted` / `normal`→`warned`），证明去掉的只有「配额」这个假信号源、真信号驱动不受影响

#### Scenario: 被拒仍返 false，但事实已记下

- **WHEN** 某账号某动作的配额已耗尽，而该动作**已经在平台上真实发生**（回执抵达），`record(action)` 被调用
- **THEN** `record` 返回 `false`（背压答案不变，红线不变）
- **AND** 该动作**已被记入**滑动窗计数并持久化（事实不因策略判定而消失）
- **AND** 风控态、`signal_count`、`last_signal_at` 均不变

### Requirement: 互动发生后必须按账号持久计数

云端 SHALL 在收到 `action.completed{action∈{like,collect,follow}, ok:true}` 时驱动 `RiskController.record(action)`（经补发 `interaction.occurred` 或等效路径），使按账号的滑动窗计数真实累加并经 `PgRiskStore` 持久化；计数 MUST 反映真实成功互动，MUST NOT 凭下发即记（下发未必成功）。

**计数 MUST 记录既成事实，且 MUST NOT 因策略事后重判而丢弃。** 一次动作的回执抵达时，它**已经发生**；此时再判一次「该账号现在还允许做这个吗」并据此**不写**计数，销毁的只有证据，改变不了已发生的事。因此：**「该不该做」MUST 在下发前判定**（那道预闸是唯一能真正阻止动作的地方）；**回执抵达后 MUST 无条件记录**，无论账号此刻的威胁态、配额余量或任何策略判定如何。这与上一段的 `MUST NOT 凭下发即记` 构成一对完整规则：**下发（意图）MUST NOT 计；做完了（既成事实）MUST 计。**

由此，任何**绕过预闸**而真实发生的动作（如运营手动命令按「操作员全权」裁决跳过配额闸）、以及任何在**预闸与回执之间**状态或配额发生变化的动作，其计数 MUST 与未绕过者一视同仁地累加。系统对自己**少报**真实活动量与**谎报**成功同属不诚实：前者是后者的镜像，且因计数器同时是配额分母的来源，少报会让后续闸门**误以为尚有余量**而放行更多真实动作。

**操作员手动动作 MUST 被记录，且 MUST NOT 被配额闸拦截。** 「跳过配额」指的是**不被拦下**，不是**不被记下**：手动动作同样被平台观察到，同样消耗该账号在平台眼里的活动预算。**「操作员全权」豁免的是权限，不是事实。** 因此任何以「人工授权 / 操作员全权」为由**跳过驱动 `record`** 的接线 MUST 改为照常记录（其**跳过闸**的豁免保持不变），且该记录 MUST 与自动动作一视同仁地累加、一视同仁地被后续闸读到。

**推论（一条必须被明确禁止的实现方式）**：一条路径若确实不该消耗预算，正确表达 MUST 是**在接线层显式不驱动 `record`**，MUST NOT 是「照常调用 `record` 但让它内部静默丢弃」——后者使「豁免」与「丢数」不可区分，读代码的人无法分辨这个 0 是设计还是 bug。

#### Scenario: 成功互动累加计数

- **WHEN** 云端收到 `action.completed{action:'like', ok:true}`
- **THEN** 该账号 like 的滑动窗计数 +1 并持久化，可被后续 `canDo` 配额判定读到

#### Scenario: 失败互动不计数

- **WHEN** 云端收到 `action.completed{action:'like', ok:false}`（如 `blocked_by_captcha`）
- **THEN** 该账号 like 计数不增加（只记真实发生的互动）

#### Scenario: 绕过预闸的真实动作照样计数

- **WHEN** 一次动作按产品裁决绕过了下发前的配额闸（如运营手动命令），在平台上真实完成，其回执抵达云端并驱动 `record`
- **THEN** 该动作照常记入计数，MUST NOT 因「此刻的配额已耗尽」而被丢弃
- **AND** 后续 `canDo` 读到的余量反映真实活动量

#### Scenario: 手动动作不被拦，但被记下

- **WHEN** 运营用手动命令触发一次动作，该账号该动作的配额已耗尽
- **THEN** 该动作 MUST 照常执行（手动跳过配额闸，操作员全权）
- **AND** 该动作 MUST 被记入计数（平台看见了它）
- **AND** 该账号后续的**自动**动作据此被闸拦下——手动动作消耗了自动预算，这是预期结果

#### Scenario: 飞行途中状态翻转不销毁证据

- **WHEN** 一次动作通过预闸后开始执行，执行期间账号因平台信号被降为 `restricted`，随后该动作的回执抵达
- **THEN** 该动作照常记入计数（它已经发生）
- **AND** 该账号后续动作仍被 `restricted` 正常拦截（拦的是未来，不是过去）

#### Scenario: 紧窗口的拒绝不得污染松窗口的账本

- **WHEN** 某账号在一小时内真实完成 N 次同一动作，而该动作的小时配额小于 N、日配额不小于 N
- **THEN** 当日计数为 N（每一次都记下）
- **AND** 日配额据此如实递减，MUST NOT 出现「日账本只记到小时上限、于是日闸误判尚有余量」

### Requirement: Facebook group join is a first-class rate-limited action

Facebook group join SHALL be a rate-limited action alongside browse/like/collect/comment, subject to the existing minute/hour/day sliding-window quotas, the three quota tiers, and risk-state scaling (warned slows all actions; restricted/frozen stops joining). A brand-new account SHALL be throttled by selecting the conservative tier rather than a bespoke warmup function. Join attempts MUST be pre-gated before dispatch.

The join quota is a **risk budget**: it bounds how much join activity the platform observes from the account. It therefore SHALL count **join actions that actually reached the platform**, not joins that succeeded. A join action reaches the platform when the edge reports that it actually performed the click on the live page (`clicked: true`); whether the group then admits the account (`ok: true`), leaves the request awaiting an admin (`ok: false, reason: 'pending'`), or demands a questionnaire is the platform's answer to an action we already took, and MUST NOT determine whether that action counted.

This MUST NOT be conflated with counting on dispatch. **Dispatch is intent; a click is an accomplished fact.** The cloud MUST NOT count a join because it sent a command — a command may never arrive or never execute. It MUST count only the edge's after-the-fact report that the click really happened. An attempt that never reached the platform — a pre-click observation that the request was already pending, an account that was already a member, an observation-only (shadow) run, a navigation or login failure before the click — reports `clicked: false` and MUST NOT count.

Counting a reached-platform join against the quota MUST NOT mark that join as successful. Success and quota are separate questions with separate answers: the success ledger continues to recognise only a judgment-confirmed join, and a counted-but-unconfirmed join MUST NOT enter the display interaction ledger, MUST NOT be reported to the operator as a completed join, and MUST NOT satisfy any requirement that depends on membership.

A **quota-usage display** is not a membership claim, and the two MUST NOT be conflated. A surface whose subject is budget consumption — how much of an action's daily allowance the account has spent — reports **actions spent**; for joins that means join actions that reached the platform, and showing a pending-approval join there is correct, not an overclaim. The surfaces whose subject is membership — which groups the account actually belongs to — MUST continue to count only judgment-confirmed joins. The same word may therefore denote an action on a budget surface and a membership on a ledger surface; each surface MUST be honest about its own subject rather than forced to the other's meaning.

The recorded-action counter SHALL faithfully hold every join action that reached the platform, including one made outside the automatic gate and one whose account was throttled mid-flight — see "互动发生后必须按账号持久计数". The confirmed-join ledger remains an independent count answering a different question. Gates MAY enforce either or both against the cap; where both are enforced, that MUST be understood as belief in two honest measurements rather than as a defect to be unified away, and a gate MUST NOT be relaxed onto a count that is looser than one it already enforces.

#### Scenario: Join quota denial prevents dispatch
- **WHEN** the risk gate denies a join for an account that has exhausted its minute, hour, or day join quota
- **THEN** no join is dispatched and a quota-denied non-success outcome is recorded

#### Scenario: A join that reached the platform counts even when approval is pending
- **WHEN** the edge reports a join in which it performed the click and the request is left awaiting group-admin approval
- **THEN** the account's join quota counter increases by one
- **AND** the join is NOT recorded as a successful or confirmed join
- **AND** the operator is not told the group was joined

#### Scenario: An attempt that never reached the platform does not count
- **WHEN** the edge reports a join outcome in which it did not perform the click — the request was already pending before this attempt, the account was already a member, the run was observation-only, or navigation or login failed first
- **THEN** the account's join quota counter does not increase
- **AND** no successful join interaction is recorded

#### Scenario: Dispatch alone still never counts
- **WHEN** the cloud dispatches a join command and no edge report of an actual click is received
- **THEN** the account's join quota counter does not increase
- **AND** the quota is never spent on intent that the edge did not confirm as actuated

#### Scenario: A quota-usage display shows actions spent, not memberships
- **WHEN** an operator views a per-account quota-usage display after the account performed one join click that is awaiting group-admin approval
- **THEN** the join budget shows one action spent against the cap
- **AND** the surfaces that report group membership still show zero groups joined and one request awaiting approval
- **AND** neither surface is required to adopt the other's meaning

#### Scenario: Only verified join counts as a successful join
- **WHEN** a join attempt returns anything other than a judgment-confirmed join
- **THEN** no successful join interaction is recorded for that account
- **AND** the success ledger's count of groups joined today is unchanged

#### Scenario: A join made outside the automatic gate still counts
- **WHEN** an operator's manual join bypasses the pre-dispatch quota gate by design, performs the click, and its receipt reaches the cloud while the hour window is already saturated
- **THEN** the account's join quota counter increases by one
- **AND** the automatic join loop reads that true count and does not resume on a short one

#### Scenario: Restricted state stops joining
- **WHEN** an account's risk state is restricted or frozen
- **THEN** the join loop for that account does not dispatch, inheriting the same state scaling as other interactions
