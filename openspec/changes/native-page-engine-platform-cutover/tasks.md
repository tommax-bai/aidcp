## 1. Admission and production-boundary inventory

- [x] 1.1 Create isolated control/Edge worktrees, install independent Edge dependencies, and record clean base revisions. <!-- control=095efc0312301819de1acb26866401ddcb27ae9b edge=2b2d9dd4a439b6e72798b1755ec8e9b6083e11aa; physical worktree-local node_modules installed with npm ci --prefer-offline -->
- [x] 1.2 Inventory every production-reachable Facebook and WeChat browser-inspection module, command surface, probe, selector/script marker, and package path; classify each as Native migration, selector-free facade, API/business orchestration, or development-only exclusion. <!-- inventory.md; baseline build: reachable=109 removed=31, all 27 Facebook modules and WeChat browser-sidecar confirmed in dist -->
- [x] 1.3 Add characterization tests for the existing Facebook facade contracts and WeChat session-candidate shape before replacing page implementations. <!-- test/native-page-engine/platform-cutover-characterization.test.ts: 2/2 pass -->

## 2. Multi-platform Native protocol and lifecycle

- [ ] 2.1 Extend the Native manifest, TypeScript client/runtime types, Rust platform enum, host allowlists, session selection, and adapter compatibility validation for `facebook` and `wechat_channels`.
- [ ] 2.2 Add bounded typed Facebook command/result families and reject selectors, JavaScript, raw CDP, unknown fields, platform mismatch, stale tasks, duplicate commands, and unbounded payloads.
- [ ] 2.3 Add bounded typed WeChat session-capture commands/results and Network-event support without exposing arbitrary requests, storage, or DOM.
- [ ] 2.4 Cover platform selection, command mismatch, cancellation, deadline, reconnect, crash, and effect-phase behavior with Rust unit, fake-CDP, fixture, and process-protocol tests.

## 3. Facebook read-only page intelligence

- [ ] 3.1 Move identity, locale/CTA normalization, page structure, fingerprint, consent, overlay, and exact post-identity logic into the Native Facebook adapter.
- [ ] 3.2 Move feed, Reels, inline-post, detail-post, and viewport-state reads into Native with bounded semantic results.
- [ ] 3.3 Move production editor, composer, media, storage, and submit-gating probes into Native and remove calibration-only probes from the production export graph.
- [ ] 3.4 Replace JavaScript readers/probes with selector-free Native facade calls and pass focused read/browse fixture and acceptance tests.

## 4. Facebook actions and verification

- [ ] 4.1 Move humanized scrolling and its movement/fallback verification into Native.
- [ ] 4.2 Move like/follow action targeting, dispatch, identity binding, and exact after-state verification into Native.
- [ ] 4.3 Move comment editor discovery, text entry, submit, duplicate protection, and bounded post-submit verification into Native.
- [ ] 4.4 Move group membership detection, join targeting, consent handling, dispatch, and membership verification into Native.
- [ ] 4.5 Move composer entry, media upload, field filling, publish submit, link capture, and ambiguous-result reconciliation into Native.
- [ ] 4.6 Route all Facebook production handlers through the facade, prohibit JavaScript fallback, and pass focused interaction/group/comment/publish acceptance tests.

## 5. WeChat browser-session capture

- [ ] 5.1 Implement Native Network enable/reload/event capture for the exact allowed WeChat authentication request and bounded cookie/user-agent extraction.
- [ ] 5.2 Replace direct CDP capture in the WeChat browser sidecar with the Native facade while preserving lease ownership, cleanup, identity validation, persistence, and API capability probes.
- [ ] 5.3 Pass focused valid, incomplete, mismatched, cancelled, timed-out, and cleanup-confirmation tests without changing ordinary WeChat API orchestration.

## 6. JavaScript removal and package enforcement

- [ ] 6.1 Delete or make production-unreachable every migrated Facebook/WeChat page implementation and verify remaining TypeScript facades contain no page selectors, browser scripts, raw page CDP, or local page-recovery rules.
- [ ] 6.2 Expand production import pruning to deny migrated paths, representative cross-platform markers, source maps, standalone router sources, wildcard production probe exports, and development probes.
- [ ] 6.3 Expand Native manifest/build/package verification and final ASAR/resource inspection for all declared adapters, architecture/digest/protocol compatibility, and packaged startup smoke coverage.
- [ ] 6.4 Prove with build-output inspection that XHS remains Native, Facebook/WeChat migrated rules are absent from distributable JavaScript, and development probes are absent from the package inputs.

## 7. Validation, integration, and release boundary

- [ ] 7.1 Run Rust formatting/lint/tests, focused Edge acceptance tests, full Edge tests, Edge typecheck, desktop build-input verification, and strict OpenSpec validation with bounded evidence.
- [ ] 7.2 Rebase the Edge worktree onto current `origin/master`, resolve only in-scope conflicts, rerun required validation, commit, fast-forward integrate, and push `master` without force.
- [ ] 7.3 Update this checklist with Edge/control commit SHAs, validation evidence, deviations, and explicit installer/real-client acceptance status; validate, commit, integrate, and push the control change.
- [ ] 7.4 Do not build or release an installer without a separate explicit request; record disposable-account Facebook/WeChat acceptance as a later release gate rather than claiming source tests prove live behavior.
