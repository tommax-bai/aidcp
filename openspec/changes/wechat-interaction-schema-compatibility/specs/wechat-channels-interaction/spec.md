## ADDED Requirements

### Requirement: Interaction schema rollout MUST degrade by capability instead of disabling safe reads

Cloud MUST distinguish the base interaction schema from the migration `0046` outbound retry schema. When the base schema is complete and the database is in the exact pre-`0046` shape, Cloud MUST start the interaction domain in a compatibility read-only mode rather than omitting the customer interaction API. In that mode Cloud MUST preserve interaction reads, sync, auth-state reads, and comment/DM read controls, while all comment-reply and DM-send paths MUST fail closed before a send attempt is created.

Cloud MUST treat the exact completed `0046` shape as full mode. A partially applied or otherwise inconsistent `0046` shape MUST NOT enter either compatibility or full mode and MUST keep the interaction domain disabled with an explicit startup error. Startup MUST NOT execute schema DDL.

#### Scenario: Exact pre-0046 schema restores safe reads

- **GIVEN** the base interaction schema is complete
- **AND** the active-attempt partial unique index from migration `0046` is absent
- **AND** the legacy `retryable` column is present
- **WHEN** Cloud starts the interaction domain
- **THEN** Cloud registers the customer interaction API in compatibility read-only mode
- **AND** interaction lists, sync, auth-state reads, and comment/DM read controls remain available

#### Scenario: Compatibility mode closes outbound capabilities at both gates

- **GIVEN** Cloud is running the interaction domain in compatibility read-only mode
- **WHEN** runtime controls are projected or an outbound comment reply / DM send is requested
- **THEN** comment-reply and DM-send controls are false
- **AND** the send orchestrator rejects the outbound request before creating a send attempt
- **AND** comment and DM read controls retain their independently configured values

#### Scenario: Completed migration preserves full behavior

- **GIVEN** the base interaction schema is complete
- **AND** the active-attempt partial unique index from migration `0046` is present
- **AND** the legacy `retryable` column is absent
- **WHEN** Cloud starts the interaction domain
- **THEN** Cloud uses full mode
- **AND** the existing global write configuration continues to govern outbound capabilities

#### Scenario: Partial migration fails closed

- **GIVEN** only one of the two migration `0046` schema markers has reached its final state
- **WHEN** Cloud starts the interaction domain
- **THEN** Cloud rejects the inconsistent schema state
- **AND** Cloud does not register the interaction customer API
- **AND** Cloud does not execute corrective DDL automatically
