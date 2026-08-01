## 1. Contract and isolation

- [x] 1.1 Run task preflight, confirm canonical control/Cloud/Console/Edge branches, and rebase the control change onto current `main` without touching unrelated files.
- [x] 1.2 Replace the previous platform-sized numeric-policy proposal with the requested global Reel cadence boundary and re-audit the current operation-policy implementation.
- [x] 1.3 Create matching isolated Cloud and Console worktrees and install physical dependencies with `npm ci --prefer-offline`.
  <!-- Baselines: aidcp-cloud 391f77d725b3d3807d9d672e4eef0040c3f0035a; aidcp-console ad5006eba80bada9fbd4c0c059f04b78032e4fb5. Both node_modules directories are physical. Cloud npm ci --prefer-offline succeeded (162 packages). Console has no tracked lockfile, so npm ci rejected without writing; npm install --prefer-offline --no-package-lock succeeded (245 packages) and left git clean. -->

## 2. Cloud policy authority

- [x] 2.1 Add API-owner migration 0104 with five global Reel cadence columns, strict `1..100` checks, defaults 4/10/15/15/15, and audited snapshot compatibility.
- [x] 2.2 Extend global policy types, schema capability, strict validation, CAS GET/PUT, audit snapshot, cloning and authority refresh for the complete `reels` object.
- [x] 2.3 Keep the five fields global-only: do not add environment/customer write fields or inherit/independent overrides.
- [x] 2.4 Update schema ownership, required/known version metadata and focused migration/store/Panel tests.
  <!-- aidcp-cloud commit 46a7003f3d8a2f9a91f53f2c6cddc89cb7263349. Migration/store/Panel/schema focused tests passed. -->

## 3. Cloud Reel runtime

- [x] 3.1 Project the complete global Reel cadence into each account mode decision without changing rule/consumption durable policy snapshots.
- [x] 3.2 Replace Reel fixed-probability like selection with exact unique-Reel cadence only for ordinary persona mode; keep Feed video behavior outside this change.
- [x] 3.3 Replace Reel fixed-probability follow selection with the current mode's exact unique-Reel cadence and default 15 for slow-start/rule/consumption.
- [x] 3.4 Preserve session reset, duplicate Reel suppression, no-debt gate failures, Edge capability, risk, cooldown, author dedupe and platform-confirmed success accounting.
- [x] 3.5 Add focused tests for mode isolation, Reel-only counting, exact N boundaries, duplicate reports, default values, invalid policy and action confirmation honesty.
  <!-- The cadence dedupe key includes effective mode plus canonical Reel identity, so mid-session mode changes do not consume another mode's counter. Ordinary persona marks every handled Reel as an external like decision to prevent a second LLM like path. -->

## 4. Admin Console

- [x] 4.1 Extend API DTOs and strict client-side validation for the complete global `reels` policy and bounds.
- [x] 4.2 Add four peer sections/fields to the existing Facebook global editor: persona Reel like/follow and slow-start/rule/consumption Reel follow.
- [x] 4.3 State clearly that the persona like value applies only to Reel visits and that reaching N is an intent still subject to safety and confirmation.
- [x] 4.4 Add focused Console tests for defaults, request payload, range validation, failed-write retention and authoritative refetch.
  <!-- aidcp-console commit f35029c4ce65b5cde2721a01143eba7c5c3108d4. EnvironmentsPage 18/18 and typecheck passed after the explicit stale-CAS retention test. -->

## 5. Validation and delivery

- [x] 5.1 Run focused Cloud tests, Cloud full tests/typecheck, Console focused/full tests/typecheck/build, and inspect any truncated failure before claiming success.
  <!-- Cloud: 4071 tests passed, 11 skipped, typecheck passed. Console: low-concurrency rerun 344 passed, 1 skipped, build passed; initial parallel-run timeouts were serially rerun and passed. -->
- [x] 5.2 Run `openspec validate configure-facebook-mode-numeric-policies --strict` and record commits, validation and deviations in this checklist.
  <!-- Control/OpenSpec commit ba1f791f8b28f9dbd1cf7896c71b45667f99b8c1; strict validation passed. Deviation: Console has no tracked lockfile, so physical dependencies used npm install --prefer-offline --no-package-lock instead of npm ci. No Edge source or package changes. -->
- [x] 5.3 Rebase, fast-forward integrate and push clean Cloud, Console and control default branches with explicit path scope.
  <!-- Pushed defaults: aidcp-cloud/master 46a7003f3d8a2f9a91f53f2c6cddc89cb7263349; aidcp-console/master f35029c4ce65b5cde2721a01143eba7c5c3108d4; aidcp/main 656476384f698ee360c4f697335a723dd34b1e85. All canonical checkouts were clean and fast-forwarded. -->
- [x] 5.4 Run DEV deployment preflight/checks and deploy Cloud/Console only if the shared schema gate proves compatible; do not deploy OL, package Edge or perform real Facebook actions without explicit authorization.
  <!-- DEV and OL target checks passed, then read-only `migrate status` proved the API ledger is currently 0103 on both targets. DEV source knows 0103; OL source only knows through 0098 and runs with AIDCP_SCHEMA_GATE=enforce plus the exact allowlist 0103_facebook_operation_global_policy. Applying 0104 from DEV would make OL fail its next restart, so no rsync, migration, restart or remote write was performed. Deployment requires explicit OL compatibility/release scope. -->
