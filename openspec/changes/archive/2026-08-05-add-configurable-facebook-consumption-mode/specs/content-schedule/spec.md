## RENAMED Requirements

- FROM: `### Requirement: Unified account automation exposes Facebook rule mode without treating it as a content action`
- TO: `### Requirement: Unified account automation projects Facebook operation mode without becoming its authority`

## MODIFIED Requirements

### Requirement: Facebook 自动加群按账号独立配置且默认关闭

系统 SHALL 为 Facebook 账号提供独立 `join_group` 自动化配置：动作开关、受限非负整数每日上限、可选 168 位动作周历覆盖、更新人/时间以及最近一次 scheduled 执行结果。无配置行、开关关闭、日上限为 0、非 Facebook 账号、全局 kill switch 关闭或权威生效 operation mode 不是 `persona` 任一 SHALL 完全不触发独立定时自动加群。该动作 SHALL 聚合进统一账号自动化目录，但其领域配置 MUST 与通用发帖/评论字段分开持久化。最近结果 MUST 来自带 `scheduled` 来源的真实审计，不能用人工结果或 membership 更新时间猜测。

内容排期配置 SHALL 只负责独立定时加群的开关、上限与时窗，MUST NOT 持久化、写入、覆盖或推导 Facebook operation mode 或 policy revision。调度器 MUST 从 environment operation-policy 权威口读取唯一生效模式；模式投影未知、陈旧、冲突或不可用时 MUST fail closed，MUST NOT 猜成 `persona`。`slow_start`、`rule` 与 `consumption` 模式 SHALL 在目标认领前跳过独立定时触发，且该跳过 MUST NOT 消耗小时 fire key、制造一次 scheduled 结果或冒充执行失败。

上述限制只约束独立定时触发源，MUST NOT 关闭既有原子加群执行器。`slow_start`、`rule`、`consumption` 或其它具名编排只有在各自契约授权的阶段 MAY 调用该执行器，并仍须逐次通过分组范围、风险、会话、精确目标、点击与平台确认闸；这类调用 MUST 归属其模式批次，MUST NOT 记成内容排期 scheduled 自动加群。

自动加群日上限的硬上限 SHALL 为 50（越界整块拒）。三个动作的硬上限 SHALL 各自独立、MUST NOT 相互推导：发帖与评论为 50、**联系评论为 10**、自动加群为 50。联系评论那个 10 是刻意与其余动作分开的既有约定，本要求 MUST NOT 被读作把它一并抬高。

硬上限 SHALL 只约束**运营可配置的天花板**，MUST NOT 改变生效值的计算规则：既有的「账号配置 MUST NOT 提高 RiskController 日额度或会话额度」保持不变，实际每日准入仍取账号配置与风控日额度的较小者，并逐次通过 `canDo('join_group')` 与剩余会话预算。因此抬高硬上限本身 SHALL NOT 使任何账号的实际加群量增加；增量只能来自运营对风控配额与会话预算的显式调整。

硬上限的事实源 SHALL 是契约层单一常量，写前校验、后台输入框上限下发与配置表约束三处 MUST 全部由它派生或与它逐字一致；任一处漂移 SHALL 被视为缺陷，MUST NOT 依赖「写入端更严即安全」来掩盖。

**「默认关闭」的适用范围**：本要求标题所称的默认关闭，SHALL 理解为「系统不会凭空为一个没有配置行的账号触发自动加群」。它 SHALL NOT 被读作「任何账号在任何情况下都必须以关闭状态起步」——真正首次登记的 Facebook 账号会被种入开启状态的配置行（见「新登记 Facebook 账号种入自动化默认配置」）。对**仍然没有配置行**的账号，本要求第一段的「无配置行即完全不触发」逐字保留、不受种入影响。

#### Scenario: 未配置账号不自动加群
- **WHEN** Facebook 账号没有自动加群配置行，即使全局 kill switch、风险额度和群目标都可用
- **THEN** 内容调度器不认领目标、不导航、不点击，也不记录一次伪执行

#### Scenario: 最近结果只取自动来源
- **WHEN** 账号最新审计是人工指定 URL 加群，而更早有一条 scheduled 自动结果
- **THEN** 账号自动化页显示更早的 scheduled 结果，不把人工结果冒充成自动执行结果

#### Scenario: 日上限可配到 50
- **WHEN** 运营为某 Facebook 账号把自动加群日上限设为 50
- **THEN** 写前校验放行、配置表约束放行、后台输入框允许输入该值，配置成功落库

#### Scenario: 超过 50 整块拒
- **WHEN** 运营把自动加群日上限设为 51
- **THEN** 写入被整块拒绝并回可诊断原因，MUST NOT 静默截断为 50 落库

#### Scenario: 抬高硬上限不放大实际加群量
- **WHEN** 某账号自动加群日上限配为 50，而该账号当前风控档位的 `join_group` 日额度为 3
- **THEN** 当日至多加入 3 个群，超出后不认领、不点击并记录可诊断拒因，MUST NOT 因账号配置为 50 而突破风控额度

#### Scenario: 联系评论硬上限不受本次抬升影响
- **WHEN** 运营把联系评论日上限设为 11
- **THEN** 写入仍被整块拒绝（其硬上限保持 10），MUST NOT 因自动加群硬上限抬到 50 而放宽

#### Scenario: 存量无行账号仍不自动加群
- **WHEN** 一个已存在但从未配过自动加群的 Facebook 账号上线
- **THEN** 它仍然没有配置行，因而不触发任何自动加群——种入只作用于真正新登记的账号

#### Scenario: Persona 模式才触发独立定时加群
- **WHEN** Facebook 账号的自动加群配置、当前时窗及全部既有闸均放行，且权威生效模式为 `persona`
- **THEN** 内容调度器可认领一次具名 scheduled 加群，而不要求任何第二个模式开关

#### Scenario: 非 persona 模式不继承排期触发
- **WHEN** 独立加群时槽到达而权威生效模式为 `slow_start`、`rule` 或 `consumption`
- **THEN** 内容调度器在认领目标前跳过，不导航、不点击、不消耗 fire key，也不写一条伪 scheduled 结果

#### Scenario: 模式编排仍可调用原子加群
- **WHEN** rule 或 consumption 编排到达其自身契约授权的加群阶段
- **THEN** 它可在全部既有闸下调用原子加群执行器，且结果归属该模式批次而非内容排期

#### Scenario: 内容排期写入不改变 operation mode
- **WHEN** 运营修改账号的自动加群开关、日上限或动作周历
- **THEN** 写入只改变 `join_group` 排期配置，MUST NOT 创建 policy revision、切换 operation mode 或覆盖环境策略

### Requirement: Unified account automation projects Facebook operation mode without becoming its authority

The unified account automation catalog and Facebook-filtered view SHALL expose the account's authoritative configured and effective operation mode, policy revision, current binding/runtime blockers, and mode-appropriate progress. For `rule`, the projection SHALL include collecting progress, the current round's position in its configured cycle and latest round summary. For `consumption`, it SHALL include the current revision's view, confirmed-like, confirmed-join and comment-stage progress. The catalog MUST obtain this data from the environment operation-policy and runtime authorities and MUST render unknown/unavailable when either projection cannot be read.

The content-schedule write path MAY continue to update its native content-action and scheduled-join fields, but it MUST NOT validate, persist, mutate or override Facebook operation mode, cadence parameters or policy revision. `/content-schedule` SHALL provide no rule/consumption mode toggle or cadence editor; authoritative policy writes belong to the environment-keyed operation-policy surface and use its compare-and-swap contract. The operation policy MUST remain a distinct environment domain record and MUST NOT be encoded as a `post`, `comment`, `contact_comment` or `join_group` mode, daily cap, hour-cell trigger, account-keyed fallback, or combination of legacy booleans. The all-platform summary MAY show the effective Facebook mode but MUST NOT expose an unsupported editor for other platforms.

The behaviour summary rendered for an account MUST describe the cadence that its stored policy revision actually encodes. It MUST NOT display a cadence taken from compiled-in constants when the stored definition differs, and it MUST NOT present unavailable policy data as persona mode, disabled, or zero progress.

#### Scenario: Facebook view exposes authoritative operation mode
- **WHEN** the operator filters account automation to Facebook and the authoritative policy projection is available
- **THEN** each Facebook row shows the configured/effective operation mode, revision, mode-appropriate behavior summary and authoritative runtime status
- **AND** rule mode still distinguishes both configured cadence tiers and current progress

#### Scenario: Other platform views have no operation-mode control
- **WHEN** the operator filters account automation to Xiaohongshu or WeChat Channels
- **THEN** no Facebook operation-mode control is rendered and a forged server policy write for that platform remains rejected

#### Scenario: Rule mode is not an hourly content action
- **WHEN** the account reaches the configured number of confirmed rule views outside any content-action hash minute
- **THEN** the rule round may be created from its count trigger without consuming or fabricating an hourly `content_schedule` fire key

#### Scenario: Join-contact frequency is reported as its own tier
- **WHEN** the operator inspects a Facebook account running rule mode
- **THEN** the view distinguishes the view-to-like tier from the round-to-join-contact tier and MUST NOT present a single combined counter

#### Scenario: Content schedule cannot switch operation mode
- **WHEN** an operator views a Facebook row on `/content-schedule`
- **THEN** the effective mode, revision, progress and blockers are read-only projections
- **AND** no control or hidden write can switch between `persona`, `slow_start`, `rule` and `consumption` or change their cadence

#### Scenario: Unavailable policy truth is not fabricated
- **WHEN** the operation policy, environment binding or runtime projection is unavailable, stale or conflicting
- **THEN** the catalog shows a named unknown/unavailable state and MUST NOT infer persona mode, disabled state, zero counters or write success

### Requirement: Standalone Facebook automatic join remains join-only

The independent scheduled Facebook `join_group` action SHALL continue to invoke only the Facebook group-join scheduler and SHALL be admitted only while the authoritative effective operation mode is `persona`. Enabling or executing that action MUST NOT implicitly start post selection, composition, approval, or either ordinary or contact comment submission. An effective `slow_start`, `rule`, or `consumption` mode MUST suppress this independent scheduled trigger before assignment and MUST NOT consume or fabricate its schedule fire.

This trigger restriction MUST NOT disable the existing atomic join executor. A non-persona mode MAY invoke that executor only through its own explicitly specified orchestration, under the existing scope, ownership, risk, session, exact-target and platform-confirmation gates. Such an invocation MUST remain attributed to its mode batch and MUST NOT be recorded as the standalone scheduled action.

#### Scenario: Standalone automatic join has no comment side effect
- **WHEN** the independent Facebook automatic-join action confirms a new membership in effective `persona` mode
- **THEN** it records the join outcome and ends without opening a group post or creating a comment

#### Scenario: Non-persona mode suppresses standalone scheduled join
- **WHEN** the independent automatic-join time arrives while effective mode is `slow_start`, `rule` or `consumption`
- **THEN** the standalone scheduler does not assign, navigate, click or record a synthetic result

#### Scenario: Consumption join does not become a scheduled join
- **WHEN** consumption reaches its confirmed-like threshold and invokes the atomic join executor
- **THEN** the join remains part of the consumption batch, does not consume the standalone schedule fire and does not implicitly comment in the newly joined group
