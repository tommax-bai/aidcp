## 1. Cloud Config And API

- [x] 1.1 Extend `FacebookCommentConfigStore` with `commentMode` and `commentTemplates`, including self-healing schema SQL, input sanitization, defaults, and focused store tests. <!-- aidcp-cloud.wt/facebook-joined-group-template-comments ccc7d81e946aba4ee5f5d52b96df42dd15645420: config store + migration 0037 implemented; validation: npx tsx --test test/config/facebook-comment-config-store.test.ts PASS -->
- [x] 1.2 Update panel API DTO/types and `/api/accounts/:id/facebook-comment-config` read/write handling to accept and return mode/templates while preserving legacy `containers`. <!-- aidcp-cloud.wt/facebook-joined-group-template-comments ccc7d81e946aba4ee5f5d52b96df42dd15645420: panel PUT accepts commentMode/commentTemplates; validation: npx tsx --test test/panel-server.test.ts PASS -->

## 2. Cloud Scheduler Behavior

- [x] 2.1 Refactor normal unpinned Facebook comment target selection so joined-group coverage selection is the runtime source regardless of legacy container config or coverage source switch. <!-- aidcp-cloud.wt/facebook-joined-group-template-comments ccc7d81e946aba4ee5f5d52b96df42dd15645420: scheduler now requires joined selector for normal targets; server selector no longer gated by old coverage switch -->
- [x] 2.2 Add generated/template body selection in `CommentScheduler`: generated mode calls the existing composer; template mode chooses a configured template and fails closed if none are valid. <!-- aidcp-cloud.wt/facebook-joined-group-template-comments ccc7d81e946aba4ee5f5d52b96df42dd15645420: template mode skips facebookCompose; missing templates => compose_skipped empty_template -->
- [x] 2.3 Preserve validator, human-review, contact-info injection, relaxed-pick annotation, success ledger updates, and failure audit behavior for both body modes. <!-- aidcp-cloud.wt/facebook-joined-group-template-comments ccc7d81e946aba4ee5f5d52b96df42dd15645420: template/generated share validation/review/contact/coverage update path -->
- [x] 2.4 Add focused scheduler tests for no keywords, no joined groups, relaxed fallback, generated mode, template mode, missing templates, invalid template body, contact template body, and no fallback to legacy containers. <!-- validation: npx tsx --test test/comment-agent/comment-scheduler.test.ts PASS -->

## 3. Console FB Configuration UI

- [x] 3.1 Update console API mirror types for `commentMode` and `commentTemplates`. <!-- aidcp-console.wt/facebook-joined-group-template-comments b90fb4f49247011d8ffaead1d6b1b9e8e7226fa0: src/types/api.ts mirrors cloud config shape -->
- [x] 3.2 Replace the FB configuration modal's target container selector with comment mode controls and multi-template editing while keeping keyword behavior unchanged. <!-- aidcp-console.wt/facebook-joined-group-template-comments b90fb4f49247011d8ffaead1d6b1b9e8e7226fa0: FB modal now edits keywords + generated/template mode + one-template-per-line text -->
- [x] 3.3 Update console tests to verify mode/template round-trip and that containers are no longer displayed or submitted from the UI. <!-- validation: npx vitest run src/components/FacebookSearchConfig.test.tsx PASS -->

## 4. Validation And Closeout

- [x] 4.1 Run focused cloud tests for config store, panel route, and comment scheduler. <!-- PASS: npx tsx --test test/config/facebook-comment-config-store.test.ts; npx tsx --test test/panel-server.test.ts; npx tsx --test test/comment-agent/comment-scheduler.test.ts; npm run typecheck -->
- [x] 4.2 Run focused console tests for the FB configuration component. <!-- PASS: npx vitest run src/components/FacebookSearchConfig.test.tsx; npm run typecheck -->
- [x] 4.3 Run `openspec validate facebook-joined-group-template-comments --strict` and update this task file with commit/validation/deployment notes. <!-- PASS: openspec validate facebook-joined-group-template-comments --strict; code commits: aidcp-cloud ccc7d81e946aba4ee5f5d52b96df42dd15645420, aidcp-console b90fb4f49247011d8ffaead1d6b1b9e8e7226fa0; dev deploy 20260712-132240 backup; health: systemd active, panel /api/health ok, 8787 returned 426, PG ok, console asset 200, columns comment_mode/comment_templates present -->
