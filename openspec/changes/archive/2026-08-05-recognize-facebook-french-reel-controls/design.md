## Context

The incident account was served `lang=fr`. On the exact commanded Reels, read-only CDP inspection found one geometrically eligible `aria-label="J’aime"` control and one author-bound `Suivre <author>` control, while the production Native probes returned `like_button_not_found` and `follow_button_not_found`. Cloud dispatch and daily accounting remained honest: the intents were sent, no Edge write was attempted, and no successful Like or Follow was counted.

The Native Facebook router owns production action vocabulary. A retained TypeScript reader and CTA helper still provide diagnostic/test parity and must not drift into recognizing a different target set.

## Goals / Non-Goals

**Goals:**

- Recognize the observed French neutral Like and Follow controls on the canonical active Reel.
- Recognize only evidence-backed French positive states needed for already-state and post-write verification.
- Preserve exact target uniqueness, active-video geometry, author proximity, fresh pre-write resolution, trusted CDP input, and bounded same-target verification.
- Keep Native and retained TypeScript semantics aligned with focused executable tests.

**Non-Goals:**

- Changing Cloud cadence, quotas, risk accounting, command contracts, or UI copy.
- Adding generic text search, fuzzy locale inference, or an online fallback after Native cannot prove a target.
- Claiming real-account acceptance, packaging an Edge client, or deploying an installed artifact.

## Decisions

1. **Extend the existing shared reaction vocabulary instead of special-casing a profile or Reel.** `J’aime` is added as an anchored neutral Like label and French reaction-picker vocabulary is added to the existing capability-neutral semantics owner. This preserves one classifier for Feed/Reels semantics while Reels continues to own geometry and uniqueness. A URL/profile exception was rejected because it would encode incident data instead of platform semantics.

2. **Use anchored French Follow tokens with the existing author witness.** `Suivre` is classified as the neutral action. The official French positive-state terms `Suivi(e)` and `Ne plus suivre` are classified as already following, but only when the remaining label identifies exactly one visible author within the existing distance bound. Broad substring matching was rejected because unrelated menu text could authorize a write or prove success.

3. **Keep success positive and same-target.** A French Like remains confirmed only by the existing selected attribute or exact reaction/remove witness on the marked control. A French Follow remains confirmed only when a fresh probe on the same Reel, video key, and author resolves a unique positive-state control. Control disappearance or merely changed text remains non-success.

4. **Maintain TypeScript parity without restoring it as a production fallback.** The retained CTA/reels helpers receive the same French tokens and focused tests, while Native remains the production authority.

## Risks / Trade-offs

- **Facebook may emit another French wording** → Unknown labels continue to fail closed and produce observable not-found/unconfirmed results; add only newly observed exact variants.
- **An accent/apostrophe representation may differ** → Accept straight and typographic apostrophes for `J’aime`, but keep the entire label anchored and do not fold arbitrary free text into a target.
- **A post-follow control may omit the author** → Verification remains unconfirmed rather than relaxing the author-binding invariant.
- **Tests cannot prove the current installed package or platform write** → Record source/test validation separately; package and real-account acceptance require explicit later authorization.
