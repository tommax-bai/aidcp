## Context

The cloud already captures and caches `accounts.nickname` through `AccountStore.getNickname(accountId)`. Console surfaces use a nickname-first fallback chain, but two Feishu paths still show raw IDs:

- `CaptchaCoordinator` builds P0/P1 blocking-alert cards with only `accountId`.
- Curated reference creation and other async result paths call `buildCommandResultCard` with only `accountId`, and the card renderer prints that ID in the account line.

The raw ID remains the stable runtime key for risk state, routing, persistence, and audits. The problem is presentation only.

## Goals / Non-Goals

**Goals:**

- Show stored nicknames in Feishu alert headers and command result account lines when available.
- Preserve honest fallback to the raw account ID when no nickname is known.
- Keep all internal APIs that target or persist account ownership keyed by `accountId`.
- Cover the two observed paths: unknown-blocking alert title suffix and curated-reference failure result card.

**Non-Goals:**

- No account lookup by display name for these asynchronous runtime paths.
- No database schema, migration, protocol, or Feishu command syntax changes.
- No attempt to backfill nicknames that have not yet been captured.

## Decisions

1. Extend Feishu card data with presentation-only `accountName`.
   - `AlertData` already has `accountName`; wire it from `CaptchaCoordinator`.
   - Add optional `accountName` to `CommandResult` and render the account line from `accountName ?? accountId`.
   - Alternative considered: replace `accountId` with nickname before card construction. Rejected because call sites and tests still need the stable ID available for fallbacks and future diagnostics.

2. Resolve display names at server wiring boundaries.
   - Inject a synchronous `getAccountName(accountId)` function into `CaptchaCoordinator`, backed by the existing `AccountStore.getNickname` cache.
   - Add a small server-local helper for async result cards so each call site can pass both ID and presentation name without awaiting PG.
   - Alternative considered: let `buildCommandResultCard` access `AccountStore` directly. Rejected because card rendering should stay pure and testable.

3. Preserve ID fallback and internal identifiers.
   - Card text uses nickname only when it is non-empty after trim.
   - `accountId` continues to be passed into schedulers, alert storage, logs, and card data for fallback.

## Risks / Trade-offs

- [Risk] A nickname may be missing or stale in the process cache. → Mitigation: fall back to the raw `accountId`; nickname capture remains a separate existing flow.
- [Risk] Displaying both nickname and ID would still make urgent cards noisy. → Mitigation: command result cards render nickname only when available; alert cards already retain ID in the structured data but the visible suffix becomes nickname-first.
- [Risk] Future result-card call sites can forget to pass `accountName`. → Mitigation: add focused tests for card rendering and for coordinator wiring; keep fallback behavior safe.
