## Context

The Native Page Engine process boundary is sound: Edge sends typed semantic commands, Native owns page inspection and actuation, and no production TypeScript fallback contains Facebook selectors or browser rules. The regression came from preserving that outer boundary while flattening capability behavior inside it.

Today the generic Rust engine owns Facebook session state plus Feed, Reels, Like, Follow, Comment, Group Join, Publish, blocker, consent, and verification workflows. The embedded Facebook router similarly contains every browser-side locator and probe in one source file. Capability probes frequently reduce a live DOM target to coordinates before Rust decides how to commit the write. That split discards platform-specific evidence such as the exact React element, author association, active-video identity, hydration state, and same-node verification witness.

Three concurrent changes are already restoring observed behavior:

- `restore-native-facebook-reels-interaction-parity`;
- `restore-native-facebook-group-join-parity`;
- `restore-native-facebook-feed-like-parity`.

They overlap the same Rust engine, Facebook adapter, browser router, facade, and focused tests. Development may remain isolated, but integration must be serialized. This change begins only after those behavior changes have committed and landed, and treats their specifications and retired TypeScript executors as behavior oracles rather than reimplementing them from memory.

## Goals / Non-Goals

**Goals:**

- Preserve every behavior landed by the three parity changes while integrating them once.
- Make one capability module own each supported Facebook command from target resolution through terminal classification.
- Keep action-specific actuation explicit: DOM activation, trusted pointer input, keyboard/text input, and file input are selected by the capability that has real-page evidence.
- Give each command one absolute deadline whose phase budgets fit inside it.
- Preserve the established coordinator-visible irreversible commit windows for Facebook Group Join, Comment, and Publish.
- Separate stable shared Facebook semantics from Feed, Reels, Group Join, Comment, and Publish workflows.
- Split browser-side router source by capability while producing the same single encoded Native artifact.
- Add executable ownership and behavior-oracle gates so a later migration cannot silently route a supported command through a generic fallback.

**Non-Goals:**

- No change to the Native process topology, Cloud protocol, Cloud planning, risk policy, pacing, quotas, or account lifecycle. The only protocol addition is a correlated local lifecycle handshake between the supervised Native child and its Edge host.
- No JavaScript page-execution fallback outside the Native artifact.
- No new retry, compatibility, feature-flag, or timeout configuration.
- No claim that source tests prove real Facebook write acceptance.
- No installer packaging, signing, OL deployment, database work, or unrelated platform refactor.

## Decisions

### 1. Integrate behavior first, refactor second

The three parity branches land serially in this order:

1. Reels Like/Follow, because it already contains the broadest shared locator and receipt changes.
2. Group Join, rebased onto the Reels result, because it overlaps router, Rust orchestration, facade deadlines, and session tests.
3. Feed Like, rebased last, because it must preserve the Reels-specialized path while replacing only non-Reels Like choreography.

Each branch reruns its focused tests after conflict resolution. This change then branches from the resulting default branch and performs module extraction without changing behavior. Mixing the refactor into any concurrent parity branch was rejected because it would obscure semantic conflicts and make the original fixes impossible to review independently.

### 2. Keep one process but move Facebook execution behind a platform runtime

The shared engine retains:

- session open/close and platform binding;
- command identity, duplicate handling, cancellation, and effect-phase storage;
- CDP connection/reconnection and transport;
- platform dispatch and typed result forwarding.

A Facebook runtime owns:

- Facebook session state;
- the Facebook command support table;
- blocker/consent gates;
- command-specific execution;
- Facebook terminal reason construction.

The generic engine calls one Facebook runtime entrypoint. It does not branch on individual Facebook commands and does not choose a Facebook actuation primitive.

A separate Facebook executable was rejected because it would duplicate the supervisor, protocol, manifest, signing, and crash lifecycle without improving behavioral ownership.

### 3. Partition Facebook by stable capabilities

The Rust adapter is organized around capability state machines rather than protocol shape:

- `session`: Facebook list-surface state, seen identities, document generation, refresh state, blocker and consent admission;
- `feed`: startup, settling, continuation, scrolling, refresh, open/back/search, and card projection;
- `feed_like`: exact Feed target, React primary commit, scoped picker commit, same-card verification, and Like receipts;
- `reels`: active-video projection, movement, cards, Like, Follow, author association, and same-Reel verification;
- `group_join`: current-group scope, readiness, hydration, protected fresh DOM commit, durable verification, and Join receipts;
- `comment`: exact editor, text input/readback, protected submit, same-account acknowledgement, pending/rejected/ambiguous classification;
- `publish`: composer entry, media, field readback, protected submit, capture, and reconciliation;
- `router`: encoded browser-router assembly, bounded DTO decoding, and shared canonical Facebook semantics.

Small modules may share canonical post identity, locale label families, geometry, and bounded evidence types through explicit shared helpers. The Native facade imports canonical post-id normalization only from the DOM-free `post-identity-core` module established by the concurrent identity-boundary change; retired browser-injection helpers remain behavior oracles and cannot become production-facade dependencies. Capability modules must not share a generic "find point and click" Facebook write pipeline.

Splitting only by command enum or by read/write was rejected because Feed and Reels use different target witnesses and actuation despite sharing command names.

### 4. Treat locate, commit, and verify as one capability-owned transaction

Every state-changing capability follows:

`admit → locate → fresh revalidate → commit once → verify the same target → classify`.

The pre-commit result carries the capability's full witness, not merely coordinates. Depending on the capability this includes canonical post identity, active video identity, author association, operation marker, current group scope, composer generation, and positive/negative state evidence.

The capability selects the proven commit primitive:

- Feed/Reel primary Like and Group Join may use fresh in-page DOM activation where real-page evidence requires the React-owned element;
- a unique scoped reaction-picker item and author-bound Reel Follow may use trusted pointer input where that behavior is established;
- Comment/Publish text and submit keep their established input and acknowledgement requirements;
- file upload remains a CDP file-input operation.

Native ownership is an execution and packaging boundary, not a requirement to express every write as coordinates. A global pointer-first policy was rejected because it contradicts recorded Facebook behavior.

### 5. Use one absolute deadline and capability-owned phase budgets

The TypeScript facade chooses a fixed deadline from a closed command table. Ordinary commands retain 30 seconds; Group Join receives 90 seconds because its established 30-second readiness, 2-second hydration, 1.5-second immediate settle, and 45-second durable verification sequence cannot fit in 30 seconds.

The Native session ceiling permits the longest supported Facebook command, but every Rust operation receives the caller's absolute deadline and computes phase time from remaining budget. Capability code must not create stacked local deadlines whose sum can exceed the command deadline.

Configurable knobs were rejected because the budgets come from observed behavior and adding configuration would hide ownership rather than solve it.

### 6. Correlate irreversible commit windows across the Native boundary

The retired Facebook executors opened the existing Edge `CommitWindowGuard` immediately before the irreversible Join, Comment, or Publish submit and closed it after confirmation or the bounded protection interval. The Native cutover removed the executor object that owned this guard, so the coordinator currently sees these writes as preemptible even after Native has crossed the commit boundary.

The supervised local protocol adds a correlated commit-window handshake:

1. the owning Facebook capability reaches its last pre-commit cancellation point;
2. Native emits a bounded `commit_window_request` containing only session/command correlation, a closed label, and the established budget;
3. the Edge host validates that the request belongs to the active command, opens the existing `CommitWindowGuard`, and returns `commit_window_ack`;
4. only after the matching acknowledgement does the capability run its fresh target revalidation and single commit;
5. the host disposes the guard when the command terminates, the Native process exits, or the declared budget expires automatically.

The established budgets remain capability-owned constants: Join `18_500ms`, Comment `20_000ms`, and Publish `20_000ms`. The request is not a new authorization or a success receipt. Missing, mismatched, duplicate, late, or timed-out acknowledgement fails before the write with `not_started`; it never causes a fallback click. A coordinator challenger arriving after acknowledgement receives the existing `window_busy` result with the guard's remaining budget. Once the protected interval expires, cancellation may stop only the verification tail and the write remains ambiguous rather than replayable.

An unacknowledged fire-and-forget progress event was rejected because Native could click before the host had opened the guard. Opening a 90-second window around the entire Join command was rejected because readiness is safely preemptible and would unnecessarily block higher-priority work.

### 7. Assemble one encoded router from capability-owned sources

Browser-side Facebook sources are split into an explicitly ordered internal source set:

- bounded shared DOM/identity/visibility helpers;
- session/feed probes;
- Feed Like;
- Reels;
- Group Join;
- Comment;
- Publish;
- one command dispatcher.

The Native build script assembles and encodes those sources into the existing binary input. Tests use the same assembly function or generated source order as the Rust build, so test and packaged routers cannot drift. Production `dist`, ASAR, and resources continue to reject every source fragment and representative marker.

Keeping one handwritten router file was rejected because unrelated capability edits currently collide and review cannot establish which behavior owns a helper. Shipping independent script files was rejected because it would weaken the Native packaging boundary.

### 8. Make capability ownership and parity executable

A closed Facebook support table maps every Native-supported command to exactly one capability owner. Unsupported Facebook commands still return `capability_unsupported` before router/CDP evaluation.

A behavior-parity ledger records for every supported command:

- retired behavior oracle and focused tests;
- canonical target witness;
- pre-commit gates;
- commit primitive and maximum dispatch count;
- verification witness;
- terminal reason/effect classes;
- total deadline.
- protected commit-window label and budget, when the capability has an irreversible submit boundary.

Tests fail when a supported command has no owner/ledger entry, when a command routes through a generic Facebook fallback, or when browser-router source exists outside the encoded assembly. Behavior tests assert externally meaningful outcomes and phase/reason semantics; string-shape tests alone are insufficient.

### 9. Keep delivery truth separate

Automated validation establishes source and artifact parity only. The result is not described as real-account verified until controlled DEV acceptance observes the named actions on an authorized account. The development Native artifact may be rebuilt after integration, but no installer or production release is implied.

## Risks / Trade-offs

- [Mechanical extraction changes visibility or borrow structure in Rust] → Move one capability at a time, keep focused tests green after each extraction, and avoid behavior edits in refactor commits.
- [Router assembly order creates hidden dependencies] → Use explicit dependency order, prohibit duplicate top-level symbols, and execute the same assembled source in tests and builds.
- [Concurrent parity branches keep changing shared files] → Do not edit their worktrees; wait for commits, integrate serially, then branch the refactor from the final default revision.
- [Legacy executors contain obsolete behavior] → Use only behavior backed by current specs, focused tests, or recorded real-page evidence; unsupported commands remain unsupported.
- [The host cannot acknowledge an irreversible commit window] → Fail before actuation; never click without coordinator protection and never treat a lifecycle request as a business result.
- [A source-equivalent write still fails on a live cohort] → Preserve honest non-success semantics and keep real-account acceptance open rather than adding an unobserved fallback.
- [Large refactor hides functional changes] → Separate behavior-integration commits from capability-extraction commits and review diffs with focused parity tests at every step.

## Migration Plan

1. Wait for the three behavior changes to commit in their isolated worktrees.
2. Rebase, validate, and land Reels, Group Join, and Feed Like serially to Edge `master` and control `main`, resolving shared files once per change.
3. Create the Edge worktree for this change from the integrated `master` revision and install physical dependencies.
4. Add ownership/ledger tests against the integrated behavior before moving code.
5. Restore the correlated local commit-window handshake, then extract the Facebook runtime and capability modules one at a time while running focused router/Rust/session tests after each move.
6. Split and assemble router sources, then verify production-dist and desktop build inputs still contain only the encoded Native artifact.
7. Run acceptance, full Edge tests, typecheck, Cargo fmt/clippy/tests, Native build/verification, and strict OpenSpec validation.
8. Rebase, fast-forward integrate, push default branches, and rebuild the local development Native artifact. Do not package an installer or claim real-account acceptance.

Rollback is a revert of the local lifecycle/refactor commits followed by rebuilding the prior Native artifact. The three parity behavior commits remain independently revertible and there is no data or Cloud protocol migration.

## Open Questions

None. Any additional Facebook layout behavior discovered during real-account acceptance is recorded as a separate observed failure and capability-specific change rather than a generic fallback.
