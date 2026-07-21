## Why

Facebook ordinary Feed contains lightweight video cards that expose a stable `data-video-id`, publisher, caption, and post action bar but may omit a canonical post permalink or semantic `[role="article"]` wrapper. Edge currently drops or cannot re-target these cards, so they can terminate browsing as unreportable and never reach a bounded, auditable like decision.

## What Changes

- Recognize a lightweight ordinary-Feed video card only when one visible card boundary contains one stable video id, one video, publisher or caption evidence, and one post-level action bar; exclude embedded Reels rails and ambiguous/mismatched layouts.
- Derive a canonical `watch?v=<video-id>` note identity when no explicit post permalink exists, and reuse that exact identity in scanning, inline reading, liking, and post-action verification.
- Treat a qualifying video as viewed once when it is actually presented in the primary viewport, then make one session-idempotent ordinary like draw at a fixed probability of `0.25`.
- Keep mandatory interactions ahead of the random policy; keep text-risk, budget, cooldown, duplicate, note-scoped execution, and platform-confirmed receipt gates authoritative.
- Add Vietnamese Facebook action labels needed to locate and verify neutral/selected like and comment controls.
- Prevent a probability-handled Feed video from reaching a second ordinary LLM like decision while preserving continued browsing after a miss or blocked hit.
- After eight bounded Feed-continuation rounds still yield no reportable card, distinguish a confirmed Facebook home surface with present-but-unreportable physical cards from a truly empty, loading, login, or checkpoint page; report that observation so Cloud can authorize one transition to Reels.
- Reuse one supported-locale lexicon across Feed and Reels while retaining surface-specific structural proof: same-card action-bar ownership for Feed and active-video geometry/identity for Reels.

## Capabilities

### New Capabilities

- `facebook-feed-video-like-policy`: Defines viewed-video qualification, the one-draw 25% ordinary-like policy, strategy precedence, idempotency, and confirmed-success accounting for ordinary Facebook Feed videos.

### Modified Capabilities

- `facebook-feed-browse`: Lightweight Feed video cards become reportable, viewport-qualified browse items without mistaking embedded Reels rails for posts.
- `facebook-note-scoped-targeting`: Strict `data-video-id` evidence may derive and resolve the same canonical post identity when the card has no explicit permalink.
- `facebook-ui-locale-normalization`: Vietnamese neutral-like, unlike, and comment labels are supported for exact post-level action location and verification.

## Impact

- `aidcp-edge`: Feed layout/identity helpers, card extraction, inline read/like target resolution, CTA normalization, and focused Facebook fixtures/tests.
- `aidcp-cloud`: RoleDispatcher Feed-video probability policy, session-local decision bookkeeping, ordinary-appraiser bypass, logging, and focused/acceptance tests.
- Control/OpenSpec: cross-repo behavioral contract and implementation/deployment evidence.
- Existing interaction commands/receipts remain unchanged. `page.cards.listState` gains a present-but-unreportable Feed observation so Cloud can authorize Reels without treating the page as empty or the scroll as truly exhausted. No database schema, Console setting, or Edge installer is required.
