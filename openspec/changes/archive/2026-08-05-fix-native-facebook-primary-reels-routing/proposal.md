## Why

DEV proves that Cloud pins the configured Reels surface and sends `page.scroll{reason:'facebook_reels_primary'}`, but the active Native Facebook executor recognizes only the evidence-based fallback reason. It therefore reports ordinary Feed cards instead of entering Reels, leaving Cloud waiting for a canonical Reel and preventing Reels business handling.

## What Changes

- Route both the configured-primary and evidence-based fallback reasons through the active Native Reels entry path.
- Keep the two reasons semantically distinct while sharing navigation, readiness, canonical-card, and honest failure postconditions.
- Add active Native router and packaged-artifact contract coverage so a retired TypeScript session cannot stand in for the shipped executor.
- Preserve ordinary Feed scrolling for every unrelated `page.scroll` reason.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-reels-browse`: Clarify that every active Facebook executor, including the shipped Native executor, must recognize `facebook_reels_primary` as a Reels-entry authorization without treating navigation alone as success.

## Impact

- Owning repo: `aidcp-edge`.
- Active code: Native Rust Facebook dispatch and its embedded Facebook router.
- Validation: focused Native router contracts, Native runtime/artifact gates, Edge typecheck, and strict OpenSpec validation.
- No Cloud policy, protocol shape, database, UI, deployment, packaging, installation, or real-account action changes.
