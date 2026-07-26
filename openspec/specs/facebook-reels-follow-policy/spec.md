# facebook-reels-follow-policy Specification

## Purpose
TBD - created by archiving change facebook-reels-random-follow. Update Purpose after archive.
## Requirements
### Requirement: Every eligible active Facebook Reel receives one independent follow draw

When an Edge connection that declares `facebook_reel_follow_v1` reports exactly one active Facebook Reel through `page.cards` with `listKind:'reels'`, a canonical Facebook `/reel/<id>` identity, and a non-empty current author, Cloud SHALL make at most one Reel-follow decision for that normalized identity in the active session. For a decision that passes existing quota and safety gates, Cloud SHALL select a follow intent exactly when its independent injectable random value is strictly less than `0.10`. A value equal to or greater than `0.10` SHALL abstain without sending a follow command. Duplicate reports MUST NOT redraw.

#### Scenario: Draw below threshold selects a note-scoped follow intent
- **WHEN** an eligible unique Reel is reported and the follow random value is `0.099999`
- **THEN** Cloud sends one existing `interaction.follow` command containing that Reel `noteId` and its observed author
- **AND** the existing 25% like decision remains independent

#### Scenario: Threshold value abstains
- **WHEN** an eligible Reel's follow random value is exactly `0.10`
- **THEN** Cloud sends no probability-selected follow command for that decision

#### Scenario: Duplicate report does not redraw
- **WHEN** the same normalized Reel identity is reported more than once in one active session
- **THEN** Cloud performs only the first follow decision and sends at most one probability-selected follow intent

#### Scenario: Invalid or authorless Reel fails closed
- **WHEN** the list is not Reels, has zero or multiple cards, lacks a canonical Facebook Reel identity, lacks a non-empty author, or belongs to another platform
- **THEN** Cloud sends no probability-selected follow command

#### Scenario: Old Edge does not receive follow
- **WHEN** the connected Edge does not declare `facebook_reel_follow_v1`
- **THEN** Cloud does not draw or send an automatic Reel follow command

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

