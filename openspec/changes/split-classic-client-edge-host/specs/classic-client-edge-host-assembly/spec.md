## ADDED Requirements

### Requirement: Classic Client MUST own the product shell and consume Host through one adapter

`aidcp-classic-client` SHALL own the Electron shell and renderer, customer login and ordinary customer-auth
data access, environment management UI, tray, notifications, update behavior and final desktop installer.
All Edge execution lifecycle and state SHALL cross one typed Classic↔Host adapter backed by
`@aidcp/edge-host`. Classic MUST NOT contain a second copy of Core, platform drivers, Native Page Engine
execution logic, AdsPower supervision or Cloud automation command routing.

#### Scenario: Renderer starts an environment

- **WHEN** a user starts an environment from Classic UI
- **THEN** Classic main maps the IPC request to the typed Host lifecycle adapter and projects its structured result without spawning Core or calling AdsPower from renderer code

#### Scenario: Duplicate execution implementation remains

- **WHEN** repository validation finds Core, platform driver or Cloud automation command implementations in Classic outside the explicit Host adapter
- **THEN** the split validation fails and Classic MUST NOT be declared independently migrated

### Requirement: Classic MUST preserve ordinary customer data when Host is stopped

Classic customer authentication, settings and ordinary Cloud data access SHALL remain independent of Host
Core and browser lifecycle. A customer SHALL be able to log in and use browser-independent product data while
Host is not created, an environment Core is closed or every browser executor is unavailable. Classic MUST
present automation unavailability separately and MUST NOT treat it as loss of customer login.

#### Scenario: All environments are closed

- **WHEN** the customer is authenticated but all Host environments and browser executors are closed
- **THEN** Classic can still load authorized browser-independent customer data and shows execution state as closed rather than signed out

#### Scenario: Host artifact fails validation

- **WHEN** Host creation fails as `edge_host_artifact_mismatch`
- **THEN** Classic exposes automation as unavailable with the named failure while retaining the valid customer session and ordinary data access

### Requirement: Classic MUST pin and verify one exact Host release

Classic `package.json` and lockfile SHALL reference one exact immutable Host version; semver ranges, mutable
branches, workspace links, symlinked packages and runtime `latest` resolution are forbidden for integration
and release evidence. Classic build SHALL verify the Host manifest, package provenance, platform/architecture
and asset hashes before producing an installer. Classic startup SHALL verify that loaded Host code and staged
runtime resources still match the embedded manifest.

#### Scenario: Exact Host version is assembled

- **WHEN** Classic CI installs its lockfile and builds an installer
- **THEN** the installer records one exact Host version, Host source commit and manifest hash that can be traced from the installed application

#### Scenario: Dependency uses a semver range

- **WHEN** Classic declares `@aidcp/edge-host` with a range or mutable source
- **THEN** dependency validation fails and no release installer is produced

### Requirement: Classic MUST project Host facts without fabricating success

Classic SHALL map structured Host snapshots, events and named errors into user-visible environment state,
activity and notifications. It MUST preserve `envId` and generation routing, distinguish accepted/in-progress,
closed, conflict, failed and platform-confirmed outcomes, and MUST NOT display running or successful state
from a submitted lifecycle request, Cloud acceptance, stale event or raw stdout text alone.

#### Scenario: Start request is accepted but Core fails

- **WHEN** Host accepts a start request and later emits a structured Core failure for the same environment generation
- **THEN** Classic shows starting followed by the named failure and MUST NOT remain visually running

#### Scenario: Stale event arrives after restart

- **WHEN** Classic receives an older generation event after a newer generation is active
- **THEN** Classic retains the newer projection and does not let stale state overwrite or misroute it

### Requirement: Classic MUST be the sole final desktop assembler

Only `aidcp-classic-client` SHALL produce customer-facing macOS `dmg` / `zip` and Windows `nsis` artifacts.
The build SHALL compile Classic, consume the exact Host release, stage spawnable/native Host assets outside
ASAR where required, sign all required native assets and embed Classic/Host provenance. `aidcp-edge-host`
MAY publish package/runtime artifacts but MUST NOT publish a competing customer desktop shell.

#### Scenario: Host package is published

- **WHEN** `aidcp-edge-host` publishes a valid versioned package
- **THEN** it is an input to Classic build and is not advertised as a standalone customer desktop application

#### Scenario: Installed Classic has no development toolchain

- **WHEN** the Classic installer is installed on a supported target without Node, npm, npx, tsx or source repos
- **THEN** Classic starts the embedded Host and Core from staged compiled resources or fails with a factual named packaging error

### Requirement: This split MUST NOT create Agent Client behavior

The repository split SHALL NOT create an `aidcp-agent-client` repository, Agent UI, conversation runtime,
Agent orchestration adapter or Agent-specific Host API. Any future Agent Client SHALL require a separate
OpenSpec change and SHALL consume the stable public Host contract rather than being inferred from Classic
internals.

#### Scenario: Classic and Host migration completes

- **WHEN** all repository split and parity gates pass
- **THEN** the delivered products are Classic Client and Edge Host only, with Agent Client still absent and unimplemented
