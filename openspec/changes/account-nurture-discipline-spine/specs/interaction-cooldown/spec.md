## ADDED Requirements

### Requirement: Post-restart cold-start quiet period prevents pacing burst

Because the per-action minimum-interval cooldown and per-session search counters are in-memory state that is zeroed on process restart, the system SHALL apply a per-account cold-start quiet period (default a few minutes) after a process restart, during which burst dispatch is suppressed so the restart moment cannot bypass the pacing cooldown and emit an action burst. Daily quotas are already persisted in PostgreSQL and are replayed on restart, so they MUST NOT be reset or altered by the quiet period.

#### Scenario: First post-restart batch is paced, not bursted
- **WHEN** the cloud process restarts and an account becomes eligible again while inside the cold-start quiet period
- **THEN** the first actions are pacing-suppressed and do not emit a burst that bypasses the min-interval cooldown

#### Scenario: Quiet period expires and normal cooldown resumes
- **WHEN** the cold-start quiet period elapses for an account
- **THEN** the account resumes the normal per-action min-interval cooldown behavior

#### Scenario: Daily quotas survive the restart untouched
- **WHEN** the process restarts
- **THEN** the account's persisted daily quota counters are replayed from PostgreSQL and are not reset or altered by the quiet period
