## 1. Single Facebook comment quota authority

- [x] 1.1 Remove the Facebook scheduler's `facebookDailyCap` / `facebookCommentedToday` dependencies and the `AIDCP_FB_COMMENT_DAILY_CAP` composition-root read.
- [x] 1.2 Preserve `risk_interactions` only for target de-duplication and prove automatic Facebook comment admission follows the injected `RiskController` decision.
  <!-- aidcp-cloud: removed the hidden env/count dependencies; the scheduler now admits automatic comments only through facebookCanComment, while risk_interactions remains the per-target de-duplication ledger. -->

## 2. Rule-mode admission and notification truth

- [x] 2.1 Preflight the rule round's comment `RiskController` decision and active-session comment budget before dispatching a group join.
- [x] 2.2 Preserve the existing post-membership and pre-submit comment gate re-reads with truthful partial terminal states.
- [x] 2.3 Label `facebook_rule_batch` combined result cards as `Facebook 规则模式` while retaining `/comment` for manual commands.
  <!-- aidcp-cloud: rule rounds stop with joinState=not_started before dispatch when the comment quota/session budget is exhausted; the two later gate reads remain intact. -->

## 3. Regression and integration validation

- [x] 3.1 Add focused scheduler and rule-dispatcher regressions for single-authority quota admission, no-join preflight refusal, gate changes after join, and source labels.
- [x] 3.2 Run focused Cloud tests and `npm run typecheck`.
- [x] 3.3 Run comment/risk acceptance coverage, the Cloud full test suite, and final typecheck.
  <!-- Validation: focused 134/134; acceptance 166/166; full 3822 passed, 0 failed, 11 explicit PostgreSQL-channel skips; npm run typecheck passed. No protocol, schema, retry, cooldown, or historical-backfill deviation. -->
- [ ] 3.4 Run `openspec validate unify-facebook-comment-quota-authority --strict`, record repository SHAs and deviations, then commit and push both default branches without force.

## 4. DEV delivery

- [ ] 4.1 Run the DEV deployment preflight, inspect concurrent runtime state, and back up Cloud plus `.env`.
- [ ] 4.2 Deploy only the clean integrated Cloud default revision, remove only the obsolete `AIDCP_FB_COMMENT_DAILY_CAP` DEV line, and restart only `aidcp-cloud.service`.
- [ ] 4.3 Verify deployed source/config, schema gates, automation writer lock, service/listeners/health, Feishu, PostgreSQL and unrelated `isales` services without issuing a Facebook write.
