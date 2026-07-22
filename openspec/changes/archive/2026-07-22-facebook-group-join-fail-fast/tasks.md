## 1. Cloud fail-fast state transition

- [x] 1.1 Replace join execution transient cooldown handling with immediate terminal `failed` membership and original-reason audit.
- [x] 1.2 Remove the obsolete minute-jitter configuration and `markTransientRetry` store surface without changing account-level pause/backoff.
- [x] 1.3 Keep manual join receipts concrete so `nav_error` says the group page failed and cannot be emitted as `no_targets`.

## 2. Focused regression coverage

- [x] 2.1 Update scheduler tests for navigation, readiness, lease, and observation failures to assert terminal failure, no cooldown, no pause, and next-target eligibility.
- [x] 2.2 Update membership-store tests to remove the transient-cooldown contract and prove terminal failed rows do not occupy the account unfinished-assignment slot.
- [x] 2.3 Add/adjust receipt coverage for direct navigation failure wording and no comment execution.
  <!-- Cloud focused regression: 138/138 pass after correcting two stale helper-name references found by the first rerun. -->

## 3. Validation and delivery

- [x] 3.1 Run focused Cloud tests, acceptance, full tests, typecheck, and diff checks; record exact results.
  <!-- Cloud: focused 138/138; acceptance 68/68; full 2,879 passed, 8 skipped, 0 failed (2,887 total); typecheck and git diff --check passed. Post-rebase focused 138/138 and typecheck also passed. -->
- [x] 3.2 Run `openspec validate facebook-group-join-fail-fast --strict`, integrate clean branches serially, and record commit SHAs.
  <!-- Cloud integrated and pushed to master at 3586c8b. Control proposal 718999e and delivery evidence b6d72ee were integrated and pushed to main. Change strict validation and all-spec strict validation passed (242/242). -->
- [x] 3.3 Deploy the clean Cloud master revision to dev only and verify service health plus database/read-model evidence that execution failures no longer create future cooldown assignments.
  <!-- DEV only: deployed Cloud master 3586c8b from the clean canonical checkout. Backup: /opt/aidcp/backups/deploy-20260722-204435-facebook-group-join-fail-fast. aidcp-cloud active since 2026-07-22 20:44:44 CST; 8787/8090/8091 listening; panel health ok; console HTTP 200; PostgreSQL SELECT 1 passed; source hashes matched; future unfinished page/network-failure cooldown rows=0; isales services remained active. OL untouched. -->
- [x] 3.4 Archive the completed OpenSpec change after verified dev delivery.
  <!-- Artifact graph complete; task checklist complete; delta sync assessed against both baseline specs. Archive command follows in the same closeout. -->
