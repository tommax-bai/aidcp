## Context

`execute_facebook_reel_navigation` (`native/page-engine/src/facebook/reels.rs`) delivers one trusted forward key, then polls `wait_for_canonical_facebook_reel_card` every 300 ms for up to 15 s. Each poll issues two CDP evaluations — `reel_cards` (`feedCards()`) and `reel_probe` (`safeActiveReel()`) — and passes both results to `canonical_facebook_reel_card_matches`, which returns true only if ten conditions hold simultaneously.

Two facts about the readers determine this design:

1. **They are not independent.** `feedCards()` on a Reels surface calls `safeActiveReel()` on its first line and builds its article list from the single node that call returns (`native/page-engine/src/facebook-router/20-feed.js:122-124`). The probe reads the same function directly. So the card identity and the probe identity have one origin; they can differ only by the time between two CDP round trips.

2. **The card count is structurally bounded.** Because that article list is either `[active.root]` or `[]`, `feedCards()` on a Reels surface yields zero or one card, and its `listState` is `'ready'` exactly when the count is one. The `list_state == Ready` and `cards.len() == 1` conditions are therefore two spellings of "a card is present".

The active-Reel reader additionally self-rejects when the two largest videos are within one pixel of each other in both area and distance-to-centre (`00-shared.js:408-410`), which is the geometry of a half-completed page turn. That rejection is upstream of this predicate and is left alone here; it matters only because it explains why samples taken mid-transition are already scarce, making the extra conditions more expensive than they look.

Production evidence: on this machine today, 688 turns confirmed and 501 did not. Accounts kept accruing views across the same window, so a large share of the 501 were turns that happened.

## Goals / Non-Goals

**Goals:**

- Make the confirmation predicate consist only of conditions that can distinguish "this Reel is a different Reel" from "this Reel is the same Reel".
- Remove the card-vs-probe equality condition, which cannot detect source disagreement and does reject valid mid-settle samples.
- Preserve every property the spec already requires: canonical identity is the only proof, no card is emitted on an unconfirmed turn, no second write in the same command, key preference still updates only after real input.
- Let a consumer separate "did not advance" from "could not be read" from the receipt alone.

**Non-Goals:**

- Cloud's response to an unconfirmed turn — the immediate re-send, the missing retry ceiling, and the session action-limit auto-resume loop. Unchanged here.
- The 15 s window and 300 ms cadence. A relaxed predicate confirms on an earlier sample when the turn worked; the full window is still spent when it genuinely did not, and bounding that is the Cloud-side layer's job.
- The mid-transition self-rejection inside the active-Reel reader.
- Protocol shape. The returned identity reuses `ActionReceipt.note_id`.

## Decisions

**Keep both identities required to parse, drop only their equality.** The card identity is not load-bearing for movement, but it is load-bearing downstream: Cloud locates a Reel by the identity on the card when it later authorizes a like. Admitting a card whose identity does not parse would push a target Cloud cannot act on. So the predicate keeps "each parses" and drops "they are equal". Movement continues to be judged on the probe identity, as today.

*Alternative considered:* require only the probe identity, treating the card as opaque. Rejected — it moves a failure from a place that reports it (unconfirmed turn) to a place that reports it worse (a like that later finds no target).

**Replace the count check with a checked first-element read.** `cards.cards[0]` is reachable only because `cards.len() != 1` returns early above it. Removing that condition without changing the access would panic on an empty batch. A checked read that maps absent to unconfirmed preserves the existing outcome for an empty batch while removing the redundant test, and is the reason the count condition can be dropped rather than merely renamed.

**Read the timeout-path identity once and attach it, rather than re-deriving it.** The timeout path already probes the surface a second time and already branches on whether the identity parses — that is how it chooses between the two reason codes. The identity is then discarded. Attaching the value it already computed costs one field and no additional page read.

**Choose the reason code from the same value that is attached.** Today the code branches on "does an identity parse", which conflates "moved but failed a structural condition" with "did not move" under `reels_navigation_unconfirmed`. With the structural conditions gone, an identity that parses and differs from the pre-state will have confirmed during the polling window and never reach the timeout path, so the remaining reachable meaning of `reels_navigation_unconfirmed` narrows to what the spec scenario already says: identity resolved, identity unchanged. No extra comparison is introduced at the timeout — the narrowing is a consequence of the predicate change, and the attached identity lets a consumer verify it rather than trust it.

## Risks / Trade-offs

**[Relaxing the predicate admits page states the removed conditions rejected]** → The two retained identity conditions bound what can get through: a non-Reel surface cannot yield a canonical `/reel/` URL, and the movement condition still requires a different Reel than the pre-state. `is_video` and the identity-kind allowlist were narrowing an already-canonical Reel URL, which is the stronger check.

**[A confirmed transition could now report a card whose identity differs from the probe identity]** → Possible in principle when the surface advances between the two reads within one poll. Both are canonical Reels the account is being shown in sequence, and the card is the one that will be reported. The prior behaviour was not to report the correct one, but to report nothing and re-send the turn — which is what produced the spinning. Accepted.

**[Fewer unconfirmed turns could mask the Cloud-side spin rather than fix it]** → Stated explicitly: this change reduces how often the Cloud path is entered, not what it does when entered. The action-limit auto-resume loop stays reachable through any remaining unconfirmed turn and is tracked as the next layer.

**[No live Facebook account in automated tests]** → Coverage is unit-level against the predicate and the timeout receipt, plus the existing `fake_cdp` harness which already asserts `reels_navigation_unconfirmed`. Real-surface confirmation is a real-machine item.

## Migration Plan

No data or protocol migration. The change is behavioural inside one Native driver: an older Cloud reading the new receipt sees a familiar reason code with a populated `note_id`, a field it already tolerates on other receipts. A newer Cloud reading an older Edge sees an empty `note_id` and behaves as it does today. Rollback is reverting the Edge commit and rebuilding the engine; no state is written that would outlive it.
