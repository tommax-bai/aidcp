## ADDED Requirements

### Requirement: The Native command manifest SHALL be a verified contract rather than documentation

Every declared column of the Native command manifest — the receipts a command produces, its request contract name, its effect class, and its cancellation class — SHALL be mechanically reconciled against the implementation that the packaged engine and its host actually run. A declared value that no implementation can produce MUST fail a repository check; it MUST NOT be accepted merely because the declared string is non-empty.

For each command, the set of receipts declared in the manifest MUST equal the union of the receipts that some reachable **successful** execution path of that command can cause the host to emit — reachable across supported platforms and surfaces, since one execution yields one output. Every declared receipt MUST have at least one such reachable emission path, and every reachable successful emission MUST be declared. The reconciliation MUST exclude failure paths, because the host emits a negative action-completion receipt for every failed command regardless of kind; counting failure paths would make the declaration trivially satisfied for that receipt and reduce the check to a tautology.

When a declared receipt has no reachable successful emission path, the divergence MUST be resolved either by emitting it or by correcting the declaration; leaving the declaration unbacked is not an acceptable outcome. The same applies in the other direction: a receipt the host does emit on a successful path but the manifest omits MUST fail the check. Any command whose divergence is deliberately deferred MUST appear in an explicit, individually justified freeze list, and that list MUST only shrink.

The manifest is an input to the capability digest that gates artifact loading, so an unverified declaration is a cryptographically pinned falsehood. Declaring a receipt MUST therefore be treated as a behavioral commitment.

#### Scenario: A command declares a receipt that no successful path emits

- **WHEN** the manifest declares that opening a post produces both a post-detail receipt and an action-completion receipt, but every successful path of that command on every supported platform produces only the post-detail receipt
- **THEN** the repository conformance check fails and names the command and the unbacked receipt
- **AND** the check does not pass merely because the declared receipt string is non-empty
- **AND** the check does not treat the negative action-completion receipt emitted on failure as backing the declaration

#### Scenario: A command emits a receipt it does not declare

- **WHEN** a successful execution of a command emits a receipt that the manifest does not list for it
- **THEN** the conformance check fails and names the undeclared receipt
- **AND** a command whose two declared receipts are both reachable — one per platform, or both within one successful path — passes without being flagged

#### Scenario: A new command is added with an unbacked receipt declaration

- **WHEN** a new Native command is added to the manifest with a receipt that no host emission path can produce
- **THEN** the conformance check fails before the artifact can be built or loaded
- **AND** the failure identifies the declared receipt rather than reporting a generic manifest error

#### Scenario: A deferred divergence is frozen explicitly

- **WHEN** a known declaration divergence cannot be resolved within the same change
- **THEN** it is recorded in the freeze list with the command, the declared value, the actual behavior, and the elimination action
- **AND** a subsequent change may remove entries from the freeze list but MUST NOT add entries that restore a previously eliminated divergence

### Requirement: The Native command vocabulary SHALL be enumerated from the engine's own command type

The check that proves the Native command vocabulary and the frozen manifest agree SHALL derive one side of the comparison from the engine's exhaustive command type, not from a hand-maintained parallel list. Any command variant that the engine can deserialize and execute but that is intentionally absent from the manifest MUST appear in an explicit exclusion set that is itself asserted, together with the reason it is excluded.

A check whose name claims to compare the command type MUST actually compare the command type. Adding a new executable command variant without updating the manifest or the justified exclusion set MUST fail.

#### Scenario: An executable variant is missing from the manifest

- **WHEN** the engine can deserialize and execute a page-probe command that the manifest does not list
- **THEN** the vocabulary check fails unless that variant is present in the asserted exclusion set with a recorded reason
- **AND** the check does not pass because a separate hand-written list happens to match the manifest

#### Scenario: A new command variant is added to the engine only

- **WHEN** a new command variant is added to the engine's command type and to no other file
- **THEN** the vocabulary check fails and names the variant
- **AND** the failure occurs in the repository check rather than at runtime on a customer machine

### Requirement: Commit-window labels and budgets SHALL have one source of truth

The protected commit window that guards an irreversible platform write SHALL have exactly one authoritative declaration of its label set and its per-label budget. The engine SHALL request a window by label, and the budget applied to that window SHALL be derived from the single authority rather than independently restated by the engine and then compared for equality.

The host SHALL remain the enforcement point for the upper bound of a protected window: it MUST NOT grant a window longer than the authority declares for that label, and it MUST NOT accept an arbitrary budget supplied by the engine.

If, despite the single authority, a request arrives with an unknown label or a budget inconsistent with the authority, the host MUST classify the condition as an attributable contract violation for that command, MUST report it as such, and MUST NOT terminate the whole engine process as an anonymous protocol violation. A tuning change to one window budget MUST NOT be able to manifest as engine termination immediately before an irreversible write.

#### Scenario: A window budget is changed on one side only

- **WHEN** the budget for a group-join commit window is edited in one language's source and not the other
- **THEN** the repository check fails before any artifact is produced
- **AND** no runtime path exists in which that edit terminates the engine at the moment before the join button is pressed

#### Scenario: An inconsistent window request still reaches the host

- **WHEN** the host receives a commit-window request whose label is unknown or whose budget does not match the authority
- **THEN** the host refuses that window with an attributable contract-violation reason bound to the requesting command
- **AND** the engine process is not terminated, and the command reports an honest non-success terminal result

#### Scenario: Engine cannot widen its own protection window

- **WHEN** the engine requests a protected window with a budget larger than the authority declares for that label
- **THEN** the host grants at most the authoritative budget
- **AND** the excess is not honored

### Requirement: A dead Native engine MUST NOT block its own recovery

Local teardown of a Native page session MUST run regardless of whether the terminating command succeeded. When the host issues the session-ending command and that command fails because the engine process is gone, the host MUST still release the cached session owner so that the next command rebuilds the engine.

A cached session handle MUST NOT be returned to a caller unless its underlying transport is affirmatively established to be live at that moment. Absence of a recorded death is not evidence of liveness: if liveness cannot be established, the host MUST treat the handle as dead, discard it, and rebuild rather than returning a handle that will immediately fail.

Recovery MUST NOT require an operator to pause and resume the environment or restart the whole core process.

#### Scenario: Session end is issued after the engine has exited

- **WHEN** the engine process has exited and the host issues the session-ending command, which fails with an engine-exited error
- **THEN** the host still performs its local session teardown and releases the cached owner
- **AND** the next admitted command starts a new engine process instead of failing with the same engine-exited error

#### Scenario: A cached handle whose transport is dead is not reused

- **WHEN** a command is admitted for an owner whose cached session's transport has already terminated
- **THEN** the host discards that cached session and opens a new one
- **AND** it does not return the dead handle and report an immediate failure

#### Scenario: Liveness of the cached handle cannot be established

- **WHEN** a command is admitted and the host cannot establish that the cached session's transport is live
- **THEN** the handle is treated as dead and the session is rebuilt
- **AND** the handle is not reused on the grounds that no death was recorded

#### Scenario: Recovery does not depend on manual operator action

- **WHEN** an engine process dies during an otherwise healthy environment
- **THEN** the environment returns to executing commands through the normal session lifecycle
- **AND** no manual pause/resume or core-process restart is required to clear the condition

### Requirement: Native reconnect SHALL bind to the admitted browser instance

When the Native engine reconnects its page connection, it SHALL resolve the browser debugging endpoint from the current provider-supplied handle rather than from a value captured when the session was first opened. A session that may live for hours MUST NOT treat the first endpoint it saw as permanently authoritative.

Target selection during reconnect MUST require evidence that the selected target belongs to the same browser instance that was admitted for this session. Matching on platform and port alone is insufficient, because debugging ports are dynamically allocated and a port released by one environment can be reissued to another on the same machine.

If the endpoint cannot be re-resolved, or if no candidate target can be proven to belong to the admitted instance, the engine MUST report an honest failure to its host and MUST NOT attach to any other target. Executing this session's commands against another environment's browser is a platform-visible cross-environment misdirection and MUST be prevented rather than detected after the fact.

#### Scenario: The debugging port has been reissued to another environment

- **WHEN** the engine reconnects and the recorded port now answers for a different environment's browser instance
- **THEN** the engine refuses to attach because the identity evidence does not match the admitted instance
- **AND** no command is executed against that browser

#### Scenario: The provider has issued a new endpoint for the admitted instance

- **WHEN** the admitted browser instance is still healthy but its debugging endpoint has changed since the session was opened
- **THEN** reconnect resolves the current endpoint from the provider-supplied handle and attaches to the admitted instance
- **AND** it does not fail because the originally captured endpoint no longer answers

#### Scenario: No identity evidence is available

- **WHEN** the engine cannot obtain evidence that any reachable target belongs to the admitted instance
- **THEN** it returns an honest executor-health failure to the host
- **AND** it does not fall back to selecting a target by platform and port alone

### Requirement: Post-reconnect retry SHALL stay inside the command budget

A retry performed after a reconnect SHALL be bounded by the same absolute deadline as the original attempt. The engine MUST NOT grant the retry an independent budget, and MUST NOT continue to occupy its single command slot past the caller's deadline. This applies to every command for which the reconnect-and-retry path is reachable at all — today only non-write commands, of which the longest-budgeted is the observe-mode group join.

Because the engine accepts one command at a time and rejects every other command while one is in flight, and because the host stops waiting once the budget expires without sending a cancellation, an unbounded retry silently converts one slow command into a period during which the environment can execute nothing. When the absolute deadline passes, the engine MUST end the attempt, release the slot, and report an honest timeout.

#### Scenario: Reconnect plus retry would exceed the command budget

- **WHEN** a non-write command with a 90-second budget consumes most of it, reconnects, and retries
- **THEN** the retry is cut off at the original absolute deadline and reports a timeout
- **AND** the command slot is released so the next admitted command is not rejected as already-in-progress

#### Scenario: Retry does not receive a fresh budget

- **WHEN** a reconnect succeeds near the end of the command budget
- **THEN** the retry runs only within the remaining budget
- **AND** the total time for the command does not become the sum of an initial budget and a second full budget

### Requirement: Page-rule root resolution and decode failures SHALL be honest and diagnosable on every platform

Page-rule root resolution MUST NOT hand an absent root to traversal. When the document is in a navigation window in which no usable root exists, the rule MUST return an honest not-started reason for the command rather than raising an in-page exception. The guard MUST live in the shared element-lookup path, so that a rule which forgets to check its own fallback cannot collapse; per-call-site null checks alone are insufficient, because the next rule that resolves a root can omit its own check.

The guard is required at the lookup layer specifically because of the failure mode it prevents on write commands: any rule-level error raised while executing a write command is classified as a possibly-actuated outcome, so an in-page exception on a write path is reported as "may already have happened" rather than "never started". No write path is currently known to reach an absent root — the presently reachable collapse is on a read path — so this requirement is a structural guard against the next rule, not a claim that a write has already been misreported.

Bounded decode diagnostics — operation phase, decode stage, field path, and exception location — MUST be produced for every platform's result-decoding entry point, not only for one platform. A decode failure on any supported platform MUST carry the same class of attributable diagnostics.

The per-character typing focus guard MUST distinguish a failure to evaluate the guard itself, or a missing guard output, from a proven loss of the input target. These MUST NOT collapse into one reason, because a collapsed reason directs every investigation toward selector correctness regardless of the real cause.

#### Scenario: Navigation window leaves no usable root

- **WHEN** a page rule resolves its root during a navigation commit and neither the preferred containers nor the document body is usable
- **THEN** the command returns an honest not-started reason
- **AND** no traversal is attempted on an absent root

#### Scenario: The shared lookup receives an absent root

- **WHEN** any rule calls the shared element-lookup path with an absent root, whether or not that rule checked its own fallback
- **THEN** the lookup returns an empty result attributable to an absent root instead of raising an in-page exception
- **AND** a write command on that path is therefore not reported as possibly actuated

#### Scenario: Decode fails on a platform other than the one that had the incident

- **WHEN** result decoding fails for a non-Facebook platform command or for the page-probe entry point
- **THEN** the failure carries the same bounded decode diagnostics as the Facebook entry point
- **AND** the diagnostics remain bounded and free of page content, credentials, and cookies

#### Scenario: The focus guard itself fails to evaluate

- **WHEN** the per-character focus guard cannot be evaluated or returns no usable output
- **THEN** the reported reason distinguishes that condition from a proven loss of the input target
- **AND** the reported reason for a proven target loss remains unchanged

### Requirement: The Facebook comment submission budget SHALL be computed once and transported

The time budget for a Facebook comment submission SHALL be computed by exactly one side of the cloud/edge boundary, from the exact string that will be typed into the editor, including any approved suffix that the platform-side rule appends. The other side SHALL derive its waiting window from the transported value rather than recomputing the same formula from its own copy of the constants.

Neither side may hold an independent copy of the base, per-character, ceiling, and floor constants for this budget. A budget derived from a shorter string than the one actually typed MUST NOT be used, because a premature timeout on the deciding side is reported as an unsubmitted comment, which suppresses the deduplication marker and can cause a second real comment on the same post.

#### Scenario: A comment carries an approved suffix

- **WHEN** a comment is submitted with an approved contact or group-code suffix that the platform rule appends to the body
- **THEN** the single computed budget accounts for the full string including the suffix
- **AND** the deciding side's waiting window is not shorter than the executing side's, so a slow but successful submission is not reported as a timeout

#### Scenario: The budget constants are changed

- **WHEN** the base, per-character, ceiling, or floor constant for this budget is changed
- **THEN** exactly one declaration changes
- **AND** no second copy of the formula remains that could keep the previous value
