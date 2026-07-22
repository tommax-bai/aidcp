## 1. Contract and platform projection

- [x] 1.1 Add search to the synchronized Cloud/Edge `UI_DAILY_USAGE_ACTIONS` contract in the user-facing order after view
- [x] 1.2 Add a platform-registry search declaration consumed by usage projection: XHS and Facebook supported, WeChat Channels unsupported, unknown fail-safe absent
- [x] 1.3 Add Cloud projection tests proving FB/XHS include search while WeChat/unknown omit it without `0/0` resurrection

## 2. Cloud daily-usage construction

- [x] 2.1 Project confirmed search risk totals and effective quotas through daily aliases and minute/hour/day windows
- [x] 2.2 Map current-session `searches` totals and limits to the client `search` key without borrowing day totals
- [x] 2.3 Extend customer-overview and compatible snapshot tests for offline HTTP truth, zero-but-supplied search, saturation, and old-peer compatibility

## 3. Edge client rendering

- [x] 3.1 Add search to the CJS daily-usage sanitizer and preserve supplied-zero versus absent semantics across aliases and all windows
- [x] 3.2 Add the static Search KPI, renderer fields, usage item, ordering, quota bars, window rows, and completion/resting label support
- [x] 3.3 Extend UI-event, daily-usage, companion UI, and renderer smoke tests for FB/XHS visibility, absent old payloads, per-window values, and stopped-engine HTTP cache retention

## 4. Validation and delivery

- [x] 4.1 Run focused Cloud tests, the required full Cloud suite, and `npm run typecheck`; record exact evidence
  <!-- Cloud: final focused daily-usage/platform/customer/snapshot 103 pass, 0 fail; final full `npm test` 2870 pass, 8 skip, 0 fail (118.312s); final `npm run typecheck` and `git diff --check` exit 0. -->
- [x] 4.2 Run focused Edge tests, the required full Edge suite, and `npm run typecheck`; do not build a desktop installer
  <!-- Edge: focused daily-usage/UI-event/companion/smoke 186 pass, 0 fail; first full run exposed one unrelated 500ms native-engine startup race, isolated file then passed 9/9; clean standard full rerun 2240 pass, 0 fail (114.412s); final `npm run typecheck` and `git diff --check` exit 0. No installer was built. -->
- [x] 4.3 Run `openspec validate show-search-in-client-daily-progress --strict`, protocol drift checks, and diff checks
  <!-- Strict validation and all diff checks pass. The changed Cloud/Edge UI_DAILY_USAGE_ACTIONS slices are byte-identical; whole protocol files retain pre-existing unrelated comment/order/text drift and were not broadened into this change. -->
- [x] 4.4 Commit feature branches with validation evidence, rebase onto current defaults, rerun affected checks, fast-forward integrate, and push Cloud/Edge defaults plus control main without overwriting unrelated changes
  <!-- Integrated/pushed: aidcp-cloud master 0c746d05d7aae511c99190de62ea75e8578e63b9; aidcp-edge master 96d5399a5cf4244507713f609d35882cd6bb5ffe; control proposal main b90cf5859960e3d1d3f2043fca29754b5c036888. Post-rebase focused checks: Cloud 103 pass + typecheck; Edge 186 pass + typecheck. Canonical control untracked changes and concurrent AGENTS.md edit were preserved. -->

## 5. Dev deployment and closeout

- [x] 5.1 Read deployment guidance, run `scripts/deploy-target dev --check`, back up dev Cloud/env, deploy the clean integrated Cloud revision, and verify hashes, service, listeners, health, PostgreSQL, Feishu, logs, and unrelated services
  <!-- DEV only. Backups: /opt/aidcp/backups/cloud-20260722-203114.tar.gz and cloud-env-20260722-203114. Deployed clean Cloud master 0c746d0; five affected runtime hashes matched. aidcp-cloud active, NRestarts=0, 8787/8090/8091 listening, internal/public panel+client health ok, PostgreSQL SELECT 1 ok, Feishu Dev.A token/bot code 0 and WS onReady, no post-restart warning/error, all four isales services active. No dependency or DB migration was needed. -->
- [x] 5.2 Perform a bounded authenticated dev projection check for FB/XHS/search when safe data is available; otherwise record the exact runtime evidence boundary without fabricating desktop-package proof
  <!-- Authenticated localhost customer API probe used enabled owned/bound rows without printing identifiers, issued 60s tokens, and logged them out. Facebook and Xiaohongshu both returned HTTP 200 with supplied search totals/quotas and session/minute/hour/day search windows: FB current 0/2; XHS current 0/10. This proves Cloud projection only, not installed-client rendering. -->
- [x] 5.3 Record that Edge source and installed desktop package availability are separate; do not build or publish an installer without explicit authorization
  <!-- This delivery changes Edge source only. Installed desktop clients remain unchanged until a separately authorized package/release is produced and installed. -->
- [x] 5.4 Sync the delta specs and archive the OpenSpec change after all implementation, validation, integration, deployment, and evidence tasks are complete
  <!-- All prerequisite tasks are complete. Archive closeout syncs the two additive delta specs into platform-search-activity and edge-companion-ui, then moves this change to the dated archive. -->
