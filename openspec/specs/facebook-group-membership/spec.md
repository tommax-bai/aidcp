# facebook-group-membership Specification

## Purpose
TBD - created by archiving change facebook-group-join-and-commenting. Update Purpose after archive.
## Requirements
### Requirement: Group join is disabled by default and fails closed

Facebook group joining SHALL be controlled by a global kill switch that defaults off. When disabled, missing, invalid, or false, no join path MUST navigate to join, click Join, record risk, or claim a membership. Per-account `accounts.status` and platform matching MUST also gate work, and a per-group `enabled=false` MUST exclude that group from assignment and joining.

#### Scenario: Default off prevents joining
- **WHEN** the cloud process starts without enabling the group-join switch
- **THEN** no group is joined or risk-recorded, even if group targets and Facebook accounts exist

#### Scenario: Disabled group is excluded
- **WHEN** a group target has `enabled=false`
- **THEN** it is never assigned to an account and never navigated to for a join attempt

### Requirement: Operator bulk-imports group targets that are deduplicated

The system SHALL let the operator bulk-import Facebook group URLs into a shared catalog, deduplicating on the canonical group URL, and expose per-group status. Import MUST NOT create duplicate rows for the same group.

#### Scenario: Duplicate import is deduplicated
- **WHEN** the operator imports a batch containing a group URL already present in the catalog
- **THEN** the catalog keeps a single row for that group and does not create a duplicate

### Requirement: Targets are lazily claimed under an atomic one-group-one-account lock with orphan reclaim

An account with join budget and no pending assignment SHALL atomically claim the next available unjoined, non-gated target whose scope contains that account's current non-empty `accounts.group_label`, such that no two accounts can hold the same group. An ungrouped account, an account whose group has no mapped target, or an account whose mapped targets are already globally owned MUST receive no target and MUST NOT fall back to the global catalog. A claimed-but-not-joined assignment held by an offline or paused account MUST be released after a bounded idle TTL so it does not permanently lock the target. Multiple account-group scopes on one target MUST NOT weaken the existing global one-group-one-account uniqueness constraint.

#### Scenario: Concurrent claim of the same group yields one owner
- **WHEN** two accounts from different mapped account groups attempt to claim the same target concurrently
- **THEN** exactly one account holds the assignment and the other receives no row for that target and proceeds only to another target in its own mapped scope

#### Scenario: Stale assignment is reclaimed
- **WHEN** an account holds an `assigned`/`joining` row that has not progressed past the idle TTL
- **THEN** the assignment is released back to the scoped pool and becomes claimable only by an account whose current group remains mapped to it

#### Scenario: Ungrouped account fails closed
- **WHEN** a Facebook account has `group_label=null` and requests the next target
- **THEN** it receives `no_targets` and no membership row is created, even if the global target catalog contains enabled unassigned groups

#### Scenario: No global fallback for unmapped group
- **WHEN** an account belongs to “华东组” but all enabled targets are mapped only to “招聘组”
- **THEN** it receives `no_targets` and does not claim a target from “招聘组”

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

自动加群和裸 `/comment --join` SHALL 在导航或点击前重新读取账号当前分组并确认目标仍映射该分组。`assigned` 或 `joining` 分配失配时 MUST 以条件写释放该未完成 membership、返回可诊断的范围失配/无目标结果，且不得导航或点击。已记录为 `joined`、`pending`、`gated` 或其它平台/判断终态的 membership MUST 保留真实事实；移除 scope 只影响未来候选，MUST NOT 把已加入伪写为 `left` 或删除。

#### Scenario: 认领后账号换组则执行前释放
- **WHEN** 账号在认领群 G 后、导航前从“华东组”改到“招聘组”，而 G 未映射“招聘组”
- **THEN** scheduler 释放该未完成分配并返回 scope mismatch，不打开 G 的页面、不点击加入

#### Scenario: 移除范围不伪造退群
- **WHEN** 群 G 已为账号 A 记录 `joined`，运营随后从 G 移除 A 当前分组的 scope
- **THEN** G 的 joined membership 保持不变；系统不声称 A 已退群，G 只是不再作为未来候选

