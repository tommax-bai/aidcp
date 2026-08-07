## MODIFIED Requirements

### Requirement: Pinned primary surface targets every unified browse redrive

Cloud SHALL address every unified browse redrive to the Facebook surface currently pinned for the session by choosing the redrive command name: `facebook.reels.scroll{reason:'resume_redrive'}` for a Reels pin and `facebook.feed.scroll{reason:'resume_redrive'}` for a Feed pin (the former `targetSurface` payload field is removed — the surface rides the command name). A task's temporary group/detail page and a later environment configuration write MUST NOT replace that pinned target. The pinned surface changes during a session only when an `unresolved` pin is corrected by the recheck channel.

#### Scenario: Reels-primary session finishes a group task

- **WHEN** a Reels-primary session completes its final group/comment page task and the final lease release is acknowledged
- **THEN** Cloud emits one `facebook.reels.scroll{reason:'resume_redrive'}`
- **AND** the temporary group page does not become the session's browse target

#### Scenario: Feed-primary session finishes a group task

- **WHEN** a Feed-primary session completes its final group/comment page task and the final lease release is acknowledged
- **THEN** Cloud emits one `facebook.feed.scroll{reason:'resume_redrive'}`
- **AND** Edge restores Facebook home before continuing if a temporary group/search page replaced `active_list_url`

#### Scenario: Configuration changes during a task

- **WHEN** the environment primary surface changes while an existing session's task is in flight
- **THEN** the post-task redrive uses the existing session's pinned surface
- **AND** the new configuration applies only to the next session

### Requirement: Unresolved primary-surface pin is corrected by a bounded recheck

An `unresolved` pin SHALL NOT be terminal: the same question re-asked later can return a different answer, so Cloud SHALL arm a bounded recheck channel for that session. On each hop Cloud SHALL re-resolve the account's operation baseline. When it resolves, Cloud SHALL replace the session pin with the authoritative surface, mark the pin `authoritative`, disarm the channel, and — when the corrected surface differs from the one the session has been browsing — issue one unified browse redrive to the corrected surface. Cloud MUST NOT introduce a new protocol message for the correction and MUST NOT emit any outward-facing write as part of it.

The channel SHALL be bounded by a maximum number of hops with backoff. On exhaustion Cloud SHALL record one terminal receipt naming the last blocker, keep the session running on Feed, and stop rechecking. The channel SHALL be disarmed when the session ends, and a session whose pin is already `authoritative` SHALL NOT arm it.

#### Scenario: Baseline becomes resolvable after session start

- **WHEN** a session pinned `unresolved` re-asks the baseline and it now resolves to `reels`
- **THEN** Cloud re-pins `reels` as `authoritative`
- **AND** Cloud issues one `facebook.reels.scroll{reason:'resume_redrive'}`
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
