## Why

Facebook automatic browsing and liking have zero implementation in the system today: the whole browse-and-interact loop is xhs-only. The Facebook edge driver deliberately advertises `capabilities=['identity','overlay','comment','join']` and does NOT declare `browse`/`interact`, and the cloud platform registry entry for `facebook` only exposes `comment`. That deliberate omission exists because the edge assembly gate keys the BrowseSession on the `browse` capability string, so declaring `browse` for Facebook before a Facebook-specific BrowseSession exists would attach the xhs BrowseSession (with xhs selectors, xhs collect semantics, xhs read-time coefficients) onto a Facebook edge — a silent cross-platform mis-mount.

The underlying orchestration is already platform-neutral and worth reusing: the cloud role-dispatcher runs a two-layer translation (role events → edge commands, edge reports → role events), and the browse-loop roles decide on structured `page.cards`/`note.detail` reports rather than on selectors. All the Facebook-specific difference — feed selectors, card extraction, the like atomic action, and the read-time model — belongs strictly below the edge driver's selector/atomic/mapping layer. This change brings Facebook into that same cloud event-driven browse loop with net-new work concentrated in the edge Facebook driver, and it leans on the account-nurture discipline spine so a fresh Facebook account gets ramped quotas and real throttle-backoff instead of running the loop at full `normal` tempo.

## What Changes

- Facebook feed self-driving browse loop reuses the existing cloud event-driven role orchestration (`feed.entered` → pick card → open → deep-read → interact → back → `feed.entered`), with cloud roles deciding on structured `page.cards`/`note.detail` reports and never on Facebook selectors.
- Facebook like is an atomic edge action with mandatory post-action verification: the like button/state must truly toggle before reporting `ok`, otherwise it honestly reports `no_target` (never `count||1`, never a silent fake success). Like counting rides the cloud `RiskController.record` PG path — no parallel in-memory counter.
- Facebook browse/like standalone commands are added to the edge `onMessage` active-command allowlist (or they get silently dropped), each command has a bounded timeout with an honest `timeout`/`no_target` receipt, and the Facebook path carries a bounded idle watchdog reusing browse-loop-resilience.
- The `browse` capability flip for Facebook lands atomically together with the Facebook BrowseSession implementation in the same change — never split — so the assembly gate can never mis-mount the xhs BrowseSession on a Facebook edge; Facebook payloads map faithfully into the existing structured shapes (Facebook has no collect/favorite, so `collect` is an honest default, never a fabricated value).
- Everything ships default-off behind the `AIDCP_FB_BROWSE_AUTO` kill switch with a shadow mode first (browse-only, or like logged but not executed) before real likes are allowed.
- Target zero changes to `protocol.ts`: reuse the existing platform-neutral messages and optional payloads, deliberately avoiding the new `feed.refresh` message being introduced by the sibling feed-refresh change.

## Capabilities

### New Capabilities

- `facebook-browse-and-like-loop`: Defines Facebook's self-driving feed browse loop over the shared cloud role orchestration, the verified atomic like action, the active-command allowlist plus bounded idle watchdog, atomic browse-capability/BrowseSession co-landing, and default-off shadow-first rollout.

### Modified Capabilities

- `platform-runtime-abstraction`: Facebook declares `browse` and `interact` capabilities and the cloud session-start platform gate admits the Facebook browse loop, with edge and cloud capability vocabularies aligned word-for-word.

## Impact

- Affected repos: `aidcp-edge` (new `src/facebook/`: Facebook feed selectors, card extraction → `page.cards`/deep-read, the like atomic executor with post-action verification, the Facebook idle watchdog), `aidcp-cloud` (platform registry `facebook` gains `browse`+`interact`, session-start platform gate opens for Facebook, role-driven Facebook browse), `aidcp` (this change document only).
- Protocol: target zero changes to either `protocol.ts`; no `facebook.*` message types. This deliberately avoids colliding with the sibling feed-refresh change's new `feed.refresh` message and keeps the two `protocol.ts` files a word-for-word pair.
- Reuse-first: reuse the cloud role-dispatcher two-layer translation, the browse roles that act on structured `page.cards`/`note.detail`, the existing `like`/`view` risk actions and quotas, and the browse-loop-resilience bounded-idle watchdog. No new orchestration surface.
- Dependency: depends on `account-nurture-discipline-spine` for cold-start ramped quotas and real throttle-backoff so a new Facebook account is not run at full `normal` tempo.
- Config/rollout: default-off `AIDCP_FB_BROWSE_AUTO`, shadow first. Deploy target `ol` during the isolation period; register real-machine acceptance items in the backlog.
- Serialization: touches the platform registry and the edge assembly gate (hot files) — must be sequenced against other Facebook-registry changes, not run in parallel on the same lines.
