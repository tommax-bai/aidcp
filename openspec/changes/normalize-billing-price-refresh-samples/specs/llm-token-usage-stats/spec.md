## ADDED Requirements

### Requirement: Manual Billing Price Refresh Sample Matching And Reporting

The manual provider/model price refresh SHALL derive prices from provider billing details when a billing sample can be deterministically matched to a local provider/model/day target, even if the provider billing label does not contain the exact internal runtime model id.

- Cloud SHALL preserve exact runtime model id matching.
- Cloud MAY add provider-specific deterministic aliases for billing labels, but MUST NOT use fuzzy similarity, public list prices, or guessed fallback prices.
- Alias matching MUST be specific enough to identify the model family and concrete variant; generic provider or family fragments alone MUST NOT match.
- If billing details do not contain a matching token quantity and a billing-derived amount from the same row, cloud SHALL return `no_billing_sample` for that target and MUST NOT write a price snapshot.
- Cloud MAY derive the row amount from same-row token unit price and token quantity when the provider rounds the billed amount to zero, but MUST NOT use public list prices or guessed fallback prices.
- The console SHALL surface skipped reason counts from the refresh response, not only the number of skipped model-days.

#### Scenario: Volcengine billing label matches runtime model id by deterministic alias

- **GIVEN** local usage contains `provider='volcengine'` and model `doubao-seed-2-0-pro-260215`
- **AND** Volcengine billing details contain token rows labelled `Doubao-Seed-2.0-pro` or `Doubao_Seed_2.0_pro_32k_infer_input`
- **WHEN** an operator triggers the manual provider model pricing refresh
- **THEN** cloud derives a billing-derived price snapshot for `doubao-seed-2-0-pro-260215`
- **AND** cloud MUST NOT require the billing row to contain the exact `-260215` runtime suffix.

#### Scenario: Missing provider billing sample remains an honest skip

- **GIVEN** local usage contains a DashScope model target for a checked day
- **AND** Aliyun billing details for that day contain no DashScope token billing row for that model
- **WHEN** an operator triggers the manual provider model pricing refresh
- **THEN** cloud returns `skipped[].reason='no_billing_sample'` for that target
- **AND** cloud writes no synthetic or public-price snapshot for that target.

#### Scenario: Volcengine rounded amount uses same-row token unit price

- **GIVEN** local usage contains `provider='volcengine'` and model `doubao-seed-character-260628`
- **AND** Volcengine billing details contain matching Doubao token rows with `Count`, `Unit='千tokens'`, `Price`, `PriceUnit='千tokens'`, and rounded `PretaxAmount='0.00'`
- **WHEN** an operator triggers the manual provider model pricing refresh
- **THEN** cloud derives the price snapshot from same-row `Price × Count`
- **AND** cloud MUST ignore non-token quantity rows such as image counts for token price snapshots.

#### Scenario: Console summarizes refresh skip reasons

- **GIVEN** the manual refresh response contains skipped targets with reasons such as `no_billing_sample` or `missing_credentials`
- **WHEN** the usage page shows the refresh result
- **THEN** the operator-facing message includes reason counts using readable labels
- **AND** a zero-write refresh with skipped targets is presented as a warning or otherwise non-green outcome.
