## 1. Split admission and frozen baseline

- [ ] 1.1 Inventory every active change that touches Edge main-process ownership, AdsPower runtime, proxy secrets, cross-process risk, auto-update or installer distribution; block `split-base` until each hotspot change is completed/integrated or has an explicit non-overlap owner and sequence.
- [ ] 1.2 Run `scripts/task-preflight` after the hotspot gate closes, confirm canonical branches/worktrees are eligible, and record the exact `aidcp`, `aidcp-edge`, `aidcp-cloud`, `aidcp-automation` and `aidcp-console` commits used as the split baseline.
- [ ] 1.3 Create and push an immutable `split-base` tag on the approved `aidcp-edge` commit after confirming the working tree and release ancestry are clean.
- [ ] 1.4 Inventory every Electron IPC, renderer import, child-process spawn, Core environment variable, credential path, stdout parser, filesystem path, Native asset, AdsPower asset and packaging rule; assign each item exactly once to Classic or Host.
- [ ] 1.5 Capture the pre-split parity matrix with focused/full tests, typecheck, development launch and the latest actually verified macOS/Windows installer evidence, including login-without-engine, start/resume browser preparation, pause/close release, human assist, AdsPower daemon reuse and quit behavior.
- [ ] 1.6 Confirm repository administration for the recommended `aidcp-edge` → `aidcp-edge-host` rename and approve the private npm registry, immutable-version policy and read-only Classic install credentials before any formal Host publication.

## 2. Independent repository foundations

- [ ] 2.1 Rename/migrate the existing `aidcp-edge` remote to `aidcp-edge-host` while preserving full Git history, issues/releases and `master`, then verify existing clones receive the intended hosting redirect.
- [ ] 2.2 Create `aidcp-classic-client` from the same `split-base`, retain relevant Classic file history, set `master` as its canonical branch and verify it is independently cloneable without the Host source checkout.
- [ ] 2.3 Add repository-local AGENTS, ownership, branch protection, dependency install, focused/full test, typecheck and secret-free CI rules to both repositories.
- [ ] 2.4 Update `aidcp` sibling inventory, `task-preflight`, worktree/new-change/spawn/land helpers and development documentation to recognize `aidcp-classic-client` and `aidcp-edge-host` as independent sibling repos.
- [ ] 2.5 Update protocol and architecture references so Cloud↔Edge v2 synchronization names `aidcp-automation` and `aidcp-edge-host`, while Classic is explicitly excluded from protocol command routing ownership.
- [ ] 2.6 Validate control repo changes with `openspec validate split-classic-client-edge-host --strict` and helper dry-runs against physical, non-symlinked dependency installs in both new repositories.

## 3. Edge Host public contract and ownership

- [ ] 3.1 Define and export Host creation options, non-authoritative `LocalEnvironmentDescriptor`, lifecycle results, snapshots, events, named errors, correlated human-assist bridge and shutdown contract from `@aidcp/edge-host`.
- [ ] 3.2 Move the multi-environment supervisor, Core entry, platform drivers, Cloud automation command routing, Native Page Engine and AdsPower runtime ownership into `aidcp-edge-host`.
- [ ] 3.3 Replace consumer-visible stdout parsing with versioned structured Host events carrying `clientInstanceId`, `envId` and generation; retain stdout/stderr only as bounded diagnostics and prove Host events cannot establish Cloud durable run/result truth.
- [ ] 3.4 Implement Core-originated `human_assist_required` with request/env/generation correlation, Classic present/complete callbacks and mandatory Core page-identity revalidation before continuation.
- [ ] 3.5 Implement explicit adapters for machine data root, client-instance data root, packaged Resources root, Cloud target, credential provider, structured logger and notification/human-assist handling without importing Classic product modules.
- [ ] 3.6 Implement MachineRuntimeCoordinator with cross-process `runtime-init`, runtime/protocol compatibility, global AdsPower Local API rate gate and non-secret owner diagnostics; fail incompatible live runtime as `ads_runtime_version_conflict` without replacement.
- [ ] 3.7 Implement the physical-profile lease keyed by immutable provider identity, including honest `environment_in_use`, ownership-safe close/shutdown and crash recovery that cannot use timeout-only takeover.
- [ ] 3.8 Preserve lifecycle parity: roster reconcile starts nothing, start/resume prepares the current engine/browser path, and pause/close releases resources according to the current accepted contract.
- [ ] 3.9 Enforce Cloud authority and the Host public-surface denylist so renderer/local descriptors cannot assert account/permission/executionTarget and clients cannot call generic or direct platform actions.
- [ ] 3.10 Add Host contract, lifecycle, human-assist, event-truth, credential-redaction, resource-path, runtime-init/rate/version, profile contention/crash and ownership-safe shutdown tests; then run focused tests, required full safety suites and `npm run typecheck`.

## 4. Host package and immutable release unit

- [ ] 4.1 Make `npm pack` produce compiled Host JavaScript, `.d.ts`, Core entry and declared runtime inputs without TypeScript runtime or source-checkout dependencies.
- [ ] 4.2 Generate `edge-host-manifest.json` with Host version, Git SHA, Host API major, protocol version, runtime format, Electron major, Node modules ABI, AdsPower runtime/protocol versions, supported platform/architecture list and SHA-256 for every staged asset.
- [ ] 4.3 Add build and startup verification for package/manifest/ABI/runtime/platform/hash mismatch with terminal `edge_host_artifact_mismatch` and no stale-resource or network-source fallback.
- [ ] 4.4 Add package validation that fails on Classic renderer/window/navigation imports, undeclared spawnable/native resources, secret-bearing metadata or unsupported mutable dependencies.
- [ ] 4.5 Enforce that installed Host/Core/Native/AdsPower template versions remain fixed by Classic installer and cannot self-update, select latest or replace runtime assets from the network.
- [ ] 4.6 Configure the approved private registry to reject version overwrite, publish a release candidate from a clean eligible Host commit and verify a fresh consumer can install the exact version read-only.

## 5. Classic Client extraction and integration

- [ ] 5.1 Move the Electron shell/renderer, customer login and customer-auth data access, environment product UI, secure local state, tray, notifications, update logic and desktop assembly config into `aidcp-classic-client`.
- [ ] 5.2 Add one Classic main-process adapter over the typed Host API and route renderer lifecycle IPC, snapshot subscriptions, correlated human assistance and application shutdown exclusively through that adapter.
- [ ] 5.3 Replace Classic child-process/stdout-derived state with envId/generation-aware Host snapshot projection and named user-visible errors that never convert accepted, stale or failed state into running/success.
- [ ] 5.4 Keep Host local engine/browser/resource facts separate from Cloud durable automation/approval/platform-result truth; use customer-auth API as authority and Host events only for local projection or bounded refetch.
- [ ] 5.5 Preserve customer login and ordinary customer data access when Host creation fails, all Core instances are closed or browser execution is unavailable; add regression tests for each state.
- [ ] 5.6 Preserve login/start/resume/pause/close behavior exactly and add regression tests proving roster reconcile starts no engine while start/resume follows the current browser preparation path.
- [ ] 5.7 Handle `human_assist_required` by request/env/generation, present the correct browser, report completion and wait for Core revalidation; ignore stale or cross-environment completion.
- [ ] 5.8 Remove duplicate Core, supervisor, platform driver, Native execution, AdsPower supervision and Cloud automation command implementations from Classic, and add a repository boundary test preventing their return.
- [ ] 5.9 Pin one exact `@aidcp/edge-host` version in Classic package metadata and lockfile, reject ranges/branches/symlinks/workspaces/self-update, and expose Classic/Host/ABI/runtime provenance in diagnostics.
- [ ] 5.10 Run Classic focused tests, lifecycle/event-truth/human-assist/failure acceptance, required full tests and `npm run typecheck` without an `aidcp-edge-host` source checkout beside it.

## 6. Desktop assembly and platform verification

- [ ] 6.1 Update Classic packaging to stage manifest-declared spawnable and native Host resources under deterministic `process.resourcesPath` directories while loading only ASAR-safe JavaScript from ASAR.
- [ ] 6.2 Inject the real packaged Resources root into Host, set Core child-process `cwd` to a real directory and add development/packaged tests covering an ASAR `app.getAppPath()`.
- [ ] 6.3 Ensure macOS hardened-runtime signing and notarization include every manifest-declared native asset, and fail the build on missing or unsigned resources.
- [ ] 6.4 Embed Classic version/commit, Host version/commit, Electron major, Node modules ABI, runtime format and Host manifest hash in every artifact, and verify they can be read from an installed application.
- [ ] 6.5 Build and smoke macOS arm64 and x64 `dmg` + `zip` on machines without a system Node toolchain, recording installer, ABI/runtime validation, launch, Host/Core and native-load evidence separately.
- [ ] 6.6 Build and smoke Windows x64 `nsis` on a machine without a system Node toolchain, recording installer, ABI/runtime validation, launch, Host/Core, tray and native-load evidence separately.

## 7. Cross-repository parity and DEV acceptance

- [ ] 7.1 Run Classic against a Host tarball built from the candidate Host commit and prove login-without-engine, single/multi-environment start, browser preparation, pause, resume, close, bounded failure, correlated human assist and application shutdown parity.
- [ ] 7.2 Prove two Host processes on a cold machine serialize runtime stage/start, adopt one compatible AdsPower daemon and share one globally paced Local API gate while using different profiles.
- [ ] 7.3 Prove an incompatible live AdsPower runtime fails as `ads_runtime_version_conflict` without stop/replacement, and one compatible Host exit leaves the other Host/daemon/profile untouched.
- [ ] 7.4 Prove two different physical environments can run under different Classic instances while the same AdsPower profile is rejected before Core/browser activity, including a dev-versus-ol collision case in a safe local test.
- [ ] 7.5 Prove renderer/local descriptors cannot override Cloud account ownership, authorization or execution target and that binding/page-identity conflicts remain named failures.
- [ ] 7.6 Prove pending Cloud work plus local Host `stopped` remains two truthful states: Classic does not auto-start, show running or fabricate success, and Host events do not replace the Cloud API result.
- [ ] 7.7 Run Cloud Automation↔Edge Host protocol-drift, unauthorized-publish, risk-honesty and relevant end-to-end safety suites; confirm Classic has no direct platform-action route.
- [ ] 7.8 On the explicitly selected DEV target, perform one bounded real-account acceptance covering login/binding, Host/Core connection, one read-only browser action and its truthful evidence; do not infer platform success from UI, handshake or Cloud acceptance.
- [ ] 7.9 Record repository, commit SHA, commands, pass/fail counts, package/ABI/runtime versions, installer identities, deployment target and every unverified boundary in concise completion comments in this `tasks.md`.

## 8. Release cutover, rollback and closeout

- [ ] 8.1 From clean eligible default checkouts, publish the verified Host version first and then build the exact Classic version that pins it; do not release from feature worktrees.
- [ ] 8.2 Keep the last verified signed monolith installer and its metadata recoverable, document the rollback trigger and rehearse restoring the download pointer without running old and new clients against the same physical environment.
- [ ] 8.3 Rehearse rollback when old/new installers embed different AdsPower runtime versions: stop owned environments first, never replace/kill a runtime with another live owner, and surface incompatibility rather than dual-run.
- [ ] 8.4 Switch the DEV download/update artifact source to `aidcp-classic-client` only after all package and DEV gates pass; verify download discovery, checksum, install, ABI/runtime manifest, launch and health without changing Console source version constants.
- [ ] 8.5 Observe the bounded DEV acceptance window, roll back to the last verified installer on any packaging/runtime gate failure, and record whether the new artifact or rollback was actually installed.
- [ ] 8.6 Remove obsolete canonical `aidcp-edge` path references and temporary migration notes after the Host rename and Classic cutover are proven, while retaining split-base and last-monolith release provenance.
- [ ] 8.7 Verify no `aidcp-agent-client`, AutomationDefinition/persona trigger, Host daemon, Cloud protocol change or Agent-specific Host API was added, run `openspec validate split-classic-client-edge-host --strict`, and archive only after every required task and truthful validation record is complete.
