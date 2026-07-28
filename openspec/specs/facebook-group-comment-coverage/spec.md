# facebook-group-comment-coverage Specification

## Purpose
TBD - created by archiving change facebook-group-join-and-commenting. Update Purpose after archive.
## Requirements
### Requirement: Daily coverage iterates an account's joined groups oldest-covered-first

The coverage selector SHALL, per account, select from that account's own joined groups the least-recently-covered ones past a per-group cooldown floor, then pick within a small window to avoid lock-step ordering. It MUST guarantee eventual coverage of every joined group without repeatedly commenting in the same few groups, and MUST only comment in groups the account itself has joined. When no joined group satisfies warmup/cooldown and the relaxed fallback is enabled, the selector SHALL fall back to joined groups ordered least-recently-commented; the relaxed result MUST be flagged for human review and MUST still exclude non-joined or left groups.

#### Scenario: Coverage rotates and does not hammer
- **WHEN** an account has many joined groups and a daily coverage slice
- **THEN** the least-recently-covered eligible group is chosen and a just-commented group is not selected again until its cooldown floor passes

#### Scenario: Only joined groups are commented
- **WHEN** the coverage selector runs for an account
- **THEN** it never comments in a group that account has not joined

#### Scenario: Relaxed fallback still chooses least-recently-commented joined groups
- **WHEN** all of an account's joined groups are inside warmup or cooldown and relaxed fallback is enabled
- **THEN** the selector chooses from `status='joined'` groups ordered by least-recently-commented and flags the result as relaxed for review

### Requirement: Auto contextual comments run unattended and carry no contact info

Mode (a) auto-generated contextual comments SHALL run on the existing unattended hard-validator path and MUST NOT contain contact info, URLs, or spam phrases (the existing Facebook validators reject these). This is the scalable daily-coverage mode.

#### Scenario: Contact info in an auto comment is rejected
- **WHEN** an auto contextual coverage comment would contain contact info
- **THEN** the existing validators reject it and no submit occurs, and it is not repaired into a post

### Requirement: Contact comments route through the human-reviewed lane, not the unattended path

Mode (b) contact/lead-gen comments SHALL route through the existing human-reviewed lane (per-account verbatim contact injection plus Feishu approval before the edge posts), never the unattended validator path. The account's contact string missing MUST fail closed (no post, no silent downgrade to a no-contact comment). A validator carve-out MUST exempt only the injected contact span, not the composed body.

#### Scenario: Contact comment requires approval before posting
- **WHEN** a contact/lead-gen comment is composed for a joined group
- **THEN** it is sent to Feishu human review and is posted only after a human approves it

#### Scenario: Missing contact string fails closed
- **WHEN** a contact comment is requested for an account with no configured contact string
- **THEN** the system produces an honest no-op and does not post a contactless comment

### Requirement: An account does not comment in a group the day it joined it

The ordinary coverage loop SHALL enforce a join-to-first-comment warmup interval: a group becomes eligible for unpinned coverage only after a bounded delay following its `joined_at`, so ordinary coverage, persona-mode comments and standalone automatic joins do not join and immediately comment in the same group on the same day.

The sole exception SHALL be a caller-pinned group joined by the same fixed Facebook rule batch. After the join stage returns platform-confirmed `joined` or `already_member` for the exact group, slow start is confirmed not active, and every comment/contact/approval/risk gate passes, that batch MAY continue to a contact comment without waiting for ordinary coverage warmup. The exception MUST NOT make the group generally warmup-eligible, MUST NOT apply to an ambiguous/pending/failed join, and MUST NOT be inferred from a bare group URL or membership row without the rule batch correlation.

#### Scenario: Same-day ordinary coverage is not commented
- **WHEN** an account joined a group earlier the same day and an unpinned coverage run considers it
- **THEN** the coverage loop does not select that group until the warmup interval has elapsed

#### Scenario: Confirmed rule batch may continue in its pinned group
- **WHEN** the same Facebook rule batch joined exact group G with a platform-confirmed result, slow start is not active and all comment gates allow
- **THEN** the batch may select and contact-comment in pinned group G without making G available to ordinary coverage

#### Scenario: Slow start prevents the scoped exception
- **WHEN** slow start becomes active before the rule batch's comment dispatch
- **THEN** the comment is not dispatched and the same-day warmup exception is not applied

#### Scenario: Unconfirmed join never receives the exception
- **WHEN** the rule batch's join result is pending, ambiguous, gated, failed or lacks the exact confirmed group identity
- **THEN** no comment starts and ordinary warmup behavior remains unchanged

### Requirement: Ledger demotion is not driven by unreliable whole-page signals

Demoting a membership from `joined` to `left` SHALL NOT be driven by an unreliable whole-page membership text signal. Demotion MUST require repeated confirmation across attempts, aligning with the anti-pollution stage/promote discipline. A group that is confirmed deleted or permanently inaccessible MUST also be demotable so it stops consuming coverage slots.

#### Scenario: A single ambiguous permission signal does not demote a valid membership
- **WHEN** one coverage attempt sees an ambiguous permission-gated signal in a group the account is actually a member of
- **THEN** the membership is not immediately demoted to `left`; demotion requires repeated confirmation

### Requirement: Coverage shares single-flight and activity budget with the join loop

The coverage loop and the join loop SHALL run on the same per-account single-flight so a Facebook edge (physically single-slot) is never asked to join and comment at once, and their combined daily activity MUST be bounded against platform tolerance rather than each cap being spent independently.

#### Scenario: Join and comment do not run concurrently on one account
- **WHEN** an account has both a pending join slot and a pending coverage slot
- **THEN** only one is dispatched at a time under the per-account single-flight lock

#### Scenario: Low membership degrades gracefully
- **WHEN** an account has very few joined groups
- **THEN** the per-group cooldown floor limits coverage to a small safe volume rather than repeatedly commenting the same groups, and zero joined groups is a clean no-op

### Requirement: Joined-group coverage selector is the normal Facebook comment container source

The Facebook comment pipeline SHALL use the joined-group coverage selector as the normal source of comment containers for unpinned Facebook comment attempts. The selector MUST only return groups the account itself has joined (`status='joined'`) and MUST return one concrete group URL for edge to use as `search.execute.container`. It MUST NOT return operator-configured container rows, random imported targets, or any whole-site search sentinel.

#### Scenario: Normal comment uses an account joined group
- **WHEN** an unpinned Facebook comment attempt starts for account A
- **THEN** the selected search container is one of account A's own joined membership rows and edge receives that group URL as the scoped search container

#### Scenario: No joined group does not fall back to legacy containers
- **WHEN** account A has no joined membership rows
- **THEN** the attempt ends with an honest no-targets result and MUST NOT fall back to legacy account-configured containers or whole-site search

