# Proposal: Manual Billing-Derived Price Refresh

## Why

The usage page needs estimated token cost, but a scheduled billing sync adds deployment and operational complexity. The user wants the cost estimate to come from billing-derived effective prices, while keeping refresh explicit and operator-controlled.

## What Changes

- Add a manual "update provider model pricing" action on the token usage page.
- The action looks at models used on T-1 and T-2, queries provider billing details for those days, derives effective token prices by provider and model, and stores them in the billing price snapshot table.
- Estimated cost uses the latest available billing-derived price for the same provider and model, not only same-day snapshots.
- If T-1/T-2 have no new billing sample for a model, keep using the previously stored price.
- If a provider/model has never had a billing-derived price, keep the estimated-cost column visible and show a pending state.
- Do not add cron, background workers, or deployment-time scheduled tasks.

## Non-Goals

- No hard-coded public model price table.
- No periodic billing sync.
- No blocking LLM calls on billing-center availability.

## Validation

- `openspec validate manual-billing-price-refresh --strict`
- Cloud tests covering latest-price fallback and refresh target selection.
- Console tests/build after adding the manual refresh action.
