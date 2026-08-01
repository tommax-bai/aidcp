## ADDED Requirements

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

Cloud SHALL pin the authoritative environment surface when a Facebook browse session starts. A later configuration write SHALL apply to the next session and MUST NOT redirect an already active session.

#### Scenario: Surface changes during a session

- **WHEN** an active Feed session's environment is changed to Reels
- **THEN** the active session continues with its pinned Feed surface
- **AND** the next session selects Reels
