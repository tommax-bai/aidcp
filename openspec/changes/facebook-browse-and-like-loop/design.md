## Context

Facebook automatic browse and interact have zero implementation. The Facebook edge driver advertises `capabilities=['identity','overlay','comment','join']` and deliberately omits `browse`/`interact`; the cloud platform registry `facebook` entry only exposes `comment`. That omission is a safety feature, not an oversight: the edge assembly gate keys the BrowseSession on the `browse` capability string, so declaring `browse` for Facebook before a Facebook BrowseSession exists would mount the xhs BrowseSession — with xhs selectors, xhs collect/favorite semantics, and xhs read-time coefficients — onto a Facebook edge. That would be a silent cross-platform mis-mount, exactly the "static fake success" red line the system forbids.

The orchestration above the driver is already platform-neutral. The cloud role-dispatcher does two-layer translation (role events → edge commands via the single command out-gate; edge reports → role events), and the browse roles decide on structured `page.cards`/`note.detail` reports, not on selectors. So the platform-specific surface that must be built for Facebook is narrow: feed selectors, card/detail extraction into the structured shapes, the atomic like action with post-action verification, and a Facebook read-time model. Everything else is reuse.

This change also depends on the account-nurture discipline spine so a brand-new Facebook account is ramped through cold-start quotas and exposed to real throttle-backoff, instead of running the loop at full `normal` tempo on Day 1.

## Decisions

- Keep the reuse boundary at the edge driver layer; put every Facebook difference below the selector/atomic/mapping layer.
  - Rationale: the cloud two-layer translation and browse roles are already platform-neutral because they act on structured reports. Building Facebook as a driver-level BrowseSession keeps the cloud untouched and avoids a second orchestration surface.
  - Alternative considered: a Facebook-specific cloud browse path. Rejected — duplicates the role loop and drifts from the shared risk/pacing wiring.

- Land the `browse` capability flip and the Facebook BrowseSession atomically in one change; never split.
  - Rationale: the assembly gate mounts a BrowseSession by the `browse` capability string. A flip without a Facebook BrowseSession mounts the xhs BrowseSession on Facebook — a silent mis-mount. Co-landing is enforced by a spec requirement and a resolution test.
  - Alternative considered: declare `browse` first, implement the session later. Rejected — creates a live mis-mount window.

- Target zero changes to `protocol.ts` and reuse platform-neutral messages with optional payloads.
  - Rationale: the browse loop is already expressed in platform-neutral messages; Facebook needs no new message type. Deliberately avoiding new messages also side-steps a collision with the sibling feed-refresh change, which is adding the `feed.refresh` message and touches the protocol four-point sync. Two concurrent changes editing the two `protocol.ts` files would serialize badly.
  - Alternative considered: a `facebook.*` command family. Rejected — violates the platform-neutral protocol contract and adds another allowlist sync point.

- `collect` is an honest default/absent value for Facebook.
  - Rationale: Facebook has no favorite/collect concept. The structured shape carries a `collect` field for xhs; fabricating a number for Facebook would be a fake-success violation. It is defaulted/absent, honestly.
  - Alternative considered: reuse the reactions count as a stand-in collect. Rejected — semantically wrong and misleads downstream decisions.

- Like counting rides the cloud `RiskController.record` PG path; no parallel edge counter.
  - Rationale: risk final state is single-writer in the cloud. A second edge-local counter would create a shadow source of truth that the risk state machine cannot see. `like`/`view` are already inside the existing risk actions and quotas.
  - Alternative considered: edge-side like tally for pacing. Rejected — duplicates state the cloud already owns.

- Facebook browse/like commands must enter the edge active-command allowlist and carry a bounded idle watchdog.
  - Rationale: the allowlist omission is invisible to typecheck (the notification-monitor silent-drop class of bug: cloud `sent`, edge no action, no receipt, session livelocks until a watchdog kills it). Standalone Facebook commands must be routed to the browse handler and guarded by a route regression assertion, and the path must reuse browse-loop-resilience bounded idle so a stuck session is bounded.
  - Alternative considered: rely on typecheck to catch the omission. Rejected — the exhaustive protocol map in the two `protocol.ts` files does not cover the runtime allowlist.

- Default-off `AIDCP_FB_BROWSE_AUTO` with shadow-first rollout, deployed to `ol` during the isolation period.
  - Rationale: unattended browse/like on a new platform is high risk; shadow (browse-only or like-logged-not-executed) validates the structured reports and honest receipts before any real like, and the account-nurture spine keeps quotas conservative.

## Open Questions

- Facebook feed selector variability: the wide vs narrow layouts and the newsfeed vs group-feed vs page-feed surfaces may need distinct selector sets; a real-machine probe pins these before extraction code is written. Whether one BrowseSession covers all surfaces or the feed source is parameterized is open.
- Read-time / pacing coefficient standardization for Facebook: whether the Facebook-specific read-time model is calibrated inside this change or delegated to the account-nurture discipline spine (which owns the pacing/quota discipline). Leaning toward the spine owning the coefficients and this change only supplying the structured signals it needs.
