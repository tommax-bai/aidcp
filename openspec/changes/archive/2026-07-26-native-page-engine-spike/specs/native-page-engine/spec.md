## ADDED Requirements

### Requirement: Native Page Engine spike SHALL remain opt-in and isolated from production execution

The Edge repository SHALL provide a standalone Rust Native Page Engine probe that is launched only through an explicit development entrypoint. Normal Electron and Edge-core startup MUST NOT require, launch, or route commands to the spike, and the existing JavaScript executor SHALL remain the sole production page-action writer.

#### Scenario: Normal client starts without a native artifact

- **WHEN** the ordinary Electron or Edge-core startup path runs without a Native Page Engine binary
- **THEN** startup and existing automation behavior remain unchanged and no native process is launched

#### Scenario: Probe is explicitly launched

- **WHEN** a developer supplies the native binary path and invokes the dedicated probe entrypoint
- **THEN** exactly one probe process is launched for that invocation and no production command handler is replaced

### Requirement: Native target discovery SHALL be bounded to the existing local browser endpoint

The native probe SHALL accept only a loopback DevTools host, valid port, supported platform identifier, and bounded timeout. It SHALL fetch the local endpoint's target list, select only a debuggable `page` target allowed by the native platform adapter, and MUST NOT accept an arbitrary WebSocket URL, selector, script, credential, or raw CDP method from JavaScript.

#### Scenario: Matching Xiaohongshu page exists

- **WHEN** the local DevTools endpoint exposes one or more targets including a debuggable Xiaohongshu page
- **THEN** the native engine selects an allowed Xiaohongshu page target and connects to its advertised debugger WebSocket

#### Scenario: No matching page exists

- **WHEN** the endpoint is reachable but exposes no allowed Xiaohongshu page target
- **THEN** the native engine returns `no_matching_target` and MUST NOT attach to an unrelated page

#### Scenario: Non-loopback endpoint is requested

- **WHEN** a probe request supplies a non-loopback host
- **THEN** the native engine rejects it as `endpoint_not_loopback` before opening an HTTP or WebSocket connection

### Requirement: Spike CDP behavior MUST be read-only and allowlisted

The native engine SHALL expose only the CDP operations required to enable Runtime and evaluate one constant, read-only page probe. It MUST NOT dispatch `Input.*`, navigation, JavaScript-dialog handling, DOM mutation, file input, permission, cookie, storage, or network-body commands, and MUST NOT expose generic CDP dispatch through IPC.

#### Scenario: Read-only page probe completes

- **WHEN** the selected page responds to the allowlisted Runtime operations before the deadline
- **THEN** the engine returns structured page state and closes the debugger connection without changing page content or navigation

#### Scenario: Unsupported operation is presented internally

- **WHEN** code attempts to construct a CDP operation outside the native allowlist
- **THEN** the operation is rejected before serialization to the debugger WebSocket

### Requirement: Page-state output SHALL be semantic, bounded, and content-free

The Xiaohongshu probe SHALL classify the page as `home`, `explore`, `search`, `note_detail`, `profile`, `login`, or `unknown`, and SHALL return only sanitized URL components, document readiness, and bounded structural booleans/counts. It MUST NOT return outerHTML, visible text, account identity, note/comment content, cookies, storage, request data, selector strings, or the evaluated probe source.

#### Scenario: Known note detail is observed

- **WHEN** positive URL and structural evidence identifies a Xiaohongshu note-detail page
- **THEN** the result reports `note_detail` plus bounded structural signals without returning page content or selector details

#### Scenario: Evidence is ambiguous

- **WHEN** the URL and structural signals do not positively identify a supported page kind
- **THEN** the result reports `unknown` and MUST NOT guess a successful known classification

### Requirement: Local IPC SHALL be versioned, correlated, and honest about failure

The native process and TypeScript client SHALL use newline-delimited JSON protocol v1 over stdin/stdout. The process SHALL emit readiness, every accepted request SHALL receive at most one correlated response, stdout SHALL contain only protocol records, and stderr SHALL carry bounded diagnostics. Protocol drift, malformed records, deadline expiry, process exit, endpoint failure, target absence, CDP failure, and probe failure SHALL remain distinguishable by stable error codes.

#### Scenario: Supported request succeeds

- **WHEN** the TypeScript client receives protocol-v1 readiness and sends a valid `probe_page` request
- **THEN** it resolves only the response with the matching request id and returns the structured native result

#### Scenario: Request exceeds its deadline

- **WHEN** readiness or a probe response does not arrive within the configured deadline
- **THEN** the TypeScript client terminates the child, returns a timeout failure, and MUST NOT report a successful page state

#### Scenario: Native process exits unexpectedly

- **WHEN** the child exits before returning the correlated response
- **THEN** the client returns `engine_exited` with bounded process metadata and MUST NOT treat partial stdout as success

### Requirement: Host-architecture build and staging SHALL be reproducible without changing ordinary packaging

The Edge repository SHALL pin the Rust toolchain and Cargo dependency lockfile, provide a release build command, and stage the host-architecture binary outside ASAR under a deterministic platform/architecture path with a SHA-256 record. Ordinary TypeScript compilation and Electron packaging MUST NOT require Rust or the staged spike artifact.

#### Scenario: Native release build succeeds

- **WHEN** the pinned Rust toolchain builds the crate with the lockfile
- **THEN** the host binary and SHA-256 record are staged at the documented deterministic path

#### Scenario: Ordinary Edge build runs without Rust

- **WHEN** the existing TypeScript or default Electron build runs on a machine without the Rust toolchain and the probe was not explicitly requested
- **THEN** the existing build path does not invoke Cargo or fail because the native spike artifact is absent

#### Scenario: Staged artifact is inspected

- **WHEN** the native staging verification runs
- **THEN** it confirms the binary is outside ASAR, matches its SHA-256 record, and does not claim signed/notarized distribution readiness
