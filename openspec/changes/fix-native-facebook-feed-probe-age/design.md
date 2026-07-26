## Context

Facebook automatic browse starts with a TypeScript facade command that is executed by the Rust Native Page Engine. The embedded browser router computes `documentAgeMs` from `Date.now()` and Chrome's high-resolution `performance.timeOrigin`; the resulting JavaScript number is fractional in real Chrome. Rust currently decodes the field as `u64`, maps the decode failure to the generic bounded-result `cdp_error`, and aborts before the startup Feed settle loop can schedule continued browsing.

The value is internal to the Native adapter and is used only to prove that an explicitly empty home Feed has remained stable for at least eight seconds.

## Goals / Non-Goals

**Goals:**

- Keep the existing unsigned-integer Rust contract and emit a matching finite, non-negative integer from the browser router.
- Cover both the producer shape and Rust consumer decode so a realistic fractional `timeOrigin` cannot regress startup.
- Preserve strict unknown-field rejection and the existing Native-only, bounded, honest failure behavior.

**Non-Goals:**

- Change Feed selection, settling, scrolling, Reels fallback, pacing, risk, or Cloud orchestration.
- Add retries, compatibility fallbacks, configuration, or a JavaScript execution fallback.
- Change the Edge-Cloud protocol, package an installer, or deploy OL.

## Decisions

### Normalize at the browser-router boundary

The router will floor the elapsed document age after applying the existing non-negative bound. This preserves elapsed-time ordering, matches Rust `u64`, and avoids widening the consumer model for a value whose sub-millisecond precision is irrelevant to the eight-second threshold.

Changing Rust to `f64` was rejected because it weakens an already useful bounded integer contract without providing product value. Adding coercion in Rust was rejected because the router is the source of the mismatched payload and should emit its declared shape.

### Test both sides of the internal boundary

The JavaScript router contract test will install a fractional browser time origin and assert an integer, non-negative `documentAgeMs`. A Rust unit test will feed the representative CDP envelope into `feed_probe_from_cdp` and prove the resulting `FacebookFeedProbe` decodes with the expected integer age.

This focused pair is preferred to adding a new JavaScript engine dependency to Rust or launching a real browser in the unit suite.

## Risks / Trade-offs

- [Flooring loses sub-millisecond precision] → The only consumer compares against an 8,000 ms stability threshold, so the loss is immaterial and conservative by less than one millisecond.
- [Separate producer and consumer tests could drift] → Both assert the same named field and representative value; existing encoded-router verification continues to ensure the shipped Native artifact embeds the source router.
- [A resident Edge process keeps the old Native binary] → Rebuild the canonical development artifact and restart the development runtime before live acceptance.

## Migration Plan

1. Land the focused Edge source and tests, then rebuild and verify the Native artifact.
2. Integrate through the default branch and deploy/publish only to `dev` from the canonical checkout.
3. Restart the active development Edge runtime before retrying the Facebook session.

Rollback is a normal revert and Native artifact rebuild. There is no data or protocol migration.

## Open Questions

None.
