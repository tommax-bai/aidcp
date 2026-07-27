## Context

The Native first-post path issues up to four `browse.scroll` commands. The Facebook router currently starts a smooth viewport scroll, waits 450 ms for that motion, and immediately calls `feedCards()`. On slow group pages, the React feed has not hydrated by that snapshot, so the Rust loop can exhaust every round before any post card becomes observable.

The router's returned `PageCards` snapshot is the evidence consumed by the Rust selection loop. A delay added only after the router returns would postpone the Rust decision while still evaluating stale pre-delay evidence.

## Goals / Non-Goals

**Goals:**

- Add a fixed 2-second hydration settle after each first-post scroll and before that round's `feedCards()` probe.
- Retain the existing 450 ms smooth-scroll completion wait.
- Preserve the fixed four-round bound and all existing candidate eligibility and exact-group checks.
- Cover the wait/probe ordering with a focused regression test.

**Non-Goals:**

- No adaptive loading observer, retry setting, configuration knob, or additional scroll round.
- No changes to search-mode comments, standalone group join, Cloud orchestration, protocol shapes, or UI.
- No claim that elapsed time alone proves Facebook rendered a post; missing candidates remain an honest failure.

## Decisions

### Put the settle inside the router scroll operation

The router SHALL wait 450 ms for the existing smooth-scroll motion, then wait an additional 2 seconds, and only then call `feedCards()`. This makes the returned `PageCards` evidence reflect the settled page.

Adding a Rust-side delay after `evaluate_facebook_router()` was rejected because the router has already captured its card snapshot at that point. Dispatching a second standalone probe after sleeping would add another protocol operation and broaden the change unnecessarily.

### Keep a fixed delay and the existing round bound

The delay is a constant rather than a new operator setting. The observed failure is insufficient hydration time, and the user selected a deterministic 2-second settle. The selector still performs an immediate initial probe and at most four scroll rounds.

### Preserve the command deadline

Four exhausted rounds can add up to 8 seconds. The existing Native command deadline remains authoritative; this change does not weaken timeouts or convert a timeout/no-candidate result into success.

## Risks / Trade-offs

- [First-post selection can take up to 8 seconds longer when no candidate appears] → Keep the existing four-round cap and stop immediately when a candidate or exhaustion evidence is returned.
- [A fixed 2-second settle may still be insufficient on an exceptionally slow page] → Preserve an honest non-success; do not add unobserved retries or fallback to search.
- [Changing only source fragments could leave bundled Native assets stale] → Rebuild the page-engine artifact and run integrity plus focused Native tests before integration.
