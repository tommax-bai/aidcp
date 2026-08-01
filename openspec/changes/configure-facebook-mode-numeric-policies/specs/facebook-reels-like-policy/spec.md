## RENAMED Requirements

- FROM: `### Requirement: Every unique active Facebook Reel receives one ordinary like draw`
- TO: `### Requirement: Only ordinary persona mode applies the configurable Reel like cadence`

## MODIFIED Requirements

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

