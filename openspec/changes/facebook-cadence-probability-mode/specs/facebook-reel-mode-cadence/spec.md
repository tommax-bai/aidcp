# facebook-reel-mode-cadence Delta

## MODIFIED Requirements

### Requirement: Reaching a Reel cadence creates an intent without faking success or debt

For each configured action, an eligible unique Reel SHALL create at most one existing note-scoped action intent when its cadence condition is met. Under the global `cadenceMode='fixed'` the condition is the existing one: the Nth eligible unique Reel in the current mode's counter. Under `cadenceMode='probabilistic'` the condition SHALL be an independent Bernoulli(1/N) draw at each eligible unique Reel's first presentation, using the same configured N; counters SHALL still advance for observability but MUST NOT drive the trigger. Every intent MUST still pass Edge capability, remaining session budget, RiskController, cooldown, author/target dedupe, Native execution and same-target postcondition gates. A rejected or unavailable gate SHALL end that cadence opportunity without creating debt; the next opportunity requires, in fixed mode, another complete N-Reel segment in the same mode, and in probabilistic mode, a later eligible Reel's independent draw.

Only a platform-confirmed new like or follow SHALL update successful activity and usage. Already satisfied, pending, ambiguous, submitted-unknown, not-started, rejected and failed outcomes MUST NOT be promoted to success.

#### Scenario: Nth Reel is risk blocked

- **WHEN** the Nth eligible Reel reaches a like or follow cadence under fixed mode but the corresponding risk gate rejects it
- **THEN** no command and no success count is produced
- **AND** the next opportunity requires another N eligible Reels rather than retrying the blocked target

#### Scenario: Probabilistic draw is per-Reel and independent

- **WHEN** the global cadence mode is probabilistic and a session presents a series of eligible unique Reels with viewsPerLike or viewsPerFollow set to N
- **THEN** each Reel gets one independent 1/N draw per configured action at first presentation, duplicates and non-canonical targets get no draw, and no fixed Nth-Reel pattern exists

#### Scenario: Platform confirmation remains required

- **WHEN** a cadence intent is dispatched but Edge cannot prove the new state on the same Reel and author
- **THEN** Cloud records no confirmed action and does not consume successful-action budget
