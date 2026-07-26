## 1. Cloud policy persistence and API

- [x] 1.1 Add self-healing account comment and group publish policy storage with strict enums, default/failure fallbacks, audit fields, existence validation, and unit tests.
- [x] 1.2 Add JWT-protected panel read/write APIs and explicit response types for account and group policies, including client approval coverage counts.
- [x] 1.3 Add a customer-authorization reverse reachability query that proves an account has an enabled customer, active authorized environment, and authoritative binding.
<!-- aidcp-cloud 8719c23; additive DDL moved to migrations/0056_scoped_approval_policy.sql by 5f9d456 after concurrent 0055 allocation was detected before deployment. -->

## 2. Comment authorization resolution

- [x] 2.1 Add one Cloud resolver for effective comment approval mode with account `auto_approve_all` precedence and conservative `source_rules` fallback.
- [x] 2.2 Apply the resolver to browse, scheduled, contact, mandatory, Feishu `/comment`, and delegated comment paths without changing their risk, quota, dedupe, target recheck, or terminal receipt semantics.
- [x] 2.3 Extend auto-approval notification routing and tests so every globally exempt source emits a best-effort side-channel notice that never gates authorization.
<!-- The shared resolver is injected into CommentApprovalGate and CommentScheduler; delegated comment executors already converge on CommentScheduler. Notification is non-blocking, and missing/failed delivery neither blocks submit nor falls back to review. -->

## 3. Publish approval-card delivery

- [x] 3.1 Resolve group publish delivery after `pending_approval` persistence and suppress only eligible no-origin review cards for provably client-reachable accounts.
- [x] 3.2 Preserve source-chat cards, default dual-channel behavior, first-writer-wins approval, and named Feishu fallback reasons for policy/read/reachability failures.
- [x] 3.3 Add focused PublishExecutor and routing tests for client-only suppression, origin override, unreachable fallback, and unaffected non-approval notifications.
<!-- PublishExecutor persists the draft first, guards manual source chat locally, and treats policy/reachability failures as named send-to-Feishu fallbacks. No approval-signal contract changed. -->

## 4. Console configuration

- [x] 4.1 Add account-level global comment approval controls with direct “global exemption” presentation, server-write truth, audit metadata, and failure handling.
- [x] 4.2 Add group-level publish review delivery controls with client coverage counts, incomplete-coverage fallback warning, and corrected routing copy.
- [x] 4.3 Add focused Console API/component tests and verify production build/type checks.
<!-- aidcp-console 88a1759; focused policy tests 2/2, typecheck passed, and production build produced assets/index-C7u2iJvP.js. -->

## 5. Validation, integration, and dev deployment

- [x] 5.1 Run focused Cloud acceptance/unit tests, full Cloud tests, and Cloud typecheck; record bounded evidence and deviations.
<!-- Cloud: focused 176/176, acceptance 65/65, full 2825 passed + 8 skipped, typecheck passed. Console: focused 2/2, build/typecheck passed; a resource-contended full run had nine unrelated 5s timeouts, and all five affected files passed serially 78/78 with a 15s harness timeout. Post-rebase focused/typecheck/build and strict OpenSpec validation passed. -->
- [x] 5.2 Run strict OpenSpec validation, commit each owning repo, rebase/fast-forward integrate to default branches, and push without unrelated changes.
<!-- Cloud feature commits 8719c23 + migration-sequence follow-up 5f9d456; Console feature commit 88a1759. Both were rebased/fast-forward integrated and are contained in pushed default revisions. Control artifacts remain isolated in codex/scoped-approval-and-notification-policy until this evidence commit is fast-forwarded. -->
- [x] 5.3 Deploy clean Cloud and Console default revisions to dev after deploy precheck and backups; verify revision hashes, service/listener/health, Feishu, PostgreSQL, and Console static content.
<!-- dev 2026-07-22: precheck passed; backups /opt/aidcp/backups/{cloud,console}.20260722-155219.tar.gz; deployed pushed Cloud master 5f9d456 and Console master 476647c (the latter includes this change plus the concurrently integrated search-activity UI). aidcp-cloud.service active, NRestarts=0, listeners 8787/8090/8091 and nginx 8088 present, all three local health endpoints plus public console/API returned 200/ok, PostgreSQL select 1 passed, ApprovalPolicyStore initialized, Feishu Dev.A returned code 0 with three visible chats and WSClient onReady, and Cloud/Console content hashes matched. isales running-service count remained 4. -->
- [x] 5.4 Update this checklist with repository commit SHAs, validation, deployment evidence, and any honest remaining limitations before archiving the change.
<!-- Named-account closeout: dev account 54d7147db4c4d67999243383 (小猫) had schedule comment_mode=auto_approve but no global row; after a table-only pg_dump backup it was set to auto_approve_all with an audited writer and authenticated panel GET returned the same truth. Rollback is the exact-row DELETE from account_comment_approval_policy. Group policy rows remain empty, so all groups retain client_and_feishu until explicitly changed in Console. No real platform comment was submitted and no Edge package was built. The active change is intentionally not archived because archive-time baseline-spec sync requires a separate operator choice. -->

## 6. Follow-up: non-gating notice and direct UI

- [x] 6.1 Make every auto-approved comment path authorize immediately and send its Feishu notice best-effort; notification absence/failure must only log and must never block or fall back to review.
- [x] 6.2 Present the account option directly as “全局免审” without explanatory alerts, tooltips, or `/comment` qualifiers.
- [x] 6.3 Add focused regressions for failed/unwired notifications, run Cloud and Console validation, strictly validate OpenSpec, integrate, and deploy the clean default revisions to dev.
<!-- Follow-up 2026-07-22: aidcp-cloud 221fc4e and aidcp-console f16c1f8 were fast-forward integrated and pushed. Cloud focused comment tests passed 132/132, full tests passed 2876 with 8 gated skips, and typecheck passed; Console focused policy tests passed 2/2 and the production build passed; strict OpenSpec validation passed. dev backups: /opt/aidcp/backups/cloud.20260722-202006.tar.gz, console.20260722-202006.tar.gz, and cloud.env.20260722-202006. Deployed source/static checksums matched; aidcp-cloud.service was active with NRestarts=0; listeners 8787/8090/8091, local and public health, PostgreSQL, ApprovalPolicyStore, and four unrelated isales services were healthy. Feishu resolved Dev.A, listed three chats, and WSClient reached onReady. Account 54d7147db4c4d67999243383 remained auto_approve_all. No real platform comment was submitted; OL and Edge were untouched. -->
