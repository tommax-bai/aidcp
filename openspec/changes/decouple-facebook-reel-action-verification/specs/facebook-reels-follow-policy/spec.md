## MODIFIED Requirements

### Requirement: Only a verified new Reel follow counts and becomes visible

A probability-selected follow SHALL remain an intent until Edge re-probes the same canonical Reel and unique author association and verifies that the freshly resolved unique control changed to Following/已关注. Replacement or transient absence of the exact pre-click control during the existing bounded verification window MUST NOT by itself terminate verification while the canonical Reel has not been observed to change; a different Reel, different author, unresolved state at the deadline, or non-unique association MUST remain an ambiguous non-success. Cloud SHALL record `interaction.occurred{action:'follow'}`, decrement session follow budget, and expose the updated daily follow total only for `ok:true` results that are not `already_followed`. Edge SHALL emit a successful follow activity and local fallback increment under the same predicate.

#### Scenario: Edge verifies a new follow
- **WHEN** Edge returns `action.completed{action:'follow',ok:true}` after fresh same-Reel and same-author verification
- **THEN** Cloud records one follow fact and consumes one session follow budget
- **AND** the client may immediately show one follow activity before the Cloud total refresh arrives

#### Scenario: Reel was already followed
- **WHEN** Edge returns `ok:true, reason:'already_followed'` without clicking
- **THEN** Cloud and Edge add no follow count and no successful follow activity

#### Scenario: Same Reel replaces the Follow control
- **WHEN** the one-time Follow commit causes the author-bound control to be temporarily absent or replaced while the same canonical Reel remains active
- **THEN** Edge continues fresh observation within the existing bounded window and confirms success only from the replacement control's Following/已关注 state

#### Scenario: Follow cannot be verified
- **WHEN** Edge returns shadow, no-target, ambiguous-target, state-unchanged, verify-indeterminate, or any other non-success result
- **THEN** Cloud records no successful follow and the client shows no successful follow activity
