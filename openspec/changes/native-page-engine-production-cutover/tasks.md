## 1. Contract freeze and test harness

- [x] 1.1 Export the current Xiaohongshu browse, interaction, notification, profile, and publish command registry into a machine-readable migration manifest, including request, result, receipt, cancellation, and effect-semantics mappings.
  <!-- aidcp-edge c5d08b7: command-manifest.json plus registry/publish-kind parity tests; 3 manifest tests passed. No package or deployment. -->
- [x] 1.2 Add a Rust fixture harness that can replay selector-free command fixtures and compare normalized Native results with the frozen TypeScript contract expectations.
  <!-- aidcp-edge c5d08b7: selector-free JSON fixture replay includes search_result_ai, detail redaction, login precedence; cargo test --locked passed 23 tests. No live write validation. -->
- [x] 1.3 Define and test Native protocol v2 envelopes for engine/session lifecycle, task and command identity, deadlines, cancellation, effect phase, structured errors, and bounded diagnostics.
  <!-- aidcp-edge c5d08b7: protocol v2, long-lived client/session transport, capability digest, identity/deadline/effect validation; cargo clippy -D warnings, focused TS tests, and npm typecheck passed. Cancellation record is frozen; cooperative in-flight cancellation remains task 2.3. -->
- [ ] 1.4 Add a deterministic fake HTTP/WebSocket CDP server covering target discovery, events, timeouts, disconnects, reconnects, and post-dispatch ambiguity.

## 2. Native engine lifecycle and CDP ownership

- [x] 2.1 Replace the one-shot probe entry point with a long-lived supervised Native engine supporting health, session open/status/close, command execution, cancellation, and graceful shutdown.
  <!-- aidcp-edge 80c9296: long-lived process/session, concurrent stdin while commands run, AbortSignal/cancel forwarding, graceful close/shutdown, and process-level cancellation test. cargo test/clippy and TS supervisor tests passed. -->
- [ ] 2.2 Implement provider-neutral target discovery, attachment, required CDP domain enablement, event dispatch, bounded reconnect, and session restoration without replaying dispatched effects.
- [ ] 2.3 Enforce one active Xiaohongshu writer per browser session, task/command ownership, deadlines, cancellation safe points, and non-interruptible atomic regions.
- [ ] 2.4 Enforce a CDP method allowlist and bounded/redacted Native diagnostics that exclude cookies, credentials, upload content, and unnecessary DOM text.

## 3. Native page model and interaction primitives

- [x] 3.1 Port page-state classification and URL compatibility for home, explore, `search_result_ai`, note detail, profile, notification, publish, login, error, and unknown states.
  <!-- aidcp-edge 80c9296: encoded Native probe and typed projections cover every listed state; fixture/unit tests include search_result_ai compatibility, query redaction, login precedence, notification, creator publish, error, and unknown behavior. -->
- [ ] 3.2 Port DOM-first locating with visibility, geometry, ambiguity rejection, bounded retry/escalation, post-action validation, and cache promotion only after repeated success.
- [ ] 3.3 Implement Native pointer, wheel, keyboard, text, and file-input primitives with current humanization bounds and cancellation-safe atomic actions.
- [x] 3.4 Define bounded structured models for feed cards, search results, note details, profiles, notifications, interaction receipts, and publish receipts.
  <!-- aidcp-edge 6866acf: deny-unknown Rust command/result types cover the complete frozen command manifest; card/note/profile/notification/action/publish projections apply explicit text/list/URL/ID bounds. cargo test and clippy -D warnings passed. Command behavior remains sections 4-6. -->

## 4. Browse, search, note, profile, and notification commands

- [ ] 4.1 Implement feed scan, `browse.next`, bounded scroll, page scroll, and feed refresh with honest exhaustion and movement evidence.
- [ ] 4.2 Implement search input, keyword submission, search URL compatibility, filters, and `search_result_ai` result extraction.
- [ ] 4.3 Implement exact-target note open/close, note detail extraction, image browsing, comment scrolling, source restoration, and error-page recovery.
- [ ] 4.4 Implement exact-target profile open and notification open/browse/back-home flows.
- [ ] 4.5 Implement captcha-assistance capture/click page operations and allowlisted legacy plan steps while keeping authorization and envelope routing in Edge.
- [ ] 4.6 Add deterministic Native contract tests for every command and page-state transition in this section.

## 5. Interaction commands and effect honesty

- [ ] 5.1 Implement exact-target note like and collect with precondition checks, post-action state verification, and idempotent receipts.
- [ ] 5.2 Implement exact-target follow from note/profile contexts with identity binding and post-action verification.
- [ ] 5.3 Implement approved comment and comment-like commands with target binding, fill/readback/submit validation, and no implicit publish.
- [ ] 5.4 Add crash, disconnect, timeout, cancellation, and duplicate-command tests proving `not_started`, `dispatched`, `confirmed`, and `ambiguous` are never upgraded to false success.

## 6. Publish commands and safety invariants

- [ ] 6.1 Implement publish-entry navigation, mode selection, field filling, topic/candidate insertion, and option setting with readback validation.
- [ ] 6.2 Implement image upload and cover selection with explicit file validation, bounded diagnostics, and no file-content leakage over IPC.
- [ ] 6.3 Implement scheduled-publish controls with exact target-time evidence and explicit timezone handling.
- [ ] 6.4 Implement submit, post-id capture, scheduled capture, and reconciliation with `ambiguous` handling that forbids blind resubmission.
- [ ] 6.5 Port the existing publish safety and integrity fixtures into Native acceptance tests.
- [ ] 6.6 Implement the legacy whole-publish transaction through the same Native primitives or retire its registration and callers under an explicit protocol-compatible migration; no JavaScript whole-publish path may remain packaged.

## 7. Edge direct production integration

- [x] 7.1 Add a selector-free TypeScript Native supervisor/facade that validates protocol v2, version compatibility, lifecycle, bounds, and child-process failures.
  <!-- aidcp-edge c5d08b7 + 80c9296: selector-free long-lived facade validates ready manifest/protocol, identities, bounded records/results, lifecycle, timeouts, exits, malformed output, stable errors, cancellation, and effect truth; focused TS tests and npm typecheck passed. Production routing remains tasks 7.2-7.5. -->
- [ ] 7.2 Start Native only after task admission, provider resolution, account/environment binding, and browser startup; keep browser lifecycle and Cloud transport owned by Edge.
- [ ] 7.3 Route the full Xiaohongshu browse/search/note/profile/notification/interaction registry directly to Native with no shadow invocation and no JavaScript fallback.
- [ ] 7.4 Route the full Xiaohongshu publish registry directly to Native with no shadow invocation and no JavaScript fallback.
- [ ] 7.5 Map Native results, effect phases, cancellation, and failures to the existing Cloud protocol and task-coordinator receipts without changing Cloud contracts.
- [ ] 7.6 Add integration tests proving Native failure is scoped to the owning task/session and non-Xiaohongshu browser providers and flows remain isolated.

## 8. Customer package removal and Native artifact delivery

- [ ] 8.1 Split any genuinely shared selector-free DTOs/utilities away from legacy Xiaohongshu page-rule modules so production Edge code has no runtime import path to them.
- [ ] 8.2 Remove the legacy Xiaohongshu page-understanding/action modules from production build inputs and add a build-time import-graph gate that fails on reintroduction.
- [ ] 8.3 Build and stage architecture-matched Native artifacts with a manifest containing protocol version, platform, architecture, and artifact hash.
- [ ] 8.4 Package Native outside ASAR, resolve it from `process.resourcesPath`, and add installed-artifact startup/health/command/shutdown smoke tests.
- [ ] 8.5 Extend CI packaging and nested signing/notarization to the Native artifact for supported macOS architectures and Windows x64; fail packaging when a required artifact is missing or incompatible.
- [ ] 8.6 Add final ASAR/resources leakage scans for legacy module paths, representative selectors/rules, source maps, debug fixtures, and unredacted diagnostics.

## 9. Validation, evidence, and release gate

- [ ] 9.1 Run Rust formatting, unit/integration/acceptance tests, clippy, and release builds for every locally supported target; record unsupported cross-target checks truthfully.
- [ ] 9.2 Run physical Edge dependency installation, focused tests, required safety acceptance suites, full tests, typecheck, and production build.
- [ ] 9.3 Run package-input graph checks, packaged smoke tests, signature verification, and leakage scans for locally produced artifacts; record Windows and alternate-architecture CI evidence separately.
- [ ] 9.4 Run the authorized read-only live Xiaohongshu matrix across home/explore/search/note/profile/notification/error/login-observable states and record exact post-conditions.
- [ ] 9.5 Run live write/action validation only under separate target-specific authorization, covering interaction and publish ambiguity without broadening the authorized action scope.
- [ ] 9.6 Update this checklist with repository commits, validation evidence, deviations, and package availability; run `openspec validate native-page-engine-production-cutover --strict`.
- [ ] 9.7 Integrate and push the clean control and Edge changes under the repository workflow. Build or publish a customer installer only after separate explicit release authorization.
