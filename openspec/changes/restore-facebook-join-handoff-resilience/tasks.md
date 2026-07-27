## 1. Native Facebook page continuity

- [x] 1.1 Change the Edge Native Facebook task-resume path to unblock commands and restart passive probing without issuing `initial_scan`; keep Xiaohongshu resume unchanged.
- [x] 1.2 Add focused Native session regression coverage proving Facebook resume preserves the current page and the next deliberate command remains executable.

## 2. Bounded Cloud readiness recovery

- [x] 2.1 Add one no-click recovery observe for `not_ready` and `nav_error`, using the existing fresh canonical observe leg and a non-terminal audit fact.
- [x] 2.2 Keep final failures non-blocking and cooldown-free, and prove clicked/ambiguous, lease, login/captcha, and unrelated failure paths are never replayed.
- [x] 2.3 Update focused scheduler tests for recovery success, repeated failure, next-target eligibility, and concrete final receipts.

## 3. Validation and integration

- [x] 3.1 Run focused Edge tests, Cargo/Native checks required by the touched host boundary, Edge full tests where required, and Edge typecheck.
  <!-- Edge: Native browse-session focused 24/24; acceptance 30/30; typecheck passed. The first full run under concurrent Cloud load had one unrelated Native client startup timeout (2476 pass, 1 fail, 1 skipped); the failing capability-manifest case passed alone, then the serialized full rerun passed 2477 with 1 skipped. `cargo` is not installed on this host; Rust sources were untouched, and diff inspection confirms the change is limited to the TypeScript Native host/session boundary plus its focused test. -->
- [x] 3.2 Run focused Cloud scheduler tests, acceptance, Cloud full tests, and Cloud typecheck.
  <!-- Cloud: scheduler focused 23/23; acceptance 154/154; full 3724 passed, 11 skipped, 0 failed (3735 total); typecheck passed. -->
- [x] 3.3 Run `openspec validate restore-facebook-join-handoff-resilience --strict` and inspect diffs for protocol/database drift.
  <!-- Strict change validation and all three `git diff --check` calls passed. Edge protocol/Rust and Cloud protocol/migrations/store diffs are empty: no protocol or database drift. -->
- [ ] 3.4 Commit the three isolated branches, rebase onto latest defaults, integrate and push Edge/Cloud/control serially without force.

## 4. DEV delivery evidence

- [ ] 4.1 Run the DEV deployment preflight, deploy only the integrated default revisions from canonical checkouts, and verify service/listener/health/database plus Edge/runtime revision evidence without performing an unauthorized Facebook write.
- [ ] 4.2 Record repository SHAs, validation, DEV deployment, remaining real-account acceptance boundary, and deviations in this task file.
