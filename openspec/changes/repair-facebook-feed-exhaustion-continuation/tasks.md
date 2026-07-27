## 1. Native Facebook Feed Evidence

- [x] 1.1 Create the isolated Edge worktree and add failing focused regressions for delayed height growth, stable explicit end markers, and bounded rounds without terminal evidence.
  <!-- aidcp-edge isolated worktree; five focused Rust regressions and one router marker regression added -->
- [x] 1.2 Extend the internal Facebook Feed probe with a distinct visible explicit end-of-feed observation while preserving the stronger explicit empty-home observation.
  <!-- aidcp-edge router contract suite passes 71/71 including localized explicitEnd != explicitEmpty -->
- [x] 1.3 Implement bounded bottom-candidate confirmation, include height in settling identity, and replace the unproved round-limit `feed_exhausted` shortcut with `feed_continuation_unconfirmed`.
  <!-- aidcp-edge focused Rust tests pass 5/5; bottom confirmation uses the existing 3.5s budget and two structural rounds -->
- [x] 1.4 Run focused Native tests and Cargo tests, then rebuild and verify the local source-run Native Page Engine artifact without packaging an installer.
  <!-- aidcp-edge router 71/71; Cargo 127/127 across unit/integration/doc tests; clippy -D warnings pass; unsigned darwin-arm64 artifact sha256 ccd371f5b775ef9323a0213ed209da16749b1197b1441db60f780ac9858832a4 -->

## 2. Cloud Continuation and Fallback Epoch

- [x] 2.1 Create the isolated Cloud worktree and add failing integration regressions for ordinary continuation, same-epoch deduplication, and confirmed Reels followed by non-empty Feed re-entry.
  <!-- aidcp-cloud worktree created; focused test baseline 8 pass / 2 expected fail before implementation -->
- [x] 2.2 Map `feed_continuation_unconfirmed` to another ordinary gated Facebook Feed scroll without authorizing Reels.
  <!-- aidcp-cloud focused fallback integration suite passes 11/11 -->
- [x] 2.3 Reset only a confirmed fallback epoch after a later non-empty ordinary Feed batch, preserving pending, empty, search/group, non-Facebook, and duplicate behavior.
  <!-- aidcp-cloud confirmed-only reset is gated by non-empty feed batch + ordinary feed context; focused suite covers pending, empty, search, duplicate, and non-Facebook paths -->

## 3. Contract and Validation

- [x] 3.1 Update the protocol documentation for the observable continuation reason without changing the protocol envelope.
  <!-- aidcp docs/protocol.md documents Edge receipt and Cloud ordinary-scroll mapping; no message/type expansion -->
- [x] 3.2 Run focused Edge/Cloud tests, Edge and Cloud typechecks, the required broader safety suites, and strict OpenSpec validation.
  <!-- Edge router 71/71, focused client 13/13, acceptance 30/30, full 2479 pass / 0 fail / 1 skip, typecheck pass; Rust 127/127 and clippy -D warnings pass. Cloud focused fallback 11/11, acceptance 154/154, full 3728 pass / 0 fail / 11 skip, typecheck pass. openspec validate --strict pass. One initial Edge full-suite run hit the existing 500ms fake-engine startup deadline under concurrent load; the focused rerun and a serialized full rerun both passed. -->
- [ ] 3.3 Record repository commits, validation results, deployment scope, and any deviations in this checklist.

## 4. Integration and DEV Verification

- [ ] 4.1 Rebase the isolated worktrees onto the latest default branches, rerun integration checks, fast-forward merge, and push Edge, Cloud, and control.
- [ ] 4.2 Run DEV deployment preflight, deploy Cloud from the eligible default checkout, restart only the documented AIDCP service, and verify service, listener, health, logs, and the Nancy continuation path when safely observable.
