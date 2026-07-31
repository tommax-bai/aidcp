## ADDED Requirements

### Requirement: Facebook operation policy is the environment-scoped mode authority

Cloud SHALL persist one authoritative base operation policy for each Facebook environment, keyed only by `envKey`. The persisted base mode SHALL select exactly one of `persona`, `rule`, or `consumption`; no account-keyed mode flag, Edge-local checkbox, content-schedule row, or inferred combination of legacy rule booleans MAY act as a second base-mode authority. The existing environment slow-start lifecycle remains the sole slow-start authority and overlays the base policy: authoritative `slow_start.state=active` yields effective mode `slow_start`, while `off` or `graduated` yields the stored base mode. Policy configuration SHALL remain readable and writable while the environment has no bound account or its local browser runtime is stopped.

Persona/content active-week configuration SHALL NOT act as a mode authority. It MUST NOT demote `rule` or `consumption` to `persona`, reinterpret a policy revision or admit persona-mode scheduled group joining while a non-persona base mode is configured.

Every read and write MUST validate the environment's authoritative normalized platform. A non-Facebook, unknown, missing, retired, or unreadable environment MUST be rejected or reported unavailable without creating a policy. At execution time Cloud SHALL resolve the account to exactly one current environment; an unknown binding, conflicting binding, cross-customer contention, or unavailable environment registry MUST fail closed with a named blocker and MUST NOT fall back to an account-keyed legacy rule value.

#### Scenario: Unbound Facebook environment is configurable

- **WHEN** an operator writes an operation policy for an authoritative Facebook environment that currently has no bound account
- **THEN** Cloud persists and reads back the environment policy
- **AND** the projection states that there is no current execution object and MUST NOT fabricate an account, progress, or effective runtime mode

#### Scenario: Rebinding carries policy but not account runtime

- **WHEN** a Facebook environment changes its bound account from A to B
- **THEN** the environment policy and current revision remain unchanged
- **AND** account B resolves the policy through the environment while account A is no longer governed by it

#### Scenario: Ambiguous reverse binding fails closed

- **WHEN** an executing account resolves to zero or more than one environment, or the binding registry is unavailable
- **THEN** Cloud does not admit persona, rule, consumption, or scheduled-join work from that unresolved policy
- **AND** it exposes a named binding blocker without selecting an arbitrary environment or legacy account configuration

#### Scenario: Unsupported platform cannot acquire a Facebook policy

- **WHEN** a caller attempts to configure an operation policy for a Xiaohongshu, WeChat Channels, unknown-platform, or missing environment
- **THEN** the entire write is rejected and no policy revision or audit success record is created

#### Scenario: Persona schedule cannot demote an operation policy

- **WHEN** the persona/content schedule is outside its active window while the authoritative base mode is `rule` or `consumption`
- **THEN** the effective operation mode remains that configured base mode unless slow start or a named fail-closed blocker wins
- **AND** Cloud MUST NOT fall back to persona behavior or its independent scheduled join source

### Requirement: Global numeric policy and environment cadence overrides are typed and server-bounded

Cloud SHALL persist one target-global Facebook numeric policy for each local `execution_target`. It SHALL contain the default rule cadence, default consumption cadence, cold-start total days, and a complete ordered daily-cap row for every cold-start day. The API SHALL infer the local target and MUST NOT accept a caller-selected execution target, generic action graph, script, prompt, arbitrary JSON parameters, account selector, or client-supplied bounds.

Each environment policy SHALL declare `cadenceSource=global|environment`. Existing materialized environment policies SHALL migrate to `environment` so current independent values are preserved. A newly created environment policy SHALL default to `global`. Global-source reads SHALL return the values materialized from the current target-global policy; environment-source reads SHALL return the independent stored values.

The initial server bounds and defaults SHALL be:

| Scope | Field | Type | Inclusive bounds | Default |
| --- | --- | --- | --- | --- |
| `rule` | `viewsPerLike` | integer | 1..100 | 5 |
| `rule` | `joinEveryNRounds` | integer | 1..20 | 2 |
| `consumption` | `viewsPerLike` | integer | 1..100 | 5 |
| `consumption` | `confirmedLikesPerJoin` | integer | 1..20 | 2 |
| `consumption` | `confirmedJoinsPerComment` | integer | 1..20 | 2 |
| `slowStart` | `totalDays` | integer | 1..30 | 7 |
| `slowStart.dailyCaps` | `view` | integer | 0..300 | current 7-day Facebook curve |
| `slowStart.dailyCaps` | `like` | integer | 0..100 | current 7-day Facebook curve |
| `slowStart.dailyCaps` | `comment` | integer | 0..15 | current 7-day Facebook curve |
| `slowStart.dailyCaps` | `follow` | integer | 0..30 | current 7-day Facebook curve |
| `slowStart.dailyCaps` | `publish` | integer | 0..2 | current 7-day Facebook curve |
| `slowStart.dailyCaps` | `search` | integer | 0..20 | current 7-day Facebook curve |
| `slowStart.dailyCaps` | `joinGroup` | integer | 0..5 | current 7-day Facebook curve |

Environment mode selection remains environment-scoped and independent of the global numeric revision. A global numeric write SHALL require a complete typed payload and global `expectedRevision`. An environment write selecting `cadenceSource=environment` SHALL require complete rule and consumption values; selecting `global` SHALL reject cadence values and materialize the current global values. Missing cold-start days, duplicate/non-contiguous day indexes, invalid types, fractional values, unknown keys, or out-of-range values MUST reject the entire write without clamping or partial persistence. Facebook-unsupported `collect`, `comment_like`, and `dm_reply` remain zero and MUST NOT be configurable. Join-to-first-comment waiting remains governed by the separate Facebook group-comment policy.

#### Scenario: New environment inherits global values

- **WHEN** a new Facebook environment policy is created while the target-global consumption cadence is `5/2/2`
- **THEN** Cloud stores `cadenceSource=global` and materializes `viewsPerLike=5`, `confirmedLikesPerJoin=2`, and `confirmedJoinsPerComment=2`
- **AND** the write-after-read response identifies inheritance rather than presenting the values as an environment override

#### Scenario: Existing and explicitly independent values are preserved

- **WHEN** an existing policy migrates or an operator selects independent configuration with complete in-range rule and consumption values
- **THEN** Cloud stores `cadenceSource=environment` and those exact values in a new environment revision
- **AND** later target-global cadence changes do not change that environment revision or its runtime counters

#### Scenario: Global cadence propagates through immutable environment revisions

- **WHEN** an administrator commits a valid target-global rule or consumption cadence change
- **THEN** Cloud creates one audited global revision and one new audited environment policy revision for every `cadenceSource=global` environment
- **AND** each inheriting revision starts new runtime progress while independent environments remain byte-for-byte unchanged

#### Scenario: Invalid global or override payload rejects atomically

- **WHEN** a global payload omits a cold-start day, contains a cap above its server bound, or an environment inheritance write also carries cadence values
- **THEN** Cloud rejects the complete write with a field-specific validation reason
- **AND** no global revision, environment revision, audit success record, or partial propagation is created

### Requirement: Cold-start configuration follows current day and graduation is sticky

Cloud SHALL derive the current cold-start day from the environment's existing server-day-aligned `slow_start_since` and SHALL resolve the current target-global daily cap on each admission. Saving cold-start configuration MUST NOT reset or shift that anchor. The configured caps SHALL remain an additional element-wise minimum with the account's current risk quotas and MUST NOT widen risk, approval, session, or platform gates.

Cloud SHALL persist sticky graduation keyed by `envKey + executionTarget`.
Before replacing a longer or shorter target-global duration, it MUST preserve
every environment already graduated under that target's prior duration; after
a shorter duration is committed, any active environment now beyond the new
duration SHALL graduate immediately for that target. A DEV duration change
MUST NOT create or clear an OL completion fact, and vice versa. Once graduated
for a target, an environment MUST NOT re-enter cold start there solely because
`totalDays` later increases. Only an explicit operator selection or re-enable
of `slow_start` for an off or graduated environment MAY clear graduation,
write a fresh current server-day anchor, and start day 1; selecting it again
while already active MUST preserve the current anchor.

#### Scenario: Active day keeps its progress

- **WHEN** an environment is active on cold-start day 5 and an administrator changes total days or day-5 caps
- **THEN** the environment remains on day 5 and immediately uses the committed day-5 caps
- **AND** no anchor, account identity, or prior-day progress is rewritten

#### Scenario: Graduated environment is not revived

- **WHEN** an environment graduated under a 7-day policy and the administrator later changes `totalDays` to 14
- **THEN** that environment remains graduated
- **AND** no slow-start action is admitted unless an operator explicitly re-enables slow start

#### Scenario: Shorter duration graduates immediately

- **WHEN** an active environment's derived current day is greater than a newly committed `totalDays`
- **THEN** its slow-start state becomes graduated in the same policy transition
- **AND** its resumable base mode becomes effective without resetting rule or consumption counters

#### Scenario: Explicit re-enable starts a new lifecycle

- **WHEN** an operator explicitly selects slow start for an off or graduated environment
- **THEN** Cloud writes the current server-day anchor, clears the sticky graduation marker, and returns day 1
- **AND** a repeated read or global policy edit does not perform that reset

### Requirement: Policy writes use compare-and-swap, immutable audit, and write-after-read truth

Every operation-policy mutation SHALL carry `expectedRevision`; `0` SHALL mean that no policy revision is expected to exist. Cloud MUST compare it against the current environment revision in the same transaction that creates the next immutable policy snapshot and appends its immutable audit record. A mismatch MUST return a conflict with the current authoritative projection and MUST NOT overwrite, merge with, or partially apply the submitted policy.

Each successful audit record SHALL include at least `envKey`, prior revision, new revision, prior normalized policy, new normalized policy, authenticated actor class and identifier, request correlation id, and server timestamp. Audit history MUST NOT be updated or deleted when a later policy is written. The success response SHALL be produced from a write-after-read of the committed revision and include the complete stored policy, revision, update time, applicable schema bounds/defaults, and current binding/effective-state projection. Dispatch, Edge receipt, or platform success MUST NOT be implied by configuration persistence.

#### Scenario: Matching revision creates one audited snapshot

- **WHEN** an operator submits a valid policy with the current `expectedRevision`
- **THEN** Cloud atomically creates exactly one next revision and exactly one matching audit record
- **AND** returns the committed write-after-read projection

#### Scenario: Stale editor loses compare-and-swap

- **WHEN** two editors read revision 7 and the first successfully writes revision 8 before the second submits
- **THEN** the second write receives a revision conflict containing the current revision 8 projection
- **AND** no revision 9, partial parameter update, or audit success record is created for the rejected write

#### Scenario: Configuration success is not runtime success

- **WHEN** Cloud commits a policy for an unbound or offline environment
- **THEN** the response reports the configuration as saved and the execution object as absent or offline
- **AND** it MUST NOT report that browsing, liking, joining, or commenting has started or succeeded

### Requirement: Runtime state is account-, target-, and policy-revision-scoped

Durable operation progress, content dedupe facts, confirmed-outcome counters, action batches, and terminal results SHALL be keyed by `account_id + execution_target + policy_revision` and SHALL retain the immutable policy snapshot used by each batch. Configuration remains environment-keyed; runtime history MUST NOT be migrated to or deduplicated through `envKey`.

A new policy revision or a newly bound account SHALL begin with zero progress and an empty dedupe set for that revision. Cloud MUST NOT reinterpret old view counts, like counts, join counts, visited-content facts, or in-flight batches under new thresholds. DEV and OL runtime rows MUST remain isolated by `execution_target`, while the environment policy revision remains the configuration identity both runtimes explicitly reference.

#### Scenario: Parameter change does not reinterpret progress

- **WHEN** account A has four collected views under revision 11 and an operator changes `viewsPerLike`, creating revision 12
- **THEN** revision 12 starts with zero collected views
- **AND** revision 11 remains historical and MUST NOT immediately trigger an action under the new threshold

#### Scenario: New account does not inherit behavior history

- **WHEN** an environment rebinds from account A to account B under the same current policy revision
- **THEN** account B starts with zero counters and an empty content-dedupe set
- **AND** account A's in-flight and historical rows remain under account A and are never reassigned to B

#### Scenario: Shared database does not mix deployment runtime

- **WHEN** DEV and OL observe the same environment policy revision
- **THEN** each deployment reads and writes only runtime rows bearing its own `execution_target`
- **AND** neither deployment may advance or settle the other's progress or batches

### Requirement: Mode and revision transitions preserve irreversible-action truth

A mode change or parameter change SHALL create a new policy revision. Once the new revision commits, Cloud MUST stop admitting new work under the superseded revision. Undispatched old-revision intents SHALL settle with a named `policy_superseded` outcome; already dispatched attempts SHALL retain their original revision and continue only through receipt/reconciliation so an irreversible action is not erased, retried, or relabelled. The new revision MAY begin only after the account's existing single-flight boundary permits it.

The unified projection SHALL accept `slow_start` as an explicit operator selection while keeping the lifecycle authority singular: selecting it SHALL activate the existing environment slow-start authority with a server-generated anchor and set the resumable base mode to `persona` in the same service transaction. Selecting `persona`, `rule`, or `consumption` SHALL deactivate an active slow start and set that base mode in the same transaction. Existing environments migrated with both active slow start and enabled rule mode SHALL preserve `rule` as the resumable base until an operator makes a new selection. Rule/consumption counters or action debt MUST NOT transfer across a base-mode or slow-start transition.

#### Scenario: Disabling a mode while an action is dispatched

- **WHEN** a rule or consumption action has already been dispatched and an operator changes the environment to persona mode
- **THEN** Cloud stops admitting later stages under the old revision but continues honest receipt reconciliation for the dispatched attempt
- **AND** the new persona revision MUST NOT claim, retry, or count the old attempt as its own

#### Scenario: Transition to slow start is atomic

- **WHEN** an operator changes an eligible Facebook environment from rule or consumption to `slow_start`
- **THEN** the new operation-policy revision and the environment slow-start activation commit atomically
- **AND** no observable committed state permits rule/consumption and slow start to be simultaneously authoritative

#### Scenario: Returning to consumption starts clean

- **WHEN** an environment leaves consumption mode and later enters consumption again
- **THEN** the later policy revision starts all consumption counters at zero
- **AND** no unfulfilled like, join, or comment opportunity from the earlier revision is carried forward as retry debt

### Requirement: Console configuration and runtime projection have one authority

The management Console SHALL edit the target-global Facebook numeric policy in one clearly labelled global card on `/environments`, using its own server-provided bounds, `expectedRevision`, pending state, conflict handling, and write-after-read response. Each Facebook environment editor SHALL remain addressed by `envKey`, show `继承全局 / 独立配置`, make numbers editable only for independent configuration, and separately show configured base mode, effective runtime mode, slow-start lifecycle, binding state, environment policy revision, current account when uniquely known, and named blockers. An unbound environment MAY be configured and SHALL be labelled as having no current execution object.

`/content-schedule` SHALL expose only read-only effective-mode, progress, batch, and blocker projections for the currently bound account. It MUST NOT retain a rule/consumption mode switch, cadence editor, hidden mutation, or account-keyed fallback that creates a second configuration authority. Failed, stale, incomplete, or unavailable reads MUST render unknown/unavailable and MUST NOT fabricate `persona`, disabled, zero progress, or a successful write.

#### Scenario: Environment page performs the authoritative edit

- **WHEN** an administrator changes a Facebook environment from rule to consumption on `/environments`
- **THEN** the Console sends one environment-keyed CAS write and waits for its complete write-after-read result
- **AND** it does not optimistically mutate `/content-schedule` or any account-keyed rule flag

#### Scenario: Content schedule is projection only

- **WHEN** an administrator views a consumption account on `/content-schedule`
- **THEN** the page may show its effective mode, current revision counters, latest batch states, and blockers
- **AND** it provides no control that can modify operation mode or cadence

#### Scenario: Unavailable projection is not a default

- **WHEN** policy, binding, or runtime projection is unavailable or incomplete
- **THEN** both Console surfaces display a named unknown/unavailable state
- **AND** neither surface presents a writable guessed value or claims that the environment is running persona mode
