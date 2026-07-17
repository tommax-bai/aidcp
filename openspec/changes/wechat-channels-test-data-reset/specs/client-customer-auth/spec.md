## ADDED Requirements

### Requirement: Customer test-data reset route is narrow and idempotent
customer-auth SHALL expose `POST /environments/:envKey/interactions/test-reset` only when the dev reset capability is enabled. The request MUST require an `Idempotency-Key`, MUST accept exactly `{channel:"comment"|"dm"}`, and MUST execute inside the same enabled-user, authoritative env ownership, and interaction account/platform binding boundary as the inbox APIs. The interaction list response SHALL include only a boolean `testTools.dataResetEnabled` exposure flag and MUST NOT expose deployment credentials or internal feature-flag values.

#### Scenario: Owned dev environment submits valid reset
- **WHEN** an enabled customer sends a valid channel reset for an environment they currently own with a new idempotency key
- **THEN** customer-auth returns the current envKey/accountId, selected channel, deletion counts, action request id and an honest accepted status after the reset command is delivered

#### Scenario: Request contains extra scope
- **WHEN** a reset body includes accountId, wildcard channel, scopeExternalId, or any unknown field
- **THEN** customer-auth rejects it as validation failure without data deletion

#### Scenario: Idempotent replay
- **WHEN** the same actor repeats a completed reset request with the same idempotency key and resource scope
- **THEN** customer-auth returns the stored response without performing a second deletion or dispatch
