## 1. Protocol and Cloud gates

- [x] 1.1 Add the negotiated `interaction_test_data_reset_v1` capability and `test_reset` sync reason across Cloud/Edge types, validation, fixtures, and protocol documentation.
  <!-- repos=aidcp-cloud:d231be1,aidcp-edge:22c5be8; control fixtures/docs in this change; WS/customer JSON Schema validation passed -->
- [x] 1.2 Add Cloud's explicit dev-plus-feature-flag exposure and pre-delete sync readiness gate with focused tests.
  <!-- repo=aidcp-cloud commit=d231be1; double-gate and old/offline Edge pre-delete tests passed -->

## 2. Cloud reset transaction and customer API

- [x] 2.1 Implement the channel-scoped Cloud reset transaction, send-history/write-pause gates, preserved-state invariants, body-free audit, and integration tests.
  <!-- repo=aidcp-cloud commit=d231be1; focused tests passed; PostgreSQL integration case added but skipped locally because AIDCP_INTERACTION_TEST_DATABASE_URL is intentionally not configured; no shared/real DB was truncated -->
- [x] 2.2 Add the strict idempotent customer reset route, partial-delivery response handling, list exposure flag, and customer authorization/API tests.
  <!-- repo=aidcp-cloud commit=d231be1; customer API/idempotency/partial-delivery tests passed -->

## 3. Edge replay reset and client surface

- [x] 3.1 Implement channel-scoped Edge checkpoint/thread-source reset inside the existing sync lock and verify replay plus other-state preservation.
  <!-- repo=aidcp-edge commit=22c5be8; state persistence, channel isolation, strict reason validation and lock ordering tests passed -->
- [x] 3.2 Add named Electron IPC/preload methods and the dev-only InteractionWorkspace reset surface with channel-specific confirmation and honest result states.
  <!-- repo=aidcp-edge commit=22c5be8; client code only, no installer built or published -->
- [x] 3.3 Add focused Electron tests covering disabled visibility, no-call confirmation mismatch, accepted refresh, safety rejection, and partial completion.
  <!-- repo=aidcp-edge commit=22c5be8; interaction workspace/security focused suite passed -->

## 4. Validation and delivery

- [x] 4.1 Run Cloud and Edge focused suites, required acceptance/full suites, typecheck/build, and strict OpenSpec validation; record concise evidence.
  <!-- Cloud focused 10/10, acceptance 55/55, full exit 0, typecheck/build passed; Edge focused 69/69, acceptance 23/23, full exit 0, typecheck/build:dist passed; OpenSpec strict and both JSON schemas passed -->
- [ ] 4.2 Rebase and fast-forward the validated commits to the latest default branches, push Cloud/Edge/control, and leave unrelated canonical checkout changes untouched.
- [ ] 4.3 Deploy Cloud to `dev` only after deployment preflight, enable both explicit dev reset gates, and verify health plus non-destructive API exposure without resetting the current real account.
