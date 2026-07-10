# Proposal: Billing-Backed Token Cost Estimates

## Why

The usage page should show an estimated cost next to token totals, but it must not use hard-coded public model prices as a fallback. Public list prices drift, discounts and resource packages change the real cost, and a stale fallback looks more authoritative than it is.

Cost should be estimated only from billing-center data or a billing-derived internal price cache. When billing data has not arrived yet, the column should stay visible and honestly show that the row is waiting for billing data.

## What Changes

- Remove the console-side hard-coded token price table.
- Keep the `/usage` estimated-cost column immediately after total tokens.
- Add cloud-side billing-derived price snapshots keyed by provider, model, and usage day.
- Extend `/api/llm-usage` rows with provider metadata and optional cost estimates derived from those snapshots.
- Show `Pending billing`/empty cost honestly when no billing-derived snapshot exists for a row.

## Non-goals

- This change does not put public price tables or provider list prices into console code.
- This change does not block LLM calls or usage reads on live billing-center API latency.
- This change does not add billing AccessKey management to the console.

## Validation

- `openspec validate estimate-token-cost-column --strict`
- cloud: `npm test`, `npm run build`
- console: `npm test`, `npm run build`
