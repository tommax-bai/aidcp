## MODIFIED Requirements

### Requirement: Orchestration capability words gate role registration and fail open

The orchestration capability matrix MUST include `follow`, `profile_visit`, `patrol`, `notification`, and `group_join`. No capability word may remain declared without a wired consumer.

For `follow`, `profile_visit`, `patrol`, and `notification` the consumer is **gating**: role registration in the dispatcher setup MUST be gated by these capabilities so a platform that does not support patrol or notification does not register the patrol roles, and a platform that does not support follow or profile visits does not register the author-evaluation and follow roles. That gate MUST fail open: only an explicit unsupported declaration skips registration, while a missing entry or a lookup exception registers as today, so a supported platform's patrol is never silently dropped on a lookup failure.

A capability word MAY instead have a **non-gating** consumer — a read-only projection of what the client is told about the account, such as which usage metrics it is shown. `group_join` is such a word: it is read only to decide whether the account is shown a group-join metric, and joining itself continues to be actuated and gated on its own dedicated path. A non-gating consumer MUST NOT dispatch, refuse, or cancel any command, MUST NOT be relied on as an enforcement point, and MUST NOT be the reason any refusal goes unaudited. Declaring a word whose only consumer is non-gating MUST NOT introduce a second gate on that action.

A non-gating consumer MUST preserve the status quo when it cannot decide, and the direction of that fail-safe depends on what the status quo is. Where the consumer's behaviour today is to act, a lookup miss or exception MUST act as today. Where the consumer's behaviour today is not to act — as for a capability word introduced together with the surface that reads it — only an explicit supported declaration may cause it to act, and a lookup miss or exception MUST NOT. Reusing a fail-open-to-supported lookup for such a word is a defect: it would let an unresolvable platform be granted a capability it does not have.

#### Scenario: Facebook does not register patrol roles

- **WHEN** a Facebook session starts and Facebook declares patrol and notification unsupported
- **THEN** the patrol roles are not registered for that connection
- **AND** the capability words are actually read, not merely declared

#### Scenario: Xiaohongshu still registers all patrol roles

- **WHEN** a Xiaohongshu session starts
- **THEN** all patrol roles and the author-evaluation and follow roles register as before
- **AND** a capability lookup miss or exception still registers them rather than dropping them

#### Scenario: The group-join word is read but gates nothing

- **WHEN** the client usage projection reads `group_join` for a Facebook account and finds it supported
- **THEN** the account is shown a group-join metric
- **AND** no command is dispatched, refused, or cancelled on account of that read
- **AND** the join scheduler's own path remains the only place that decides whether a join is actuated

#### Scenario: An unresolvable platform is not granted group joining

- **WHEN** the client usage projection cannot resolve an account's platform, or the `group_join` lookup throws
- **THEN** the account is not shown a group-join metric
- **AND** the projection does not fall back to treating the capability as supported, because a platform that cannot be identified has not declared that it has groups
