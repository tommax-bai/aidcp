## 1. Edge Desktop Recovery

- [x] 1.1 Add a recoverable AdsPower dedicated-group failure detector for `group is deleted or archived`.
  <!-- repo=aidcp-edge commit=16294ba added isDeletedOrArchivedGroupError in ads-create-env-service.cjs -->
- [x] 1.2 Clear the cached dedicated group id and retry creation once after that specific failure.
  <!-- repo=aidcp-edge commit=16294ba createEnvironmentWithGroupRecovery clears cached group id and skips the failed id on the one retry -->
- [x] 1.3 Preserve honest failure behavior for non-group errors and repeated group failures.
  <!-- repo=aidcp-edge commit=16294ba non-group create failures return without retry; retry result is surfaced honestly -->

## 2. Verification

- [x] 2.1 Add focused tests for retrying with a newly resolved group and not retrying unrelated failures.
  <!-- repo=aidcp-edge commit=16294ba added ads-create-env-service.test.ts coverage for recovery and no-retry paths -->
- [x] 2.2 Run focused edge tests for the touched Electron modules.
  <!-- repo=aidcp-edge validation="npm test -- --test-name-pattern='ads-create-env-service|ads-create-flow|ads-write-api|ads-local-api' passed; command traversed full suite, 631/631 pass; npm run typecheck passed" -->
- [x] 2.3 Run `openspec validate recover-adspower-archived-group --strict`.
  <!-- repo=aidcp validation="openspec validate recover-adspower-archived-group --strict passed" -->
