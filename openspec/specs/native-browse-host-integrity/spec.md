# native-browse-host-integrity Specification

## Purpose
TBD - created by archiving change restore-native-xiaohongshu-session-guards. Update Purpose after archive.
## Requirements
### Requirement: Per-command receipt diagnostics SHALL be platform-neutral

The Edge host that drives the Native page engine SHALL emit one bounded diagnostic record for every command receipt it processes, for every platform, containing at least the action name, whether it succeeded, the effect phase, and the terminal reason code. Platform identity MUST NOT gate whether the record is emitted.

Diagnostic records MUST remain bounded and redacted: reason codes and action names MUST pass the existing token normalization, and records MUST NOT carry page body text, credentials, captcha answers, upload content, or page selectors.

The reason this is a contract rather than a convenience: when one platform has per-command evidence and another has only "session started" and "session failed", defects on the silent platform can only be found by reading source. Uneven diagnostics make an uneven defect backlog, and the silent platform's regressions stay invisible.

#### Scenario: Xiaohongshu browse loop leaves per-command evidence

- **WHEN** a Xiaohongshu browse session executes a scroll, opens a note, performs an interaction, and returns
- **THEN** each command receipt produces one diagnostic record with action name, success, effect phase, and reason code
- **AND** the same records are produced for the equivalent Facebook commands, with no platform-identity guard deciding whether they appear

#### Scenario: Diagnostics stay bounded and redacted

- **WHEN** a command fails with a reason that is not a normalized token, or the receipt carries page text
- **THEN** the diagnostic record substitutes a normalized placeholder for the reason and omits the page text
- **AND** it carries no credentials, captcha answer, upload content, or selector

### Requirement: Native browse sessions SHALL emit platform-neutral lifecycle diagnostics

Beyond per-command receipts, the host SHALL emit a bounded diagnostic for each Native browse session state transition, for every platform: session ready, blocking state detected, blocking state cleared, yielding to an exclusive task and resuming, and terminal stop with its reason.

These records are operator-facing evidence, not product presence. Product-level presence and activity events for the companion interface MAY remain scoped to the platforms that declare them; that scoping MUST NOT be used to suppress the lifecycle diagnostics above, and the absence of presence events on a platform MUST NOT be recorded as a diagnostics gap.

#### Scenario: Blocking transitions are visible on every platform

- **WHEN** any Native browse session detects a blocking state and later observes it cleared
- **THEN** both transitions produce lifecycle diagnostics naming the classification and the observed location
- **AND** the records appear regardless of which platform the session drives

#### Scenario: Presence scoping does not suppress diagnostics

- **WHEN** a platform declares no companion-interface presence events
- **THEN** its sessions still emit ready, yield/resume, and terminal-stop diagnostics
- **AND** the missing presence events are treated as an explicit product scope, not as an observability defect to be re-fixed

### Requirement: Compile-time-unreachable host assembly SHALL NOT be retained

The Edge host MUST NOT retain an assembly block whose entry condition is statically false, and MUST NOT declare shadow ambient bindings for modules that the production build prunes in order to keep such a block compiling. That combination type-checks, prunes, and tests green while executing nothing, so no gate reports that the capabilities inside it have stopped running.

When a capability is removed from the host — because its execution moved elsewhere or because it is retired — the removal MUST be reconciled item by item, and each item MUST resolve to exactly one of:

- a named owner in the new execution path, recorded with its landing point, or
- a registered gap, recorded where open work is tracked.

An item that resolves to neither MUST block the removal. Leaving the old code present as "reference" MUST NOT be used in place of that reconciliation, and re-enabling such a block behind a runtime flag MUST NOT be used either — that would create a real fallback execution path and reintroduce the pruned page rules into the shipped package.

A mechanical check MUST fail when a statically-false assembly entry condition or a shadow ambient declaration for a pruned module is reintroduced, and MUST name the offending file and line.

#### Scenario: Unreachable assembly is rejected

- **WHEN** the host source contains an assembly entry condition that is statically false, or an ambient declaration standing in for a module the production build prunes
- **THEN** the mechanical check fails and names the file and line
- **AND** the build does not pass on the grounds that type-checking, pruning, and unit tests are green

#### Scenario: Capability removal is reconciled item by item

- **WHEN** a host assembly block containing several capabilities is removed
- **THEN** every capability in it is recorded as either owned by a named new landing point or registered as an open gap
- **AND** an unreconciled capability blocks the removal instead of disappearing silently

#### Scenario: Flag-gated revival of the block fails the gate

- **WHEN** the host source reintroduces the assembly block behind a runtime flag, so that the entry condition is no longer statically false
- **THEN** the packaged-output verifier fails because the modules the block references are page-rule modules the production build prunes, and it names them
- **AND** no packaged build is produced that contains both the block and those modules

#### Scenario: Reconciliation record replaces the retained block

- **WHEN** the removal of the unreachable block is complete
- **THEN** the host source contains neither the block nor its shadow ambient declarations, and the source-level check passes
- **AND** every capability the block contained is findable in the reconciliation record as either an owned landing point or a registered gap, so no reader needs the deleted code as reference

### Requirement: Browse-session start failures SHALL leave the process

Every browse-session start site SHALL route its failure through one named reporting path that reports to the cloud, moves the host's runtime posture off normal, and classifies the failure as structural or not. The periodic observation loop MUST be armed regardless of whether the first scan succeeded.

A browse session's first scan is the ignition of the whole browse loop: the cloud's role graph starts on the edge's first structured page report. If that first scan fails and the failure stays inside the edge process, the cloud does not learn that a session was attempted — no watchdog fires, no escalation happens, and no operator-visible state changes. The session is dead and every other signal reads healthy.

Every browse-session start site — first start, restart after identity re-establishment, resume from pause, and wake from cold standby — MUST route its failure through one named reporting path rather than terminating in a per-site log statement.

That path MUST do all of the following:

- **Report to the cloud.** A start failure MUST be observable outside this process. Being unable to reach the cloud at that moment does not remove the obligation; it defers it.
- **Move the host's runtime posture off "normal".** The shell decides whether the core has halted from a named set of signals. A start failure that is not in that set leaves automation projected as ready-and-idle, which is what lets a dead session be presented as a working one.
- **Classify the failure as structural or not, and say which.** Structural means: the identical step, replayed on a freshly loaded page, cannot produce a different result — admission rejections and unsupported-capability refusals are structural. Endpoint-unreachable, browser-not-ready and comparable conditions are not. A structural failure MAY reach a terminal state and its receipt MUST state why a retry cannot change the outcome. A non-structural failure MUST NOT reach a terminal state and MUST retain a bounded self-heal path.

**Arming the periodic observation loop MUST NOT be conditional on the first scan succeeding.** A first scan that fails is precisely the state in which periodic re-observation is the only remaining route back to a working session; sequencing the arming after the scan removes the recovery path exactly when it is needed, and no start site re-triggers it.

#### Scenario: A start failure reaches the cloud
- **WHEN** a browse session's first scan fails at any start site
- **THEN** the failure is reported to the cloud rather than terminating in a local log line

#### Scenario: A start failure is visible in the host's runtime posture
- **WHEN** a browse session fails to start while the core process is alive and the transport is connected
- **THEN** the host's runtime posture leaves the normal state
- **AND** automation is not projected as ready-and-idle

#### Scenario: A structural start failure states why retrying cannot help
- **WHEN** a session is refused at the engine's admission
- **THEN** the receipt records a structural failure and states that an identical retry cannot change the result

#### Scenario: A non-structural start failure keeps a bounded recovery path
- **WHEN** a session fails to start because the browser endpoint is not reachable
- **THEN** the failure is not recorded as terminal
- **AND** a bounded self-heal path remains armed

#### Scenario: Periodic observation is armed despite a failed first scan
- **WHEN** the first scan of a browse session fails
- **THEN** the periodic observation loop is still armed

