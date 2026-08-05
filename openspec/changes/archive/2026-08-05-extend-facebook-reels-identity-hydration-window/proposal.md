## Why

Real Facebook execution reached the Reels surface for account `ads-k1f6n4yp`, but the canonical Reel identity hydrated after the current five-second card verification window. Edge therefore returned `ambiguous/reels_identity_unresolved` even though a later read-only probe found one ready canonical Reel, so the bounded verification window needs to accommodate the observed slower hydration without weakening success proof.

## What Changes

- Extend the shared Facebook Reels canonical-identity/card hydration verification window from 5 seconds to 15 seconds.
- Keep the timer start point unchanged: only after Edge has reached a Reels surface or observed an active-video transition.
- Keep the same fail-closed terminal receipts when no canonical Reel appears by the deadline.
- Do not add navigation retries, extra keyboard/wheel/pointer input, Cloud behavior changes, protocol fields, packaging, installation, or deployment.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-reels-browse`: require up to 15 seconds of canonical-card hydration verification after a Reels entry reaches the target surface.
- `facebook-reels-navigation`: require up to 15 seconds of canonical-identity verification after an active-video transition while preserving input suppression and ambiguous failure semantics.

## Impact

- Owning repo: `aidcp-edge` Native Facebook Reels executor and focused Fake CDP/unit tests.
- Control repo: OpenSpec delta and validation evidence.
- No Cloud, Console, protocol, database, package, installed-client, or deployment change.
