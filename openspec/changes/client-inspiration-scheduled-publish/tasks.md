## 1. Cloud pending-draft customer reads

- [x] 1.1 Add account/status-scoped pending-draft list/detail projections with consistent pagination, publish-plan parsing, and minimum-disclosure DTOs.
  <!-- aidcp-cloud 7088b96; focused store and customer-auth tests passed; deployment recorded in 4.3. -->
- [x] 1.2 Add customer-auth `/publish-drafts` list/detail routes using persistent env binding and stable unknown/conflict/not-found behavior.
  <!-- aidcp-cloud 7088b96; client-auth route suite passed, including persistent binding and 404 non-disclosure. -->
- [x] 1.3 Add Cloud tests for multi-draft pagination, account/status isolation, minimum disclosure, offline reads, binding failures, and detail 404 non-disclosure.
  <!-- aidcp-cloud 7088b96; test/client-auth-server.test.ts and pending-list store tests passed. -->

## 2. Cloud schedule-aware client approval

- [x] 2.1 Extend `PublishApprovalActionPayload` with optional publish mode/time while preserving old-client current-plan behavior and rejection semantics.
  <!-- aidcp-cloud 7088b96 + aidcp-edge 116fd0f; protocol blocks compared identical and AC-PROTO-19 passed in both repos. -->
- [x] 2.2 Validate and preflight the requested plan, CAS-edit the same pending draft only when the plan changes, use its write-after version, and bind approval to that version before dispatch.
  <!-- aidcp-cloud 7088b96; schedule-aware approval unit suite passed with preflight-before-CAS and write-after version assertions. -->
- [x] 2.3 Add focused tests for scheduled/immediate changes, unchanged-plan no-op, version/time/account/status failures, cancel no-edit, old payload compatibility, and no partial approval.
  <!-- aidcp-cloud 7088b96; 10 focused approval cases passed. -->

## 3. Edge multi-draft review workspace

- [x] 3.1 Add narrow preload/main IPC methods for pending-draft list/detail reads with fixed customer-auth paths, pagination/id validation, main-owned envKey/token, and security tests.
  <!-- aidcp-edge 116fd0f; content-workspace IPC security tests passed. -->
- [x] 3.2 Upgrade the draft review page to a paginated inspiration-style card list plus detail view, with single-item fast path, honest empty/error/fallback states, navigation restoration, handled-item filtering, and account-switch stale-response invalidation.
  <!-- aidcp-edge 116fd0f; companion jsdom coverage passed for multi-item cards, single fallback, continuation, and stale account responses. -->
- [x] 3.3 Add immediate/scheduled controls at the approval position with explicit Asia/Shanghai parsing, local range feedback, cancel independence, busy/error behavior, and multi-item continuation after success.
  <!-- aidcp-edge 116fd0f; pure timezone/range tests and renderer interaction tests passed. -->
- [x] 3.4 Extend Edge approval IPC validation/payload forwarding and add renderer tests for multi-draft reachability, schedule submissions, invalid-time blocking, failure retention, and old Cloud/single-preview fallback.
  <!-- aidcp-edge 116fd0f; IPC source-contract, companion UI, and legacy fallback tests passed. -->

## 4. Protocol, validation, and integration

- [x] 4.1 Synchronize Cloud/Edge `PublishApprovalActionPayload` and result version fields, update protocol contract tests and `docs/protocol.md`, and verify the protocol blocks remain identical.
  <!-- aidcp-cloud 7088b96 + aidcp-edge 116fd0f + aidcp control commit containing this task; Compare-Object returned no protocol diff. -->
- [x] 4.2 Run focused Cloud/Edge tests, acceptance suites, full suites, typechecks, and any relevant syntax checks without packaging Electron.
  <!-- Cloud: 2507 pass/8 gated skip; Edge: 1789 pass; both acceptance and typecheck pass; node --check pass. Windows deviation: quoted Cloud npm test discovers 0, so full suite ran via npx tsx --test test/**/*.test.ts. No Electron package built. -->
- [ ] 4.3 Run `openspec validate client-inspiration-scheduled-publish --strict`, record commit SHAs/validation evidence, integrate and push with repository helpers, deploy Cloud only from the eligible canonical default checkout, and do not build an Electron installer without explicit user request.
