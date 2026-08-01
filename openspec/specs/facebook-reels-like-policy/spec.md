# facebook-reels-like-policy Specification

## Purpose
TBD - created by archiving change facebook-reels-random-like. Update Purpose after archive.
## Requirements
### Requirement: Reel probability is the sole ordinary interaction appraisal for the handled Reel

After Cloud has handled a Reel through the probability policy, the later ordinary interaction appraiser MUST NOT call its LLM or emit another ordinary like or collect intent for that Reel. It SHALL emit an observable skip that preserves the existing browsing-loop completion. An explicit mandatory interaction rule SHALL be evaluated before this skip and MAY still force its required like.

#### Scenario: Miss is not followed by an LLM-selected like
- **WHEN** the Reel probability draw abstains and the same Reel later reaches ordinary interaction appraisal
- **THEN** the appraiser skips without calling the LLM or emitting an ordinary interaction intent

#### Scenario: Mandatory like overrides ordinary Reel handling
- **WHEN** a handled Reel later carries a confirmed mandatory interaction rule requiring like
- **THEN** the appraiser emits the mandatory like intent without applying the ordinary-handled skip

### Requirement: Only platform-confirmed Reel likes count as success

A probability-selected like SHALL remain an intent until Edge executes the existing note-scoped Reel action and returns a same-Reel positive selected-state witness. Risk accounting, session budget consumption, cooldown timestamps, and user-visible successful activity MUST update only from the existing confirmed `ok:true` receipt. A blocked draw, suppressed dispatch, stale target, ambiguous target, already-liked state, shadow execution, unchanged state, or indeterminate verification MUST NOT be reported or counted as a successful like.

#### Scenario: Probability hit is blocked before dispatch
- **WHEN** the draw selects like but an existing risk, budget, cooldown, or duplicate-action gate rejects it
- **THEN** Cloud sends no like command and neither records nor displays a successful like

#### Scenario: Edge cannot confirm the selected state
- **WHEN** Cloud sends the probability-selected like command but Edge returns a non-success result
- **THEN** Cloud does not consume successful-like budget or record a confirmed like for that Reel

#### Scenario: Edge confirms the same Reel is liked
- **WHEN** Edge returns `ok:true` with the existing same-Reel observation witness
- **THEN** Cloud uses the existing action receipt path to account for and display the confirmed like exactly once

### Requirement: Only ordinary persona mode applies the configurable Reel like cadence

When the effective Facebook browse mode is ordinary persona, Cloud SHALL mark each eligible unique active Reel as handled by the ordinary Reel policy and SHALL select one like intent exactly on each configured `viewsPerLike` boundary. The default boundary SHALL be 4. A miss before the boundary SHALL NOT be followed by an LLM-selected ordinary like for the same Reel. Slow-start, rule, consumption, blocked and unsupported modes MUST NOT advance or execute this ordinary persona like cadence.

This requirement applies only to canonical one-card Reel presentations. It MUST NOT count or change ordinary Feed, Feed-video or detail-page like behavior.

#### Scenario: Fourth unique persona Reel selects the default intent

- **WHEN** an ordinary persona session presents four distinct eligible Reels under the default policy
- **THEN** the first three are handled without a like intent and the fourth selects exactly one existing note-scoped like intent

#### Scenario: Slow-start does not reuse persona Reel likes

- **WHEN** the same account's effective mode is slow-start and Reels are presented
- **THEN** the persona Reel like counter does not advance and this policy sends no like command

#### Scenario: Feed video remains outside the configurable Reel counter

- **WHEN** an ordinary Feed video is presented between eligible Reels
- **THEN** it does not advance the persona Reel counter
- **AND** its existing independent policy is unchanged by this requirement

