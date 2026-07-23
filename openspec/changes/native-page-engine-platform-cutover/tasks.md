## 1. Admission and production-boundary inventory

- [x] 1.1 Create isolated control/Edge worktrees, install independent Edge dependencies, and record clean base revisions. <!-- control=095efc0312301819de1acb26866401ddcb27ae9b edge=2b2d9dd4a439b6e72798b1755ec8e9b6083e11aa; physical worktree-local node_modules installed with npm ci --prefer-offline -->
- [x] 1.2 Inventory every production-reachable Facebook and WeChat browser-inspection module, command surface, probe, selector/script marker, and package path; classify each as Native migration, selector-free facade, API/business orchestration, or development-only exclusion. <!-- inventory.md; baseline build: reachable=109 removed=31, all 27 Facebook modules and WeChat browser-sidecar confirmed in dist -->
- [x] 1.3 Add characterization tests for the existing Facebook facade contracts and WeChat session-candidate shape before replacing page implementations. <!-- test/native-page-engine/platform-cutover-characterization.test.ts: 2/2 pass -->

## 2. Multi-platform Native protocol and lifecycle

- [x] 2.1 Extend the Native manifest, TypeScript client/runtime types, Rust platform enum, host allowlists, session selection, and adapter compatibility validation for `facebook` and `wechat_channels`. <!-- edge=4f04e9c; multi-platform-v1 declares xiaohongshu-v1, facebook-v1, and wechat-channels-v1 with exact host binding -->
- [x] 2.2 Add bounded typed Facebook command/result families and reject selectors, JavaScript, raw CDP, unknown fields, platform mismatch, stale tasks, duplicate commands, and unbounded payloads. <!-- command-manifest digest=8ec2b0281599d863e250398c598d41ac8ed233e57764fa61513abb898fc8a8a3; Rust serde deny_unknown_fields plus fixed enum/size/deadline/owner validation -->
- [x] 2.3 Add bounded typed WeChat session-capture commands/results and Network-event support without exposing arbitrary requests, storage, or DOM. <!-- Native accepts only the exact channels.weixin.qq.com auth request and bounded cookies/UA/request context -->
- [x] 2.4 Cover platform selection, command mismatch, cancellation, deadline, reconnect, crash, and effect-phase behavior with Rust unit, fake-CDP, fixture, and process-protocol tests. <!-- cargo test --locked: 49/49; cargo clippy --all-targets -- -D warnings: pass -->

## 3. Facebook read-only page intelligence

- [x] 3.1 Move identity, locale/CTA normalization, page structure, consent, overlay, and exact post-identity logic into the Native Facebook adapter; retain no standalone production fingerprint probe. <!-- c_user is authoritative; lookalike hosts rejected; fingerprint probe was calibration-only and is absent from production exports -->
- [x] 3.2 Move feed, Reels, inline-post, detail-post, and viewport-state reads into Native with bounded semantic results. <!-- Facebook router returns bounded PageCards/NoteDetail/ActionReceipt projections -->
- [x] 3.3 Move runtime editor, composer, media, and submit-gating page checks into Native and remove calibration-only fingerprint/storage/gated-submit probes from the production export graph. <!-- src/facebook/index.ts exposes only driver and companion-ui; production dist contains only dist/facebook/driver.js -->
- [x] 3.4 Replace JavaScript readers/probes with selector-free Native facade calls and pass focused read/browse fixture and acceptance tests. <!-- Native/WeChat focused suite: 73/73; characterization: 2/2 -->

## 4. Facebook actions and verification

- [x] 4.1 Move humanized scrolling and its movement/fallback verification into Native. <!-- bounded smooth scroll with before/after position and page-card reread -->
- [x] 4.2 Move like/follow action targeting, dispatch, identity binding, and exact after-state verification into Native. <!-- exact-card target identity and changed-state receipt required -->
- [x] 4.3 Move comment editor discovery, text entry, submit, duplicate protection, and bounded post-submit verification into Native. <!-- editor readback plus visible server comment id required; optimistic client ids do not confirm -->
- [x] 4.4 Move group membership detection, join targeting, consent handling, dispatch, and membership verification into Native. <!-- in-scope Join CTA only; Joined/member after-state required -->
- [x] 4.5 Move composer entry, media upload, field filling, publish submit, link capture, and ambiguous-result reconciliation into Native. <!-- Rust owns DOM.setFileInputFiles; composer close and exact matching post prove success -->
- [x] 4.6 Route all Facebook production handlers through the facade, prohibit JavaScript fallback, and pass focused interaction/group/comment/publish acceptance tests. <!-- Native-only routing contract 10/10; Facebook router contract 8/8 -->

## 5. WeChat browser-session capture

- [x] 5.1 Implement Native Network enable/reload/event capture for the exact allowed WeChat authentication request and bounded cookie/user-agent extraction. <!-- bounded request-event queue; exact channels.weixin.qq.com host/path; matching WeChat-domain cookies only -->
- [x] 5.2 Replace direct CDP capture in the WeChat browser sidecar with the Native facade while preserving lease ownership, cleanup, identity validation, persistence, and API capability probes. <!-- sidecar has no direct page CDP; Native closes before the physical browser -->
- [x] 5.3 Pass focused valid, incomplete, mismatched, cancelled, timed-out, and cleanup-confirmation tests without changing ordinary WeChat API orchestration. <!-- focused Native/WeChat suite 73/73; ordinary black-box/API probes remain TypeScript -->

## 6. JavaScript removal and package enforcement

- [x] 6.1 Delete or make production-unreachable every migrated Facebook/WeChat page implementation and verify remaining TypeScript facades contain no page selectors, browser scripts, raw page CDP, or local page-recovery rules. <!-- compile-time-unreachable legacy source is excluded by dependency pruning; dist/facebook contains only selector-free driver.js -->
- [x] 6.2 Expand production import pruning to deny migrated paths, representative cross-platform markers, source maps, standalone router sources, wildcard production probe exports, and development probes. <!-- prune-production-dist rejects all listed paths/markers and source maps -->
- [x] 6.3 Expand Native manifest/build/package-input verification for all declared adapters, architecture/digest/protocol compatibility, and staged-resource startup requirements. <!-- darwin-arm64 release artifact verified: sha256=c96ffb160ed914553bf9a61e111719055a5fb26bd04106dd78ce601d93b569e3; final signed installer/ASAR inspection remains the separately authorized release gate in 7.4 -->
- [x] 6.4 Prove with build-output inspection that XHS remains Native, Facebook/WeChat migrated rules are absent from distributable JavaScript, and development probes are absent from the package inputs. <!-- build:dist reachable=77 removed=64 legacy_page_rules=absent source_maps=absent; desktop build input verified loadable -->

## 7. Validation, integration, and release boundary

- [x] 7.1 Run Rust formatting/lint/tests, focused Edge acceptance tests, full Edge tests, Edge typecheck, desktop build-input verification, and strict OpenSpec validation with bounded evidence. <!-- post-rebase: cargo fmt/check + clippy pass; Rust 49/49; acceptance 30/30 with 1 gated live skip; Edge 2281/2281; typecheck/build-input pass; OpenSpec strict validation recorded in control closeout -->
- [x] 7.2 Rebase the Edge worktree onto current `origin/master`, resolve only in-scope conflicts, rerun required validation, commit, fast-forward integrate, and push `master` without force. <!-- edge master=4f04e9c10aa4c6dd94639c593d886689fbec2c85, pushed to origin/master; no force -->
- [x] 7.3 Update this checklist with Edge/control commit SHAs, validation evidence, deviations, and explicit installer/real-client acceptance status; validate, commit, integrate, and push the control change. <!-- edge=4f04e9c10aa4c6dd94639c593d886689fbec2c85; control proposal=84e4b70 evidence=ead0689; final strict validation pass; canonical control checkout had unrelated dirty/untracked files, so integration used a fast-forward-only HEAD:main push from the clean rebased worktree instead of touching or stashing user work -->
- [x] 7.4 Do not build or release an installer without a separate explicit request; record disposable-account Facebook/WeChat acceptance as a later release gate rather than claiming source tests prove live behavior. <!-- no installer built/released; no real Facebook/WeChat account interaction performed; final ASAR/resources, signing/notarization, packaged startup, and disposable-account acceptance remain release gates -->
