## 1. Contract and fixtures

- [x] 1.1 Extend the customer-auth v1 schema with read-controls request/response and replyConfig projection while keeping internal write fields inaccessible.
- [x] 1.2 Add synthetic missing/draft/published and read-control fixtures, validate them against JSON Schema, and run strict OpenSpec validation.

## 2. Cloud customer and internal APIs

- [x] 2.1 Implement env-scoped customer read-controls CAS update that preserves every write field and reuses the existing Edge runtime-control delivery path.
- [x] 2.2 Add fail-closed replyConfig readiness projection to interaction list/detail and read-controls responses.
- [x] 2.3 Implement explicit permission-gated reply-config initialization as safe draft v1 with no publish, template, rule, send, auto-send or runtime-control side effects.
- [x] 2.4 Cover ownership, body allowlist, CAS races, write-field preservation, delivery truth, projection states and initialization with Cloud unit/acceptance tests.

## 3. Electron interaction self-service

- [x] 3.1 Add named preload/main IPC and request validation for customer read-controls updates plus a scoped system-notification bridge.
- [x] 3.2 Render the interaction settings card with total/comment/DM read switches and stored/applied/effective status, including honest disabled/empty/refresh copy.
- [x] 3.3 Split common mutation gates from channel send capability so non-send actions remain usable and every disabled action has a visible reason.
- [x] 3.4 Render reply-config missing/draft/published guidance without calling internal APIs.
- [x] 3.5 Render unread markers and env-scoped badges, establish a no-notify initial baseline, and notify each later unread messageId at most once.
- [x] 3.6 Cover switches, env scope, version conflicts, status matrix, action gate parity and notification dedupe with Electron tests.

## 4. Console configuration initialization

- [x] 4.1 Add the reply-config initialize API client and distinguish missing config from permission/general load errors.
- [x] 4.2 Render and test the explicit safe-draft initialization flow, truthful post-init draft/published state and concurrent conflict recovery.

## 5. Integration and delivery

- [x] 5.1 Run Cloud tests/acceptance/typecheck, Edge tests/acceptance/typecheck, Console tests/build, strict OpenSpec and contract fixture validation.
  <!-- Validation: Cloud acceptance 54 passed + 1 gated skip, full suite 2306 passed + 6 skipped, typecheck passed; Edge acceptance 22 passed, full suite 1545 passed, final interaction/IPC suite 20 passed after convergence-poll review, typecheck passed; Console 151 passed + 1 skipped and production build passed. Both JSON Schema fixture sets and `openspec validate wechat-channels-client-self-service --strict` passed. -->
- [x] 5.2 Commit and push each sibling default branch through isolated worktrees, update this task evidence with SHAs and deviations, then commit and push Control.
  <!-- Landed and pushed to default branches: aidcp-cloud `47e87c2`, aidcp-edge `5ce88ae`, aidcp-console `340d93f`. Cloud and Edge feature commits were rebased onto the latest remote master without conflict before the non-force fast-forward pushes. No behavior deviation from the proposal. -->
- [x] 5.3 Deploy committed Cloud and Console artifacts to dev through the documented backup/restart/healthcheck path; do not build an Edge installer or perform real platform writes.
  <!-- DEV deploy 2026-07-16: target preflight passed; backups `/opt/aidcp/cloud.bak.20260716-205849.tar.gz`, `/opt/aidcp/cloud/.env.bak.20260716-205849`, and `/opt/aidcp/console.bak.20260716-205849.tar.gz`; exact local/remote SHA-256 matched before restart. `aidcp-cloud.service` active; 8787/8090/8091/8088 listening; panel/customer/capi health passed; PostgreSQL `select 1` passed; Feishu `WSClient onReady`; Console served the new bundle; no fatal startup errors. Edge source was pushed only: no installer build and no real platform write validation. -->
