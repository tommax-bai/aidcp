## 1. Console interaction simplification

- [x] 1.1 Add deterministic four-state processing-mode helpers that map to the frozen `mode/generateDrafts/sendReplies` DTO and load legacy combinations fail closed.
- [x] 1.2 Replace the three independent basic-strategy controls with one reply-processing selector, relabel channel participation, and show channel auto scope only in auto mode.
- [x] 1.3 Present rule auto-send as a monotonic “must review” restriction, force AI-polished rules to human review, and simplify the publish summary.
- [x] 1.4 Separate immediate runtime controls and read-only hard gates from versioned strategy wording, and make preview permission denial explain that no preview ran.

## 2. Validation

- [x] 2.1 Add or update focused component/helper tests for all four mappings, legacy fail-closed normalization, contextual channel auto controls, rule review semantics, publish summary, and preview permission copy.
- [x] 2.2 Run focused Console tests, the full Console test suite with stable worker settings, and the production build.
  <!-- Console validation: focused 37/37 passed; full 170 passed, 1 skipped; `npm run typecheck` passed; `npm run build` passed. One unrelated curated-content async test flaked during a concurrent build, passed alone, then the independent full-suite rerun passed. -->

## 3. Closeout

- [x] 3.1 Record implementation commits and validation evidence, then run `openspec validate wechat-reply-settings-simplification --strict`.
  <!-- Console implementation: aidcp-console commit 7981506. Validation: focused 37/37, full 170 passed + 1 skipped, typecheck passed, production build passed, browser visual QA passed with no console errors. Strict OpenSpec validation is recorded by the control-repo commit containing this task evidence. -->
- [ ] 3.2 Rebase and integrate clean default branches, push control and Console changes, deploy Console to `dev`, and verify the documented health/static entry without any real platform write.
