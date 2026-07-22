## 1. Cloud fail-fast state transition

- [ ] 1.1 Replace join execution transient cooldown handling with immediate terminal `failed` membership and original-reason audit.
- [ ] 1.2 Remove the obsolete minute-jitter configuration and `markTransientRetry` store surface without changing account-level pause/backoff.
- [ ] 1.3 Keep manual join receipts concrete so `nav_error` says the group page failed and cannot be emitted as `no_targets`.

## 2. Focused regression coverage

- [ ] 2.1 Update scheduler tests for navigation, readiness, lease, and observation failures to assert terminal failure, no cooldown, no pause, and next-target eligibility.
- [ ] 2.2 Update membership-store tests to remove the transient-cooldown contract and prove terminal failed rows do not occupy the account unfinished-assignment slot.
- [ ] 2.3 Add/adjust receipt coverage for direct navigation failure wording and no comment execution.

## 3. Validation and delivery

- [ ] 3.1 Run focused Cloud tests, acceptance, full tests, typecheck, and diff checks; record exact results.
- [ ] 3.2 Run `openspec validate facebook-group-join-fail-fast --strict`, integrate clean branches serially, and record commit SHAs.
- [ ] 3.3 Deploy the clean Cloud master revision to dev only and verify service health plus database/read-model evidence that execution failures no longer create future cooldown assignments.
- [ ] 3.4 Archive the completed OpenSpec change after verified dev delivery.
