# facebook-group-comment-coverage Specification

## Purpose
TBD - created by archiving change facebook-group-join-and-commenting. Update Purpose after archive.
## Requirements
### Requirement: Daily coverage iterates an account's joined groups oldest-covered-first

The coverage loop SHALL, per account per day, select from that account's own joined groups the least-recently-covered ones past a per-group cooldown floor, then pick within a small window to avoid lock-step ordering. It MUST guarantee eventual coverage of every joined group without repeatedly commenting in the same few groups, and MUST only comment in groups the account itself has joined.

#### Scenario: Coverage rotates and does not hammer
- **WHEN** an account has many joined groups and a daily coverage slice
- **THEN** the least-recently-covered eligible group is chosen and a just-commented group is not selected again until its cooldown floor passes

#### Scenario: Only joined groups are commented
- **WHEN** the coverage loop runs for an account
- **THEN** it never comments in a group that account has not joined

### Requirement: The comment-source switch is per-account, never global

Switching a Facebook account's comment source from operator-configured containers to the joined-group ledger SHALL be controlled per account (allowlist). A single global boolean that switches all Facebook accounts at once MUST NOT be used, so single-account staged rollout does not affect other accounts.

#### Scenario: Enabling coverage for one account leaves others unchanged
- **WHEN** the operator enables joined-group coverage for one Facebook account
- **THEN** other Facebook accounts continue using their existing operator-configured comment source unchanged

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

The coverage loop SHALL enforce a join-to-first-comment warmup interval: a group becomes eligible for coverage only after a bounded delay following its `joined_at`, so an account does not join and immediately comment in the same group on the same day.

#### Scenario: Same-day join is not commented
- **WHEN** an account joined a group earlier the same day
- **THEN** the coverage loop does not select that group until the warmup interval has elapsed

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

