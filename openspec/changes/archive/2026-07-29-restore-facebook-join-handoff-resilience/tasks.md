## 1. Native Facebook page continuity

- [x] 1.1 Change the Edge Native Facebook task-resume path to unblock commands and restart passive probing without issuing `initial_scan`; keep Xiaohongshu resume unchanged.
- [x] 1.2 Add focused Native session regression coverage proving Facebook resume preserves the current page and the next deliberate command remains executable.

## 2. Bounded Cloud readiness recovery

- [x] 2.1 Add one no-click recovery observe for `not_ready` and `nav_error`, using the existing fresh canonical observe leg and a non-terminal audit fact.
- [x] 2.2 Keep final failures non-blocking and cooldown-free, and prove clicked/ambiguous, lease, login/captcha, and unrelated failure paths are never replayed.
- [x] 2.3 Update focused scheduler tests for recovery success, repeated failure, next-target eligibility, and concrete final receipts.

## 3. Validation and integration

- [x] 3.1 Run focused Edge tests, Cargo/Native checks required by the touched host boundary, Edge full tests where required, and Edge typecheck.
  <!-- Edge: Native browse-session focused 25/25; landing acceptance 30/30; landing full 2478 passed, 1 skipped, 0 failed (2479 total); typecheck passed. The first full run under concurrent Cloud load had one unrelated Native client startup timeout (2476 pass, 1 fail, 1 skipped); the failing capability-manifest case passed alone, then the serialized rerun and final landing gate both passed. `cargo` is not installed on this host; Rust sources were untouched, and diff inspection confirms the change is limited to the TypeScript Native host/session boundary plus its focused test. -->
- [x] 3.2 Run focused Cloud scheduler tests, acceptance, Cloud full tests, and Cloud typecheck.
  <!-- Cloud: scheduler focused 23/23; acceptance 154/154; full 3724 passed, 11 skipped, 0 failed (3735 total); typecheck passed. -->
- [x] 3.3 Run `openspec validate restore-facebook-join-handoff-resilience --strict` and inspect diffs for protocol/database drift.
  <!-- Strict change validation and all three `git diff --check` calls passed. Edge protocol/Rust and Cloud protocol/migrations/store diffs are empty: no protocol or database drift. -->
- [x] 3.4 Commit the three isolated branches, rebase onto latest defaults, integrate and push Edge/Cloud/control serially without force.
  <!-- Edge e7c732a and Cloud edbf17d were rebased, fast-forward integrated, and pushed to origin/master by land-change. Control artifacts were committed as d052900 and the delivery-evidence commit is the final fast-forward payload to origin/main; no force push was used. -->

## 4. DEV delivery evidence

- [x] 4.1 Run the DEV deployment preflight, deploy only the integrated default revisions from canonical checkouts, and verify service/listener/health/database plus Edge/runtime revision evidence without performing an unauthorized Facebook write.
  <!-- DEV target preflight resolved 121.89.85.150 with the documented key. From clean aidcp-cloud master@edbf17d, backup /opt/aidcp/cloud.bak.20260727-234433.tar.gz plus .env.bak.20260727-234433 was created, the committed tree was rsynced without .env/node_modules/.git, .deploy-sha was set to edbf17d, and only aidcp-cloud.service was restarted. Migration status reported content 20/20 through 0069, automation 51/51 through 0093, api 59/59 through 0092, with zero pending. Post-restart: active/running, NRestarts=0, 8787/8090/8091 listening, /api/health={"ok":true}, all three schema enforce gates passed, automation writer lock held for target=dev, and Feishu WS onReady. No Facebook write was performed. -->
- [x] 4.2 Record repository SHAs, validation, DEV deployment, remaining real-account acceptance boundary, and deviations in this task file.
  <!-- Delivered source revisions: Edge e7c732a, Cloud edbf17d, control d052900 plus this evidence update. Edge master and Cloud master match their origins. The currently running /Applications/AIDCP.app is not runtime proof for e7c732a: its app.asar mtime is 2026-07-27 23:01:38 CST while the Edge commit is 23:37:53 CST. No installer/package was requested or built, so real-account acceptance remains: load an Edge artifact containing e7c732a, then perform one authorized group join and confirm there is no group→home→group bounce and that a slow first observation receives exactly one fresh no-click observe before terminal failure. Deviations: Cargo unavailable on the host; no Rust files changed. One concurrent Edge full-run startup timeout was disproved by the isolated case, serialized rerun, and final landing gate. -->
