## 1. Spec

- [x] 1.1 Add OpenSpec delta for scaled quota rounding semantics.
- [x] 1.2 Validate the OpenSpec change with `openspec validate ceil-scaled-risk-quotas --strict`.

## 2. Cloud

- [x] 2.1 Change `scaleWindowQuotas` to round scaled quotas upward. <!-- aidcp-cloud 5987b91 -->
- [x] 2.2 Update/add tests for warned quota windows and provider-backed scaling. <!-- aidcp-cloud 5987b91 -->
- [x] 2.3 Run cloud acceptance tests, full tests, and typecheck. <!-- aidcp-cloud 5987b91 clean detached validation passed: npm run test:acceptance, full explicit tsx test (1322 pass), npm run typecheck. Final default branch snapshot aidcp-cloud 8be807b also passed npm run test:acceptance, full explicit tsx test (1325 pass), npm run typecheck. -->

## 3. Release

- [ ] 3.1 Commit and push the control/cloud changes.
- [ ] 3.2 Deploy cloud from the default branch snapshot and run production healthchecks.
