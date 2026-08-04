## 1. aidcp-edge — Native readiness wait

- [x] 1.1 Introduce one shared Facebook readiness window (30s) plus first-probe delay (3s) and probe interval (2s) constants, and drop the per-call-site window argument from the readiness wait.
<!-- aidcp-edge b65d44c -->
- [x] 1.2 Repoint all Facebook readiness call sites (feed, search, detail, inline-read fallback, back-to-list, refresh, active-list guard, Reels entry, first group post, identity bootstrap) to the shared wait, and remove the now-redundant Reels-entry constant.
- [x] 1.3 Keep the group-root landing wait and every landing/identity postcondition untouched.

## 2. aidcp-edge — Command budget tables

- [x] 2.1 Raise the Facebook non-specialised command budget to 90s in all three layers (request value, admission cap, engine ceiling).
- [x] 2.2 Raise the Facebook identity bootstrap request value so the 30s readiness window fits under its own budget.

## 3. Regression coverage

- [x] 3.1 Native unit coverage pinning the three readiness constants and the no-argument call shape at every Facebook readiness call site.
- [x] 3.2 Extend the timeout-chain contract test with the new Facebook default family and with per-family assertions that the worst-case inner chain fits under the family budget.

## 4. Validation and delivery

- [x] 4.1 Native fmt + clippy + serialized cargo tests; Edge `npm run test:acceptance`, `npm test`, `npm run typecheck`.
- [x] 4.2 `openspec validate unify-facebook-page-readiness-probe --strict`, integrate to `master`, push, and record evidence here.

## Delivery Evidence

- Edge repository: `aidcp-edge`, commit `b65d44c` on `master`, rebased onto `223ef13` (a concurrent session had changed the Reels entry route mid-gate; the rebase repointed this change's entry-URL assertion at that session's new named constant).
- Readiness contract: one shared 30s window, first probe at 3s, then one probe every 2s; the window is no longer a call-site argument, so a site cannot drift back to a shorter one.
- Call sites repointed: 11 in `facebook/feed.rs`, 2 in `facebook/runtime.rs`, 1 in `facebook/session.rs`.
- Budgets: Facebook non-specialised commands 45s → 90s across request value (`browse-session.ts`), admission cap (`client.ts`), and engine ceiling (`engine.rs`); Facebook startup identity request 12s → 40s.
- Modelling口径 recorded in the contract test: each command is costed with **one** pathological readiness window plus nominal readiness (first probe + one interval) for its other navigations. Two simultaneously pathological navigations in one command may still hit the outer wall; that outcome is accepted because it is a non-terminal, re-drivable failure.
- Validation: Native fmt + clippy clean; serialized cargo tests all green (202 library + 75 fake-CDP integration); Edge acceptance 39/39; Edge typecheck clean; full Edge suite green.
- Known flake observed once under load and not reproducible afterwards (5/5 clean re-runs, and it also fails/passes independently of this change): `facebook_reel_follow_uses_one_pointer_write_and_same_author_postcondition` asserts a per-frame pointer count derived from remaining wall clock.
- Behavioural cost: every Facebook navigation now spends at least 3 seconds before its first readiness probe.
- Runtime boundary: no Edge package was built or installed, no Cloud or Console change, no deployment; the packaged client keeps the old windows until it is rebuilt.
