## Why

On 2026-08-04 a live Facebook session died on its very first step: the session-start feed scan navigated to the Facebook home document and gave it only 8 seconds to become ready. The document was not ready in time, the command failed with `probe_failed`, and because nothing was reported the session stayed inert until Cloud's 240-second idle nudge re-drove it — a four-minute hole in which the account did nothing and never reached its configured primary Reels surface.

The preceding change `extend-facebook-reels-entry-readiness-window` had already established that 8 seconds is too tight for a real Facebook landing, but it widened only the two Reels-entry waits. The identical 8-second window remained on the other thirteen Facebook readiness waits, including the session-start feed scan that actually failed. Meanwhile the readiness probe polls every 250 ms, which spends CDP evaluations on a document that cannot plausibly be ready yet.

## What Changes

- Give every Facebook document-readiness wait one shared 30-second window instead of a per-call-site literal, so no navigation keeps the former 8-second boundary.
- Change the readiness probe cadence to a 3-second first probe followed by one probe every 2 seconds, replacing the 250 ms poll.
- Remove the Reels-specific readiness constant now that the shared window carries the same 30 seconds, and remove the per-call-site window argument so a call site cannot silently drift back to a shorter window.
- Raise the Facebook non-specialised command budget from 45 to 90 seconds across the request, admission, and engine-ceiling layers, and raise the Facebook identity bootstrap request from 12 to 40 seconds, so a 30-second readiness window plus each family's remaining inner waits still fails with its own named receipt instead of being cut into an outer synthetic timeout.
- Keep every existing outcome semantic: readiness alone still proves nothing, the honest failure at window exhaustion is unchanged, and no success is fabricated.
- Do not change Cloud behaviour, the protocol, the 180-second scroll/session budgets, the 240-second Cloud idle watchdog, the Xiaohongshu readiness path, packaging, or deployment.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-feed-continuity`: every Facebook navigation readiness wait uses one shared 30-second window probed at 3 seconds and then every 2 seconds, and each command family's outer budget stays larger than its own worst-case inner chain.

## Impact

- Owning repo: `aidcp-edge` — Native Facebook readiness wait and its call sites, the Facebook command timeout tables in the Native host, the Facebook identity bootstrap request value, and the timeout-chain contract test.
- Control repo: OpenSpec delta and delivery evidence.
- No Cloud, Console, protocol, database, or configuration change.
- Behavioural cost accepted deliberately: every Facebook navigation now spends at least 3 seconds before its first readiness probe.
- No Edge installer build or installed-client update unless separately requested; the running packaged client keeps the old windows until it is rebuilt.
