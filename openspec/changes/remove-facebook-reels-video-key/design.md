## Context

The maintained Native Facebook reader currently emits a `videoKey` built from media attributes plus a session-local DOM element number. Rust uses it to prove movement, to suppress later fallback writes, and to retain a pending transition across later Cloud commands. Facebook may replace the video element or media URL without changing the Reel, so that implementation identity can drift independently of the business object. The resulting pending latch can make every later `page.scroll` read-only until the generic Cloud idle watchdog intervenes.

Cloud already has the right business boundary in most places: a canonical single-card Reel advances cadence, and existing specifications reject anonymous Reel views. The remaining inconsistency is that risk accounting currently accepts the same one-card shape with `noteId ?? '-'`, while failed Reels scroll receipts are excluded from generic recovery.

## Goals / Non-Goals

**Goals:**

- Keep Reels browsing and interaction progressing without any session-local media/DOM identity.
- Make canonical `noteId` the sole Reel business identity used for cards, view accounting, cadence, likes, and follows.
- Preserve honest outcomes: input dispatch is not success, missing identity is not a view, and only confirmed platform state is a successful interaction.
- Keep the implementation small: no temporary DOM identity, cross-command transition state, anonymous quota facts, retry debt, or new policy knob.

**Non-Goals:**

- Guarantee that every trusted input changes the Reel or that every transient Reel receives its desired dwell.
- Change Feed scrolling, global cadence values, risk limits, successful-like accounting, protocol v2, or Edge packaging/release.

## Decisions

### 1. Canonical `noteId` is the only Reel identity

The JavaScript probe will still resolve the unique active video and its current geometry so an input can be targeted safely, but its serialized result will not contain `videoKey`. A Reel is reportable only when the active video's freshly resolved container or canonical route yields an exact Facebook Reel URL.

Likes and follows receive that canonical `noteId` from Cloud and freshly resolve the active Reel at probe, commit, and verification time. They compare canonical `noteId`, author where applicable, and the requested selected state; they retain no DOM node or navigation identity between evaluations.

Alternative considered: retain `videoKey` only inside a command or introduce an opaque DOM token. Rejected because either still assigns business meaning to mutable media/DOM implementation state and adds a second identity lifecycle that the product does not need.

### 2. One trusted forward actuation per scroll command

Each Reels `page.scroll` performs a fresh active-video/axis probe, dispatches exactly one axis-specific trusted key, then performs one bounded post-actuation observation window. It reports a card only when the post-state has canonical `noteId` and either the pre-state had no canonical identity or the identity changed. Missing, unchanged, or ambiguous post-state returns one honest terminal receipt and clears all command-local state.

There is no key/wheel/button ladder and no pending transition stored on the session. This accepts a possible missed or skipped dwell as the cost of guaranteeing that one unstable observation cannot disable future scroll commands.

Alternative considered: keep the multi-actuator ladder and compare only `noteId`. Rejected because delayed route hydration could make multiple writes skip more than one Reel within a single command.

### 3. A canonical presentation is one shared view fact

Cloud validates the exact canonical Reel `noteId` before enqueueing the risk `view` fact. Only after that enqueue succeeds does the same `page.cards` event reach cadence selection. Missing or malformed identity produces no risk fact and no like/follow cadence, while normal content evaluation may still continue and later scrolling remains available. No `'-'` discriminator or deferred interaction debt is created.

### 4. Reels terminal receipts immediately re-enter normal scroll admission

When a confirmed Reels session returns a Reels-specific terminal scroll reason, Cloud sends one next scroll through `sendScrollCommand`. That path retains the existing view-quota gate, soft-pause/interaction holds, session limits, and dwell parameters. Thus recovery is prompt but not a high-rate bypass. Each Edge command remains independent; the generic 240-second idle nudge is only a final watchdog, not ordinary control flow.

## Risks / Trade-offs

- [Canonical route hydration can lag beyond the observation window] → Edge reports no view and Cloud performs the next normally paced scroll; it never fabricates identity or locks the session.
- [The single key may occasionally fail where an old wheel/button fallback worked] → The next independent Cloud command can try again under normal pacing; focused diagnostics expose terminal reasons and repeated failure.
- [A late route update could correspond to a transition triggered outside the command] → Accept it only within the bounded post-actuation window and only as a canonical active-Reel presentation; no write success beyond the view is inferred.
- [Edge and Cloud version skew] → Cloud already rejects malformed/multi-card cadence inputs and will be tightened to reject anonymous risk views; old Edge receipts continue to be honest failures. Deploy Cloud after integration; packaging an Edge client remains separate and explicit.

## Migration Plan

1. Land and validate Edge source changes and Cloud source changes independently.
2. Deploy Cloud to DEV from the clean canonical default checkout after integration and verify service/health/log boundaries.
3. Do not package or install Edge in this change; installed-client behavior remains unchanged until a separately authorized package/release.
4. Rollback is the prior Edge/Cloud commit pair; there is no schema or durable-data migration.

## Open Questions

None.
