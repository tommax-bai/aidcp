# facebook-reel-mode-cadence Specification

## Purpose
TBD - created by archiving change configure-facebook-mode-numeric-policies. Update Purpose after archive.
## Requirements
### Requirement: Facebook Reel cadence is global, mode-specific and Reel-only

Cloud SHALL expose one target-global Reel cadence policy with exactly six `1..100` integers: ordinary persona `viewsPerLike` and `viewsPerFollow`, slow-start `viewsPerLike` and `viewsPerFollow`, plus rule and consumption `viewsPerFollow`. Defaults SHALL be 4, 10, 15, 15, 15 and 15 respectively. These values MUST be editable only through the internal management backend global policy route; customer, account and environment routes MUST NOT accept overrides.

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
- **THEN** Cloud validates every value, advances the target-global revision, writes audit and returns complete write-after-read truth atomically
- **AND** any missing, extra, fractional or out-of-range value rejects the whole request

#### Scenario: Environment override cannot change Reel cadence

- **WHEN** an operator edits an environment's inherit/independent rule or consumption cadence
- **THEN** the six Reel cadence values remain the target-global values
- **AND** the environment route rejects any Reel cadence field

### Requirement: Reaching a Reel cadence creates an intent without faking success or debt

For each configured action, the Nth eligible unique Reel SHALL create at most one existing note-scoped action intent. Every intent MUST still pass Edge capability, remaining session budget, RiskController, cooldown, author/target dedupe, Native execution and same-target postcondition gates. A rejected or unavailable gate SHALL end that cadence opportunity without creating debt; another attempt requires another complete N-Reel segment in the same mode.

Only a platform-confirmed new like or follow SHALL update successful activity and usage. Already satisfied, pending, ambiguous, submitted-unknown, not-started, rejected and failed outcomes MUST NOT be promoted to success.

#### Scenario: Nth Reel is risk blocked

- **WHEN** the Nth eligible Reel reaches a like or follow cadence but the corresponding risk gate rejects it
- **THEN** no command and no success count is produced
- **AND** the next opportunity requires another N eligible Reels rather than retrying the blocked target

#### Scenario: Platform confirmation remains required

- **WHEN** a cadence intent is dispatched but Edge cannot prove the new state on the same Reel and author
- **THEN** Cloud records no confirmed action and does not consume successful-action budget

