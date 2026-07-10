## Why

The manual provider/model price refresh can currently report "0 written, 10 skipped" even when billing credentials are valid, because provider billing detail names do not always contain the exact internal model id. Operators also cannot see the skip reason from the usage page toast, making `no_billing_sample` look like an opaque successful refresh.

## What Changes

- Normalize safe provider billing model labels before matching billing lines to internal model ids, starting with Volcengine Ark/Doubao billing names such as `Doubao-Seed-2.0-pro` versus runtime ids such as `doubao-seed-2-0-pro-260215`.
- Keep the honesty boundary: if provider billing details do not contain a token amount and bill amount for a matching model sample, cloud still returns a skip instead of synthesizing a public-list or fallback price.
- Make the usage page refresh result surface skipped reasons, so operators can distinguish missing credentials, unsupported providers, billing API failures, absent local usage, and absent billing samples.
- Add focused tests for alias matching, absent DashScope samples, and console skip-reason presentation.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `llm-token-usage-stats`: manual billing-derived price refresh must match provider billing samples through deterministic provider-specific model normalization where exact internal model ids are absent, and the console must expose refresh skip reasons honestly.

## Impact

- aidcp-cloud: billing price refresh model-line matching and tests.
- aidcp-console: token usage page refresh result message/detail rendering and tests.
- aidcp control repo: OpenSpec proposal/design/spec/tasks and validation.
- Production: cloud restart and console static release are required after code changes; no database schema or secret change is expected.
