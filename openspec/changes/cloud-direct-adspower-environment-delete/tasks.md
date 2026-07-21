## 1. Cloud AdsPower direct client and credentials

- [x] 1.1 Add a narrow Cloud AdsPower client for single-profile delete and authoritative existence checks with server-only base, timeout, throttling, bearer auth, and redacted errors
- [x] 1.2 Register the encrypted AdsPower API Key credential with env fallback, masked Panel metadata, and per-request hot runtime reads
- [x] 1.3 Add focused unit tests for allowed endpoints, fixed request bodies, credential handling, response validation, throttling, timeouts, and redaction

## 2. Cloud environment deletion orchestration

- [x] 2.1 Replace waiting-Edge request creation with a direct begin/complete/fail state transition that serializes one envKey and preserves scheduling/soft-delete audit boundaries
- [x] 2.2 Change the internal Panel deletion endpoint to call AdsPower directly, return deleted only after Cloud persistence, and map configuration/transport/business/unknown failures honestly
- [x] 2.3 Retire the Cloud customer-auth maintenance poll/claim/result execution surface while preserving non-destructive schema compatibility for historical rows
- [x] 2.4 Cover direct success, failure, concurrent/idempotent retry, authoritative already-missing proof, customer-token isolation, and account/environment projection behavior with focused tests

## 3. Console settings and environment UX

- [x] 3.1 Extend mirrored credential types and SettingsPage grouping/help text so AdsPower Key is masked, independently editable, and described as effective on the next deletion without restart
- [x] 3.2 Replace waiting-client deletion copy with direct in-progress/success/failure feedback, refresh on terminal success, and give legacy waiting_edge rows an honest retry label
- [x] 3.3 Update focused SettingsPage and EnvironmentsPage tests for credential isolation, non-disclosure, immediate-effect copy, exact confirmation, success, and failure

## 4. Edge legacy path retirement

- [x] 4.1 Remove startup of the remote environment-maintenance poller/outbox so Edge no longer executes management-console deletion responsibilities
- [x] 4.2 Remove or update focused Edge tests and comments while preserving local desktop two-step delete behavior and ordinary customer-auth HTTP data reads

## 5. Validation and delivery

- [x] 5.1 Run focused Cloud/Console/Edge tests and typechecks, then required acceptance/full suites for the touched environment-deletion safety path
  <!-- Cloud: acceptance 64 passed with 1 gated skip, land full 2782 passed with 8 skips, focused direct-delete tests passed, and typecheck passed. Console: focused 15/15, production build and typecheck passed; shared-load full runs hit unrelated 5s UI-test timing failures, while the deciding single-worker full rerun passed 228 with 1 skip. Edge: acceptance 28/28, land full 2156/2156, focused deletion-path tests and typecheck passed. -->
- [x] 5.2 Run `openspec validate cloud-direct-adspower-environment-delete --strict` and record repository commits, validation evidence, deviations, and the no-real-profile test boundary in this task file
  <!-- Strict validation passed. Final default-branch commits: aidcp-cloud d108a69, aidcp-console 7aa3f39, aidcp-edge 2704ff2. No real AdsPower profile was queried for deletion or deleted; automated coverage uses fakes and the live route probe used a guaranteed-nonexistent sentinel while the key was absent. -->
- [x] 5.3 Commit each repository worktree, rebase and serially fast-forward integrate/push Cloud, Console, and Edge default branches without force
  <!-- Cloud and Edge landed through scripts/land-change --yes. Console's fixed-concurrency land gate repeatedly hit unrelated shared-load timeouts; after a complete single-worker 228/228 pass plus typecheck, the exact documented fetch/rebase/ff-push/sync/cleanup steps were executed manually. All three origin default branches advanced without force. -->
- [x] 5.4 Run the dev deployment target check, deploy Cloud/Console from clean canonical default checkouts with backup, and verify service/listeners/health/settings/environment UI plus the configured AdsPower API reachability truth
  <!-- dev 2026-07-21: deploy-target check passed; backups cloud/console-20260721-183146.tgz; deployed from clean d108a69/7aa3f39 checkouts; local/served source hashes match; service active; 8787/8090/8091 listening; health and /environments HTTP 200; served asset index-CHmTy2Bt.js; authenticated settings and environments APIs 200 with 37 rows. AdsPower credential is editable but currently unconfigured, and the effective default http://local.adspower.net:50325 is not reachable from ECS. A non-existent route probe returned 503 adspower_key_missing and created zero deletion rows. No Edge installer was built. -->
