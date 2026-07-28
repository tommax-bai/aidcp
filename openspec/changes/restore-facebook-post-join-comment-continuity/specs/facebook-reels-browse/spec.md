## ADDED Requirements

### Requirement: Reels re-entry MUST NOT depend on a non-empty ordinary feed as its only unlock

Re-authorizing the Reels surface SHALL be reachable for an account whose ordinary home feed produces nothing. A confirmed-empty or confirmed-exhausted ordinary feed is decisive evidence that the Reels surface should be re-authorized and SHALL return the fallback state to its authorizable state, exactly as a non-empty ordinary feed does.

An account MUST NOT be able to reach a state in which it has been returned to the ordinary feed, cannot produce content there, and can never be re-authorized onto Reels. Whatever returns the account to the ordinary feed — including an unconditional batch-tail browse command that carries no task identity — MUST NOT create that state.

#### Scenario: Empty ordinary feed re-authorizes Reels
- **WHEN** an account previously confirmed on Reels is returned to its ordinary home feed
- **AND** that feed is confirmed empty or confirmed exhausted
- **THEN** the fallback state becomes authorizable again
- **AND** the account can be sent back to the Reels surface

#### Scenario: Non-empty ordinary feed keeps its existing behaviour
- **WHEN** a non-empty ordinary feed arrives for an account previously confirmed on Reels
- **THEN** the fallback state becomes authorizable as it already did
- **AND** ordinary browsing continues on that feed

#### Scenario: Return to the ordinary feed cannot strand the session
- **WHEN** any command returns a Reels-confirmed account to the ordinary feed
- **THEN** the account either finds content there or becomes eligible for Reels re-authorization
- **AND** it does not remain on a surface that yields no work with no path off it
