## 1. Contract and workspace setup

- [x] 1.1 Create matching Cloud and Console worktrees with physical dependencies, record branch ownership, and confirm canonical checkouts remain on default branches.
<!-- Control `/Users/baitianxing/codes/aidcp.wt/wechat-group-scoped-reply-config`, Cloud `/Users/baitianxing/codes/aidcp-cloud.wt/wechat-group-scoped-reply-config`, Console `/Users/baitianxing/codes/aidcp-console.wt/wechat-group-scoped-reply-config`; all use `codex/wechat-group-scoped-reply-config`. Canonical branches remained `main/master/master`. Cloud `npm ci --prefer-offline` succeeded. Console has no tracked lockfile, so `npm ci` correctly failed and physical dependencies were installed with `npm install --prefer-offline`; neither dependency tree is linked. -->
- [x] 1.2 Add v2 internal/customer API schema and fixtures for config scopes, effective source, scope CRUD/publish/preview/audit, and validate them locally.
<!-- Added `docs/contracts/wechat-channels-interaction/v2` overlay with stable source/head/snapshot/effective/preview/inventory contracts and customer replyConfig source projection. `check-jsonschema --check-metaschema schemas/*.schema.json`, internal fixtures, and customer fixtures all passed. -->

## 2. Cloud scoped configuration storage

- [x] 2.1 Add an additive PostgreSQL migration for stable reply config scopes, immutable scope versions/templates/rules/profiles, scope audit, and reply-job `config_scope_id` provenance.
<!-- Cloud `migrations/0048_wechat_group_reply_config.sql`; additive tables/column/index only, legacy account config untouched. Migration contract test passed. -->
- [x] 2.2 Implement the scope store with CAS draft mutations, validation, publish, immutable lookup, list/member counts, and exact group/default resolution.
<!-- Cloud `ReplyConfigScopeStore`; immutable JSONB aggregate snapshots, row-locked CAS, publish validation, exact group/default membership and scope audit. -->
- [x] 2.3 Add migration inventory/fingerprint and `legacy|shadow|scoped` resolver modes without logging message/template bodies.
<!-- Cloud `ReplyConfigResolver`; default legacy, body-free SHA-256 behavior fingerprint, inventory conflict flag and shadow metadata-only observation. Resolver tests passed. -->

## 3. Cloud runtime and APIs

- [x] 3.1 Add internal scope management/effective-source endpoints with grants, validation, preview account membership checks, audit, and explicit legacy write deprecation behavior.
<!-- Cloud `InteractionScopeInternalApi`; scope CRUD/publish/preview/audit/effective-source/migration-inventory. `interaction-scope-internal-api.test.ts` covers list/effective, CAS and fail-closed preview membership. -->
- [x] 3.2 Update reply generation, approval, editing and sending to freeze/load `configScopeId + configVersion` while preserving legacy jobs.
<!-- Workflow freezes both fields for new scoped jobs; approval/edit/send/result paths use frozen scope snapshots, while null scope IDs continue legacy lookup. Resolver historical-job test passed. -->
- [x] 3.3 Update customer-auth replyConfig projections to use the effective resolver and expose only non-sensitive source/version state.
<!-- Customer projection now reports mode/source/status/version metadata from the resolver and never returns config bodies. Existing customer API tests remained green in the full suite. -->
- [x] 3.4 Ensure offboarding removes account data and legacy config without deleting shared scopes; add regression coverage.
<!-- Existing per-account purge remains unchanged for legacy config/runtime/content and explicitly does not delete scope heads, immutable versions or scope audit; purge regression passed. -->

## 4. Console group/default strategy management

- [x] 4.1 Add scope/effective-source DTOs and API clients from the shared contract without inventing a parallel schema.
<!-- Console mirrors the v2 contract in `interactionReplyConfig.ts`/types; API path and effective-source tests passed. -->
- [x] 4.2 Add a “视频号策略” page listing default/group scopes, account counts, versions and missing states, with scope-scoped editing/publish/audit and representative-account preview.
<!-- Added `/wechat-strategies` navigation/page and reused the validated editor in scope mode; default/group listing and stable-scope mutation tests passed. -->
- [x] 4.3 Change the account surface to show effective source and keep account runtime controls separate from shared strategy editing.
<!-- Account rows now show actual resolver mode/source, link to the strategy page and open a runtime-only drawer that works without legacy reply config. -->
- [x] 4.4 Add focused UI tests for default/group resolution, missing config, account switching, permission/version conflicts and no-side-effect preview wording.
<!-- Added scope API/page/editor coverage and retained the existing 34-case editor suite for stale switching, missing config, permissions, CAS conflicts and preview no-send honesty. -->

## 5. Validation, integration and rollout

- [x] 5.1 Run Cloud acceptance/focused tests, full tests and typecheck; run Console focused tests, serial full suite, typecheck and build.
<!-- Cloud commit `9e1380d`: focused 22/22, acceptance 59/59 (one gated E2E skipped), full 2608 passed/8 skipped, typecheck passed. Console commit `1bed7cf`: focused legacy editor 34/34 plus scope/API/page 5/5, serial full 193 passed/1 skipped before the final added scope editor test (which passed separately), typecheck and production build passed; only pre-existing jsdom/chunk-size warnings remained. -->
- [x] 5.2 Run `openspec validate wechat-group-scoped-reply-config --strict`, record repo commits/validation/deviations in this task file, and push feature branches.
<!-- Feature commits pushed: Cloud `9e1380d`, Console `1bed7cf`, Control artifacts `750d4f5`. Strict OpenSpec and all v2 JSON metaschema/fixture checks passed. Deviation: Console has no tracked lockfile, so its worktree used physical `npm install --prefer-offline` after the required `npm ci` failure. -->
- [x] 5.3 Rebase and fast-forward integrate Control, Cloud and Console default branches in dependency order, rerun required validation, and push.
<!-- Defaults advanced during development, so Control and Cloud were rebased without conflicts and without force-pushing the already-published feature refs. Fast-forward integration/push completed: Control `c21f5f0` on `main`, Cloud `4212e54` on `master`, Console `1bed7cf` on `master`. Post-integration strict OpenSpec, Cloud focused 22/22 + typecheck, and Console scope focused 5/5 + typecheck all passed. -->
- [ ] 5.4 Check the named dev deployment boundary; deploy only additive eligible artifacts when the database target is isolated/safe, otherwise record the exact blocker without touching ol.
