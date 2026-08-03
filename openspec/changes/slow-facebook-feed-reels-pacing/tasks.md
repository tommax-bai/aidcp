## 1. Cloud Facebook center

- [x] 1.1 Change the Facebook platform page-scroll floor from 7,000 ms to 11,000 ms without changing other platform pacing.
- [x] 1.2 Update focused Cloud coverage for the Facebook floor and the shared Feed/Reels scroll command center.

## 2. Edge bounded Facebook jitter

- [x] 2.1 Add a center-preserving reflected lognormal helper with relative bounds and an absolute cap, plus deterministic unit coverage.
- [x] 2.2 Apply `sigma=0.30`, `0.55x..1.90x`, and the 60-second cap only to Facebook `page.scroll`, preserving elapsed-time subtraction, inline-read max semantics, cancellation, and non-Facebook behavior.
- [x] 2.3 Extend bounded command-dwell diagnostics and focused browse-session coverage for sampled target, elapsed time, final wait, platform scope, and timeout independence.

## 3. Validation

- [x] 3.1 Run focused Cloud tests and Cloud typecheck.
- [x] 3.2 Run focused Edge tests and Edge typecheck.
- [x] 3.3 Run `openspec validate slow-facebook-feed-reels-pacing --strict` and verify the OpenSpec change is apply-ready.

<!-- Validation before and after rebase: Cloud focused platform/dispatcher coverage 51 passed, Edge timing/pacing coverage 26 passed, both repository typechecks exited 0, and strict OpenSpec validation passed. -->

## 4. Delivery

- [ ] 4.1 Rebase, commit, push, and safely integrate the control, Cloud, and Edge changes into their default branches with explicit file scopes.
- [x] 4.2 Run the DEV deployment gates, deploy the integrated Cloud runtime, and verify deployed SHA, service/listener/health/log evidence without touching OL.
- [ ] 4.3 Record commits, validation, DEV deployment evidence, deviations, and the explicit no-Edge-package/no-install/no-real-account boundary in this task file.

<!-- DEV Cloud deployment 2026-08-03: target preflight passed for 121.89.85.150. Backups are /opt/aidcp/cloud.bak.20260803-105522.tar.gz and /opt/aidcp/cloud/.env.bak.20260803-105522. A clean Cloud master archive was synced with local/remote registry sha256 a65a6129a2dbee7c06bf62ac3a5dce401a6ca53e05e052211596822f3244afda and .deployed-commit=f67aec9f4c2687c61b5a88379bc8c8c05e08f42a. Migration status reported content 20/20, automation 57/57, and api 68/68 applied with zero pending. DEV remains on the existing monolith topology because the separately tracked three-process API composition-root gate is still open; only aidcp-cloud.service was stopped then started. It is active with NRestarts=0, 8787/8090/8091 listen, panel and client-auth health return ok, enforce schema gates pass for content 0069 / automation 0106 / api 0108, the target=dev automation writer lock is held, and Feishu WSClient reached onReady. Unrelated isales unit states were unchanged. OL was not accessed. -->
