## RENAMED Requirements

- FROM: `Every eligible active Facebook Reel receives one independent follow draw`
- TO: `Every supported Facebook browse mode uses its own configurable Reel follow cadence`

## MODIFIED Requirements

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

