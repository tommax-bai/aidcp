## MODIFIED Requirements

### Requirement: console provides token usage table and 10-minute chart

The management console SHALL provide a `/usage` page showing token usage by day, account, role, and model, plus a 10-minute total-token chart.

- The table SHALL include date, account, role, model, prompt tokens, completion tokens, total tokens, and call count.
- Console MUST NOT estimate token cost from a hard-coded public model price table.
- Console MUST NOT derive a cost by multiplying total tokens by an average price when billing-derived input/output prices are unavailable.
- If a future implementation shows cost on this page, that cost MUST come from billing-center data or an internal cache derived from billing-center data, and the UI MUST expose that source/date honestly.
- The chart SHALL remain a single total-token line, constrained by the page filters and rendered on an `Asia/Shanghai` time axis.
- The page SHALL provide date range, account, role, and model filters.
- Role tags SHALL render as human-readable labels; unknown tags SHALL fall back to a readable form without exposing raw internal tag strings.
- The single-tenant `default` account SHALL remain honestly labelled as such until real multi-account usage is available.

#### Scenario: Usage table remains token-only without billing-derived cost

- **WHEN** billing-derived prices are unavailable
- **THEN** `/usage` shows the token table and chart without a cost column
- **AND** console does not show a hard-coded or average-price estimate

#### Scenario: Future cost display is billing-backed

- **WHEN** a future implementation displays a cost value on `/usage`
- **THEN** the value is derived from billing-center data or a billing-derived internal cache
- **AND** the UI makes the data source/date clear enough that operators do not confuse it with a real-time provider price catalog
