## Why

Feishu alerts and asynchronous command result cards currently expose raw account IDs in operator-facing text even when the cloud already knows the account's real nickname. This makes urgent cards harder to read and contradicts the existing nickname-first operator experience in the console and command input.

## What Changes

- Display the account nickname in Feishu P0/P1 alert card headers when `accounts.nickname` is available, falling back honestly to the raw account ID only when no nickname has been captured.
- Display the account nickname in Feishu command result card account lines for asynchronous outcomes such as curated-reference creation failures.
- Keep all routing, persistence, audit, and command targeting keyed by the real `accountId`; nickname is presentation-only.
- Do not introduce a database schema, protocol, or Feishu command syntax change.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `captcha-incident-handling`: P0/P1 blocking-alert cards should identify the affected account with the stored nickname when available.
- `feishu-command-ingestion`: command result cards should identify related accounts with the stored nickname when available while preserving honest status semantics.

## Impact

- Affected repo: `aidcp-cloud`.
- Affected areas: Feishu card data model/rendering, captcha coordinator card wiring, curated action result-card wiring, related unit tests.
- No edge, console, protocol, database, or deployment contract changes.
