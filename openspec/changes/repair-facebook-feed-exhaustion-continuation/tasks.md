## 1. Native Facebook Feed Evidence

- [x] 1.1 Create the isolated Edge worktree and add failing focused regressions for delayed height growth, stable explicit end markers, and bounded rounds without terminal evidence.
  <!-- aidcp-edge isolated worktree; five focused Rust regressions, one router marker regression, and fake-CDP ordering coverage for foreground-before-input added -->
- [x] 1.2 Extend the internal Facebook Feed probe with a distinct visible explicit end-of-feed observation while preserving the stronger explicit empty-home observation.
  <!-- aidcp-edge router contract suite passes 71/71 including localized explicitEnd != explicitEmpty -->
- [x] 1.3 Implement bounded bottom-candidate confirmation, include height in settling identity, and replace the unproved round-limit `feed_exhausted` shortcut with `feed_continuation_unconfirmed`.
  <!-- aidcp-edge foregrounds the exact Facebook target before page_scroll input; bottom confirmation then uses one existing 3.5s budget. DEV live inspection found a constant-height skeleton without Feed-scoped loading semantics, so a complete stable window returns feed_continuation_unconfirmed immediately and only a stable visible end marker can emit feed_exhausted -->
- [x] 1.4 Run focused Native tests and Cargo tests, then rebuild and verify the local source-run Native Page Engine artifact without packaging an installer.
  <!-- final rebase: router 73/73; Cargo 135/135 across unit/integration tests plus doc tests; acceptance 30/30; typecheck and clippy -D warnings pass. Canonical unsigned darwin-arm64 artifact verified at sha256 8405ba930dde5d1a869fdbcd8dd9d3f2b97254f2a13dc9cf77697c66976155c6; no installer was packaged -->

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
  <!-- Edge initial integration: focused client 13/13, acceptance 30/30, full 2479 pass / 0 fail / 1 skip. Final rebase: router 73/73, acceptance 30/30, typecheck, Cargo 135/135, and clippy -D warnings pass. Cloud focused fallback 11/11, acceptance 154/154, full 3728 pass / 0 fail / 11 skip, typecheck pass. openspec validate --strict pass. One initial Edge full-suite run hit the existing 500ms fake-engine startup deadline under concurrent load; the focused rerun and a serialized full rerun both passed. -->
- [ ] 3.3 Record repository commits, validation results, deployment scope, and any deviations in this checklist.
  <!-- Commits so far: aidcp-edge 1b58851 + 74dcc9d + b14007b, aidcp-cloud dede7a3, aidcp control 48e0e9c plus the pending final evidence update. Scope is DEV only; OL and installer packaging remain excluded. -->

## 4. Integration and DEV Verification

- [ ] 4.1 Rebase the isolated worktrees onto the latest default branches, rerun integration checks, fast-forward merge, and push Edge, Cloud, and control.
  <!-- Edge final follow-up rebased through origin/master 02313f1, then fast-forwarded/pushed as b14007b. Cloud remains dede7a3. Control final evidence update still needs integration. -->
- [x] 4.2 Run DEV deployment preflight, deploy Cloud from the eligible default checkout, restart only the documented AIDCP service, and verify service, listener, health, logs, and the Nancy continuation path when safely observable.
  <!-- DEV preflight passed. Cloud dede7a3 deployed from clean master after backup /opt/aidcp/backups/cloud-pre-dede7a3-20260728-001848.tar.gz plus target-local env backup. Migration status: content 20/20, automation 51/51, api 59/59, pending 0 and no anomalies. Only aidcp-cloud.service restarted; active with NRestarts=0, schema enforce passed for all three owners, automation writer lock held for dev, 8787/8090/5432 healthy, panel /api/health ok, three PostgreSQL SELECT 1 probes passed, Feishu WSClient onReady, and four isales services remained running. With Nancy's task still paused, AdsPower profile k1enonmg was started for read-only DEV inspection: the inactive target reproduced an unanswered wheel call, Page.bringToFront made it return, and canonical source artifact 8405ba9 then completed page_scroll in 1.029s with movement 3130→3721 and 15 cards. Cloud continuation mapping remains covered by the 11/11 focused suite; no Facebook write or task resume was performed. -->
