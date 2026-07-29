# native-page-engine Specification

## Purpose
TBD - created by archiving change native-page-engine-spike. Update Purpose after archive.
## Requirements
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

### Requirement: Native typed-result failures SHALL expose bounded decode-path diagnostics

When a typed browser result cannot be produced or decoded, the Native Page Engine SHALL preserve its existing stable error code and static message and SHALL add a bounded, content-free diagnostic identifying the operation stage, decode stage, expected router result kind when applicable, failing typed field path when available, and actual JSON value category. For an evaluated-router exception, it MAY additionally include only a finite exception class/reason, bounded line/column, and an identifier-only token extracted from a recognized engine-generated pattern. The diagnostic MUST NOT include the offending value, raw CDP result, raw exception/parser message, evaluated source, selector, URL, DOM text, cookie, credential, or storage value.

The diagnostic fields SHALL use finite allowlisted stage/category values and bounded paths. An optional diagnostic added to an internal Native IPC protocol-v2 error record MUST remain compatible with clients that do not consume it, and the current TypeScript client SHALL preserve it in the raised Native error detail without changing the stable error code or effect truth. This internal IPC addition MUST NOT change the Edge-Cloud WebSocket protocol.

#### Scenario: Nested typed field is incompatible

- **WHEN** a Facebook router result has the expected wrapper and result kind but one nested typed field carries an incompatible JSON category
- **THEN** the failure retains `cdp_error` and the static bounded message while its diagnostic identifies `typed_value`, the exact bounded field path, expected result kind, and actual JSON category without including the field value

#### Scenario: Wrapper and result-kind failures remain distinguishable

- **WHEN** CDP returns an exception, omits `result.value`, omits the router output value, or returns an unexpected router output kind
- **THEN** the diagnostic reports the corresponding finite decode stage rather than collapsing those cases into an indistinguishable field failure

#### Scenario: Evaluated router exception is classified without raw text

- **WHEN** the browser returns `exceptionDetails` because a router helper reads a property from null during a transient navigation document
- **THEN** the diagnostic identifies `cdp_exception`, its finite error class/reason, bounded location, and safe identifier token without returning the raw exception description or evaluated source

#### Scenario: Diagnostic is safely absent

- **WHEN** an older or unrelated Native failure carries no diagnostic object
- **THEN** the TypeScript client preserves the existing stable error behavior and does not require or fabricate diagnostic fields

#### Scenario: Untrusted content is redacted

- **WHEN** a typed decode failure is caused by a string, object, or array containing page-derived text
- **THEN** serialized stdout, bounded stderr, and the TypeScript error detail contain only its field path and JSON category and contain none of the raw value or parser text

### Requirement: Observation-only group join failures SHALL remain not started

A Native Facebook `group_join` command whose `click` parameter is false SHALL be classified as observation-only. If it fails to navigate, probe, or decode, its effect phase SHALL be `not_started`; it MUST NOT be upgraded to `ambiguous` solely because the command kind can support a separate `click=true` write path. A `click=true` failure MUST retain conservative write-effect truth unless the orchestration has explicit actuation-boundary evidence.

#### Scenario: Observation decode fails

- **WHEN** `group_join(click=false)` fails while decoding a pre-actuation browser result
- **THEN** the error retains its diagnostic and reports `effectPhase=not_started`, not `native_effect_ambiguous`

#### Scenario: Write-capable invocation remains conservative

- **WHEN** `group_join(click=true)` fails and the engine cannot prove whether actuation occurred
- **THEN** it remains ambiguous and MUST NOT be reclassified as not started by the observation-only rule

### Requirement: Group-join action receipts SHALL preserve the structured observation across the Native bridge

When the Rust Native Page Engine returns a group-join action receipt, the Edge TypeScript bridge SHALL forward the group-specific structured observation as the `action.completed.observation` witness even when the serialized generic observation field is JSON `null`. The bridge MUST preserve an existing non-null generic observation, MUST remove the internal group-specific alias before sending the Edge-Cloud payload, and MUST NOT infer success, membership, or actuation from the normalization.

#### Scenario: Rust null option does not discard the group observation

- **WHEN** a Native action receipt contains `observation: null` and a non-null `groupObservation` object
- **THEN** Edge forwards that object as `action.completed.observation` and omits `groupObservation`

#### Scenario: Existing generic observation remains authoritative

- **WHEN** a Native action receipt contains both a non-null generic observation and a group-specific observation
- **THEN** Edge preserves the generic observation as-is and does not replace it

#### Scenario: Both observation forms are absent

- **WHEN** a Native action receipt has neither a non-null generic observation nor a non-null group observation
- **THEN** Edge does not fabricate evidence and Cloud remains able to fail closed

