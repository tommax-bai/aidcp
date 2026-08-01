# facebook-reels-follow-policy Specification

## Purpose
TBD - created by archiving change facebook-reels-random-follow. Update Purpose after archive.
## Requirements
### Requirement: Reel follow probability remains subordinate to every quota and safety gate

Before drawing or dispatching an automatic Reel follow, Cloud SHALL reserve the Reel's one-time decision, require positive remaining session follow budget, require the authoritative RiskController to allow `follow` under its current minute/hour/day limits and risk state, and require the existing follow cooldown to pass. Dispatch SHALL continue through the existing comment-subline suppression and same-account `InteractionGuard`. A blocked decision MUST NOT send a command, consume successful-follow budget, or be presented as a successful follow.

#### Scenario: Session follow budget is exhausted
- **WHEN** an otherwise eligible Reel appears after the session follow budget reaches zero
- **THEN** Cloud sends no follow command and performs no follow random draw for that Reel

#### Scenario: RiskController quota rejects follow
- **WHEN** a minute, hour, day, slow-start, or risk gate rejects `follow`
- **THEN** Cloud sends no follow command and records no successful follow

#### Scenario: Cooldown or duplicate-author guard blocks dispatch
- **WHEN** the follow cooldown has not elapsed or another node already owns/completed the same author follow
- **THEN** Cloud sends no duplicate platform write and does not consume successful-follow budget

### Requirement: Only a verified new Reel follow counts and becomes visible

A probability-selected follow SHALL remain an intent until Edge re-probes the same canonical Reel and unique author association and verifies that the unique control changed to Following/已关注. Cloud SHALL record `interaction.occurred{action:'follow'}`, decrement session follow budget, and expose the updated daily follow total only for `ok:true` results that are not `already_followed`. Edge SHALL emit a successful follow activity and local fallback increment under the same predicate.

#### Scenario: Edge verifies a new follow
- **WHEN** Edge returns `action.completed{action:'follow',ok:true}` after same-Reel verification
- **THEN** Cloud records one follow fact and consumes one session follow budget
- **AND** the client may immediately show one follow activity before the Cloud total refresh arrives

#### Scenario: Reel was already followed
- **WHEN** Edge returns `ok:true, reason:'already_followed'` without clicking
- **THEN** Cloud and Edge add no follow count and no successful follow activity

#### Scenario: Follow cannot be verified
- **WHEN** Edge returns shadow, no-target, ambiguous-target, state-unchanged, verify-indeterminate, or any other non-success result
- **THEN** Cloud records no successful follow and the client shows no successful follow activity

### Requirement: Every supported Facebook browse mode uses its own configurable Reel follow cadence

For each active session, Cloud SHALL count eligible unique canonical Reels separately under the effective mode and SHALL select one follow intent on each configured `viewsPerFollow` boundary. Ordinary persona SHALL default to 10; slow-start, rule and consumption SHALL each default to 15. The four values SHALL be independently configurable in the target-global management policy. A Reel observed under one mode MUST NOT advance another mode's counter.

Follow selection SHALL continue to require the current Reel's non-empty author and an Edge connection declaring `facebook_reel_follow_v1`. Missing author, old Edge, risk rejection, exhausted budget, cooldown or duplicate-author ownership MUST send no follow and create no success or action debt.

#### Scenario: Default ordinary persona follow boundary

- **WHEN** ordinary persona mode presents ten eligible unique Reels under the default policy
- **THEN** the tenth selects at most one follow intent and the earlier nine select none

#### Scenario: Default rule follow boundary is independent

- **WHEN** rule mode presents fifteen eligible unique Reels after persona mode previously accumulated nine Reel visits
- **THEN** rule mode selects its first follow intent only on its own fifteenth Reel
- **AND** the persona counter does not affect that boundary

#### Scenario: Old Edge fails closed at the boundary

- **WHEN** the mode reaches its follow boundary but the connected Edge lacks `facebook_reel_follow_v1`
- **THEN** Cloud sends no follow command, records no confirmed follow and carries no target debt

