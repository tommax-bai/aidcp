## MODIFIED Requirements

### Requirement: Facebook Reel cadence is global, mode-specific and Reel-only

Cloud SHALL expose one cross-target global Reel cadence policy with exactly six `1..100` integers: ordinary persona `viewsPerLike` and `viewsPerFollow`, slow-start `viewsPerLike` and `viewsPerFollow`, plus rule and consumption `viewsPerFollow`. Defaults SHALL be 4, 10, 15, 15, 15 and 15 respectively. These values MUST be editable only through the internal management backend global policy route; customer, account and environment routes MUST NOT accept overrides.

The policy SHALL NOT be scoped by execution target: every deployment target reads and writes the same single record, and its revision SHALL form one sequence shared by all targets. A write made from one target's backend MUST become the effective value on every other target.

Only the first presentation of a canonical, one-card Facebook Reel in the active session SHALL advance the current mode's Reel counter. Feed cards, Feed videos, detail pages, searches, malformed targets and duplicate reports MUST NOT advance it. Counters SHALL be isolated by mode and reset at the existing session boundary; they MUST NOT move between accounts or create cross-session action debt.

#### Scenario: Ordinary persona counts only Reels

- **WHEN** an ordinary persona session sees Feed videos, details, duplicate Reel reports and N unique canonical one-card Reels
- **THEN** only the N unique Reels advance the ordinary persona counters and the Nth may create the configured intent

#### Scenario: Slow-start uses its own like and follow cadence

- **WHEN** the effective mode is slow-start and N unique canonical one-card Reels reach its configured like or follow boundary
- **THEN** only the slow-start counter advances and the Nth Reel may create the matching slow-start intent
- **AND** neither ordinary persona cadence nor another mode's counter advances

#### Scenario: Rule and consumption do not gain Reel like cadence

- **WHEN** the effective mode is rule or consumption
- **THEN** neither the ordinary persona nor slow-start Reel like counter advances and no Reel-cadence like intent is sent
- **AND** only that mode's own Reel follow counter may advance

#### Scenario: Global write is strict and atomic

- **WHEN** an internal operator writes all six cadence values with the current expected revision
- **THEN** Cloud validates every value, advances the single shared revision, writes audit and returns complete write-after-read truth atomically
- **AND** any missing, extra, fractional or out-of-range value rejects the whole request

#### Scenario: A write from one target is effective on every target

- **WHEN** an operator writes the six cadence values through one deployment target's backend
- **THEN** every other deployment target reads the same six values and the same revision
- **AND** no target retains a separate copy of the previous values

#### Scenario: Environment override cannot change Reel cadence

- **WHEN** an operator edits an environment's inherit/independent rule or consumption cadence
- **THEN** the six Reel cadence values remain the shared global values
- **AND** the environment route rejects any Reel cadence field
