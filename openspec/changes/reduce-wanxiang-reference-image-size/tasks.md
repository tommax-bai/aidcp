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

- [ ] 4.1 Commit both repositories, rebase onto their latest default branches, repeat required validation, fast-forward push the default branches, and record the final SHAs.
- [ ] 4.2 Deploy the clean integrated `aidcp-cloud/master` artifact to `dev`, preserving `.env`, then verify service health, listeners, panel health, PostgreSQL, and Feishu state without touching unrelated services.
- [ ] 4.3 Verify `dev` has no runtime override masking the new `1K` default and record deployment evidence, rollback boundary, and any deviations in this task file.
