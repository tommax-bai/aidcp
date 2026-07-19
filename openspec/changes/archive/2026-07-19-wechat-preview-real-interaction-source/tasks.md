## 1. Cloud preview context projection

- [x] 1.1 Add an account-and-environment-scoped store query for recent latest-inbound preview contexts.
- [x] 1.2 Add the permission-gated read-only internal API endpoint for comment and DM preview contexts.
- [x] 1.3 Add focused Cloud tests for scoping, response minimization, empty binding, and DM full-text permission.

## 2. Console real interaction selection

- [x] 2.1 Add preview-context API types and a scoped client helper.
- [x] 2.2 Add a real-interaction/manual source selector that defaults to the newest eligible context and populates visible preview inputs.
- [x] 2.3 Add focused Console tests for default selection, title propagation, manual fallback, empty/error states, account changes, and DM permission handling.

## 3. Validation and delivery

- [x] 3.1 Run focused Cloud and Console tests plus each repository's required typecheck/build validation.
- [x] 3.2 Run `openspec validate wechat-preview-real-interaction-source --strict` and record implementation evidence.
- [x] 3.3 Commit and land Cloud and Console through their isolated worktrees, then deploy the integrated default branches to dev and verify the preview flow without creating jobs or sends.

## Validation evidence

- Cloud focused preview/store/internal API tests: 10 passed.
- Cloud `npm run typecheck` and `npm run build`: passed.
- Console focused reply settings tests: 33 passed.
- Console full `npm test -- --run`, `npm run typecheck`, and `npm run build`: passed.
- `openspec validate wechat-preview-real-interaction-source --strict`: passed.
- Landed default-branch commits: Cloud `ffab5ea`, Console `41cc4fc`, control contract `ca0e79d`.
- Deployed to dev `121.89.85.150` after backups stamped `20260719-114836`; Cloud, ports `8787`/`8090`, panel health, PostgreSQL, Feishu, Console `8088`, and same-host isales remained healthy.
- Live authenticated context read returned `videoTitle=血小板的cos，[偷笑][偷笑]`; reply-job/send-attempt counts were unchanged at `3/3` across the request.
