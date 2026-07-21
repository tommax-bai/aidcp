## 1. Persist explicit rejection evidence

- [x] 1.1 Extend publish metadata with a durable explicit-user-rejection decision.
- [x] 1.2 Make `rejectPendingApproval` atomically persist the decision while transitioning the pending draft.
- [x] 1.3 Expose only the normalized user-rejection fact in delegated candidate snapshots.

## 2. Reconcile cancellation honestly

- [x] 2.1 Add a delegated execution cancellation result and settle it as not dispatched with honest task progress.
- [x] 2.2 Map only evidenced user-rejected `needs_review` candidates to cancellation; preserve failure for unproven states.
- [x] 2.3 Suppress delegated failure and partial-completion receipts for the explicit user-cancellation outcome.

## 3. Regression coverage

- [x] 3.1 Cover atomic rejection metadata persistence and candidate snapshot propagation.
- [x] 3.2 Cover zero-success and partial-success cancellation settlement plus unproven `needs_review` failure behavior.
- [x] 3.3 Cover notification silence for explicit cancellation without weakening real publish-failure alerts.

## 4. Validation and closeout

- [x] 4.1 Run focused delegated publish/store/notification tests.
- [x] 4.2 Run Cloud publish acceptance tests, full test suite, and typecheck.
- [x] 4.3 Record commits and validation evidence, then run strict OpenSpec validation without merging or deploying.

<!--
Implementation: aidcp-cloud commit 150017ccae44573ca5a39699efd64ae6ba8ffe37.
Validation: focused delegated/store/notification tests 53 passed; npm run test:acceptance 64 passed with the deployment-gated E2E case skipped; full Cloud test suite passed; npm run typecheck passed; git diff --check passed; openspec validate suppress-cancelled-publish-alert --strict passed.
Deployment: not run per user instruction. Integration: not merged to master per user instruction.
-->
