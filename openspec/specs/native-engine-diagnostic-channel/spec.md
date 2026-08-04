# native-engine-diagnostic-channel Specification

## Purpose
TBD - created by archiving change surface-native-engine-diagnostics. Update Purpose after archive.
## Requirements
### Requirement: Engine diagnostics written on a successful path MUST reach an operator-readable sink

The Native engine runs as a host-spawned child process whose error output is its only free-form channel. Diagnostics the engine writes there MUST reach a place an operator can read **without requiring the engine process to fail or exit**.

Retaining the error output solely as evidence attached to a process-level failure object is NOT sufficient and MUST NOT be treated as satisfying this requirement: the majority of the engine's existing diagnostics are written on paths where the command returns normally and the process stays alive, so a failure-only surface discards them entirely. A diagnostic that is written but structurally unreachable is equivalent to no diagnostic, and any requirement or accounting that depends on such a line MUST be read as unmet until this channel exists.

The existing bounded rolling tail MUST be preserved for process-level failure attribution. Forwarding is additive: the same output serves both surfaces.

#### Scenario: Diagnostic emitted while a command succeeds

- **WHEN** the engine writes a diagnostic line to its error output during a command that then returns successfully and the process stays alive
- **THEN** the host forwards that line to the operator-readable sink
- **AND** the command's own result and receipt are unchanged

#### Scenario: Failure-only surface no longer sole path

- **WHEN** the engine returns an error response for a rejected request without exiting
- **THEN** the diagnostic the engine wrote for that rejection is forwarded
- **AND** it does not depend on the process subsequently dying

#### Scenario: Process-level failure attribution is preserved

- **WHEN** the engine process crashes, times out, or violates the IPC protocol
- **THEN** the host still attaches the bounded rolling tail to the raised failure detail exactly as before

### Requirement: Forwarded engine output MUST be line-framed and honest about incomplete lines

The host MUST maintain its own line buffer over the child's error stream and MUST emit only complete lines, except where explicitly marked otherwise. A line split across two read chunks MUST be forwarded as one line, not two.

A line exceeding the per-line bound MUST be forwarded truncated **with an explicit truncation marker**; it MUST NOT be silently shortened. A partial line still buffered when the process exits MUST be flushed **with an explicit incompleteness marker**; it MUST NOT be discarded, because the fragment written immediately before a crash is frequently the most informative one.

#### Scenario: Line split across read chunks

- **WHEN** the engine's error output arrives as two chunks that split a single line
- **THEN** the host forwards exactly one complete line

#### Scenario: Over-long line

- **WHEN** a single error-output line exceeds the per-line bound
- **THEN** the host forwards the bounded prefix together with an explicit marker that it was truncated

#### Scenario: Partial line at process exit

- **WHEN** the process exits while an unterminated fragment remains in the line buffer
- **THEN** the host flushes that fragment marked as incomplete rather than dropping it

### Requirement: Each forwarded line MUST carry honest attribution

Every forwarded line MUST identify the command in flight when it arrived. Where no command is in flight — session open, reconnect, or shutdown — the line MUST be marked as having no in-flight command. It MUST NOT be attributed to the preceding or following command.

Attribution MUST be derived from the layer that actually knows which command is executing. Inferring it from the count of outstanding IPC records is NOT permitted: control records may be outstanding concurrently with a command, so that count does not identify a command.

#### Scenario: Line arrives during a command

- **WHEN** a diagnostic line arrives while a command is executing
- **THEN** the forwarded line names that command

#### Scenario: Line arrives between commands

- **WHEN** a diagnostic line arrives during session open, reconnect, or shutdown with no command executing
- **THEN** the forwarded line states that there was no in-flight command
- **AND** it is not attributed to the adjacent command in either direction

### Requirement: Forwarding volume MUST be bounded and the bound MUST be announced

Forwarding MUST be bounded per command. When the bound is reached, the host MUST retain the **earliest** lines and MUST emit an explicit count of the lines it suppressed.

Going quiet after the bound is NOT permitted. A channel that forwards the first N lines and then stops without saying so is indistinguishable from an engine that stopped writing, which converts a volume limit into a false negative.

#### Scenario: Volume under the bound

- **WHEN** a command produces fewer diagnostic lines than the per-command bound
- **THEN** every line is forwarded and no suppression notice is emitted

#### Scenario: Volume over the bound

- **WHEN** a command produces more diagnostic lines than the per-command bound
- **THEN** the earliest lines up to the bound are forwarded
- **AND** an explicit suppressed-line count is emitted for that command
- **AND** the channel does not simply fall silent

### Requirement: All engine error output MUST be forwarded and classified

The host MUST forward every line, not only lines matching the engine's named diagnostic family. Each forwarded line MUST be classified as either a recognized engine diagnostic or unclassified output.

Filtering to the recognized family only is NOT permitted: it would discard panics and backtraces — the highest-value output the engine ever produces — and would discard them silently. Classification is load-bearing rather than decorative: it makes "the host forwarded something it does not recognize" a visible fact instead of merging it into the recognized set.

#### Scenario: Recognized diagnostic

- **WHEN** the engine writes a line belonging to its named diagnostic family
- **THEN** the forwarded line is classified as recognized

#### Scenario: Panic or backtrace

- **WHEN** the engine panics and writes a message and backtrace to its error output
- **THEN** those lines are forwarded and classified as unclassified output
- **AND** they are not dropped for failing to match the recognized family

### Requirement: Content safety of engine error output is the engine's obligation and MUST be stated as such

The engine MUST NOT write page-derived content to its error output: no selector, URL, DOM text, cookie, credential, storage value, or raw page-supplied string. Diagnostics MUST be composed of engine-generated, bounded, finite-vocabulary elements.

This obligation exists today only for the typed-decode diagnostic path, where it was safe partly because nothing consumed the output. Once forwarding exists the output is persisted to the local log, so the obligation MUST apply to **every** write to the engine's error output.

The host MUST apply a length bound, and MUST NOT be described or relied upon as validating content: the host cannot distinguish an engine-generated token from a page-derived one. Where a bound is the only host-side protection, that MUST be stated rather than implied.

#### Scenario: Decode failure diagnostic

- **WHEN** a typed decode failure produces a diagnostic
- **THEN** the forwarded line contains only the field path, stage, and value category
- **AND** it contains none of the offending value, raw parser text, evaluated source, selector, or URL

#### Scenario: Host bound is not content validation

- **WHEN** the host forwards a line
- **THEN** it enforces only the length bound and classification
- **AND** it does not claim to have verified the line is free of page-derived content

### Requirement: The diagnostic sink MUST be wired in the production path, not merely available

Offering the sink as an injectable option is NOT sufficient. The production runtime MUST supply a sink, and that wiring MUST be asserted by reference rather than inferred from the option's existence.

The failure this guards against is specific and silent: the option is added, every unit test of the option passes, the production construction path never passes one, and the channel therefore still does not exist — while the work reads as complete.

#### Scenario: Production runtime construction

- **WHEN** the production Native page runtime constructs its engine client
- **THEN** it supplies a diagnostic sink
- **AND** a test asserts that supplied sink by reference rather than asserting only that the option is accepted

#### Scenario: Sink absent

- **WHEN** a client is constructed without a sink, as in a fixture
- **THEN** behavior is identical to the pre-change behavior and no error is raised

### Requirement: Forwarded diagnostics MUST stay on the local machine

Forwarded engine diagnostics MUST reach only local sinks. They MUST NOT be sent over the Edge-Cloud connection, and this change MUST NOT alter the Edge-Cloud protocol or the Native IPC protocol version.

#### Scenario: Diagnostics remain local

- **WHEN** engine diagnostics are forwarded
- **THEN** they appear only in local operator-readable sinks
- **AND** no Edge-Cloud message is emitted as a result
- **AND** neither the Edge-Cloud protocol version nor the Native IPC protocol version changes

