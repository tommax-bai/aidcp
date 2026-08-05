# facebook-group-membership Specification

## Purpose
TBD - created by archiving change facebook-group-join-and-commenting. Update Purpose after archive.
## Requirements
### Requirement: Operator bulk-imports group targets that are deduplicated

The system SHALL let the operator bulk-import Facebook group URLs into a shared catalog, deduplicating on the canonical group URL, and expose per-group status. Import MUST NOT create duplicate rows for the same group.

#### Scenario: Duplicate import is deduplicated
- **WHEN** the operator imports a batch containing a group URL already present in the catalog
- **THEN** the catalog keeps a single row for that group and does not create a duplicate

### Requirement: Targets are lazily claimed under an atomic one-group-one-account lock with orphan reclaim

An account with join budget and no pending assignment SHALL atomically claim the next available unjoined, non-gated target whose explicit scope either is `global` or is `restricted` and contains that account's current non-empty `accounts.group_label`, such that no two accounts can hold the same group. Global scope SHALL allow a Facebook account with any group label or no group label, but MUST still require a present, fresh Facebook account projection. A restricted ungrouped account, an account whose group has no mapped restricted target, or an account whose eligible targets are already globally owned MUST receive no target. A claimed-but-not-joined assignment held by an offline or paused account MUST be released after a bounded idle TTL so it does not permanently lock the target. Global scope and multiple account-group scopes MUST NOT weaken the existing global one-group-one-account uniqueness constraint.

#### Scenario: Concurrent claim of the same global group yields one owner
- **WHEN** two Facebook accounts from different account groups concurrently attempt to claim the same global target
- **THEN** exactly one account holds the assignment and the other receives no row for that target and proceeds only to another eligible target

#### Scenario: Stale assignment is reclaimed
- **WHEN** an account holds an `assigned`/`joining` row that has not progressed past the idle TTL
- **THEN** the assignment is released back to the pool and becomes claimable only by an account still eligible under the target's current global or restricted scope

#### Scenario: Ungrouped account may claim only global target
- **WHEN** a fresh Facebook account has `group_label=null` and requests the next target
- **THEN** it may claim an otherwise eligible `global` target but MUST NOT claim any `restricted` target

#### Scenario: No fallback from restricted scope
- **WHEN** an account belongs to “华东组” but all enabled restricted targets are mapped only to “招聘组”
- **THEN** it receives no restricted target and MUST NOT treat unrelated restricted targets as global

#### Scenario: Stale or non-Facebook projection cannot use global scope
- **WHEN** an account projection is stale, missing, or belongs to a non-Facebook platform while a global target exists
- **THEN** the account receives no target and no membership row is created

### Requirement: The edge join action reports observations and never decides the join gate from whole-page text

The edge `join_group` action SHALL navigate to the group, collect a scoped group-header observation, click Join at most once only when instructed, collect a post-click observation, and dismiss an optional post-join survey while never submitting a required membership questionnaire. The edge MUST NOT classify the join gate (public-instant vs approval-gated) from whole-page body text; it reports structured observations for the cloud judgment role to classify. A join receipt with `ok=true` MUST correspond to a real, member-now state.

#### Scenario: Edge reports observation instead of concluding
- **WHEN** the edge lands on a group page with an ambiguous membership signal
- **THEN** it reports the structured group-header observation and does not itself decide joined vs not-joined

#### Scenario: Required questionnaire is not submitted
- **WHEN** clicking Join opens a required membership questionnaire (approval-gated)
- **THEN** the edge does not submit it, leaves no dangling pending request beyond what is honestly reported, and returns `questionnaire_required`

### Requirement: A cloud judgment role classifies the join gate fail-closed

A cloud judgment role SHALL classify the edge's structured observation as instant-join, approval-gated, already-member, or ambiguous before any click, and classify the post-click observation as joined, pending/gated, or failed. When the classification is uncertain the role MUST choose skip (never click, never write a false `joined`). The role's input observation and verdict MUST be recorded for audit.

#### Scenario: Ambiguous observation is skipped, not joined
- **WHEN** the judgment role cannot confidently classify a group as instant-join
- **THEN** it returns a skip verdict and no Join click is issued

#### Scenario: Approval-gated group is not clicked
- **WHEN** the pre-click observation classifies the group as approval-gated
- **THEN** the join is skipped and the group is marked non-public without leaving a pending request

### Requirement: Membership is recorded only on a verified join and learned gating excludes the fleet

The membership ledger SHALL set `joined_at` and a `joined` status only when the judgment role confirms a real join from the edge observation. A group classified as approval-gated or requiring a questionnaire MUST be recorded as non-public (learned once) so the whole fleet stops attempting it. Account-transient failures (checkpoint/login/captcha) MUST pause that account's join loop and leave the group retryable rather than marking the group gated.

#### Scenario: Only verified join writes membership
- **WHEN** the edge returns anything other than a judgment-confirmed join
- **THEN** no `joined_at` is written and the account's verified-join count is not incremented

#### Scenario: Learned gating excludes the fleet
- **WHEN** any account learns that a group is approval-gated
- **THEN** the catalog marks that group gated and no account claims or attempts it again

### Requirement: Shadow mode observes and judges without joining

Group-join shadow mode SHALL navigate, collect observations, run the judgment role, and write audit rows, but MUST NOT click Join, record risk, or write a membership. Shadow output SHALL be auditable so join-gate classification accuracy can be measured before real joining is enabled.

#### Scenario: Shadow classifies but does not join
- **WHEN** shadow mode classifies a target as instant-join
- **THEN** it records the observation and verdict and does not click Join or write `joined`

### Requirement: Group join uses a distinct capability and never the browse capability string

The Facebook driver SHALL expose a distinct `join` capability for group joining and MUST NOT reuse the `browse` capability string (which would attach the xhs browse session on a Facebook edge). The `group.join` command MUST be routed through the Facebook command handler and MUST appear in the edge active-command whitelist so it is not silently dropped.

#### Scenario: Join does not attach a browse session
- **WHEN** a Facebook edge receives a `group.join` command
- **THEN** it is handled by the Facebook command handler without starting an xhs browse session or watchdog

### Requirement: 未完成群分配在执行前重新校验账号分组范围

自动加群和裸 `/comment --join` SHALL 在导航或点击前重新读取新鲜账号投影，并确认目标当前为 `global`，或目标为 `restricted` 且仍映射账号当前非空分组。`assigned` 或 `joining` 分配失配时 MUST 以条件写释放该未完成 membership、返回可诊断的范围失配/无目标结果，且不得导航或点击；投影陈旧时 MUST fail-closed 且不得误删合法分配。已记录为 `joined`、`pending`、`gated` 或其它平台/判断终态的 membership MUST 保留真实事实；修改 scope 只影响未来资格，MUST NOT 把已加入伪写为 `left` 或删除。

#### Scenario: 全局分配在账号换组后仍有效
- **WHEN** 账号认领全局群 G 后、导航前改变账号分组或变为未分组，且投影仍新鲜
- **THEN** 分配仍为 eligible，调度器可继续执行其它既有闸

#### Scenario: 受限认领后账号换组则执行前释放
- **WHEN** 账号在认领受限群 G 后、导航前从“华东组”改到“招聘组”，而 G 未映射“招聘组”
- **THEN** scheduler 释放该未完成分配并返回 scope mismatch，不打开 G 的页面、不点击加入

#### Scenario: 移除范围不伪造退群
- **WHEN** 群 G 已为账号 A 记录 `joined`，运营随后把 G 从 global 改为不匹配 A 的 restricted 范围
- **THEN** G 的 joined membership 保持不变；系统不声称 A 已退群，G 只是不再作为未来候选

#### Scenario: 投影陈旧既不放行也不误删
- **WHEN** 执行前账号投影已过新鲜期，无论目标当前为 global 或 restricted
- **THEN** 重验返回具名陈旧结果，不导航、不点击，也不删除现有未完成分配

### Requirement: Group join is controlled by scoped account automation and fails closed

Facebook independent time-scheduled unattended group joining SHALL be controlled by the account's explicit group-join automation configuration, active schedule window, platform match, account state, and authoritative effective operation mode. The scheduler MAY trigger only when that mode is `persona`. Effective `slow_start`, `rule`, or `consumption` mode MUST suppress the independent scheduled trigger before target assignment or navigation. The mode MUST be resolved from the environment operation-policy authority; an unavailable, unknown, conflicting, or stale projection SHALL fail closed and MUST NOT be guessed as `persona`.

The scheduled join path MUST NOT require a process-global automatic or shadow environment variable. A per-group `enabled=false` or scope mismatch MUST exclude that group from assignment and joining. Risk quota, session budget, pre-click observation/judgment, exact target and confirmed outcome remain mandatory.

This restriction governs the independent schedule trigger, not the atomic group-join executor. Rule, consumption, slow-start, manual, or other explicitly specified orchestration MAY invoke that existing executor only according to its own contract, while preserving all group scope, ownership, risk, session, target, observation, click and confirmation gates. Invoking the executor from a mode-specific orchestration MUST NOT create, consume, or impersonate an independent scheduled-join fire.

#### Scenario: Account automation off prevents joining
- **WHEN** an account's group-join automation configuration is disabled or its daily cap is zero
- **THEN** no independently scheduled group is joined or risk-recorded even if stale global join variables are enabled

#### Scenario: Account automation on needs no global switch
- **WHEN** account group-join automation and its current schedule slot are enabled, the effective mode is `persona`, and all target/risk/session gates pass
- **THEN** the scheduler may attempt one scoped join without requiring `AIDCP_FB_GROUP_JOIN_AUTO`

#### Scenario: Disabled group is excluded
- **WHEN** a group target has `enabled=false`
- **THEN** it is never assigned to an account and never navigated to for a join attempt

#### Scenario: Non-persona mode suppresses the independent scheduler
- **WHEN** the time-scheduled join slot arrives while the authoritative effective mode is `slow_start`, `rule`, or `consumption`
- **THEN** the scheduler does not assign a target, navigate, click, dispatch a join or create a synthetic scheduled outcome

#### Scenario: Mode-specific orchestration can use the atomic executor
- **WHEN** rule or consumption orchestration reaches its own contractually authorized join stage
- **THEN** it may invoke the atomic group-join executor subject to every existing scope, risk, session, exact-target and confirmed-outcome gate
- **AND** that invocation is attributed to the mode-specific batch rather than the independent schedule

#### Scenario: Unknown operation mode fails closed
- **WHEN** the scheduled join tick cannot resolve one authoritative fresh effective operation mode for the account's environment
- **THEN** it does not join, risk-record, or infer `persona`, and exposes the named policy or binding blocker

