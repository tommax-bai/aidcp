## MODIFIED Requirements

### Requirement: Token Usage Cost Estimates

The admin console SHALL show estimated cost in the token usage detail table without relying on hard-coded model prices.

- The table SHALL include date, account, role, provider/model, prompt tokens, completion tokens, total tokens, estimated cost, and call count.
- Console MUST NOT estimate token cost from a hard-coded public model price table.
- Console MUST NOT compute cost locally from provider public list prices.
- Cloud MAY estimate a row's cost by applying a billing-derived internal price snapshot to that row's token counts.
- Cloud SHALL use the latest available billing-derived price for the same provider and model when no same-day price exists.
- A manual panel action SHALL refresh provider/model prices by querying T-1 and T-2 provider billing samples for recently used models.
- The manual refresh action MUST NOT be implemented as a scheduled task, cron job, or background worker.
- Rows for provider/model pairs without any historical billing-derived price MUST keep the estimated-cost column visible and show an honest pending/empty state.

#### Scenario: Manual price refresh updates estimates

- **GIVEN** T-1 or T-2 billing details contain a provider/model token charge
- **WHEN** an operator triggers the manual provider model pricing refresh
- **THEN** cloud derives an effective token price from billed amount and billed tokens
- **AND** stores the result as a billing-derived price snapshot
- **AND** subsequent `/api/llm-usage` responses may use that price for matching provider/model rows.

#### Scenario: Missing recent billing sample reuses historical price

- **GIVEN** a provider/model already has a billing-derived price snapshot from an earlier refresh
- **AND** T-1 and T-2 billing details contain no new sample for that provider/model
- **WHEN** `/api/llm-usage` returns rows for that provider/model
- **THEN** cloud estimates cost using the latest available historical billing-derived price
- **AND** the row does not show pending solely because recent billing data is absent.

#### Scenario: No historical billing price remains pending

- **GIVEN** a provider/model has no billing-derived price snapshot
- **WHEN** `/api/llm-usage` returns rows for that provider/model
- **THEN** `/usage` still shows the estimated-cost column
- **AND** that row shows an honest pending/empty cost state.
