## 1. Console implementation

- [x] 1.1 Replace the account table platform addon and video-only runtime prop with one optional account configuration render prop.
- [x] 1.2 Render the unified “配置” column with explicit empty state while keeping read-only table consumers unchanged.
- [x] 1.3 Route Facebook configuration and Video Channels runtime control into the unified column from `AccountsPage`.

## 2. Regression coverage

- [x] 2.1 Update account-page tests to verify the “配置” header, platform-only cells, per-platform entry placement, and unsupported-platform empty state.
- [x] 2.2 Run focused Console tests plus full test, typecheck, and build validation.
  <!-- Validation: focused `WechatChannelsReplySettings.test.tsx` 44/44 passed; full single-worker suite 37 files, 255 passed, 1 skipped; `npm run typecheck` passed; `npm run build` produced `dist/assets/index-Bv4dvn6e.js` and `index-6m7oiVLn.css`. Parallel full-suite attempt timed out under contention and was superseded by the clean serial run. -->
- [x] 2.3 Run `openspec validate unify-account-configuration-entry --strict` and record validation evidence.
  <!-- `openspec validate unify-account-configuration-entry --strict`: valid on 2026-07-22. -->

## 3. Integration and delivery

- [x] 3.1 Commit the Console implementation and OpenSpec artifacts with scoped pathspecs.
  <!-- Console `e622f56`; control OpenSpec `880e20f`. Only the three Console source/test files and this change directory were staged. -->
- [x] 3.2 Rebase and fast-forward integrate the Console change to `master`, then push without force.
  <!-- `origin/master` fast-forwarded from `f16c1f8` to Console `e622f56`; canonical Console checkout synced clean. `scripts/land-change` correctly stopped on parallel-only timeout noise, so integration used the documented manual equivalent after the green 255-test single-worker suite and explicit ancestor check. -->
- [x] 3.3 Deploy the Console static build to dev from the clean canonical checkout with backup and verify hashes, HTTP health, and the account-page UI.
  <!-- Target `dev` passed `scripts/deploy-target dev --check`. Clean canonical Console `master@e622f56` built assets `index-Zu-xxYLH.js` and `index-6m7oiVLn.css`; backup `/opt/aidcp/backups/console.bak.20260722-124636Z.tar.gz` was created before rsync without `--delete`. Remote SHA-256 matched local for index/JS/CSS; `/`, `/accounts`, JS, CSS, and `/api/health` returned 200/ok. Cloud stayed active with `NRestarts=0`; 8787/8090/8088 listened; PostgreSQL returned 1; four isales services stayed active. In-app browser reached the normal `/login` guard but had no authenticated session, so post-login visual inspection was not claimed; focused DOM tests are the UI placement evidence. -->
- [x] 3.4 Update this task log with repo commit, validation, deployment, and deviation evidence.
  <!-- Delivery summary: Console `e622f56` fast-forwarded to `origin/master`; focused 44/44, full single-worker 255 passed + 1 skipped, typecheck/build and strict OpenSpec validation passed. The repo has no committed lockfile, so worktree setup used `npm install --prefer-offline --no-package-lock` after the required `npm ci` failed with EUSAGE. Default parallel Vitest attempts showed unrelated 5-second timeouts; the clean single-worker full suite is the authoritative green run. No Cloud/Edge/API/data migration and no Edge installer. -->
