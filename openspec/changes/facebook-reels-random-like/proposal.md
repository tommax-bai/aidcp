## Why

Facebook Reels currently reuses the ordinary content-based interaction appraisal, so there is no bounded, auditable way to express the requested lightweight behavior of liking roughly one quarter of viewed Reels. A dedicated Reel policy is needed so the configured probability is the sole ordinary-like decision on that surface instead of an extra gate layered on top of the LLM.

## What Changes

- Detect each unique canonical Facebook Reel when Edge reports it as the active one-card Reels list.
- For each ordinary Reel presentation, make one injectable Bernoulli draw with probability `0.25`: a hit sends one note-scoped like intent and a miss records an explicit abstention.
- Keep explicit mandatory-interaction rules ahead of the Reel probability policy.
- Keep risk, budget, cooldown, note-scoped Edge execution, and platform-confirmed success accounting unchanged; a probability hit is an intent, not a claimed successful like.
- Prevent the later ordinary content appraiser from making a second like decision for the same Reel; keep non-Reel Facebook and all other platform interaction appraisal unchanged.

## Capabilities

### New Capabilities

- `facebook-reels-like-policy`: Defines the one-draw 25% ordinary-like policy for canonical Facebook Reels and its interaction with mandatory rules and existing safety gates.

### Modified Capabilities

None.

## Impact

- `aidcp-cloud`: interaction appraisal and focused/integration tests.
- Control/OpenSpec: new behavioral contract and implementation record.
- No protocol shape, database schema, Console surface, or Edge locator change is required.
- Runtime behavior changes on Cloud and therefore requires the normal `dev` deployment and health verification after integration.
