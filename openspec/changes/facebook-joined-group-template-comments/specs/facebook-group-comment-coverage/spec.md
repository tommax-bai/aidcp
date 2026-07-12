## ADDED Requirements

### Requirement: Joined-group coverage selector is the normal Facebook comment container source

The Facebook comment pipeline SHALL use the joined-group coverage selector as the normal source of comment containers for unpinned Facebook comment attempts. The selector MUST only return groups the account itself has joined (`status='joined'`) and MUST return one concrete group URL for edge to use as `search.execute.container`. It MUST NOT return operator-configured container rows, random imported targets, or any whole-site search sentinel.

#### Scenario: Normal comment uses an account joined group
- **WHEN** an unpinned Facebook comment attempt starts for account A
- **THEN** the selected search container is one of account A's own joined membership rows and edge receives that group URL as the scoped search container

#### Scenario: No joined group does not fall back to legacy containers
- **WHEN** account A has no joined membership rows
- **THEN** the attempt ends with an honest no-targets result and MUST NOT fall back to legacy account-configured containers or whole-site search

## MODIFIED Requirements

### Requirement: Daily coverage iterates an account's joined groups oldest-covered-first

The coverage selector SHALL, per account, select from that account's own joined groups the least-recently-covered ones past a per-group cooldown floor, then pick within a small window to avoid lock-step ordering. It MUST guarantee eventual coverage of every joined group without repeatedly commenting in the same few groups, and MUST only comment in groups the account itself has joined. When no joined group satisfies warmup/cooldown and the relaxed fallback is enabled, the selector SHALL fall back to joined groups ordered least-recently-commented; the relaxed result MUST be flagged for human review and MUST still exclude non-joined or left groups.

#### Scenario: Coverage rotates and does not hammer
- **WHEN** an account has many joined groups and a daily coverage slice
- **THEN** the least-recently-covered eligible group is chosen and a just-commented group is not selected again until its cooldown floor passes

#### Scenario: Only joined groups are commented
- **WHEN** the coverage selector runs for an account
- **THEN** it never comments in a group that account has not joined

#### Scenario: Relaxed fallback still chooses least-recently-commented joined groups
- **WHEN** all of an account's joined groups are inside warmup or cooldown and relaxed fallback is enabled
- **THEN** the selector chooses from `status='joined'` groups ordered by least-recently-commented and flags the result as relaxed for review

## REMOVED Requirements

### Requirement: The comment-source switch is per-account, never global

**Reason**: Facebook comments no longer switch between operator-configured containers and joined-group coverage. Joined-group selection is the normal source for unpinned Facebook comment attempts, so a per-account source switch is no longer the contract.

**Migration**: Keep rollout safety under the existing Facebook comment kill switch, account schedule toggles, caps, risk gates, and review. Legacy source-switch configuration, if present, must not be required for normal joined-group target selection.
