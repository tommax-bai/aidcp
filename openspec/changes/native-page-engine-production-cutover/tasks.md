## 1. Contract freeze and test harness

- [x] 1.1 Export the current Xiaohongshu browse, interaction, notification, profile, and publish command registry into a machine-readable migration manifest, including request, result, receipt, cancellation, and effect-semantics mappings.
  <!-- aidcp-edge 450cede: command-manifest.json plus registry/publish-kind parity tests; 3 manifest tests passed. No package or deployment. -->
- [x] 1.2 Add a Rust fixture harness that can replay selector-free command fixtures and compare normalized Native results with the frozen TypeScript contract expectations.
  <!-- aidcp-edge 450cede: selector-free JSON fixture replay includes search_result_ai, detail redaction, login precedence; cargo test --locked passed 23 tests. No live write validation. -->
- [x] 1.3 Define and test Native protocol v2 envelopes for engine/session lifecycle, task and command identity, deadlines, cancellation, effect phase, structured errors, and bounded diagnostics.
  <!-- aidcp-edge 450cede: protocol v2, long-lived client/session transport, capability digest, identity/deadline/effect validation; cargo clippy -D warnings, focused TS tests, and npm typecheck passed. Cancellation record is frozen; cooperative in-flight cancellation remains task 2.3. -->
- [x] 1.4 Add a deterministic fake HTTP/WebSocket CDP server covering target discovery, events, timeouts, disconnects, reconnects, and post-dispatch ambiguity.
  <!-- aidcp-edge 317cd47: fake CDP integration covers correlated execution, read reconnect, post-dispatch ambiguity/no replay, typed projections, and process cancellation; Rust suite passed 40 tests. No live write validation. -->

## 2. Native engine lifecycle and CDP ownership

- [x] 2.1 Replace the one-shot probe entry point with a long-lived supervised Native engine supporting health, session open/status/close, command execution, cancellation, and graceful shutdown.
  <!-- aidcp-edge 372936c: long-lived process/session, concurrent stdin while commands run, AbortSignal/cancel forwarding, graceful close/shutdown, and process-level cancellation test. cargo test/clippy and TS supervisor tests passed. -->
- [x] 2.2 Implement provider-neutral target discovery, attachment, required CDP domain enablement, event dispatch, bounded reconnect, and session restoration without replaying dispatched effects.
  <!-- aidcp-edge 317cd47: Native owns target refresh/domain setup and permits one read reconnect while dispatched writes become ambiguous; fake CDP tests passed. -->
- [x] 2.3 Enforce one active Xiaohongshu writer per browser session, task/command ownership, deadlines, cancellation safe points, and non-interruptible atomic regions.
  <!-- aidcp-edge 317cd47: runtime/session ownership, single active command, task switching, cancellation, deadlines, write dedupe, and no-replay behavior are enforced and tested. -->
- [x] 2.4 Enforce a CDP method allowlist and bounded/redacted Native diagnostics that exclude cookies, credentials, upload content, and unnecessary DOM text.
  <!-- aidcp-edge 317cd47: explicit CDP allowlist plus deny-unknown bounded command/result models reject generic and sensitive surfaces; Rust and protocol tests passed. -->

## 3. Native page model and interaction primitives

- [x] 3.1 Port page-state classification and URL compatibility for home, explore, `search_result_ai`, note detail, profile, notification, publish, login, error, and unknown states.
  <!-- aidcp-edge 372936c: encoded Native probe and typed projections cover every listed state; fixture/unit tests include search_result_ai compatibility, query redaction, login precedence, notification, creator publish, error, and unknown behavior. -->
- [ ] 3.2 Port DOM-first locating with visibility, geometry, ambiguity rejection, bounded retry/escalation, post-action validation, and cache promotion only after repeated success.
  <!-- 承接边界登记（2026-07-30，由 restore-native-actuation-humanization-and-locating 的 5.8 回写；本条仍不勾） -->
  - **本条只被部分承接，勿整条勾掉。** `restore-native-actuation-humanization-and-locating` 只承接**三道闸**
    （后置校验 / 有界重试与升级 / 反污染回写），已于 `aidcp-edge 4a2c8d4` 建 `native/page-engine/src/locating.rs`、
    `55c9d2e` 接进第一条真实命令（Facebook 点赞在 Reels 面、`note_id` 非 `/reel/` 地址那条分支）。
  - **仍未承接、仍属本 change**：可见性 / 几何 / 歧义拒绝归各平台的目标解析能力；匹配唯一性闸、守卫层、
    模型兜底、语义 class 白名单、可换接口均不在那条 change 内（见其 5.8 与 oracle.md 覆盖漏洞一节）。
  - **「cache promotion only after repeated success」这半条在生产上仍是空转**：晋升逻辑与阈值已实现，
    但每个定位器都是编译进二进制的固定选择器、无任何非确定性锚点来源，暂存区恒空。
    那条 change 的 7.16 正因此**待人裁定**，其 5.4 / 5.5 明令裁定前不得按已实现勾掉 —— 本条同理，
    **MUST NOT 因为「模块已存在」就把这半条读成已完成**。
- [ ] 3.3 Implement Native pointer, wheel, keyboard, text, and file-input primitives with current humanization bounds and cancellation-safe atomic actions.
  <!-- Partial 2026-07-27, aidcp-edge 745b754: shared text input now preserves per-Unicode-scalar pacing, cancellation, and deadlines; captcha text uses bounded real keyDown/keyUp pairs with Shift cleanup. The broader pointer/wheel/file primitive task remains open. -->
  <!-- Partial 2026-07-28, aidcp-edge 02313f1: Facebook Feed and comment lazy-load wheel input now preserves the existing 650 px +/-20% distance across 8-15 frames with 16-60 ms inter-frame delays, an interior acceleration/deceleration peak, exact total distance, and cancellation/deadline checks. Rust unit/fake-CDP/full suites, clippy -D warnings, Edge acceptance/full tests, and typecheck passed. Pointer and file-input coverage remain open; no package, deployment, or live-account validation was performed. -->
  <!-- 承接边界登记（2026-07-30，由 restore-native-actuation-humanization-and-locating 的 5.8 回写；本条仍不勾） -->
  - **文件输入（file-input）这一半不在那条 change 内**，勿因其拟人化原语落地就把本条整条勾掉：
    那条 change 承接的是指针 / 滚轮 / 键盘 / 文本四类原语的拟人化边界，**file-input 原语仍属本 change**。
- [x] 3.4 Define bounded structured models for feed cards, search results, note details, profiles, notifications, interaction receipts, and publish receipts.
  <!-- aidcp-edge 804aadc: deny-unknown Rust command/result types cover the complete frozen command manifest; card/note/profile/notification/action/publish projections apply explicit text/list/URL/ID bounds. cargo test and clippy -D warnings passed. Command behavior remains sections 4-6. -->
- [x] 3.5 Restore Native Facebook comment and Xiaohongshu search text entry to one humanized `Input.insertText` call per Unicode scalar, with pre-submit cancellation/deadline checks, exact readback, and cleanup before any failed commit.
  <!-- aidcp-edge 745b754: Facebook comment includes approved group-code suffix in its Cloud-equivalent length-aware ceiling, commit-window cleanup, and no Enter after pre-submit failure; Xiaohongshu search preserves pointer focus, a 700 ms submit floor, and Enter text '\r'. -->
- [x] 3.6 Replace Native captcha text `Input.insertText` with validated visible-ASCII real keyDown/keyUp pairs, real Shift wrapping, bounded dwell/RTT compensation, and best-effort key release after dispatch failure.
  <!-- aidcp-edge 745b754: captcha text is 1..24 visible ASCII, produces zero Input.insertText calls, and reports post-point/type failures no earlier than dispatched. -->
- [x] 3.7 Add fake-CDP event-sequence regressions for Native Facebook comment, Xiaohongshu search, and captcha text input.
  <!-- aidcp-edge 745b754: tests assert per-scalar input, zero captcha insertText, Shift/key release, deadline cleanup/no Enter, commit-window rejection cleanup/no Enter, and group-code-aware comment timing; full Rust 111/111 and focused TypeScript passed. -->
- [x] 3.8 Bind every Native text sequence to its exact target before clearing or typing: Facebook publish/comment require exact editor focus and editor-local selection, Xiaohongshu search requires the visible input instance plus active-target verification, and captcha text requires the frozen `editable` / `opaque` / `none` focus tiers. Fake CDP tests must reject writes to an unfocused target.
  <!-- aidcp-edge 5e66ef4: all four Native text paths now fail with zero character dispatch when focus cannot be proven; fake CDP models focus ownership instead of auto-appending every input event. Rust 115/115, Native focused TypeScript 136/136, Edge full 2435 pass / 1 skip, and production boundary checks passed. -->

## 4. Browse, search, note, profile, and notification commands

- [x] 4.1 Implement feed scan, `browse.next`, bounded scroll, page scroll, and feed refresh with honest exhaustion and movement evidence.
  <!-- aidcp-edge 317cd47: encoded Native router implements feed extraction/scroll/refresh with bounded movement and typed empty/exhausted outcomes; focused router tests and full Edge suite passed. -->
- [x] 4.2 Implement search input, keyword submission, search URL compatibility, filters, and `search_result_ai` result extraction.
  <!-- aidcp-edge 317cd47: Native search route applies keyword/sort/time filters and accepts both search URL forms; fixture and focused routing tests passed. -->
- [x] 4.3 Implement exact-target note open/close, note detail extraction, image browsing, comment scrolling, source restoration, and error-page recovery.
  <!-- aidcp-edge 317cd47: note routes bind note identity, preserve source navigation, and return bounded typed detail/traversal evidence; Rust/TS suites passed. -->
- [x] 4.4 Implement exact-target profile open and notification open/browse/back-home flows.
  <!-- aidcp-edge 317cd47: profile and notification routes use high-level commands with exact profile binding and page-kind postchecks; full Edge suite passed. -->
- [x] 4.5 Implement captcha-assistance capture/click page operations and allowlisted legacy plan steps while keeping authorization and envelope routing in Edge.
  <!-- aidcp-edge 317cd47: bounded screenshot ring, coordinate click, text entry/readback, and allowlisted plan execution are Native; authorization/Cloud envelopes remain Edge-owned. -->
- [ ] 4.6 Add deterministic Native contract tests for every command and page-state transition in this section.

## 5. Interaction commands and effect honesty

- [x] 5.1 Implement exact-target note like and collect with precondition checks, post-action state verification, and idempotent receipts.
  <!-- aidcp-edge 317cd47: Native action router binds current note, recognizes already-satisfied state, verifies changed state, and returns effect-phase receipts; focused tests passed. -->
- [x] 5.2 Implement exact-target follow from note/profile contexts with identity binding and post-action verification.
  <!-- aidcp-edge 317cd47: follow is bound to the requested author/profile and confirms terminal state before success; typed route and full Edge tests passed. -->
- [x] 5.3 Implement approved comment and comment-like commands with target binding, fill/readback/submit validation, and no implicit publish.
  <!-- aidcp-edge 317cd47: comment routes require exact note/comment binding, verify editor readback, and do not expose a generic submit surface; full Edge tests passed. -->
- [x] 5.4 Add crash, disconnect, timeout, cancellation, and duplicate-command tests proving `not_started`, `dispatched`, `confirmed`, and `ambiguous` are never upgraded to false success.
  <!-- aidcp-edge 317cd47: effect, fake-CDP, process-protocol, and TypeScript supervisor tests cover these boundaries; Rust 40, focused 33, and rebased full Edge 2235 tests passed. -->

## 6. Publish commands and safety invariants

- [x] 6.1 Implement publish-entry navigation, mode selection, field filling, topic/candidate insertion, and option setting with readback validation.
  <!-- aidcp-edge 317cd47: all retained atomic publish setup commands route to Native and require field/mode/options postchecks; router and manifest tests passed. -->
- [x] 6.2 Implement image upload and cover selection with explicit file validation, bounded diagnostics, and no file-content leakage over IPC.
  <!-- aidcp-edge 317cd47: Edge downloads bounded HTTPS images to temporary files; Native sets file inputs and selects only an already-confirmed upload index. No file content crosses IPC. -->
- [x] 6.3 Implement scheduled-publish controls with exact target-time evidence and explicit timezone handling.
  <!-- aidcp-edge 317cd47: schedule setup/readback and scheduled capture require exact target time; focused exact-evidence tests passed. -->
- [x] 6.4 Implement submit, post-id capture, scheduled capture, and reconciliation with `ambiguous` handling that forbids blind resubmission.
  <!-- aidcp-edge 317cd47: submit/capture/reconcile are atomic Native commands with independent evidence and no write replay after dispatch; Rust effect tests passed. -->
- [ ] 6.5 Port the existing publish safety and integrity fixtures into Native acceptance tests.
- [x] 6.6 Implement the legacy whole-publish transaction through the same Native primitives or retire its registration and callers under an explicit protocol-compatible migration; no JavaScript whole-publish path may remain packaged.
  <!-- aidcp-edge 317cd47: obsolete publish.request handler is unregistered; retained publish.command atoms route only to Native, with tombstone metadata preserved for protocol compatibility. -->

## 7. Edge direct production integration

- [x] 7.1 Add a selector-free TypeScript Native supervisor/facade that validates protocol v2, version compatibility, lifecycle, bounds, and child-process failures.
  <!-- aidcp-edge 450cede + 372936c: selector-free long-lived facade validates ready manifest/protocol, identities, bounded records/results, lifecycle, timeouts, exits, malformed output, stable errors, cancellation, and effect truth; focused TS tests and npm typecheck passed. Production routing remains tasks 7.2-7.5. -->
- [x] 7.2 Start Native only after task admission, provider resolution, account/environment binding, and browser startup; keep browser lifecycle and Cloud transport owned by Edge.
  <!-- aidcp-edge 317cd47: main starts the required Native runtime only inside the admitted Xiaohongshu browser lifecycle; Edge retains provider, lease, account, and WebSocket ownership. -->
- [x] 7.3 Route the full Xiaohongshu browse/search/note/profile/notification/interaction registry directly to Native with no shadow invocation and no JavaScript fallback.
  <!-- aidcp-edge 317cd47: command manifest parity and direct-routing tests prove every retained Xiaohongshu route is Native-only and the legacy browse executor is absent from main. -->
- [x] 7.4 Route the full Xiaohongshu publish registry directly to Native with no shadow invocation and no JavaScript fallback.
  <!-- aidcp-edge 317cd47: every retained publish.command kind maps to one typed Native command; publish.request is retired and no JavaScript fallback is registered. -->
- [x] 7.5 Map Native results, effect phases, cancellation, and failures to the existing Cloud protocol and task-coordinator receipts without changing Cloud contracts.
  <!-- aidcp-edge 317cd47: Native browse/publish facades emit the existing page/action/publish receipts and preserve correlation, cancellation, and effect truth; acceptance 29/29 passed. -->
- [x] 7.6 Add integration tests proving Native failure is scoped to the owning task/session and non-Xiaohongshu browser providers and flows remain isolated.
  <!-- aidcp-edge 317cd47: supervisor ownership/failure tests and direct-routing isolation checks passed; full Edge suite kept Facebook and other platform tests green. -->

## 8. Customer package removal and Native artifact delivery

- [x] 8.1 Split any genuinely shared selector-free DTOs/utilities away from legacy Xiaohongshu page-rule modules so production Edge code has no runtime import path to them.
  <!-- aidcp-edge 317cd47: browse quiesce types moved to a selector-free module; Facebook no longer imports the legacy Xiaohongshu browse implementation. -->
- [x] 8.2 Remove the legacy Xiaohongshu page-understanding/action modules from production build inputs and add a build-time import-graph gate that fails on reintroduction.
  <!-- aidcp-edge 317cd47: build:dist keeps only the static main graph and fails on forbidden legacy modules/markers; production check reported reachable=109, removed=31. -->
- [x] 8.3 Build and stage architecture-matched Native artifacts with a manifest containing protocol version, platform, architecture, and artifact hash.
  <!-- aidcp-edge 228e3e9 + 317cd47 + 87cd1ab: locked host build stages outside ASAR with engine/protocol/adapter versions, capability digest, platform, arch, executable, and SHA-256; darwin-arm64 worktree b919422... and canonical recovery 952ce40... artifacts verified locally. No installer was built. -->
- [x] 8.4 Package Native outside ASAR, resolve it from `process.resourcesPath`, and add installed-artifact startup/health/command/shutdown smoke tests.
  <!-- aidcp-edge d7e178f + 317cd47 + 87cd1ab: extraResources, startup checks, afterPack smoke, and Electron dev/OL verify-or-rebuild bootstrap are wired and contract-tested; rustup resolves the crate-pinned toolchain when Cargo is absent from PATH. Final installer execution remains release gate 9.3. -->
- [ ] 8.5 Extend CI packaging and nested signing/notarization to the Native artifact for supported macOS architectures and Windows x64; fail packaging when a required artifact is missing or incompatible.
- [x] 8.6 Add final ASAR/resources leakage scans for legacy module paths, representative selectors/rules, source maps, debug fixtures, and unredacted diagnostics.
  <!-- aidcp-edge 317cd47: final ASAR scanner accepts a clean Native facade fixture and rejects legacy paths/markers/maps; production dist reports legacy_xhs=absent and source_maps=absent. -->

## 9. Validation, evidence, and release gate

- [ ] 9.1 Run Rust formatting, unit/integration/acceptance tests, clippy, and release builds for every locally supported target; record unsupported cross-target checks truthfully.
- [x] 9.2 Run physical Edge dependency installation, focused tests, required safety acceptance suites, full tests, typecheck, and production build.
  <!-- aidcp-edge 317cd47: physical npm tree; focused 33/33, acceptance 29/29, rebased full 2235/2235, typecheck, build:dist, Rust 40/40, rustfmt, and clippy -D warnings passed. No live or packaged-app validation. -->
- [ ] 9.3 Run package-input graph checks, packaged smoke tests, signature verification, and leakage scans for locally produced artifacts; record Windows and alternate-architecture CI evidence separately.
- [ ] 9.4 Run the authorized read-only live Xiaohongshu matrix across home/explore/search/note/profile/notification/error/login-observable states and record exact post-conditions.
- [ ] 9.5 Run live write/action validation only under separate target-specific authorization, covering interaction and publish ambiguity without broadening the authorized action scope.
- [x] 9.6 Update this checklist with repository commits, validation evidence, deviations, and package availability; run `openspec validate native-page-engine-production-cutover --strict`.
  <!-- aidcp control + aidcp-edge 317cd47: checklist records completed source gates and explicitly leaves cache/humanization completeness, all-command fixtures, cross-target package/signature, live read/write, and installer release unchecked. Strict validation passed. -->
- [x] 9.7 Integrate and push the clean control and Edge changes under the repository workflow. Build or publish a customer installer only after separate explicit release authorization.
  <!-- aidcp-edge master 317cd47 pushed after fast-forward; this control evidence commit is the final fast-forward input for main. No customer installer was built or published. -->
