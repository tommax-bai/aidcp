## 1. Contract and preconditions

- [x] 1.1 Validate the proposal, design, and `facebook-proxy-preflight` delta with strict OpenSpec validation before implementation.
  <!-- repo=aidcp validation=openspec validate refresh-proxy-preflight-on-manual-start --strict passed before Edge implementation deviation=none -->
- [x] 1.2 Create isolated matching control and Edge worktrees from current default branches, preserving unrelated canonical changes, and install physical Edge dependencies with `npm ci --prefer-offline`.
  <!-- repos=aidcp,aidcp-edge branches=codex/refresh-proxy-preflight-on-manual-start worktrees=../aidcp.wt/refresh-proxy-preflight-on-manual-start,../aidcp-edge.wt/refresh-proxy-preflight-on-manual-start validation=npm ci --prefer-offline passed with physical node_modules deviation=npm audit reports pre-existing 13 vulnerabilities -->

## 2. Edge implementation

- [x] 2.1 Make the single-environment `edge:start` IPC invalidate only that environment's proxy-preflight evidence before choosing ordinary start or standby wake.
  <!-- repo=aidcp-edge files=src/electron/main.cjs implementation=edge:start refreshes only completed per-environment evidence before manual wake or queue deviation=in-flight checking is intentionally preserved to avoid superseded unknown -->
- [x] 2.2 Preserve selection prewarm, automatic wake, batch start, `no_proxy`, per-attempt singleflight, and authority/chain invalidation behavior.
  <!-- repo=aidcp-edge validation=source contract confirms helper is absent from wakeColdStandby, queueStartEnv, and startAllEnvs; existing no_proxy and revision paths unchanged deviation=none -->

## 3. Regression coverage

- [x] 3.1 Add focused tests proving explicit single-environment start invalidates pre-click settled evidence before both start branches, preserves an in-flight singleflight request, and does not add forced invalidation to automatic or batch paths.
  <!-- repo=aidcp-edge files=test/electron/proxy-preflight.test.ts,test/electron/proxy-runtime.test.ts coverage=cached failure refreshes to new success; in-flight probe remains singleflight; manual branch ordering and automatic/batch exclusions -->
- [x] 3.2 Run focused proxy-preflight, lifecycle, and browser-slot scheduling tests.
  <!-- repo=aidcp-edge validation=node --import tsx --test test/electron/proxy-preflight.test.ts test/electron/proxy-runtime.test.ts test/electron/lifecycle-contract.test.ts test/electron/browser-slot-scheduling.test.ts passed 63/63; git diff --check passed deviation=none -->

## 4. Validation and integration

- [x] 4.1 Run the complete Edge test suite, typecheck, and `git diff --check`.
  <!-- repo=aidcp-edge validation=npm test passed 2719 with 1 gated skip and 0 failures in 124.5s; npm run typecheck passed; git diff --check passed deviation=none -->
- [x] 4.2 Record implementation commit, validation, installation/deployment boundary, and deviations in this task file; run `openspec validate refresh-proxy-preflight-on-manual-start --strict`.
  <!-- repo=aidcp-edge commit=5b93dbcc5594375fc31a4c2f475448a81e9a79d6 validation=focused 63/63, full 2719 passed plus 1 gated skip, typecheck and diff-check passed boundary=source only; no Cloud deployment, installer build, or installed-client update deviation=in-flight probe is preserved instead of invalidated because controller cancellation returns non-blocking superseded -->
- [x] 4.3 Commit with explicit pathspecs, rebase onto latest default branches, rerun required validation, fast-forward integrate into clean eligible canonical checkouts, and push Edge `master` plus control `main` without building an installer.
  <!-- repos=aidcp-edge,aidcp edge_commit=5b93dbcc5594375fc31a4c2f475448a81e9a79d6 control_commit=4f08e5f6dc7eb1029a7d5872dd58654a5ac6a6ab integration=fast-forwarded and pushed aidcp-edge master plus aidcp main validation=post-rebase focused 63/63, typecheck, diff-check, and strict OpenSpec passed boundary=no installer built or installed-client update deviation=unrelated canonical dirty and untracked files preserved -->
