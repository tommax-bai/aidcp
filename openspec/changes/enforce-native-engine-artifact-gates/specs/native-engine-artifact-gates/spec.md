## ADDED Requirements

### Requirement: Embedded page-rule inventory has exactly one source of truth

The ordered source manifest that the Native engine build reads SHALL be the single authority for which page-rule fragments are embedded. Every gate, scanner, or test that enumerates those fragments MUST derive its enumeration from that manifest at run time and MUST NOT carry a hand-copied literal list. The build MUST fail when a file in the fragment directory is not registered in the manifest, when a manifest entry has no corresponding file, or when a manifest entry is not covered by every gate that claims to enumerate fragments.

#### Scenario: A new fragment is added to the manifest

- **WHEN** a page-rule fragment file is created and registered in the ordered source manifest
- **THEN** every leakage gate and packaging scanner covers it without any additional edit
- **AND** no gate needs a second list to be updated for the fragment to be guarded

#### Scenario: A fragment file exists but is not registered

- **WHEN** a file is placed in the fragment directory without being added to the ordered source manifest
- **THEN** the build fails and names the unregistered file
- **AND** the build MUST NOT succeed with that fragment silently absent from the produced binary

#### Scenario: A gate enumerates fragments from a private copy

- **WHEN** any gate or scanner enumerates page-rule fragments from a literal list rather than the manifest
- **THEN** the mechanical gate suite fails and identifies the private copy

### Requirement: Negative gates MUST be able to prove that they can fail

Every gate whose contract is "this content MUST NOT appear here" SHALL be accompanied by a mechanical self-test that plants the forbidden content in the corpus the gate inspects and asserts that the gate rejects it. A gate without such a self-test MUST NOT be counted as coverage in any completion claim. A gate whose inspected location cannot be produced by any supported build MUST be re-anchored to the corpus that can actually carry the leak, or removed; it MUST NOT be left in place reporting a pass.

#### Scenario: Gate is exercised against planted content

- **WHEN** the mechanical gate suite runs
- **THEN** each negative gate is executed once against a corpus containing planted forbidden content and is observed to reject it
- **AND** a gate that accepts the planted content fails the suite

#### Scenario: Gate inspects a location the build can never produce

- **WHEN** a negative gate enumerates paths under a directory that no supported build emits
- **THEN** the gate suite fails and reports the gate as inapplicable
- **AND** the gate's silent pass MUST NOT be reported as evidence that the guarded content is absent

#### Scenario: An allow-list widening reopens the leak path

- **WHEN** the packaging allow-list is widened so that page-rule source files could enter the archive
- **THEN** packaging fails and names the widened allow-list pattern
- **AND** the failure is raised by the allow-list assertion itself, not only in the case where the widened pattern happens to match an entry the derived forbidden-entry list enumerates

#### Scenario: Assertion on gate source text is not accepted as proof

- **WHEN** the only evidence for a gate is a test asserting that its script text contains a given identifier or literal
- **THEN** that evidence MUST NOT be treated as proof that the gate performs a judgement
- **AND** the gate still requires a planted-content self-test

### Requirement: Cleartext sentinels MUST be proven live before a scan counts as coverage

Each forbidden-cleartext marker used to scan a built engine artifact SHALL be verified to still occur in sources that enter the release compilation of the page-rule or engine code. A marker that occurs only in test-only compilation units, only in documentation, or nowhere at all MUST fail the gate as an expired sentinel. Removing an expired sentinel without replacement MUST be an explicit, recorded decision rather than a silent deletion.

#### Scenario: A marker survives only in a test-only unit

- **WHEN** a forbidden-cleartext marker occurs only inside a compilation unit that is excluded from release builds
- **THEN** the gate fails and names the marker as expired
- **AND** the scan result MUST NOT be reported as passing

#### Scenario: A renamed identifier silences a marker

- **WHEN** a rename or attribute removal makes a sentinel string absent from all release-compiled sources
- **THEN** the build fails at the sentinel liveness check rather than reporting a clean scan
- **AND** the failure message identifies which sentinel lost its subject

### Requirement: Fragment assembly MUST NOT depend on incidental source formatting

The build MUST NOT rely on each fragment happening to end with a newline in order for concatenation to be correct. The assembler SHALL either insert an explicit separator between fragments or assert that every fragment terminates with a newline, and MUST fail the build when the chosen invariant is violated. Any replica of the assembly used by tests or tooling SHALL apply the identical rule.

#### Scenario: A fragment loses its trailing newline

- **WHEN** a fragment file is saved without a trailing newline
- **THEN** the build fails and names that fragment
- **AND** the build MUST NOT emit a binary in which the following fragment's first line has been absorbed into a trailing comment

#### Scenario: Tooling replica stays consistent with the build

- **WHEN** a test or tool reassembles the fragments outside the build
- **THEN** it applies the same separator or newline-termination rule as the build
- **AND** a divergence between the two assemblies fails the gate suite

### Requirement: Artifact verification MUST be derived from the engine's own sources

The staged artifact manifest SHALL record a digest computed from the engine's source inputs — the Rust sources, the page-rule fragments, the ordered source manifest, the build script, and the command manifest. Verification SHALL recompute that digest from the working tree and compare it. When the digests differ, verification MUST report the artifact as stale and MUST NOT report success. Any development entrypoint that decides whether to rebuild SHALL make that decision from this comparison.

#### Scenario: A page-rule source is edited without rebuilding

- **WHEN** a page-rule fragment or Rust source file is modified and the development entrypoint runs
- **THEN** verification reports the staged artifact as stale and triggers a rebuild
- **AND** it MUST NOT print a verification-passed message while the running engine still corresponds to the previous sources

#### Scenario: Nothing changed since the last build

- **WHEN** verification runs and the recomputed source digest equals the digest recorded in the staged manifest
- **THEN** verification succeeds and no rebuild is performed

#### Scenario: Self-consistency is not accepted as verification

- **WHEN** the only checks available are the artifact's own checksum file, its own generated manifest, a crate version, and a capability digest that does not change with implementation edits
- **THEN** those checks MUST NOT be reported as verifying that the artifact matches the current sources

### Requirement: Native toolchain gates run where the TypeScript gates run

The Edge repository SHALL expose repository-level commands that run the engine crate's formatting check, static analysis, and tests. Those commands SHALL resolve the pinned toolchain regardless of the directory from which they are invoked, and MUST fail with a clear message when the toolchain or a required component is unavailable — they MUST NOT report the check as skipped, non-blocking, or passed. The integration gate that runs the TypeScript acceptance, unit, and typecheck steps SHALL also run these commands.

#### Scenario: Gate invoked from the repository root

- **WHEN** the native gate command is run from the repository root rather than the crate directory
- **THEN** it resolves the pinned toolchain and its required components and runs the checks

#### Scenario: A required component is missing

- **WHEN** the resolved toolchain lacks a component the gate needs
- **THEN** the command exits non-zero with a message naming the missing component and the toolchain it resolved
- **AND** the result MUST NOT be recorded as a skipped or non-blocking check

#### Scenario: Integration gate covers the native side

- **WHEN** a change touching the engine crate or its page-rule fragments goes through the integration gate
- **THEN** the native formatting, static-analysis, and test commands run as part of that gate
- **AND** their failure blocks integration exactly as a TypeScript gate failure does

### Requirement: A fixture that declares a cross-language source contract MUST be replayed on both sides

When a test fixture records that its expectations derive from a type defined in another language, both the language that replays the fixture and the language that owns the declared type SHALL have an executing assertion over that fixture. The owning side MUST assert that the declared type identifier still exists and that every fixture case's expected payload is still accepted by it. A one-sided replay MUST NOT be reported as evidence that the two sides agree, and the declared source contract MUST NOT be dropped as a way of resolving the asymmetry.

#### Scenario: Only the replaying side asserts

- **WHEN** a fixture declares a source contract naming a type in another language and only the replaying side has an assertion over it
- **THEN** the mechanical gate suite fails and names the fixture and the side that has no assertion

#### Scenario: The declared type is renamed or its shape changes

- **WHEN** the type named by the fixture's declared source contract is renamed, removed, or changed so that a fixture case's expected payload no longer conforms
- **THEN** the owning side's assertion fails and names the fixture case
- **AND** the failure MUST NOT be limited to a path-string comparison that stays green after the rename

### Requirement: The embedded-rule encoding is scan resistance, not confidentiality

Project documentation SHALL state that the encoding applied to embedded page rules provides resistance to casual scanning only, and that anyone holding a distributed artifact can recover the rules. The project MUST NOT place credentials, tokens, or any material granting access to remote systems into this channel, and MUST NOT justify doing so on the basis that the rules are encrypted. The encoding key SHALL have exactly one definition shared by the build and every runtime consumer, so that rotating it cannot take effect in some consumers and not others. A decode-and-inspect assertion over the embedded content SHALL run in the mechanical gate suite.

#### Scenario: Guardrail documentation states the boundary

- **WHEN** a contributor reads the repository guardrail documentation before adding an embedded asset
- **THEN** the documentation states that the encoding is scan resistance only and does not provide confidentiality

#### Scenario: Sensitive material is proposed for the same channel

- **WHEN** a change would embed a credential, token, or remote-access key through the encoded page-rule channel
- **THEN** the change is rejected on the recorded ground that this channel provides no confidentiality

#### Scenario: Key rotation cannot be applied partially

- **WHEN** the encoding key is changed
- **THEN** the build and every runtime consumer take the new value from the single definition
- **AND** a decode assertion over the embedded content runs in the gate suite and fails if any consumer disagrees

### Requirement: Retired-path coverage MUST NOT be presented as production coverage

The Edge test suite SHALL distinguish tests whose subject is a module excluded from the production build from tests that cover production-reachable behavior, and SHALL report the two counts separately. A completion claim for behavior that now lives in the Native engine MUST NOT cite retired-path tests as its coverage. Retired-path tests MUST NOT be silently skipped or deleted as a way of resolving this distinction while they remain the only recorded behavior oracle for a not-yet-ported capability.

#### Scenario: Suite reports both counts

- **WHEN** the Edge test suite finishes
- **THEN** it reports how many tests covered production-reachable modules and how many covered modules excluded from the production build

#### Scenario: A native behavior claims coverage from a retired test

- **WHEN** a change claims a Native engine behavior is covered, and the only failing-on-regression test targets a module on the production exclusion list
- **THEN** that claim is rejected and the missing native coverage is recorded

#### Scenario: A production module is added to the exclusion list

- **WHEN** a module is newly excluded from the production build
- **THEN** the tests targeting it are reclassified as retired-path coverage rather than left counted as production coverage

### Requirement: Engine gate tests MUST NOT fail from scheduling jitter alone

Tests that exercise time-bounded engine behavior SHALL derive their deadlines from an injectable or test-controlled clock, or SHALL be given budgets that cannot be exhausted by ordinary scheduling and process-startup contention under the suite's default parallelism. A test MUST NOT compute an absolute wall-clock deadline at construction time with a margin smaller than the contention it will run under. Where a test genuinely requires exclusive timing, it SHALL be serialized explicitly rather than left flaky.

#### Scenario: Deadline behavior is exercised deterministically

- **WHEN** a test asserts what happens when a command crosses its deadline
- **THEN** the crossing is produced by the test-controlled clock rather than by real elapsed time
- **AND** the test yields the same result under serial and parallel runs

#### Scenario: Client test spawns a real child process

- **WHEN** an engine client test starts a real child process and performs a protocol handshake
- **THEN** its per-command budget accommodates process startup under the suite's default parallelism, or the test is explicitly serialized
- **AND** a first-run failure attributable only to contention is treated as a defect in the test, not as an unrelated flake to be re-run
