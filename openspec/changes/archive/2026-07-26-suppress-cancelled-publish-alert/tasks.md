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
- [x] 4.3 Record commits, integration, validation, and deployment evidence, then run strict OpenSpec validation.

<!--
Implementation: aidcp-cloud commit 150017ccae44573ca5a39699efd64ae6ba8ffe37; fast-forwarded and pushed to master. OpenSpec artifacts fast-forwarded and pushed to aidcp main at c7f8f44bb96d9f12733b46b9106b38a30cab013a.
Validation: after rebasing to the latest defaults, focused delegated/store/notification tests 53 passed; npm run test:acceptance 64 passed with the deployment-gated E2E case skipped; full Cloud test suite passed; npm run typecheck passed; git diff --check passed; openspec validate suppress-cancelled-publish-alert --strict passed.
Deployment: deployed aidcp-cloud master 150017ccae44573ca5a39699efd64ae6ba8ffe37 to dev only on 2026-07-21. Backup: /opt/aidcp/backups/cloud-before-150017c-20260721T040637Z.tar.gz. The six changed runtime files matched local SHA-256 before restart. aidcp-cloud.service became active at 2026-07-21 12:07:38 CST; ports 8787 and 8090 listened; local and nginx /api/health returned {"ok":true}; PostgreSQL select 1 passed; no service error-priority logs were present. Dev AIDCP_FEISHU_WS_ENABLED=false, so no Feishu connection was expected. Runtime module smoke returned cancelled_publish_alert=none. No migration, console deploy, OL deploy, or unrelated service operation was performed.
-->
