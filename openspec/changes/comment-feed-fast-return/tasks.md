## 1. Cloud command and task propagation

- [x] 1.1 Parse trailing `--feed` in both comment command parsers, document it in help text, and persist it as a manual task constraint.
- [x] 1.2 Propagate fast-return intent through delegated execution, `CommentScheduler`, Xiaohongshu/Facebook edge steps, and the shared optional protocol field.
- [x] 1.3 Add focused Cloud tests for parsing, manual-only propagation, and submitted-unconfirmed no-retry semantics.

## 2. Edge fast-return behavior

- [x] 2.1 Implement the Xiaohongshu post-submit 500 ms fast-return branch with direct Explore navigation and honest `submitted_unconfirmed` reporting.
- [x] 2.2 Implement the Facebook post-submit 500 ms fast-return branch with direct home navigation and honest `verification_ambiguous` reporting.
- [x] 2.3 Add focused Edge tests for both fast-return branches and default confirmation-path preservation.

## 3. Validation and delivery

- [x] 3.1 Run focused Cloud and Edge tests, full acceptance/full suites required for comment protocol/write changes, and both repositories' typechecks.
  <!-- Cloud: focused 119/119, acceptance 63/63, full 2711 passed + 8 skipped, typecheck passed. Edge: focused fast-return coverage passed, acceptance 27/27, full 2051/2051, typecheck passed. -->
- [ ] 3.2 Run strict OpenSpec validation and record commits, validation results, deployment result, and any honest deviations in this checklist.
- [ ] 3.3 Integrate and push clean default branches, deploy runtime changes to `dev`, and verify the documented service/health checks without touching unrelated services.
