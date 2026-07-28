## ADDED Requirements

### Requirement: Reels re-entry MUST NOT require a non-empty ordinary feed as its only unlock

An account whose ordinary home feed produces nothing SHALL still be able to be re-authorized onto the Reels surface. Re-authorization MUST NOT depend solely on a non-empty ordinary feed returning, because an account is on Reels precisely when its ordinary feed produced nothing — that unlock can never fire for the accounts that need it.

The re-entry evidence SHALL be a scroll receipt reporting no available target on the ordinary feed. A stale ordinary-feed empty/exhaustion report arriving while the account is already confirmed on Reels MUST NOT unlock re-entry: such a report is most likely a late signal from before the surface switch, and treating it as current would mistake stale emptiness for a genuine return to an empty home feed.

Re-entry SHALL be bounded per session. Once the bound is spent, the browse loop MUST reach a terminal state rather than alternating between two surfaces that both yield nothing.

#### Scenario: Confirmed on Reels, returned to an empty ordinary feed
- **WHEN** an account confirmed on Reels is returned to its ordinary home feed and a scroll there reports no available target
- **THEN** the fallback state returns to its authorizable state and Reels is authorized again
- **AND** the account is not left on a surface that yields no work

#### Scenario: Stale ordinary-feed empty report does not unlock
- **WHEN** an ordinary-feed empty or exhaustion confirmation arrives while the account is already confirmed on Reels
- **THEN** it does not reopen the fallback epoch
- **AND** the existing epoch idempotency is unchanged

#### Scenario: Non-empty ordinary feed keeps its existing behaviour
- **WHEN** a non-empty ordinary feed arrives for an account confirmed on Reels
- **THEN** the fallback state becomes authorizable as it already did
- **AND** ordinary browsing continues on that feed

#### Scenario: Re-entry is bounded
- **WHEN** re-entry has already been used its allowed number of times in one session
- **THEN** further no-target scroll receipts do not reopen the epoch
- **AND** the session reaches a terminal state instead of alternating indefinitely
