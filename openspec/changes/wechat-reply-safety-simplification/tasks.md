## 1. Workspace and contract readiness

- [x] 1.1 Create isolated Cloud, Edge, and Console worktrees on matching `codex/wechat-reply-safety-simplification` branches and install a physical dependency tree in each worktree.
  <!-- Worktrees created from current origin/master after task-preflight and fetch. Cloud/Edge: npm ci --prefer-offline. Console has no lockfile, so npm ci is mechanically unavailable; used npm install --prefer-offline --package-lock=false to create an isolated physical tree without adding a lockfile. No dependency links. -->
- [x] 1.2 Validate the proposal, design, and four spec deltas before touching business code.
  <!-- openspec validate wechat-reply-safety-simplification --strict: passed before business-code edits. -->

## 2. Cloud safety admission simplification

- [x] 2.1 Replace the zero reply-policy defaults with the conservative positive rate-limit preset while preserving default-off generation, sending, channels, and automation.
- [x] 2.2 Make video-channel send admission ignore only `RiskController` `quota:*` denials while retaining controller absence, risk-state, unknown-reason, interaction-rate, CAS, idempotency, and result gates for both auto and manual paths.
- [x] 2.3 Apply the new-login cooldown only to auto sends and remove platform-auth admission from Cloud-only generate, edit, and approve operations.
- [x] 2.4 Update confirmed-send risk accounting labels so generic quota membership is not presented as the video-channel interaction policy result.
- [x] 2.5 Add focused Cloud regression tests for defaults, manual/auto cooldown, quota-vs-state admission, offline draft actions, and confirmed accounting.
  <!-- Cloud rebased commit c373430: focused interaction tests 27/27 and latest group-scope regression tests 22/22 passed after rebase; full test invocation before rebase completed successfully (2604 passed, 8 skipped, 0 failed); post-rebase typecheck passed. -->

## 3. Edge combined review and send

- [x] 3.1 Replace the approval-required primary action with a save-if-needed, approve, then send sequence that uses the approved job version and stops honestly on either failure.
- [x] 3.2 Preserve direct send retry from `approved` and add renderer tests for full success plus approve-success/send-failure state and copy.
  <!-- Edge rebased commit 2fc75c3: interaction workspace focused suite 48/48 and typecheck passed after rebase; no installer was built. -->

## 4. Console rate-limit presets

- [x] 4.1 Add pure conservative/standard/custom preset projection helpers with exact-value matching and no implicit mutation.
- [x] 4.2 Render preset-first safety controls, summaries, and collapsed advanced numeric fields while keeping the existing policy draft save/publish boundary.
- [x] 4.3 Add focused Console tests for preset mapping, historical custom/zero values, deliberate preset application, and advanced true-value rendering.
  <!-- Console rebased commit 16ad709: preset helper and reply-settings focused suites 39/39 plus production build passed after rebase; selecting custom was verified to produce no PUT. -->

## 5. Validation and integration

- [x] 5.1 Run Cloud focused interaction tests, acceptance/full tests required by the risk area, and typecheck.
  <!-- Cloud evidence: focused 27/27; acceptance 59/59; full 2604 passed, 8 skipped, 0 failed; typecheck passed. -->
- [x] 5.2 Run Edge focused Electron tests, acceptance/full tests required by the write path, and typecheck without building an installer.
  <!-- Edge evidence: focused renderer 48/48; acceptance 26 passed, 1 gated E2E skipped; full 1922/1922; typecheck passed; no installer built. -->
- [x] 5.3 Run Console focused tests, full tests, typecheck, and production build.
  <!-- Console evidence: focused 38/38; full 193 passed, 1 skipped, 0 failed; typecheck and Vite production build passed. Existing jsdom getComputedStyle and chunk-size warnings remain non-fatal. -->
- [x] 5.4 Update task evidence and run `openspec validate wechat-reply-safety-simplification --strict`.
  <!-- openspec validate wechat-reply-safety-simplification --strict: passed after implementation and validation. -->
- [ ] 5.5 Commit each repository with explicit path scope, rebase onto current defaults, serially fast-forward/push Cloud, Edge, Console, and control changes, and preserve unrelated canonical WIP.

## 6. Dev rollout and closeout

- [ ] 6.1 Read the deployment guide, run `scripts/deploy-target dev --check`, deploy Cloud and Console only from clean canonical default branches, and avoid unrelated `isales` services.
- [ ] 6.2 Verify dev service/listeners/health, Console assets, Feishu, PostgreSQL, and honest video-channel read/write-gate state without claiming a real platform send unless one is actually confirmed.
- [ ] 6.3 Record commits, validations, deployment evidence, deviations, and any remaining real-machine acceptance item; finish strict validation and archive only when every required task is complete.
