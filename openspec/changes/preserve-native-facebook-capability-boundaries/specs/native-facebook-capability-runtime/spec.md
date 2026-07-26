## ADDED Requirements

### Requirement: Every supported Native Facebook command has one capability owner
The Native Facebook runtime SHALL map every supported Facebook page command to exactly one capability-owned execution path. The generic engine SHALL own session supervision, command lifecycle, CDP transport, cancellation, and typed result delivery, but MUST NOT implement command-specific Facebook locating, actuation, verification, or terminal classification. A Facebook command without a complete capability owner MUST return `capability_unsupported` before browser-router or CDP page actuation.

#### Scenario: Supported command enters its capability
- **WHEN** a supported Facebook Feed, Reel, Group Join, Comment, or Publish command is admitted
- **THEN** the shared engine dispatches it once to the declared Facebook capability owner
- **AND** no generic Facebook fallback or second capability attempts the operation

#### Scenario: Command has no complete owner
- **WHEN** the generic command vocabulary contains a command that the Facebook support table does not bind to one complete capability
- **THEN** the runtime returns `capability_unsupported` before router evaluation, navigation, scrolling, clicking, typing, or file input

### Requirement: Facebook capability owners preserve the complete platform transaction
Each state-changing Facebook capability SHALL own its complete `admit → locate → fresh revalidate → commit → same-target verify → classify` transaction. The target witness carried across that transaction MUST retain the identity and association evidence required by the capability and MUST NOT be reduced to a stale coordinate when the established behavior requires a live React element, operation marker, active-video/author association, current-group scope, or composer generation.

#### Scenario: React-owned control requires in-page activation
- **WHEN** recorded Facebook behavior requires fresh in-page activation of the current React-owned Feed Like, Reel primary Like, or Group Join element
- **THEN** the owning capability re-resolves that exact element at the commit boundary and invokes it once inside the Native browser router
- **AND** the generic engine does not replace that commit with a saved coordinate click

#### Scenario: Capability uses trusted pointer input
- **WHEN** recorded Facebook behavior requires pointer input for a unique scoped reaction-picker item or author-bound Reel Follow control
- **THEN** the owning capability validates the current target and returns one bounded pointer target for at most one dispatch
- **AND** verification remains bound to the same canonical post or Reel witness

#### Scenario: Target witness is lost after dispatch
- **WHEN** a write was dispatched but its tagged card, active Reel/video, author binding, current-group scope, or composer witness can no longer be proven
- **THEN** the capability returns an ambiguous non-success terminal result without replaying the commit

### Requirement: Facebook command deadlines are coherent end to end
The Edge facade and Native Facebook runtime SHALL use one absolute deadline per command, and every capability's readiness, hydration, commit, settle, and verification phases MUST fit within that deadline. Ordinary Facebook commands SHALL retain the established 30-second deadline, while Group Join SHALL receive the established 90-second deadline required for its bounded 30-second readiness, 2-second hydration, 1.5-second immediate settle, and 45-second durable verification sequence. The runtime MUST NOT stack independent phase deadlines beyond the caller's remaining budget.

#### Scenario: Slow Group Join retains its verification window
- **WHEN** the Join control appears near the end of readiness and Facebook requires the established hydration and durable verification periods
- **THEN** the host and Native session allow the sequence to use the remaining Group Join budget up to 90 seconds
- **AND** the operation is not truncated by the ordinary 30-second command ceiling

#### Scenario: Ordinary command does not inherit Join time
- **WHEN** a non-Join Facebook command is executed
- **THEN** its facade deadline remains 30 seconds and its capability phases are bounded by that same absolute deadline

### Requirement: Embedded Facebook router sources remain capability-owned and Native-only
Facebook browser rules SHALL be maintained as capability-owned internal source modules and assembled in an explicit deterministic order into the single encoded Native router artifact. Native build and router tests MUST consume the same source set and order. Production TypeScript, `dist`, ASAR, package resources, and caller inputs MUST NOT contain or supply the source modules, selectors, JavaScript payloads, or a browser-rule fallback.

#### Scenario: Router tests and Native build assemble identical sources
- **WHEN** a capability router module is added, removed, or reordered
- **THEN** both the focused router test harness and Native build consume the updated explicit source manifest
- **AND** a missing, duplicate, or unordered module fails validation

#### Scenario: Desktop artifact is inspected
- **WHEN** production dist and desktop build inputs are verified
- **THEN** every Facebook router source fragment and representative page-rule marker is absent outside the encoded Native artifact

### Requirement: Supported Facebook behavior has an executable parity ledger
The Edge repository SHALL maintain a closed behavior-parity ledger for every Native-supported Facebook command. Each entry SHALL identify its capability owner, behavior oracle, canonical target witness, pre-commit gates, commit primitive and maximum dispatch count, verification witness, terminal reason/effect classes, and total deadline. Automated validation MUST fail when a supported command lacks an entry, an entry has no focused externally meaningful regression case, or implementation routing disagrees with the declared owner.

#### Scenario: New supported command lacks parity evidence
- **WHEN** a Facebook command is added to the Native support table without a complete ledger entry and focused behavior test
- **THEN** the ownership/parity validation fails before integration

#### Scenario: Capability behavior is mechanically moved
- **WHEN** a Facebook workflow is extracted from the generic engine or monolithic router into a capability module
- **THEN** its focused tests continue to prove the same target, dispatch-count, verification, effect-phase, and terminal-reason behavior

### Requirement: Validation claims preserve real-account truth
Source, fixture, fake-CDP, build, and package validation SHALL be reported separately from real-account acceptance. A Native Facebook write capability MUST NOT be described as live-verified merely because its router, Rust, acceptance, full Edge, typecheck, Native build, or strict OpenSpec checks pass.

#### Scenario: Source and artifact validation pass without a real write
- **WHEN** all automated and artifact checks pass but no explicitly authorized real Facebook action is observed
- **THEN** the change is reported as source/artifact validated with real-account acceptance still pending
