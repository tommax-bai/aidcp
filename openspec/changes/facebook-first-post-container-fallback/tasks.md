## 1. Contracts and regression coverage

- [x] 1.1 Add Edge router fixtures for a Vietnamese group post with a live comment editor, no top-level `role=article`, and only opaque group-root story links.
- [x] 1.2 Add Native runtime tests for canonical-permalink preference, strict fallback target-reference parsing, and in-place detail correlation.
- [x] 1.3 Add Cloud edge-step and scheduler tests that accept the strict reference only from first-post selection, preserve dedup/approval/submit plumbing, and reject it from ordinary open/search paths.

## 2. Edge implementation

- [x] 2.1 Implement bounded first-commentable-container discovery, deterministic reference generation, and a page-local live binding in the Native Facebook router.
- [x] 2.2 Route `note.open` context reads plus comment editor/fill/recheck/ack probes through the bound container while failing closed on detach, evidence change, or ambiguity.
- [x] 2.3 Extend the Rust first-post executor to prefer canonical URLs and otherwise use the strict in-place reference without navigation or fabricated canonical identity.

## 3. Cloud and protocol integration

- [x] 3.1 Update Cloud first-post correlation to return a target reference union while retaining canonical-only validation for search and ordinary open.
- [x] 3.2 Preserve the selected target through dedup, approval, submit, and audit without presenting the internal reference as a Facebook permalink.
- [x] 3.3 Synchronize Edge/Cloud protocol comments and `docs/protocol.md` with the first-post-only target-reference semantics.

## 4. Validation and closeout

- [x] 4.1 Run focused Edge JavaScript/Native tests, `cargo test`, `cargo clippy`, Edge acceptance/full tests, and Edge typecheck.
  <!-- aidcp-edge d3fe159: router 75/75; Native cargo test + fmt + clippy; acceptance 30/30; full 2484 pass, 1 gated skip; typecheck pass. -->
- [x] 4.2 Run focused Cloud edge-step/scheduler tests, Cloud acceptance/full tests, and Cloud typecheck.
  <!-- aidcp-cloud 21ab6ff: focused 133/133; acceptance 154/154; full 3733 pass, 11 expected skips; typecheck pass. -->
- [x] 4.3 Run `openspec validate facebook-first-post-container-fallback --strict`, review scoped diffs, and record repository commits plus validation evidence.
  <!-- aidcp 9ac7f12: strict OpenSpec validation and scoped diff review pass. No installer packaging, OL deployment, or real-account write. -->
- [x] 4.4 Deploy Cloud commit `21ab6ff` to DEV after explicit user authorization and verify the runtime.
  <!-- DEV 2026-07-28: backup /opt/aidcp/backups/cloud-20260727T182028Z-pre-21ab6ff.tgz; remote focused tests 133/133; schema gates content/automation/api pass; writer lock held; 8787/8090/8091 listening; panel health ok; Feishu WS ready; Gi Vo Edge reconnected. -->

## 5. Trusted comment-editor activation regression

- [x] 5.1 Add router and fake-CDP regression coverage proving editor hydration uses one Native mouse move/press/release sequence and never DOM `click()`.
- [x] 5.2 Implement a same-target comment-action point probe and Native CDP click with bounded editor post-state validation.
- [x] 5.3 Record the repository-wide real-input invariant in `AGENTS.md` and `docs/architecture.md`.
  <!-- aidcp-edge 8f5bae9: router fixture covers the Vietnamese primary action plus avatar/GIF/sticker decoys; fake CDP proves one mouseMoved/mousePressed/mouseReleased sequence and same-target editor post-state. -->
- [x] 5.4 Run focused Edge router/Native tests, full Native validation, Edge acceptance/full tests and typecheck; then strict OpenSpec validation, scoped review, commit, and push.
  <!-- Validation 2026-07-28: router 76/76; focused fake CDP 1/1; full cargo test pass; cargo fmt/clippy pass; Edge acceptance 30/30; Edge full 2485 pass, 1 gated skip; typecheck pass; strict OpenSpec and scoped diff review pass. aidcp-edge 8f5bae9 integrated and pushed to master. No installer packaging, deployment, or real-account write. -->
