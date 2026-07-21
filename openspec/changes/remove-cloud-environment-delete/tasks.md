## 1. Cloud write-surface removal

- [x] 1.1 Remove the Cloud AdsPower direct client and all runtime reads of the AdsPower API Key while preserving unrelated credential providers
- [x] 1.2 Remove the internal Panel environment deletion route/orchestration so old requests fail with zero AdsPower, audit, or lifecycle writes
- [x] 1.3 Remove AdsPower from the platform credential registry and cover GET omission plus rejected legacy PUT behavior with focused tests
- [x] 1.4 Update environment deletion tests to prove environment/account reads and historical lifecycle projections remain available without any deletion write surface

## 2. Console read-only environment management

- [x] 2.1 Remove environment delete buttons, confirmation/progress/retry state, deletion API calls, and direct-delete copy while preserving filters, history, and account deep links
- [x] 2.2 Remove AdsPower API Key cards, browser-service grouping, types, and immediate-delete-effect copy from platform settings
- [x] 2.3 Update focused EnvironmentsPage and SettingsPage tests to prove no deletion action or AdsPower credential is rendered while unrelated reads and credential editing still work

## 3. Edge boundary and validation

- [x] 3.1 Confirm the retired remote maintenance poller remains absent and the desktop local two-step `user/delete` path remains covered without changing Edge runtime code
- [x] 3.2 Run focused Cloud/Console tests, Cloud/Console typechecks, Console production build, and proportionate full/acceptance gates for the deletion safety boundary
  <!-- Validation: Cloud focused 113 passed; acceptance 64 passed; post-rebase full 2766 passed, 8 skipped; typecheck passed. Console focused 7 passed; isolated two-worker full 227 passed, 1 skipped; typecheck and production build passed. A forced single-thread Console run was discarded because shared DOM globals leaked across unrelated files. -->
- [x] 3.3 Run `openspec validate remove-cloud-environment-delete --strict` and record validation evidence plus the no-real-delete boundary
  <!-- Validation: openspec validate remove-cloud-environment-delete --strict passed. No real environment or AdsPower profile was deleted during source validation. -->

## 4. Integration and dev delivery

- [x] 4.1 Commit, rebase, fast-forward integrate, and push Cloud, Console, and control-repo changes without force while preserving unrelated work
  <!-- Integration: Cloud a8e964e and Console 88cc565 were rebased/fast-forward pushed to origin/master and synced to clean canonical checkouts. Control artifacts are committed and pushed by this task update. No force operation was used; unrelated worktrees and canonical output/tmp files were preserved. -->
- [x] 4.2 Run the dev deployment target check, deploy Cloud before Console from clean canonical default checkouts, and verify health/listeners plus normal environment/settings reads
  <!-- Dev 121.89.85.150: deploy-target check passed. Backups: cloud.bak.20260721-112953Z.tar.gz, cloud/.env.bak.20260721-112953Z, console.bak.20260721-112953Z.tar.gz. Cloud was deployed first and only aidcp-cloud.service was restarted; active with NRestarts=0, 8787/8090/8091 listening, both health routes 200, PostgreSQL query succeeded, Feishu WS onReady, and all four isales services remained active. Console index and asset returned 200 and matched local SHA-256. -->
- [x] 4.3 Verify the former deletion route has zero write effects, the served environment page has no delete action, the served settings page has no AdsPower Key, and no real AdsPower profile was touched
  <!-- Authenticated dev probe: environments 200 with 40 assets; config 200 with no adspower/api_key entry; malformed sentinel POST to the former deletion path returned 404; client_environment_deletion_requests stayed 4 -> 4. Served asset index-CBbxZB64.js contains the read-only/stopped-history copy and contains no AdsPower API Key, confirmation field, or /deletion request string. No existing envKey was submitted and no real AdsPower profile was touched. The four retired deployed source/test files were removed only after backup and are recoverable from the cloud backup. -->
