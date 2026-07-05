# Proposal: Billing-Only Token Cost Estimates

## Why

The usage page should not show hard-coded public model prices as a fallback. Public list prices drift, discounts and resource packages change the real cost, and a stale fallback looks more authoritative than it is.

Cost should only be shown when it is backed by billing-center data or a billing-derived internal price cache.

## What Changes

- Remove the console-side hard-coded token price table and the estimated-cost column that used it.
- Preserve the current token usage table and chart unchanged.
- Define the product rule for future cost work: any cost shown on `/usage` must be billing-derived.

## Non-goals

- This change does not yet integrate Alibaba Cloud or Volcengine billing APIs.
- This change does not add cloud database tables or credentials.
- This change does not alter token usage collection or aggregation.

## Validation

- `openspec validate estimate-token-cost-column --strict`
- console: `npm test`, `npm run build`
