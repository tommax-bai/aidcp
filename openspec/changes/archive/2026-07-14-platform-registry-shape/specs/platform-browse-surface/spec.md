## ADDED Requirements

### Requirement: Note-scoped action support is declared per platform and gated at one point

The cloud registry MUST declare, for every platform, whether each note-scoped action (`read_content`, `like`, `collect`, `comment`, `comment_like`, `browse_images`, `scroll_comments`) is supported, as a fully-covered mapping so the type checker forces every cell to be stated. Every unsupported action MUST carry a non-empty reason. A single dispatch wrapper MUST be the only place that reads this support: when an action is unsupported for the connected platform, the command MUST NOT be dispatched and the refusal MUST be audited with its reason. Support MUST NOT be inferred from numeric coincidence (for example a metric that happens to be zero).

#### Scenario: Facebook collect is refused explicitly, not by coincidence

- **WHEN** the interaction appraiser requests both a like and a collect for a Facebook note
- **THEN** the like is dispatched and the collect is refused at the single dispatch gate with its declared reason
- **AND** the refusal does not depend on Facebook's collect metric being zero

#### Scenario: Unsupported deep-read actions are not dispatched

- **WHEN** the platform declares `browse_images` or `scroll_comments` unsupported
- **THEN** those commands are never dispatched to the edge
- **AND** no round-trip or model call is spent producing a command that the edge would only reject

### Requirement: Surface is a declared platform fact meaning whether an action leaves the list

The registry MUST declare, per platform, the surface (`feed` or `detail`) on which `read_content`, `like`, and `comment` are performed, where surface means whether orchestration must leave the list context. Surface MUST NOT encode page form (dialog, drawer, modal, overlay, profile are driver-internal details and MUST NOT be added to the surface set). Surface MUST be declared only for those three actions; actions that are unsupported or that ride on an already-opened detail reading chain MUST NOT be given a surface. A single pure resolver MUST be the only reader of these surface declarations.

#### Scenario: Xiaohongshu reads, likes, and comments all on detail

- **WHEN** the platform is Xiaohongshu
- **THEN** the surface resolver returns `detail` for read, like, and comment
- **AND** loop closure and comment-migration decisions read this static value

### Requirement: Loop closure and comment migration are driven by the static table, not runtime inference

The decision to return to the list with a back command versus continuing with a scroll, and the decision to trigger a comment migration, MUST be computed from the static surface resolver plus a per-note migration flag that the cloud sets when it emits a migration command. The observed-surface echo MUST be audit-only and MUST NOT drive any control-flow branch. Because Xiaohongshu declares read on detail and its comment surface equals its read surface, its loop closure MUST always be a back command and a comment migration MUST be structurally unreachable, independent of the order in which edge reports arrive.

#### Scenario: Xiaohongshu loop closure is order-independent

- **WHEN** a `page.cards` report interleaves between a Xiaohongshu `note.detail` and the next `feed.entered`
- **THEN** the closure command is still a back command
- **AND** the outcome does not depend on which report arrived first

### Requirement: Deep-read short-circuit is injected, fail-open, and honest

Roles MUST learn platform support only through injected closures, never by importing the registry or branching on a platform literal. When a deep-read sub-action is unsupported, the role MUST take its existing else branch and report the truthful outcome (for example zero images browsed with a reason), never fabricating success. The injected closures MUST fail open: when the registry lookup is missing or throws, the closure MUST return true so the platform behaves as it does today, never silently disabling a supported platform.

#### Scenario: Registry miss does not disable a supported platform

- **WHEN** the deep-read support closure cannot resolve a registry entry or throws
- **THEN** it returns true and the deep-read command is still dispatched as today
- **AND** no platform is silently downgraded

#### Scenario: Unsupported deep-read is reported honestly

- **WHEN** `browse_images` is unsupported for the connected platform
- **THEN** the role emits its images-done event with zero images browsed and a reason
- **AND** it does not call the model or claim images were viewed

### Requirement: Adding a platform must not require changing shared orchestration

Onboarding a new platform MUST NOT change any of: the protocol message-type set or semantics, the command-bridge action-to-message mapping, the edge active-command allowlist, the role-name enumeration, the risk controller or its state machine, the pacing center-value algorithm, or any orchestration role code and the dispatcher event-translation layer. Onboarding a new platform SHALL require only adding a registry entry (with the type checker forcing every support and surface cell to be stated), extending the platform id union, implementing the edge driver/session/executors, and running real-machine probes.

#### Scenario: A new platform is a registry entry plus an edge driver

- **WHEN** a new platform is onboarded
- **THEN** the change is limited to a new registry entry, the platform id union, and edge driver/session/executor code plus probes
- **AND** no shared orchestration, protocol, risk, pacing, or role code is modified
