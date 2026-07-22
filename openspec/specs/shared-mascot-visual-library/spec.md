# shared-mascot-visual-library Specification

## Purpose
TBD - created by archiving change centralize-mascot-visual-library. Update Purpose after archive.
## Requirements
### Requirement: Shared mascot design sources have a product-wide owner
The project SHALL keep reusable mascot concept artwork, visual identity anchors, generation guidance, and semantic selection rules in the `aidcp` control repository rather than an individual application repository.

#### Scenario: A reusable mascot concept is added
- **WHEN** a mascot asset or rule is intended for more than one AIDCP surface
- **THEN** its canonical source and documentation live under `aidcp/docs/design/`

#### Scenario: The current Edge concept library is centralized
- **WHEN** the visual action library is migrated from Edge
- **THEN** all eight concept PNGs and their usage guidance are available from `aidcp/docs/design/mascot/`
- **AND** `aidcp-edge/docs/design/mascot/` no longer owns a duplicate source library

### Requirement: Runtime consumers remain independently buildable
Each application SHALL keep any mascot file required at build or runtime inside its own packaging inputs, even when the reusable design source is owned by `aidcp`.

#### Scenario: Electron packages its current mascot states
- **WHEN** Edge renders task-execution, monitoring, or celebration guidance
- **THEN** it resolves the existing files under `aidcp-edge/src/electron/renderer/assets/`
- **AND** its build does not require a sibling `aidcp` checkout

#### Scenario: A shared concept is adopted by an application
- **WHEN** an application chooses a concept from the shared library for production UI
- **THEN** it derives or copies a purpose-named production asset into that application's packaging tree
- **AND** it validates the production asset in the owning application repository

### Requirement: Mascot states preserve honest product semantics
Mascot selection guidance SHALL distinguish visual intent from evidence that an external action or outcome occurred.

#### Scenario: Work is only in progress
- **WHEN** the product has started work but has no confirmed external success
- **THEN** it uses an execution, thinking, observing, or monitoring concept as appropriate
- **AND** it does not use celebration as proof of completion

#### Scenario: Success is confirmed
- **WHEN** the product has a confirmed success state for the represented action
- **THEN** it may use the celebration concept as positive feedback

