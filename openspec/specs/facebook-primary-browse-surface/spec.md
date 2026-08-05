# facebook-primary-browse-surface Specification

## Purpose
TBD - created by archiving change configure-facebook-primary-browse-surface. Update Purpose after archive.
## Requirements
### Requirement: Facebook primary browse surface is environment-authoritative

Cloud SHALL persist one primary browse surface, `feed` or `reels`, for every Facebook environment. The surface SHALL have its own compare-and-swap revision and immutable audit history, separate from the operation-mode revision. A surface-only write MUST NOT supersede, reset, reinterpret, or transfer rule-mode or consumption-mode progress.

#### Scenario: Surface-only change preserves operation progress

- **WHEN** an environment with current rule or consumption progress changes its primary surface from Reels to Feed or from Feed to Reels
- **THEN** Cloud advances only the surface revision and audit
- **AND** the operation-policy revision and existing runtime progress remain unchanged

#### Scenario: Stale surface edit loses compare-and-swap

- **WHEN** two client edits submit the same expected surface revision and one commits first
- **THEN** the later edit receives a revision conflict with the current authoritative surface projection
- **AND** it does not overwrite the committed value

### Requirement: Reels is the default for new and existing Facebook environments

The migration SHALL seed every existing Facebook environment with `primarySurface:'reels'`, and new Facebook environment provisioning SHALL persist `reels` unless the creation request explicitly selects `feed`. Non-Facebook environments MUST NOT receive a Facebook primary-surface row or accept this setting.

#### Scenario: Existing Facebook environment is migrated

- **WHEN** the surface migration runs for an existing Facebook environment
- **THEN** Cloud stores `reels` with a migration-attributed audit record
- **AND** the environment's operation-policy revision is unchanged

#### Scenario: New Facebook environment uses the default

- **WHEN** a client creates a Facebook environment without overriding the preselected primary surface
- **THEN** provisioning atomically persists and returns `primarySurface:'reels'`

### Requirement: Primary surface is pinned per browse session

Cloud SHALL pin the authoritative environment surface when a Facebook browse session starts, and SHALL record with each pin whether it is `authoritative` (the environment baseline was read) or `unresolved` (the baseline could not be resolved at that instant and the session runs conservatively on Feed). The two MUST remain distinguishable for the whole session; Cloud MUST NOT represent an `unresolved` pin as an operator-chosen Feed.

A later configuration write SHALL apply to the next session and MUST NOT redirect a session whose pin is `authoritative`.

#### Scenario: Surface changes during a session

- **WHEN** an active Feed session's environment is changed to Reels
- **THEN** the active session continues with its pinned Feed surface
- **AND** the next session selects Reels

#### Scenario: Baseline resolves at session start

- **WHEN** a Facebook browse session starts and the account's operation baseline resolves
- **THEN** Cloud pins the environment's authoritative surface with resolution `authoritative`
- **AND** no recheck channel is armed for that session

#### Scenario: Baseline cannot be resolved at session start

- **WHEN** a Facebook browse session starts and the account's operation baseline cannot be resolved
- **THEN** Cloud pins `feed` with resolution `unresolved` and the named blocker that caused it
- **AND** the session is not treated as an operator-chosen Feed session

### Requirement: Pinned primary surface targets every unified browse redrive

Cloud SHALL use the Facebook surface currently pinned for the session as the `targetSurface` of `page.scroll{reason:'resume_redrive'}`. A task's temporary group/detail page and a later environment configuration write MUST NOT replace that pinned target. The pinned surface changes during a session only when an `unresolved` pin is corrected by the recheck channel.

#### Scenario: Reels-primary session finishes a group task

- **WHEN** a Reels-primary session completes its final group/comment page task and the final lease release is acknowledged
- **THEN** Cloud emits one `page.scroll{reason:'resume_redrive', targetSurface:'reels'}`
- **AND** the temporary group page does not become the session's browse target

#### Scenario: Feed-primary session finishes a group task

- **WHEN** a Feed-primary session completes its final group/comment page task and the final lease release is acknowledged
- **THEN** Cloud emits one `page.scroll{reason:'resume_redrive', targetSurface:'feed'}`
- **AND** Edge restores Facebook home before continuing if a temporary group/search page replaced `active_list_url`

#### Scenario: Configuration changes during a task

- **WHEN** the environment primary surface changes while an existing session's task is in flight
- **THEN** the post-task redrive uses the existing session's pinned surface
- **AND** the new configuration applies only to the next session

### Requirement: Every unresolved primary-surface pin is named in the receipt

Cloud MUST NOT fall back to Feed silently. Whenever the primary-surface pin resolves to `unresolved`, Cloud SHALL emit one operational receipt carrying the account, the environment when known, and the **named** blocker returned by the baseline resolution. Every short-circuit path in that resolution SHALL carry a distinct name to the receipt — platform not Facebook, configuration replica stale, and each named baseline blocker (account-to-environment binding unavailable / unknown / conflicting, and environment browse-surface baseline absent). A blocker that the receipt cannot name MUST be reported as an explicit unrecognised value rather than folded into an existing name.

#### Scenario: Baseline blocker reaches the receipt

- **WHEN** the baseline resolution short-circuits with a named blocker at session start
- **THEN** Cloud emits one receipt naming that blocker verbatim
- **AND** the receipt distinguishes it from every other short-circuit path

#### Scenario: Authoritative pin stays quiet

- **WHEN** the baseline resolves and the pin is `authoritative`
- **THEN** Cloud emits no unresolved-pin receipt for that session

#### Scenario: Repeated rechecks do not become a log pulse

- **WHEN** the recheck channel re-asks the baseline several times within one session
- **THEN** Cloud emits at most one receipt per distinct blocker value per session
- **AND** an unchanged blocker on a later hop does not emit another receipt

### Requirement: Unresolved primary-surface pin is corrected by a bounded recheck

An `unresolved` pin SHALL NOT be terminal: the same question re-asked later can return a different answer, so Cloud SHALL arm a bounded recheck channel for that session. On each hop Cloud SHALL re-resolve the account's operation baseline. When it resolves, Cloud SHALL replace the session pin with the authoritative surface, mark the pin `authoritative`, disarm the channel, and — when the corrected surface differs from the one the session has been browsing — issue one unified browse redrive to the corrected surface. Cloud MUST NOT introduce a new protocol message for the correction and MUST NOT emit any outward-facing write as part of it.

The channel SHALL be bounded by a maximum number of hops with backoff. On exhaustion Cloud SHALL record one terminal receipt naming the last blocker, keep the session running on Feed, and stop rechecking. The channel SHALL be disarmed when the session ends, and a session whose pin is already `authoritative` SHALL NOT arm it.

#### Scenario: Baseline becomes resolvable after session start

- **WHEN** a session pinned `unresolved` re-asks the baseline and it now resolves to `reels`
- **THEN** Cloud re-pins `reels` as `authoritative`
- **AND** Cloud issues one `page.scroll{reason:'resume_redrive', targetSurface:'reels'}`
- **AND** the recheck channel is disarmed

#### Scenario: Corrected surface equals the surface already in use

- **WHEN** a session pinned `unresolved` re-asks the baseline and it now resolves to `feed`
- **THEN** Cloud marks the pin `authoritative` without issuing any redrive
- **AND** the recheck channel is disarmed

#### Scenario: Recheck budget is exhausted

- **WHEN** the recheck channel reaches its hop limit and the baseline still does not resolve
- **THEN** Cloud records one terminal receipt naming the last blocker
- **AND** the session continues on Feed without further rechecks

#### Scenario: Session ends while a recheck is armed

- **WHEN** the browse session ends with the recheck channel armed
- **THEN** Cloud disarms the channel
- **AND** no recheck hop fires against the ended session

#### Scenario: Correction reaches a session started by the start-gate recheck

- **WHEN** a browse session that the start-gate recheck channel started is pinned `unresolved`, and the baseline later resolves to `reels`
- **THEN** Cloud re-pins `reels` and redrives that session into Reels
- **AND** the session does not remain on Feed for its remaining lifetime

