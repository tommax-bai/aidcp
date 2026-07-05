## MODIFIED Requirements

### Requirement: console provides token usage table and 10-minute chart

The management console SHALL provide a `/usage` page showing token usage by day, account, role, and model, plus a 10-minute total-token chart.

- The table SHALL include date, account, role, provider/model, prompt tokens, completion tokens, total tokens, estimated cost, and call count.
- Console MUST NOT estimate token cost from a hard-coded public model price table.
- Console MUST NOT compute cost locally from provider public list prices.
- Cloud MAY estimate a row's cost by applying a billing-derived internal price snapshot to that row's token counts.
- Billing-derived price snapshots MUST be keyed at least by provider, model, and usage day.
- Cost estimates MUST expose their source/date honestly enough that operators do not confuse them with real-time provider price catalogs.
- Rows without a matching billing-derived price snapshot MUST keep the estimated-cost column visible and show an honest pending/empty state instead of using a fallback price.
- The chart SHALL remain a single total-token line, constrained by the page filters and rendered on an `Asia/Shanghai` time axis.
- The page SHALL provide date range, account, role, and model filters.
- Role tags SHALL render as human-readable labels; unknown tags SHALL fall back to a readable form without exposing raw internal tag strings.
- The single-tenant `default` account SHALL remain honestly labelled as such until real multi-account usage is available.

#### Scenario: Usage table shows pending cost without billing-derived data

- **WHEN** billing-derived prices are unavailable for a usage row
- **THEN** `/usage` still shows the estimated-cost column
- **AND** that row shows an honest pending/empty cost state
- **AND** console does not show a hard-coded or public-list-price estimate

#### Scenario: Billing-backed estimate is displayed

- **WHEN** cloud has a billing-derived price snapshot matching a usage row's provider, model, and day
- **THEN** `/api/llm-usage` returns an estimated cost for that row
- **AND** `/usage` displays the amount in the estimated-cost column
- **AND** the UI exposes the estimate source/date
