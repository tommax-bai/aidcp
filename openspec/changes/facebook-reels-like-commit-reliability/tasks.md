## 1. Isolated Setup

- [x] 1.1 Create the matching `aidcp-edge` worktree and branch from the latest `origin/master`, with a physical worktree-local dependency tree.
  <!-- aidcp-edge worktree `/Users/baitianxing/codes/aidcp-edge.wt/facebook-reels-like-commit-reliability`, branch `facebook-reels-like-commit-reliability`, baseline `375962b`; `npm ci --prefer-offline` completed and `node_modules` is a physical non-symlink directory. -->
- [x] 1.2 Confirm the current Reel failure receipts and implementation boundary are captured without changing Cloud policy or protocol.
  <!-- Dev evidence: Reel likes for `ads-k1etgm0e` at 2026-07-22T06:14:42Z and 06:15:52Z were received/dispatched by Edge, then Cloud returned `ok=false` after the bounded verification interval; the same runtime had a confirmed Reel like at 06:12:49Z. Scope remains Edge-only: no Cloud/protocol change. -->

## 2. Edge Reel Like Commit

- [x] 2.1 Refactor Reel primary-control probing so the commit boundary freshly resolves the expected canonical Reel, active video, and unique supported control.
- [x] 2.2 Activate the fresh primary React control in-page, use explicit positive state witnesses, and terminate safely on movement or ambiguity.
- [x] 2.3 Add one picker-scoped Like locator and trusted pointer commit with uniqueness, viewport, and one-attempt guards.
  <!-- The primary control receives a unique transient marker at the commit boundary; verification and picker association consume that marker so picker items and document-level Like decoys cannot become the primary target. -->
- [x] 2.4 Add bounded redacted diagnostics for primary activation, picker handling, verification, and terminal non-success.
- [x] 2.5 Add focused tests for direct selection, picker selection, outside-picker decoys, off-screen/ambiguous pickers, movement, and unchanged state.
  <!-- `node --import tsx --test test/facebook/reels-reader.test.ts`: 27/27 passed, including explicit-state versus generic-image proof and jsdom picker scoping. -->

## 3. Validation

- [x] 3.1 Run focused Facebook Reel and like-control tests in the isolated Edge worktree.
  <!-- Focused Reel suite 27/27 passed; the combined Reel/CTA/like/two-step/session command exited 0. -->
- [x] 3.2 Run the Edge protocol acceptance suite and full test suite.
  <!-- `npm run test:acceptance`: 29/29 passed. `npm test`: 2209/2209 passed in 111.8s. -->
- [x] 3.3 Run Edge typecheck and verify the worktree has no shared or symlinked dependency tree.
  <!-- `npm run typecheck` and `git diff --check` passed; worktree-local `node_modules` exists and is not a symlink. -->
- [x] 3.4 Run `openspec validate facebook-reels-like-commit-reliability --strict`.
  <!-- Strict validation passed after implementation. -->

## 4. Integration and Development Acceptance

- [x] 4.1 Rebase the Edge worktree onto current `origin/master`, rerun required validation, commit, and fast-forward push to `master` without force.
  <!-- Edge commit `22ae4336dfc9e71483108e6839d293c2bdb75cb8` was pushed by the guarded `land-change` flow to `origin/master` with a fast-forward from `375962b`; canonical checkout and remote now match. Final integration gate: acceptance 29/29, full suite 2209/2209, and typecheck passed. The first full-suite attempt exposed two unrelated 1s native-engine timing failures under contention; their focused file passed 5/5 immediately, and no unrelated test or production code was changed. -->
- [ ] 4.2 Rebuild and restart the local development Edge runtime, then perform one bounded exact-target Reel like acceptance that records the commit path and same-Reel selected-state post-condition.
  <!-- Partial 2026-07-22 dev acceptance: canonical `22ae433` rebuilt with `npm run build:dist` and the local Electron client restarted. Only `ads-k1etgm0e` was started through the client's named `edge:start` IPC. It established Facebook identity and Cloud connectivity, then remained in Feed until RiskController returned `view_quota:day` at 2026-07-22T07:17:11Z; the runtime entered resting/browser-closed state with 8 views and 0 likes for this run. No Reel was presented and no new `[fb-reels][like] commit=...` line occurred, so no platform write was attempted and same-Reel selected-state acceptance remains pending. We did not switch accounts, force Reels, or bypass quota. The client was then returned to a normal `npm run electron:dev` launch without a remote-debugging port. -->
- [ ] 4.3 Record Edge commit, validation, live evidence, runtime boundary, and deviations in this task file; commit and push the control change on `main`.
