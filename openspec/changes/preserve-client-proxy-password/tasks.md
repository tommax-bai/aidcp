## 1. Edge proxy password data path

- [x] 1.1 Update AdsPower profile normalization so an API-returned `proxy_password` is exposed only as the in-memory `proxyConfig.proxyPassword` field while summaries remain non-sensitive.
- [x] 1.2 Update the existing-environment proxy editor to display the returned password and keep it in the form payload unless the operator changes or clears it.

## 2. Regression coverage and security boundaries

- [x] 2.1 Update normalization tests for returned and absent proxy passwords, including proof that the environment summary remains non-sensitive.
- [x] 2.2 Add renderer coverage proving the existing password is visibly prefilled and is submitted unchanged when another proxy field is edited.
- [x] 2.3 Run focused Electron proxy/renderer tests and Edge typecheck; confirm write-body allowlisting and redaction tests remain green. <!-- aidcp-edge worktree commit 32bacbd; `npx tsx --test --test-reporter=dot test/electron/ads-local-api.test.ts test/electron/ads-proxy-config.test.ts test/electron/ads-write-api.test.ts test/electron/renderer-smoke.test.ts` PASS (126); `npm run typecheck` PASS. Read-only local AdsPower probe: 30 profiles, 13 password fields, 12 non-empty; no values emitted. -->

## 3. Closeout

- [x] 3.1 Run `openspec validate preserve-client-proxy-password --strict` and record Edge commit and validation evidence in this task list. <!-- Strict validation PASS; Edge source/test worktree commit 32bacbd. -->
- [ ] 3.2 Integrate the validated control and Edge commits onto their default branches and push; do not package or deploy a desktop installer unless separately requested.
