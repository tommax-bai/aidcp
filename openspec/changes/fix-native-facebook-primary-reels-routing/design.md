## Context

Cloud already owns the Facebook primary-surface decision. For a Reels-primary session it sends `page.scroll{reason:'facebook_reels_primary'}` and waits for a canonical `page.cards{listKind:'reels'}` result before evaluating or counting content. The shipped Edge path is the Native Rust engine plus an embedded Facebook page router, but only the retired TypeScript session was updated when the primary-surface change landed.

The active Rust dispatcher currently navigates to `/reels/` only for `empty_feed_reels_fallback`; every other `page.scroll` reason uses the ordinary Feed/Reels continuation actuator. The embedded router likewise exempts only the fallback reason from its Reels-surface continuation guard. Both layers therefore need the same narrow reason classification.

## Goals / Non-Goals

**Goals:**

- Make the shipped Native executor recognize both authorized Reels-entry reasons.
- Reuse the existing navigation, readiness wait, canonical-card hydration, and honest failure boundaries.
- Prove the active Rust classification and embedded-router behavior with focused tests.
- Keep unrelated `page.scroll` reasons on their current Feed or Reels continuation paths.

**Non-Goals:**

- Changing Cloud surface authority, command payload shape, cadence, or accounting.
- Treating navigation or route readiness alone as success.
- Reworking the existing Reels reader or next-card actuator.
- Packaging, installing, deploying, or running real Facebook actions.

## Decisions

### Classify entry reasons once in the active Rust dispatcher

Add a small predicate used by the `NativeCommand::PageScroll` guard. It accepts exactly `facebook_reels_primary` and `empty_feed_reels_fallback`. This keeps configured entry and evidence-based fallback distinct at the protocol level while sharing their page action.

Alternative considered: make Cloud send the fallback reason for configured entry. Rejected because it would erase the distinction between environment authority and observed Feed exhaustion, weakening logs, recovery state, and auditability.

### Keep the existing Reels entry postconditions

After navigation the dispatcher continues to wait for Facebook readiness and poll the embedded router until it returns reportable cards. No new success receipt is introduced. Missing canonical identity remains pending, no-target, ambiguous, or an existing typed failure rather than a fabricated view.

Alternative considered: return success when `/reels/` loads. Rejected because a route can be ready without a canonical active Reel.

### Synchronize the embedded router allowlist

The page router will allow `facebook_reels_primary` through the same entry-hydration branch as `empty_feed_reels_fallback`. Other `page_scroll` reasons on a Reel surface continue to be refused so only the Native next-card actuator can advance Reels.

### Test the shipped path rather than the retired session

Add a Rust unit test for the exact entry-reason predicate and a JavaScript router contract showing that both entry reasons can return a canonical Reel card while an unrelated Feed-scroll reason remains rejected on Reels. Existing TypeScript session tests remain useful compatibility coverage but are not accepted as proof of Native routing.

## Risks / Trade-offs

- [The two active layers drift again] → Cover the same two-reason set in Rust and embedded-router tests, then run the Native gate.
- [A broad reason match redirects ordinary Feed work] → Match only the two explicit literals and retain a negative test for an unrelated reason.
- [Navigation is mistaken for platform progress] → Preserve canonical Reel-card polling and the existing honest terminal states.
