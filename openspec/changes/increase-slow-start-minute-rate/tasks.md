## 1. OpenSpec contract

- [x] 1.1 Add the interaction-risk-gating delta for the `/10` minute derivation and its precedence boundaries
- [x] 1.2 Run `openspec validate increase-slow-start-minute-rate --strict` <!-- 2026-07-28: pass -->

## 2. Cloud implementation

- [x] 2.1 Change the shared daily-to-minute derivation divisor from 20 to 10 without changing zero, burst-cap, hour, or day behavior
- [x] 2.2 Add focused regression coverage for generic derivation and Facebook slow-start day-1 `view=2/minute`
- [x] 2.3 Run focused risk tests, Cloud acceptance tests, the full Cloud test suite, and `npm run typecheck` <!-- 2026-07-28: focused 46/46 pass; acceptance 166/166 pass; full 3829 pass + 11 skipped; typecheck pass -->

## 3. Integration and development verification

- [x] 3.1 Commit the Cloud implementation and control artifacts with validation evidence recorded here <!-- Cloud 911a4c2; control commit contains this record. Focused 46/46, acceptance 166/166, full 3829 pass + 11 skipped, typecheck and OpenSpec strict validation pass. -->
- [ ] 3.2 Rebase and fast-forward Cloud/control default branches, then push
- [ ] 3.3 Deploy the Cloud change to dev and verify service, listeners, health, configuration mirrors, Feishu, PostgreSQL, and the effective `/10` quota behavior
