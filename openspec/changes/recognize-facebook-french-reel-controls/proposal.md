## Why

Facebook serves this account's Reels UI in French, but Edge's evidence-backed Like and Follow vocabularies do not include the observed `J’aime` and `Suivre <author>` controls. Cloud therefore dispatches the planned interactions, while Edge truthfully returns `like_button_not_found` and `follow_button_not_found` without attempting a write.

## What Changes

- Add exact French Like neutral/selected vocabulary to the shared Native Facebook reaction semantics used by Reels.
- Add exact French Follow/Following vocabulary to the canonical-Reel, author-bound Follow target classifier.
- Keep action-rail geometry, target uniqueness, trusted CDP actuation, same-Reel verification, and honest non-success outcomes unchanged.
- Keep the retained TypeScript diagnostic/read path semantically aligned with Native.
- Add focused contract tests for French controls plus decoy, ambiguity, and post-state safeguards.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `native-facebook-localized-action-semantics`: Extend the evidence-backed localized Like/reaction vocabulary to French without weakening target or verification gates.
- `facebook-reels-inline-follow`: Recognize French Follow and already-followed states while retaining exact author association and same-Reel verification.

## Impact

- Owning runtime: `aidcp-edge` Native Facebook router and retained TypeScript Facebook readers.
- Tests: Native page-engine Facebook router contracts and TypeScript Reels/CTA semantics.
- No protocol, Cloud cadence, risk accounting, Console, database, or deployment-topology change.
- Installed clients require a future Edge package/update before the fix affects real accounts; this change does not authorize a package build or live Facebook write.
