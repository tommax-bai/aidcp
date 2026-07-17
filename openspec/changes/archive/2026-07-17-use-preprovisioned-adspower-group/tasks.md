## 1. Edge Environment Provisioning

- [x] 1.1 Resolve the exact pre-provisioned `aidcp` group for every platform and return actionable list/missing-group failures without creating a group.
  <!-- repo=aidcp-edge files=src/electron/ads-create-env-service.cjs,src/electron/ads-local-api.cjs exact group_name query + platform-neutral fixed-group resolver -->
- [x] 1.2 Preserve one bounded deleted/archived cached-id recovery by re-listing only, with no replacement-group creation.
  <!-- repo=aidcp-edge file=src/electron/ads-create-env-service.cjs stale id is excluded on one re-resolution; missing replacement stops before a second user/create -->
- [x] 1.3 Remove `group/create` and its convenience wrapper from the Electron AdsPower write client.
  <!-- repo=aidcp-edge file=src/electron/ads-write-api.cjs allowlist=user/create,user/delete,user/update -->

## 2. Verification

- [x] 2.1 Add focused service tests for all-platform fixed-group assignment, list failure, missing group, and stale-id recovery without group creation.
  <!-- validation="npx tsx --test test/electron/ads-create-env-service.test.ts test/electron/ads-write-api.test.ts test/electron/ads-local-api.test.ts" result="46/46 pass" -->
- [x] 2.2 Update write-client tests to prove `group/create` is rejected while the remaining allowlist and wrappers stay intact.
  <!-- repo=aidcp-edge files=test/electron/ads-create-env-service.test.ts,test/electron/ads-write-api.test.ts,test/electron/ads-local-api.test.ts -->
- [x] 2.3 Run focused Edge tests, the full Edge test suite, and `npm run typecheck`.
  <!-- validation="npm test -- --test-reporter=dot" result="1576/1576 pass, real E2E gated/skipped"; validation="npm run typecheck" result=pass; dependency_note="worktree node_modules symlinked to canonical checkout for module resolution" -->

## 3. Contract and Closeout

- [x] 3.1 Run `openspec validate use-preprovisioned-adspower-group --strict`.
  <!-- validation="openspec validate use-preprovisioned-adspower-group --strict" result=pass -->
- [x] 3.2 Record Edge commit, validation, integration, and deviations in this task file; commit and push the control artifacts.
  <!-- repo=aidcp-edge commit=c86bd94 integration=origin/master validations="focused 46/46; full 1576/1576; typecheck pass" deviations=none deployment="not applicable: desktop source change; installer packaging was not requested" -->
