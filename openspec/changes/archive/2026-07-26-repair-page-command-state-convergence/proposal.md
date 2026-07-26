## Why

Two live DEV failures show that Edge and Cloud can disagree about whether a page command is executable or which list surface currently owns the browser. Xiaohongshu task commands are rejected by the same quiesce state that correctly blocks ordinary browsing, while Facebook can navigate to Reels without committing Reels state; both paths then lose immediate recovery and appear healthy but stop making progress.

## What Changes

- Admit a Native Xiaohongshu command when it carries the currently acquired task lease, while continuing to reject ordinary browse commands and stale/foreign task commands during the lease.
- Preserve the original search activity correlation and emit one schema-valid terminal receipt when Native admission or execution fails, so Cloud can finish the waiting step immediately without recording a search that never reached the page.
- Keep Native Xiaohongshu AI search compatible with the live textarea-based composer: use trusted CDP input, verify the exact keyword before Enter, reuse a matching `search_result_ai` route, and wait boundedly for result-card hydration.
- Treat a confirmed Facebook Reels route with a not-yet-readable active card as a recoverable Reels transition rather than reverting Edge state to Feed.
- Keep Cloud's one-shot Reels authorization retryable until Edge confirms a usable Reels card, and perform bounded surface-aware recovery instead of waiting for the generic 240-second idle nudge.
- Add focused Edge/Cloud regression coverage for task-lease admission, honest search failure correlation, late Reels rendering, retry idempotence, and prevention of Reels-to-home rollback.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `edge-task-execution-coordination`: task takeover pauses ordinary browse work without blocking commands owned by the current task lease.
- `platform-search-activity`: pre-actuation Native failures retain activity correlation and produce exactly one valid `not_submitted` terminal.
- `facebook-feed-continuity`: a confirmed Reels navigation remains a Reels-owned surface while the first card is still rendering, and fallback authorization remains retryable until confirmation.
- `browse-loop-resilience`: a recoverable list-surface transition failure is retried within a bounded interval rather than relying on the generic idle watchdog.

## Impact

- `aidcp-edge`: Native browse-session admission/reporting, Native AI-search actuation/parsing, Facebook Reels transition state, and focused tests.
- `aidcp-cloud`: Facebook fallback authorization/retry state, RoleDispatcher recovery behavior, and focused tests.
- Existing Cloud message types remain unchanged; the repair uses current optional search receipt and page/action fields.
- DEV Cloud is redeployed after integration. Source-built Edge production components are validated locally against the exact accounts; no installer is built unless separately requested.
