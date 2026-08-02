## 1. Regression Coverage

- [x] 1.1 Add Native tests for axis-free Reels key probing: `ArrowRight` success, fresh re-probe before `ArrowDown`, late first-key movement suppression, and honest no-change termination.
- [x] 1.2 Add Native tests for Reels entry recovery: successful first navigation without foreground activation, ineffective navigation with one exact-target activation and one retry, late success suppression, and blocker/target-drift fail-closed behavior.
- [x] 1.3 Add Edge UI tests that label primary and fallback Reels entry commands as `进入 Reels`, preserve ordinary scroll wording, and keep dispatch-stage wording honest.
- [x] 1.4 Add strict Native decode and Fake CDP regressions for the real `reel_next_target.inputSafe` shape, including a newly unsafe next-target probe that dispatches zero keys.

## 2. Edge Implementation

- [x] 2.1 Replace the Reels axis prerequisite with bounded verified-key probing while preserving fresh target checks and post-key video identity confirmation.
- [x] 2.2 Add session-local preference for the last verified Reels key without treating it as permanent page-layout truth.
- [x] 2.3 Recover an ineffective Reels entry by foregrounding the exact bound page once, re-probing, and retrying navigation at most once; do not foreground a successful first entry.
- [x] 2.4 Map Reels entry reasons to a dedicated UI command title and summary without changing ordinary `page.scroll` diagnostics.
- [x] 2.5 Synchronize `FacebookReelNextTarget` with the router's input-safety field and require the fresh target observation to remain keyboard-safe before probing directions.

## 3. Validation And Delivery

- [x] 3.1 Run focused Native and UI regression tests, formatting/lint checks, Edge typecheck, and the proportionate serialized Native gate.
- [x] 3.2 Run `openspec validate stabilize-facebook-reels-entry-and-navigation --strict` and record repository, commit, validation, packaging, and deployment boundaries in this task file.
  <!-- Evidence: aidcp-edge commit e84770d. Passed focused Reels entry/key/router/diagnostic/renderer regressions, renderer-smoke 108/108, Facebook router contract 113/113, `npm run typecheck`, `npm run gate:native:fmt`, `npm run gate:native:clippy`, and serialized `RUST_TEST_THREADS=1 npm run gate:native:test` (all Native suites green, including lib 188/188 and fake_cdp 66/66). `openspec validate stabilize-facebook-reels-entry-and-navigation --strict` passed. No installer was packaged or installed, no Cloud/Console deployment occurred, and no real-account action was run. -->
- [x] 3.3 Rebase and fast-forward integrate the Edge change, push the owning default branch, then commit and push the control-repo OpenSpec change without packaging an installer.
  <!-- Integration evidence: the first `scripts/land-change aidcp-edge stabilize-facebook-reels-entry-and-navigation --yes` run exposed a pre-existing inventory omission from dfb57f1: `facebook_auth_start_ad_data_review` was implemented as a write command but absent from `command-postconditions.json`. After explicit user approval, the final Edge branch added a separate confirmed-postcondition registry commit whose evidence requires the exact ad-data choice successor; button/loading/navigation evidence alone remains Ambiguous. The second land run passed acceptance 38/38, full Edge tests 3027 passed / 1 skipped / 0 failed, `npm run typecheck`, and Native fmt/clippy/all tests, then fast-forward pushed Edge commits e84770d and 52cd8d9 to `origin/master`. No installer was packaged or installed, no Cloud/Console deployment occurred, and no real-account action was run. -->
- [x] 3.4 Run focused strict-decode/key-dispatch regressions, Native fmt/clippy/serialized tests, Edge typecheck, strict OpenSpec validation, then fast-forward integrate and push Edge/control follow-up commits without packaging or installing a client.
  <!-- Follow-up evidence: aidcp-edge commit be286ec synchronizes the strict `FacebookReelNextTarget` decoder with the router's `inputSafe` field and rejects a fresh unsafe target before dispatching either direction key. Focused validation passed the strict-decode unit, 13/13 Reels Fake CDP tests, and the Facebook router contract 109/109. Integration validation passed acceptance 38/38, full Edge tests 3037 passed / 1 skipped / 0 failed, `npm run typecheck`, Native fmt/clippy, and all 375 Native tests. `scripts/land-change aidcp-edge stabilize-facebook-reels-entry-and-navigation --yes` rebased and fast-forward pushed be286ec to `origin/master`. No installer was packaged or installed, no running client was replaced, no Cloud/Console deployment occurred, and no real-account action was run. -->
