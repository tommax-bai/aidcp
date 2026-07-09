## ADDED Requirements

### Requirement: Facebook group join is a first-class rate-limited action

Facebook group join SHALL be a rate-limited action alongside browse/like/collect/comment, subject to the existing minute/hour/day sliding-window quotas, the three quota tiers, and risk-state scaling (warned slows all actions; restricted/frozen stops joining). A brand-new account SHALL be throttled by selecting the conservative tier rather than a bespoke warmup function. Join attempts MUST be pre-gated before dispatch, and a join MUST count against the quota only after a verified join.

#### Scenario: Join quota denial prevents dispatch
- **WHEN** the risk gate denies a join for an account that has exhausted its minute, hour, or day join quota
- **THEN** no join is dispatched and a quota-denied non-success outcome is recorded

#### Scenario: Only verified join counts
- **WHEN** a join attempt returns anything other than a judgment-confirmed join
- **THEN** no successful join interaction is recorded for that account

#### Scenario: Restricted state stops joining
- **WHEN** an account's risk state is restricted or frozen
- **THEN** the join loop for that account does not dispatch, inheriting the same state scaling as other interactions

### Requirement: Join and comment share the per-account single-flight and activity budget

Facebook join and Facebook comment for the same account SHALL be dispatched under the same per-account single-flight so the physically single-slot edge is never asked to do both at once, and their combined daily activity SHALL be bounded against platform tolerance. The worst-case aggregate of the join daily cap plus the comment daily cap MUST be a considered value, not two independently-spent caps.

#### Scenario: One account never joins and comments simultaneously
- **WHEN** an account has both a pending join slot and a pending comment slot in the same tick
- **THEN** only one is dispatched, held by the same per-account single-flight lock used for commenting
