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
  <!-- aidcp 9ac7f12: strict OpenSpec validation and scoped diff review pass. Source-only closeout: no installer packaging, DEV/OL deployment, or real-account write by task boundary. -->
