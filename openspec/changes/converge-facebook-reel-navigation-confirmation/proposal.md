## Why

`facebook-reels-native-scroll` already states that canonical `noteId` transition is the only proof of Reels progress, and that active-video uniqueness, control structure, and DOM shape MUST NOT be prerequisites. The installed implementation does not match that spec: confirming one page turn requires ten simultaneous conditions, and six of them are structural or redundant. Roughly four in ten delivered page turns therefore fail to confirm on this machine (688 confirmed vs 501 ambiguous today), even though the account keeps accruing views — the turn happened, the confirmation could not see it.

The most costly of those six is a self-comparison masquerading as cross-validation: the probe side reads `safeActiveReel()`, and the card side reads `feedCards()`, which on a Reels surface calls `safeActiveReel()` on its first line and reports only the node it returned. Requiring the two identities to be equal cannot detect any source disagreement — there is only one source — but it does reject every sample where the page moved between two CDP round trips, which is exactly what happens right after a forward key is delivered.

The spec's own honest-termination scenarios distinguish "canonical identity remains unchanged" (`reels_navigation_unconfirmed`) from "canonical identity remains absent" (`reels_identity_unresolved`). The implementation picks between those two reasons by testing only whether an identity parses, never whether it changed, so a page turn that did move but failed one of the structural conditions is reported under the reason reserved for a page that did not move. Cloud consequently cannot tell a stuck Reel from an unreadable one and re-sends the turn either way.

## What Changes

- Converge the post-turn confirmation predicate to the four conditions that carry information: the output is a card batch, its list kind is `reels`, both the card identity and the probe identity parse as canonical Reel URLs, and — when movement is required — the probe identity differs from the pre-turn identity.
- Remove the six conditions that do not: list state `Ready` and card count `== 1` (equivalent to each other on a Reels surface, where the reader yields either zero or one card), probe `ok` (already implied by identity parsing, since a failed probe carries no identity field), `is_video`, the `note_id_kind` allowlist, and the card-identity-equals-probe-identity check.
- Replace the fixed `cards[0]` index with a checked first-element read, so removing the card-count condition cannot panic on an empty batch; an absent card means unconfirmed, preserving today's behaviour without the redundant test.
- Carry the already-observed canonical identity back on the timeout path, so `reels_navigation_unconfirmed` is emitted with the identity the driver is standing on rather than an empty field. This makes "identity unchanged" and "identity unreadable" separable at the receipt level, as the spec's scenarios already assume. No card is emitted, preserving the existing no-card rule.
- Do not change Cloud's handling of an unconfirmed turn, the absent retry ceiling, or the session action-limit auto-resume loop that turns repeated unconfirmed turns into idle spinning. Those are a separate layer and stay out of this change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-reels-native-scroll`: state that post-turn confirmation rests on canonical identity transition alone, name the structural observations that MUST NOT gate it, and require the unconfirmed receipt to carry the observed canonical identity so an unchanged Reel is distinguishable from an unreadable one.

## Impact

- Owning repo: `aidcp-edge`, Native page engine Facebook Reels driver (`native/page-engine/src/facebook/reels.rs`) and its receipt helper in `native/page-engine/src/facebook/shared.rs`.
- No protocol change: the returned identity reuses the existing `ActionReceipt.note_id` field. No new message type, no Cloud-side contract change, no `docs/protocol.md` edit.
- Cloud behaviour is unchanged by this change alone. Confirmed turns increase, so the existing unconfirmed-handling path is exercised less often, but its logic is untouched.
- Risk: relaxing the predicate admits page states that the removed conditions previously rejected. The retained identity conditions bound this — a non-Reel card cannot produce a canonical `/reel/` URL — and the movement condition still requires a different Reel than the pre-turn one.
