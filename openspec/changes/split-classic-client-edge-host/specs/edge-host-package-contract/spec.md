## ADDED Requirements

### Requirement: Edge Host MUST be an independently versioned embeddable package

`aidcp-edge-host` SHALL publish an immutable, semantically versioned `@aidcp/edge-host` package that contains
the compiled Host API, Edge Core entry, required runtime descriptors and TypeScript declarations. The package
MUST be loadable from an Electron main or compatible Node runtime without importing Classic renderer, Classic
navigation, customer content workspace or Electron window components. Target machines MUST NOT require npm,
tsx, TypeScript or a source checkout at runtime.

#### Scenario: Host runs from a packed artifact

- **WHEN** a consumer installs an `npm pack` artifact for an exact Host version and creates Host from Electron main
- **THEN** Host loads its compiled API and Core entry without resolving files from an `aidcp-edge-host` source checkout or interpreting TypeScript

#### Scenario: Product UI dependency is introduced

- **WHEN** the Host package dependency graph imports Classic renderer, window, navigation or product workspace modules
- **THEN** Host package validation fails and the artifact MUST NOT be published

### Requirement: Host public API MUST expose lifecycle control but not platform action primitives

Host SHALL expose typed contracts for reconciling environment descriptors, reading snapshots, starting,
pausing, resuming and closing an environment, requesting human assistance, subscribing to structured events
and shutting down. It MUST NOT expose client-callable search, browse, click, input, like, comment, publish or
generic platform-command execution. Platform actions SHALL continue to arrive from Cloud Automation through
the versioned Cloud↔Edge command protocol and existing authorization, identity, risk and result gates.

#### Scenario: Classic starts an environment

- **WHEN** Classic calls the typed Host lifecycle operation for an admitted environment
- **THEN** Host supervises the corresponding Core lifecycle and returns a structured result without Classic knowing the Core entry path, child-process environment or browser/CDP implementation

#### Scenario: Client attempts a direct comment action

- **WHEN** a client tries to invoke comment or a generic page command through the public Host contract
- **THEN** no such public operation exists and the action can only enter Edge through the authorized Cloud Automation command path

### Requirement: Host MUST own execution runtime state and emit structured facts

Host SHALL own Core and browser-executor handles, runtime lifecycle, platform runtime coordination, local
execution logs and per-environment state. It SHALL emit versioned structured snapshots and events carrying at
least `clientInstanceId`, `envId`, a monotonic generation, event type, timestamp and factual state or named
error. Consumers MUST NOT need to parse child stdout/stderr to determine lifecycle or execution state;
stdout/stderr SHALL remain diagnostic evidence only.

#### Scenario: Core exits unexpectedly

- **WHEN** an environment Core child process exits unexpectedly
- **THEN** Host emits a structured event for that environment and generation with the factual exit/error state, while raw process output is retained only as diagnostics

#### Scenario: Events from two environments interleave

- **WHEN** two environment workers emit state changes concurrently
- **THEN** every Host event remains attributable to the correct `envId` and generation, and a consumer can project both states without text parsing or cross-environment leakage

### Requirement: Host creation MUST use explicit adapters and real runtime paths

Creating Host SHALL require explicit inputs for a unique client instance, machine-level Host data root,
client-instance data root, real packaged resource root, Cloud target, credential provider, structured logger
and notification/human-assist bridge as applicable. Host MUST NOT read Classic renderer stores, assume the
current working directory is a source checkout, or treat an ASAR file path as a child-process working
directory. Credentials and tokens MUST NOT be included in snapshots, events, owner metadata or ordinary logs.

#### Scenario: Packaged Classic supplies Resources root

- **WHEN** Classic starts Host from an installed ASAR application and supplies its real `process.resourcesPath`-derived root
- **THEN** Host resolves spawnable Core and native runtime assets from that real directory and does not use the ASAR file as `cwd`

#### Scenario: Credential provider returns a token

- **WHEN** Host obtains an execution credential through the injected provider
- **THEN** it uses the credential only for the authorized execution connection and omits it from events, snapshots, lease metadata and ordinary logs

### Requirement: Every Host release MUST carry a verifiable runtime manifest

Each Host release SHALL contain a machine-readable manifest recording Host version, source commit, Host API
major, Cloud↔Edge protocol version, supported platform/architecture targets and SHA-256 for every staged Core,
Native and AdsPower runtime asset. Package code and runtime assets MUST share the same Host version and source
provenance. A missing, unsupported or mismatched manifest MUST fail by the named error
`edge_host_artifact_mismatch`; Host MUST NOT download source, select `latest`, reuse an unverified previous
asset or continue in a partial state.

#### Scenario: Package and runtime assets match

- **WHEN** the imported Host code version, manifest, target platform/architecture and all asset hashes match
- **THEN** Host admits runtime creation and exposes that provenance in a non-secret diagnostic snapshot

#### Scenario: A stale Core asset is packaged

- **WHEN** Host code is version N but the staged Core file hash is absent from or differs from version N's manifest
- **THEN** creation fails as `edge_host_artifact_mismatch` before any Core or browser is started

### Requirement: Host shutdown MUST be bounded, explicit and ownership-safe

Host SHALL track every resource it starts. `close(envId)` SHALL stop only the named environment's supervised
resources and release its execution ownership after shutdown is confirmed. `shutdown()` SHALL stop all
resources owned by that Host instance, report any unconfirmed termination honestly and release only its own
leases. Host MUST NOT stop or adopt resources owned by another Host instance.

#### Scenario: Classic exits with two environments running

- **WHEN** Classic calls Host shutdown while two environments are running
- **THEN** Host performs bounded shutdown for its two environments, reports each result and releases only the leases it owns

#### Scenario: Another Host owns the environment

- **WHEN** shutdown observes diagnostic metadata for an environment owned by another live Host instance
- **THEN** it leaves that environment untouched and MUST NOT delete, terminate or adopt the other owner's resource
