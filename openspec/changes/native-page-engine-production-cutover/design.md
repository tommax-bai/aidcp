## Context

The current Edge core is browser-independent until a `page_automation` operation passes browser-slot admission, starts a provider, attaches CDP, verifies page identity, and acquires the page-task lease. After that boundary, Xiaohongshu execution is distributed across roughly 11,000 lines of TypeScript in `src/browse` and the Xiaohongshu publish handlers. Ordinary Electron packaging compiles all of those modules into `dist/**/*` inside readable ASAR.

The completed `native-page-engine-spike` added a Rust 2024 sidecar with loopback-only target discovery, a versioned high-level IPC, direct CDP WebSocket support, content-free page classification, deterministic tests, and an opt-in host build. Live validation proved the binary can attach to the real dynamic AdsPower endpoint and identify search, explore, note-detail, profile, and unknown Xiaohongshu states. The spike intentionally cannot write, does not run in production, is unsigned, and is not packaged.

The product decision for this change is to skip shadow execution. There will be no production period in which both JavaScript and Native evaluate the same command and no customer-build fallback to JavaScript. Development remains isolated and fully tested; cutover occurs atomically at package construction after all required command families pass their gates.

Stable boundaries remain unchanged:

- Cloud owns planning, content decisions, risk state, approval, scheduling, persistence, and final business truth.
- The Edge TypeScript core owns customer/core lifecycle, provider startup/stop, operation classification, account binding and identity admission, page-task leases, protocol v2, and mapping Native results to existing receipts.
- The Native Page Engine owns Xiaohongshu target selection, CDP attachment after admission, page rules, locating, input actuation, bounded retry, post-action verification, and page-session recovery.
- Browser-provider implementations still return a loopback DevTools handle. They do not gain Xiaohongshu-specific behavior.
- Non-Xiaohongshu executors are unchanged.

## Goals / Non-Goals

**Goals:**

- Make the Rust binary the only production Xiaohongshu page executor in supported desktop packages.
- Cover the complete currently registered Xiaohongshu page-command surface: browse/search/navigation/read, note and profile traversal, notifications, interactions, captcha assistance, bounded legacy plan steps, the legacy whole-publish command, and atomic publish steps.
- Preserve existing Cloud protocol payloads and honest outcome semantics while moving all selectors, page scripts, CDP writes, retries, and verification into Native.
- Supervise a long-lived Native session with explicit protocol/version negotiation, correlation, deadlines, cancellation, crash handling, and no ambiguous-write replay.
- Remove migrated Xiaohongshu page rules and action modules from distributable JavaScript and prove that removal by inspecting the final package.
- Produce architecture-correct, integrity-verified, nested-signed Native artifacts for every supported official desktop target.
- Keep rollback recoverable through an installer/package rollback without embedding a runtime JavaScript fallback.

**Non-Goals:**

- Moving Cloud planning, risk, approval, account scheduling, customer authentication, or protocol v2 orchestration into Rust.
- Rewriting the Electron renderer, AdsPower browser-provider lifecycle, Facebook, Douyin, WeChat Channels, or other platform executors.
- Claiming that Native code is impossible to reverse engineer or observe dynamically.
- Allowing arbitrary JavaScript, selectors, raw CDP methods, credentials, prompts, or Cloud envelopes across Native IPC.
- Releasing or deploying an installer before source, package, signing, and authorized real-machine acceptance gates pass.
- Disabling Electron `RunAsNode`; the existing Edge core and bundled AdsPower CLI still require that launch mechanism in this change.

## Decisions

### D1. Cut over atomically in the distributable, without shadow or fallback

Source migration may proceed command family by command family in an isolated worktree, but the official package gate is atomic. A Xiaohongshu-capable package includes a compatible Native binary and routes every registered Xiaohongshu page command to it. If the binary, manifest, architecture, signature, or protocol is invalid, Xiaohongshu page automation is unavailable with an explicit startup/admission failure. The core MUST NOT import or invoke the legacy executor.

The alternatives were a shadow reader and a runtime feature flag. Shadow was rejected by product decision. A fallback flag was rejected because it retains the readable core in the customer artifact, creates two behavioral truths, and can turn a Native failure into an unreviewed JavaScript write.

### D2. Keep a standalone long-lived sidecar supervised by the Edge core

The spike's process boundary remains. The Edge core starts one Native Page Engine per admitted Xiaohongshu browser executor, passes the loopback endpoint and a new session identity, negotiates protocol/engine versions, and closes it when the executor is released. The Native process owns its CDP WebSocket and target refresh/reconnect for the lifetime of that session.

A `.node` addon was rejected because Electron/Node ABI coupling, in-process crashes, and packaging complexity provide no benefit to the security boundary. A one-process-per-command model was rejected because it discards CDP/session state, increases latency, and cannot model reconnect or cancellation honestly.

### D3. Use a high-level command protocol, not a generic browser RPC

IPC remains newline-delimited JSON with bounded records, stdout reserved for protocol records, and stderr for bounded diagnostics. Production protocol v2 introduces:

- `session_open`, `session_status`, and `session_close` lifecycle messages;
- one correlated command message carrying `commandId`, `taskId`, deadline, command kind, and typed business parameters;
- progress records only at named safe phases where the Edge supervisor needs observability;
- exactly one terminal result for every accepted command;
- an explicit cancellation request correlated to the active task and command;
- an engine manifest record containing protocol, engine, platform-adapter, and artifact versions.

Command kinds mirror the existing Xiaohongshu execution surface rather than CDP methods: page/feed refresh and scroll, search, note open/close/read/browse, navigation back, profile and notification traversal, like/collect/follow/comment/comment-like, captcha capture/click, allowlisted legacy plan actions, the legacy whole-publish transaction, and each existing atomic publish step. IPC never accepts selector text, evaluated source, WebSocket URLs, raw CDP method names, free-form plan goals, or arbitrary command payloads. For legacy `plan.response`, Edge sends only allowlisted `actionId`/operation/value tuples after validation; descriptive goals remain outside Native and cannot select arbitrary elements.

### D4. Represent write outcomes as effect phases

Every Native command result carries one of four effect phases:

- `not_started`: no platform write was dispatched; bounded retry by the existing owner may be allowed by the command contract;
- `dispatched`: the platform write may have happened but post-check has not confirmed it;
- `confirmed`: the command-specific independent post-condition proves success;
- `ambiguous`: dispatch occurred and final truth cannot be established.

The Edge mapper may emit existing success receipts only for `confirmed`. It maps `not_started` to the existing honest failure/retry semantics, and maps `dispatched`/`ambiguous` to the existing unknown/needs-review contract where available. It MUST NOT replay a `dispatched` or `ambiguous` write, and MUST NOT invoke JavaScript as a fallback.

This makes process crash, CDP disconnect, cancellation, and timeout behavior explicit instead of inferring safety from whether a function returned.

### D5. Preserve the single-writer task lease across the process boundary

The existing Edge task coordinator remains the admission authority. It opens a Native session only after provider startup, CDP readiness, real page identity verification, and task admission. Every Native command includes the current `taskId` and a monotonically increasing per-session `commandId`. Native accepts at most one page-writing command at a time, rejects stale task identities, and queues nothing beyond the single active command.

Cancellation is cooperative at declared safe points. A mouse/key press pair, file chooser assignment, and platform submit dispatch are atomic regions. Cancellation after dispatch waits for the command's bounded post-check and returns `confirmed` or `ambiguous`; it never reports `not_started` merely because the caller cancelled.

### D6. Native owns the entire downstream Xiaohongshu CDP lifecycle

The provider-neutral Edge handle supplies only loopback host/port and lifecycle ownership. Native fetches `/json`, selects the allowed Xiaohongshu target, opens the page WebSocket, enables required domains, applies page-session configuration, refreshes targets after navigation, and performs bounded reconnect after unexpected CDP loss.

Reconnect re-establishes domains and page state but never replays the interrupted command. If the disconnect happened before a write's dispatch phase, the result can be `not_started`; after dispatch it is `ambiguous` unless the reconnected page provides command-specific proof. Provider differences do not enter the Native platform adapter.

### D7. Port behavior by command contract and keep rules in Rust modules

The Rust crate is divided into platform/session infrastructure and Xiaohongshu command families:

- target/session/CDP transport and correlated deadlines;
- semantic page model and page-state transitions;
- locating primitives with visibility, geometry, ambiguity, and post-validation gates;
- humanized pointer, wheel, key, and timing primitives;
- browse/search/note/profile/notification adapters;
- interaction adapters;
- publish adapters and file-input handling;
- typed result projection with content bounds and redaction.

Selectors and evaluated page scripts are compile-time encoded in the Native artifact and absent from IPC. Encoding raises static extraction cost but is not treated as a cryptographic guarantee. Tests exercise decoded rules inside Rust and final-binary scans reject representative cleartext markers.

### D8. Preserve existing external behavior and Cloud protocol

The TypeScript facade converts existing protocol-v2 envelopes into Native typed commands and maps Native terminal results back into the same `page.cards`, `note.detail`, `action.completed`, publish command result, and recovery behaviors. Cloud sees no new message type or payload requirement in this cutover.

Existing contracts remain authoritative, including exact-target action attribution, human approval, risk gating, command-comment identity recheck, search-result keyword verification, source-list return, publish submit integrity, scheduled-publish semantics, and honest no-target/ambiguous results. Native implementation tests are derived from those baseline scenarios; migration does not relax them.

Captcha-assistance authorization, coordinate mapping, fresh screenshot semantics, and click-result truth also remain authoritative. Edge keeps authorization and external envelope routing, while Native owns the page screenshot/input CDP operations. `edge.task.acquire`/`edge.task.release`, `session.end`, and pacing updates remain Edge coordination inputs; Edge reflects their resulting task/session/config state through the typed Native lifecycle protocol without retaining a Xiaohongshu CDP executor.

### D9. Remove legacy Xiaohongshu core from customer JavaScript

The production TypeScript entrypoint imports only the Native facade for Xiaohongshu. Electron build inputs explicitly exclude migrated Xiaohongshu browse and publish rule modules after dependency inspection proves nothing in the packaged graph requires them. A package scanner inspects `app.asar` and source maps for:

- forbidden legacy module paths;
- representative selectors, page-script fragments, and raw CDP action sequences;
- source maps or embedded TypeScript sources for the migrated core;
- a manifest mismatch between the facade and Native protocol.

The source repository may retain historical modules during implementation and test migration, but an official package cannot contain them. The final source cleanup deletes modules that have no non-Xiaohongshu consumers.

### D10. Couple Native and Edge versions in one signed installer

The Native artifact is built with Cargo `--locked` for each official platform/architecture and staged under a deterministic `build/native-page-engine/<platform>-<arch>/` path with a manifest and SHA-256. Electron `extraResources` includes exactly the matching artifact. Startup verifies manifest, hash, executable architecture, and protocol compatibility before page admission.

macOS CI signs the inner executable with the same Developer ID before signing/notarizing the app and verifies both signatures plus Gatekeeper after packaging. Windows CI builds the matching Rust target and includes it in the NSIS input before Authenticode packaging is considered distributable. Unsupported or missing targets fail the build; packages never download executable code at runtime.

### D11. Roll back by installer, not runtime downgrade

Release rollout uses a new desktop version. Rollback republishes/reinstalls the last known-good signed installer and reverts the source commits. There is no environment variable, remote flag, or hidden local setting that activates legacy Xiaohongshu JavaScript in the new package.

## Risks / Trade-offs

- [Direct cutover can expose missed page variants immediately] → Require fixture replay for every command, complete Edge acceptance/full tests, package inspection, and authorized real-machine end-to-end acceptance before any installer is published.
- [The migration is much larger than the spike] → Implement by command family in the worktree while keeping the release gate atomic; never label a partial family as production-ready.
- [Native can still be dynamically observed] → Treat the goal as raising copying cost, keep high-level IPC narrow, encode rule strings, sign artifacts, and avoid claiming irreversibility.
- [A Native crash can strand an action after dispatch] → Persist effect phase in the terminal result path, map post-dispatch uncertainty to `ambiguous`, and prohibit automatic replay/fallback.
- [Long-lived Native and Edge state can drift] → Bind every record to session/task/command identities, negotiate versions, expose bounded status, and fail closed on stale or malformed records.
- [Removing JavaScript modules can break non-XHS shared consumers] → Inventory imports and split genuinely shared DTO/timing utilities into selector-free modules before exclusion; package graph tests enforce the boundary.
- [Cross-platform native builds/signing increase CI cost] → Pin Rust/dependencies, cache Cargo per target, keep ordinary TypeScript builds independent, and run release-native jobs only for official desktop builds.
- [Native file input or publish code mishandles local paths] → Keep file authorization and approval in Edge, pass only already-authorized absolute paths, validate scope/size/type again in Native, and preserve existing publish post-checks.
- [Page identity changes after admission] → Recheck the current target origin/account evidence at command boundaries required by existing contracts; fail without dispatch on mismatch.

## Migration Plan

1. Freeze and enumerate the current Xiaohongshu command/receipt contracts and create fixture cases from existing TypeScript tests and live evidence.
2. Extend the Native protocol, session supervisor, CDP transport, effect phases, cancellation, and deterministic fake-CDP test harness.
3. Port read/navigation command families, then interactions, then publish steps into isolated Rust modules. Each family must pass its contract fixtures before the next family starts.
4. Add the TypeScript Native facade and direct Xiaohongshu routing in the feature worktree. Do not add shadow comparison or JavaScript fallback.
5. Remove production imports of the legacy executor, exclude/delete migrated modules from package inputs, and add final-ASAR leakage/graph tests.
6. Add macOS arm64/x64 and Windows x64 Native build/staging, manifest verification, nested signing, packaged smoke, and CI gates.
7. Run Rust format/test/clippy, focused Edge tests, acceptance, full tests, typecheck, ordinary build, per-target native builds, and package inspection.
8. On an authorized disposable Xiaohongshu environment, execute the complete read and write acceptance matrix with explicit gates for real likes/comments/follows/publish. No real write runs without the user's specific authorization at that point.
9. Integrate source only after all non-live gates pass. Build/release/deploy an installer only after live-write acceptance and a separate explicit release instruction.
10. Rollback is source revert plus reinstalling the previous signed package; no runtime fallback exists.

## Open Questions

- The current official Windows packaging path is not yet self-contained in CI. This change treats a Windows package as non-distributable until the existing AdsPower runtime and the new Native artifact are both staged and signed; macOS completion does not permit falsely claiming Windows readiness.
- Real write acceptance needs target-specific authorization for like, collect, follow, comment, immediate publish, and scheduled publish. Until granted, those paths can reach deterministic and packaged smoke completion but cannot be marked live-platform confirmed.
