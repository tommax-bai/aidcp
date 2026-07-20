## Context

The Edge `FacebookReelsReader` already resolves one active video by maximum viewport intersection, derives a canonical `https://www.facebook.com/reel/<id>` identity, and applies the same identity before and after a like. `FacebookSession` routes likes to that reader while `listMode==='reels'`, but currently sends every `interaction.follow` command to the generic unsupported branch.

The authorized live probe supplied the missing DOM facts. On Reel `1964804494173822`, the active video and author `Salon de Comolis` were each unique; the only nearby follow candidate had visible text `关注` and accessible label `关注Salon de Comolis`; after a trusted CDP click the same control exposed `已关注` / `已关注Salon de Comolis`. These strings are evidence for the locale matcher, not permission to rely on global text order.

The protocol already has `interaction.follow`, and existing accounting distinguishes a real new follow from `already_followed`. The missing pieces are a Reel target identity on that payload and an Edge actuator. Automatic strategy is intentionally separate: another active change owns the Reel interaction-decision hotspot, and no follow probability or quality rule was requested.

## Goals / Non-Goals

**Goals:**

- Execute an explicitly commanded follow only against the canonical active Reel and its uniquely associated inline author control.
- Preserve `off` / `shadow` / `on` behavior: off rejects browsing commands, shadow proves the target without clicking, and on may click.
- Prove a real success from a same-Reel Following state; preserve the existing `already_followed` no-op contract and receipt-based accounting.
- Keep Edge and Cloud protocol types plus `docs/protocol.md` synchronized without introducing a new message type.
- Keep a durable, fail-closed live probe that is read-only by default.

**Non-Goals:**

- Deciding when an account should follow a Reel author, assigning a probability, or changing a persona prompt.
- Supporting Facebook Feed/profile follow, changing Facebook's global orchestration capability declaration, or exposing a Console control.
- Building or releasing an Edge installer.

## Decisions

### 1. Extend the existing follow payload with an optional Reel note target

`InteractionFollowPayload` gains optional `noteId`. Existing Xiaohongshu/profile callers continue sending `authorId`; a Facebook Reels execution requires a non-empty canonical Reel `noteId`. This is a backward-compatible payload extension and does not add a protocol message.

Using only `authorId` was rejected because the current Reel card does not expose a stable numeric author id and a delayed command could act on a different visible Reel. Using only “the current page” was rejected for the same stale-target reason.

### 2. Resolve the follow control from the same active-Reel/author observation

`FacebookReelsReader.follow(noteId, shadow)` first reuses the active Reel probe and requires exact canonical identity equality. It requires the active card to contain one author label, then collects visible button-like controls whose text or accessible label represents Follow/Following in the supported Facebook locales and associates them with that author label. Zero candidates returns `no_target`; multiple candidates returns `ambiguous_target`; no DOM-order fallback is allowed.

The live label includes the author name, so accessible-name binding is preferred when available. A bounded geometric association to the unique author label remains the fallback for visible text-only markup. Broad document-wide “first Follow” and positional button indexes were rejected because neighbouring Reels remain mounted and Facebook contains unrelated Follow controls.

### 3. Trusted click plus same-Reel post-condition defines success

An unfollowed unique target in `on` mode is clicked with CDP pointer events. Verification is bounded and re-runs the full Reel/author/control probe. Success requires the requested Reel identity to remain active and exactly one associated control to expose Following/已关注. Rounded counters, disappearance alone, dispatch completion, or a different Reel's control never prove success.

If the initial state is already Following, the executor returns `ok:true, reason:'already_followed', executed:false`. Shadow returns `ok:false, reason:'shadow', executed:false`. A dispatched click that cannot prove the state returns `state_unchanged` or `verify_indeterminate` with `executed:true`; it is never rewritten as success.

### 4. Route follow only on the Reels list surface

`FacebookSession` routes `interaction.follow` through `runBrowseCommand` only when `listMode==='reels'`; other Facebook surfaces retain `capability_unsupported`. The session forwards the executor's terminal reason unchanged. Cloud protocol types accept `noteId`, but this change does not flip the platform-wide `follow` capability because that declaration currently controls the profile-based FollowAgent and would overstate Feed/profile support.

### 5. The probe is an evidence tool, not a second production executor

The probe defaults to read-only, requires an explicit AdsPower profile id, exact author name, canonical Reel, unique target, and `AIDCP_FB_PROBE_FOLLOW=1` before clicking. Production tests use exported probe/target builders so the durable selector logic stays aligned; the one-off navigation from a profile Reels tab remains probe-only.

## Risks / Trade-offs

- [Facebook changes accessible labels or locale strings] → Centralize locale patterns, keep structural association to the unique active author, add jsdom fixtures, and fail closed on unknown/ambiguous markup.
- [The Reel advances between command receipt and click] → Re-probe immediately before the write and require exact `noteId`; re-probe after the write before success.
- [The click was dispatched but the UI never settles] → Return an executed-but-unconfirmed failure and do not consume success accounting.
- [Global Facebook capability still says follow unsupported] → This change deliberately supplies only the Reel actuator; a future explicit selection-policy change can add a surface-specific consumer without pretending Feed/profile support.
- [The probe's authorized account remains followed] → The probe never auto-unfollows; the real run is recorded as a material external side effect.

## Migration Plan

1. Add protocol type compatibility in Edge, Cloud, and `docs/protocol.md`.
2. Implement the Reel target/verify path and route it in the Edge Facebook session with focused tests.
3. Run Edge acceptance/full tests/typecheck, Cloud protocol-focused/full tests/typecheck, and strict OpenSpec validation.
4. Integrate and push source changes. Do not build an installer; installed clients gain the feature only in a later explicit package/release.
5. Roll back the Edge commit to restore `capability_unsupported`; the optional payload field remains wire-compatible if Cloud type/docs land first.

## Open Questions

- What automatic policy, if any, should select Reel authors for follow? This requires an explicit product decision and is not inferred from the actuator request.
