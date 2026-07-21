## 1. Cloud environment identity and durable claim

- [x] 1.1 Expose welcomed online account identities with strictly parsed `ads-<envKey>` values and keep the existing account-id projection compatible.
- [x] 1.2 Add the latest-hour-cell PostgreSQL claim table and atomic automatic-post claim API, including focused store tests.
- [x] 1.3 Make the content scheduler consume online identities, require the server-stamped `dev|ol` target, and claim the post cell before triggering; cover restart/multi-process idempotency and fail-closed identity cases.

<!-- Cloud eb7b8b8: connection identity projection, deployment target parser, content_schedule_hour_claims, scheduler claim/binding, and focused coverage. -->

## 2. Publish attribution and target isolation

- [x] 2.1 Carry immutable scheduled execution attribution through trigger input and persist it in publish metadata, failing closed if an automatic draft cannot record it.
- [x] 2.2 Filter approval scans by the local target, repeat the target check before direct dispatch, and require the frozen `envKey` at Edge resolution while preserving legacy and manual draft behavior.
- [x] 2.3 Add focused publish scheduler, executor, metadata-store, and dispatcher tests for attribution persistence and cross-target/environment skips.

<!-- Cloud eb7b8b8: scheduleExecution metadata, needs_review-before-attribution ordering, target-filtered recovery, and exact ads-<envKey> dispatch binding. -->

## 3. Validation and delivery

- [x] 3.1 Run Cloud focused tests, publish safety acceptance suites, the full test suite, and typecheck; resolve only failures attributable to this change.
- [x] 3.2 Record Cloud commits and validation evidence in this task list, then run `openspec validate bind-auto-publish-to-connected-environment --strict`.
- [ ] 3.3 Rebase and fast-forward integrate the control and Cloud branches into their latest defaults, push both defaults, and keep canonical checkouts clean.
- [ ] 3.4 Back up and deploy Cloud to dev, then verify the service, listener, health, PostgreSQL, deployment-target handling, and unchanged unrelated services; record the deployment evidence and any scope deviation.

<!-- Validation on Cloud eb7b8b8: focused 151/151; acceptance 65/65; full 2778 passed, 0 failed, 8 gated skips; npm run typecheck passed. OpenSpec strict validation passed. -->
