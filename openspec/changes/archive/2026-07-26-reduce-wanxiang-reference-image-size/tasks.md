## 1. Isolated Workspace

- [x] 1.1 Create the matching `aidcp-cloud` worktree from current `origin/master` and install a physical dependency tree with `npm ci --prefer-offline`. <!-- aidcp-cloud worktree codex/reduce-wanxiang-reference-image-size from origin/master f57bfb7; npm ci added 162 packages; existing audit report: 5 vulnerabilities -->

## 2. Cloud Implementation

- [x] 2.1 Change the Wanxiang reference-image constructor fallback from `2K` to `1K` while preserving the explicit option and environment override precedence. <!-- aidcp-cloud src/publish-agent/wanxiang-client.ts -->
- [x] 2.2 Add focused tests for default reference `1K`, explicit reference-size override, and unchanged non-reference sizing. <!-- aidcp-cloud test/publish-agent/wanxiang-client.test.ts -->

## 3. Validation

- [x] 3.1 Run the focused Wanxiang client tests. <!-- node --import tsx --test test/publish-agent/wanxiang-client.test.ts: 11/11 passed -->
- [x] 3.2 Run publish acceptance tests, the full cloud test suite, and `npm run typecheck` in that order. <!-- acceptance 59 passed, 1 gated skip; full 2651 passed, 8 skipped, 0 failed; typecheck passed -->
- [x] 3.3 Run `openspec validate reduce-wanxiang-reference-image-size --strict`. <!-- strict validation passed -->

## 4. Integration and Dev Rollout

- [x] 4.1 Commit both repositories, rebase onto their latest default branches, repeat required validation, fast-forward push the default branches, and record the final SHAs. <!-- aidcp-cloud 2c19b1d7df2e459a834746fdd1403c8cf27e7a43 pushed to master; aidcp artifact commit 6b91af37a83c1a48208c22ee59784d9080eca2e5 pushed to main; post-rebase acceptance 59 passed, full 2651 passed/8 skipped/0 failed, typecheck passed, strict OpenSpec passed -->
- [x] 4.2 Deploy the clean integrated `aidcp-cloud/master` artifact to `dev`, preserving `.env`, then verify service health, listeners, panel health, PostgreSQL, and Feishu state without touching unrelated services. <!-- deployed source+focused test from clean master 2c19b1d; backup /opt/aidcp/backups/cloud.pre-reduce-wanxiang-reference-image-size.20260720-142305.tar.gz; aidcp-cloud active; 8787/8090 listening; /api/health ok; PG SELECT 1; Feishu WS started; isales untouched -->
- [x] 4.3 Verify `dev` has no runtime override masking the new `1K` default and record deployment evidence, rollback boundary, and any deviations in this task file. <!-- dev AIDCP_WANXIANG_REFERENCE_IMAGE_SIZE unset; deployed/canonical SHA-256 matched for both files; runtime source fallback is 1K; remote mocked request-shape suite 11/11 passed. No billable real generation was triggered, so real 1K byte size remains observational follow-up. Rollback: set AIDCP_WANXIANG_REFERENCE_IMAGE_SIZE=2K and restart, or restore backup/redeploy prior commit. ol not changed. -->
