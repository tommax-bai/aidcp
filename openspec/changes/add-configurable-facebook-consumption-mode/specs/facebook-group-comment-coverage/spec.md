## RENAMED Requirements

- FROM: `### Requirement: An account does not comment in a group the day it joined it`
- TO: `### Requirement: Join-to-first-comment eligibility uses a revisioned backend interval`

## MODIFIED Requirements

### Requirement: Daily coverage iterates an account's joined groups oldest-covered-first

The coverage selector SHALL, per account, select from that account's own joined groups the least-recently-covered ones past a per-group cooldown floor, then pick within a small window to avoid lock-step ordering. It MUST guarantee eventual coverage of every joined group without repeatedly commenting in the same few groups, and MUST only comment in groups the account itself has joined. When no joined group satisfies warmup/cooldown and the relaxed fallback is enabled, the selector SHALL fall back to joined groups ordered least-recently-commented; the relaxed result MUST be flagged for human review and MUST still exclude non-joined or left groups.

**放开兜底的默认极性 SHALL 为关闭**，且 MUST 只能由显式配置开启。缺少配置、配置为空或取值无法识别时，选群口 SHALL 走严格模式：一个合规群都没有就本轮不评论，MUST NOT 退而求其次去评一个不满足预热或仍在冷却中的群。

该默认值 MUST 由代码承载，MUST NOT 仅依赖运行时配置来维持。理由是失效模式：运行时配置文件不进版本库、部署时被显式排除，因此「它应该是关的」这件事在代码库里没有任何记录；换机、重建或从更早备份恢复都会让它静默回到开启，而且**不报错、不告警、日志里也看不出来**。把默认极性放在代码里，是让这条安全姿态跟着版本走、而不是跟着某一台机器上的一个文件走。

放开兜底 SHALL 被理解为一次**具名的临时放宽**，而不是一个常备档位：它在最需要预热与冷却的时刻把这两道闸丢掉，因此开启它 MUST 是一个显式且可追溯的决定。

Consumption-mode historical-group selection SHALL always use the strict path. It MUST NOT consult, inherit, or be relaxed by the ordinary coverage fallback setting, even when an operator has explicitly enabled that setting for ordinary coverage. A consumption selection with no timestamp-eligible joined group SHALL remain a truthful `waiting_target` obligation and MUST NOT choose a warmup-ineligible or cooldown-ineligible group.

For consumption selection, group eligibility SHALL be determined only from authoritative membership/comment timestamps: `joined_at` MUST satisfy the current group-comment policy's `joinToFirstCommentHours`, and the latest confirmed group-comment timestamp MUST satisfy the independent 72-hour re-comment cooldown. The 72-hour cooldown MUST NOT be derived from, replaced by, or reset when `joinToFirstCommentHours` changes. The selector MUST NOT additionally exclude either of the two groups newly joined in the current consumption cycle; either group MAY be selected if and only if the same timestamp predicates already make it eligible.

#### Scenario: Coverage rotates and does not hammer
- **WHEN** an account has many joined groups and a daily coverage slice
- **THEN** the least-recently-covered eligible group is chosen and a just-commented group is not selected again until its cooldown floor passes

#### Scenario: Only joined groups are commented
- **WHEN** the coverage selector runs for an account
- **THEN** it never comments in a group that account has not joined

#### Scenario: Relaxed fallback still chooses least-recently-commented joined groups
- **WHEN** all of an account's joined groups are inside warmup or cooldown and relaxed fallback is enabled
- **THEN** the selector chooses from `status='joined'` groups ordered by least-recently-commented and flags the result as relaxed for review

#### Scenario: 未配置时走严格模式
- **WHEN** 放开兜底的配置缺失、为空或取值无法识别，且账号名下所有已加入群都处在预热期或冷却中
- **THEN** 本轮不评论、不加群，如实回报无可用目标，MUST NOT 选中任何不合规的群

#### Scenario: 只有显式开启才放开
- **WHEN** 运维显式把放开兜底配置为开启，且账号名下所有已加入群都不合规
- **THEN** 选群口按最久没评排序选出一个已加入群，并把结果标记为放开态交人把关

#### Scenario: Consumption never uses the relaxed fallback
- **WHEN** consumption reaches its confirmed-join comment threshold, no joined group satisfies both timestamp gates, and ordinary coverage relaxation is explicitly enabled
- **THEN** consumption keeps one named `waiting_target` obligation and does not select, open, or comment in any group

#### Scenario: Join wait does not weaken the re-comment cooldown
- **WHEN** `joinToFirstCommentHours` is lowered but a joined group received a confirmed comment less than 72 hours ago
- **THEN** that group remains ineligible for consumption until the independent 72-hour re-comment cooldown elapses

#### Scenario: Current-cycle groups receive no extra exclusion
- **WHEN** consumption has just confirmed its second new join and one of those two groups already satisfies both timestamp predicates
- **THEN** that group remains in the strict candidate set and is not excluded merely because it was joined in the current cycle

### Requirement: Join-to-first-comment eligibility uses a revisioned backend interval

The ordinary coverage loop SHALL enforce the target-scoped Facebook group-comment policy's revisioned `joinToFirstCommentHours`: a group becomes eligible for unpinned coverage only when the current time is at least that many hours after its authoritative `joined_at`. The server SHALL own and return the field's integer-hours bounds and default; the initial default SHALL be 24 hours. A missing persisted row SHALL resolve through the explicitly reported legacy-environment/default migration chain, and an invalid type, fractional value, or out-of-range value SHALL reject the entire policy write rather than clamp or partially apply it.

Each coverage run or waiting consumption obligation SHALL read the current group-comment policy immediately before selecting a target, then pin that revision with the selected group. A later timing update MUST NOT invalidate or retarget a group already selected and dispatched under an older revision, while an obligation that is still waiting for a target SHALL be re-evaluated under the new revision. Eligibility MUST NOT depend on calendar-day boundaries, the group being described as old or new, the current consumption cycle's two joined-group identities, list position, or any hidden age category. Ordinary coverage, persona-mode comments and standalone automatic joins MUST apply the same timestamp predicate.

The sole exception SHALL be a caller-pinned group joined by the same fixed Facebook rule batch. After the join stage returns platform-confirmed `joined` or `already_member` for the exact group, slow start is confirmed not active, and every comment/contact/approval/risk gate passes, that batch MAY continue to a contact comment without waiting for ordinary coverage warmup. The exception MUST NOT make the group generally warmup-eligible, MUST NOT apply to an ambiguous/pending/failed join, and MUST NOT be inferred from a bare group URL or membership row without the rule batch correlation.

#### Scenario: Same-day ordinary coverage is not commented under the default
- **WHEN** an account joined a group earlier the same day, the pinned policy uses the default 24-hour interval and an unpinned coverage run considers it
- **THEN** the coverage loop does not select that group until 24 hours after its authoritative `joined_at`

#### Scenario: Configured interval is evaluated by elapsed time
- **WHEN** the current group-comment policy configures an in-range `joinToFirstCommentHours` and that exact elapsed duration passes after a group's `joined_at`
- **THEN** the group passes the join-to-first-comment predicate regardless of calendar date or which consumption cycle joined it, subject to the independent re-comment cooldown and remaining gates

#### Scenario: Server-provided bounds reject an invalid update
- **WHEN** an operator submits a timing value outside the bounds returned by the server schema
- **THEN** Cloud rejects the complete group-comment policy write, preserves the current revision and returns the field-specific validation reason

#### Scenario: Confirmed rule batch may continue in its pinned group
- **WHEN** the same Facebook rule batch joined exact group G with a platform-confirmed result, slow start is not active and all comment gates allow
- **THEN** the batch may select and contact-comment in pinned group G without making G available to ordinary coverage

#### Scenario: Slow start prevents the scoped exception
- **WHEN** slow start becomes active before the rule batch's comment dispatch
- **THEN** the comment is not dispatched and the join-to-first-comment exception is not applied

#### Scenario: Unconfirmed join never receives the exception
- **WHEN** the rule batch's join result is pending, ambiguous, gated, failed or lacks the exact confirmed group identity
- **THEN** no comment starts and ordinary warmup behavior remains unchanged

## ADDED Requirements

### Requirement: Join-to-first-comment timing has a backend configuration authority

Cloud SHALL persist one Facebook group-comment policy for each local `execution_target`, containing integer `joinToFirstCommentHours`, monotonically increasing `revision`, and audit metadata. The initial server bounds SHALL be `1..168` hours and the default SHALL be 24 hours. This setting SHALL remain distinct from the existing same-group re-comment cooldown and changing it MUST NOT reset or replace that cooldown.

`GET /api/facebook/groups/comment-policy` SHALL return the local target's committed value, revision, server bounds/default, update metadata, and `source=db|legacy_env|default`. `PUT /api/facebook/groups/comment-policy` SHALL accept only the full value, `expectedRevision`, and optional reason. It MUST compare-and-swap, append an immutable before/after audit record, and return a database write-after-read. Unknown fields, stale revision, invalid bounds, or unavailable storage MUST fail without partial mutation.

During additive migration only, a missing database row SHALL fall back first to `AIDCP_FB_GROUP_COVERAGE_WARMUP_HOURS` and then to 24, while reporting the source. The fallback MUST NOT be treated as a committed revision and SHALL be removed only by a later explicit cleanup after each runtime target has a persisted row.

The management Console SHALL provide this setting on `/facebook-groups` under the label “入群后首次评论等待（小时）”, display the independent same-group re-comment cooldown separately, use server-provided bounds and `expectedRevision`, and show only write-after-read truth. It MUST NOT call either value generically “群组冷却”.

#### Scenario: Default and legacy source are explicit

- **WHEN** the local execution target has no persisted group-comment policy
- **THEN** Cloud returns the validated legacy environment value when present or 24 otherwise
- **AND** marks the source without fabricating a database revision

#### Scenario: Valid write becomes current truth

- **WHEN** an operator writes an in-range value with the current `expectedRevision`
- **THEN** Cloud atomically creates one next revision and one matching audit row
- **AND** all later unpinned target selections on that execution target use the committed value

#### Scenario: Stale timing editor cannot overwrite

- **WHEN** an operator submits an `expectedRevision` older than the committed group-comment policy
- **THEN** Cloud returns a conflict and current projection without changing the value or adding a success audit row

#### Scenario: Console distinguishes the two intervals

- **WHEN** an operator opens `/facebook-groups`
- **THEN** the Console labels join-to-first-comment waiting and same-group re-comment cooldown as separate concepts
- **AND** editing the former does not claim to edit the latter

### Requirement: Consumption opens the first commentable item from the top of the selected group

After Cloud strictly selects one timestamp-eligible joined group for a consumption comment, it SHALL issue the existing atomic group-post open action with the explicit selector `first_commentable_group_post` and the exact selected group identity. This selector MUST ignore configured search keywords and MUST scan from the top of the current discussion stream for the first item on which the account can comment. A pinned item MAY satisfy the selector and counts as first when it is the topmost commentable item encountered.

The open result MUST bind the group identity and exact post identity used by the ordinary comment approval, risk, target-freshness and confirmed-outcome path. If no commentable item is found in the bounded scan, the result SHALL be an honest named no-op. Consumption MUST NOT search for a more desirable post, switch to keyword selection, skip a commentable pinned item merely because it is pinned, or fall back to another group after opening the selected group.

#### Scenario: Pinned first item is commentable
- **WHEN** the selected group's top discussion item is pinned and exposes a valid comment control
- **THEN** `first_commentable_group_post` selects that pinned item as the exact comment target

#### Scenario: Non-commentable items are skipped from the top
- **WHEN** the first items encountered from the top have no valid comment control and a later item does
- **THEN** the selector returns that first later commentable item without applying keyword or content-quality ranking

#### Scenario: No commentable item is an honest no-op
- **WHEN** the bounded top-down scan finds no commentable group post
- **THEN** no comment is composed or dispatched, the batch records the named no-target result, and no alternative group or selector is tried
