## Context

Facebook page execution is Native-only. Cloud correctly emits Reel like and follow intents, but current Native probes reuse generic article-local selectors:

- `activeReel().root` is commonly the video parent or nearest article, while Facebook may render the Reel action rail and author CTA in sibling DOM branches;
- the generic like matcher only accepts labels beginning with a bare Like word and misses established neutral reaction labels such as `留下心情` and `Bày tỏ cảm xúc Thích…`;
- the follow matcher requires an exact bare verb and misses author-qualified labels such as `关注Salon de Comolis`;
- the current primary like uses a saved point, and the picker probe is document-wide rather than bound to the active Reel;
- failed Native receipts reach Cloud, but local logs retain only receive/dispatch evidence and Cloud logs retain only `action + ok`, so the exact terminal reason is lost.

The existing TypeScript Reel executor and its tests remain the behavior oracle. The implementation stays inside the Native Rust process plus embedded router; no TypeScript page fallback is restored.

## Goals / Non-Goals

**Goals:**

- Resolve like and follow controls against one uniquely active canonical Reel across nested and sibling action-rail layouts.
- Restore established multilingual neutral, reacted, follow, and following label semantics.
- Re-probe at the commit boundary, use at most one primary like activation and one picker commit, and verify a positive state witness on the same Reel.
- Preserve trusted pointer actuation for picker/follow commits and honest effect phases for not-started versus ambiguous writes.
- Record bounded local receipt diagnostics containing action, effect phase, and reason without page content.
- Protect the Native path with behavior-level regression tests derived from the established Reel oracle.

**Non-Goals:**

- Change Cloud like/follow probability, quotas, risk gates, pacing, accounting, or protocol types.
- Add selector fallbacks, retries, feature flags, JavaScript execution fallbacks, or unsupported Facebook capabilities.
- Claim the existing live-account acceptance task complete based on local tests.
- Package an installer, deploy OL, or trigger a real interaction solely for verification.

## Decisions

### 1. Bind Reel controls by active-video identity and geometry, not DOM ancestry alone

The router will keep `activeReel()` as the canonical identity authority, then derive a bounded Reel interaction region from visible controls spatially associated with that video and its nearby author/action rail. A candidate remains eligible only when the active Reel canonical identity matches the command. Multiple equally valid candidates return `ambiguous_target`; absence returns the existing control-not-found reason.

Using only a wider ancestor was rejected because it can admit controls for adjacent Reels. Falling back to the first document control was rejected because it violates exact-target guarantees.

### 2. Port semantic label families, not old TypeScript classes

The embedded router will encode the established neutral-like, selected-like, follow, and following label families, including author-qualified and Vietnamese variants. It will retain structural and numeric-count exclusions. This keeps the Native boundary self-contained while preserving proven platform semantics.

### 3. Restore the two-stage Reel like commit contract

The initial probe is read-only. At the commit boundary, a dedicated internal router operation freshly resolves the active Reel and primary reaction control, marks that control for same-Reel verification, and activates the fresh in-page React element once. Rust then polls a same-Reel selected-state probe.

If the primary activation opens a reaction picker, a second internal probe may return exactly one visible Like item from exactly one visible multi-reaction picker associated with the marked primary control. Rust dispatches at most one trusted pointer commit to it. Reel movement, target loss, ambiguity, off-screen picker state, or unproven selection terminates without another click.

Keeping the current stale-point primary path was rejected because React hydration/layout can invalidate the earlier coordinates. Keeping the document-wide picker probe was rejected because another post's bare Like control can be selected.

### 4. Follow remains a single trusted write with same-Reel verification

The follow probe will return one author-bound visible follow control or an already-following witness for the active canonical Reel. Rust dispatches one trusted pointer click and polls the same probe. Movement or loss after dispatch yields an ambiguous effect, while pre-dispatch absence or ambiguity remains not-started.

### 5. Preserve terminal reason at the local facade boundary

`NativeBrowseSession` will log one bounded diagnostic for each action receipt with action, `ok`, effect phase, and a length-bounded reason token. It will not log note text, author content, URLs, cookies, or credentials. The protocol payload remains unchanged.

## Risks / Trade-offs

- [Spatial association may vary across Facebook cohorts] → Reuse the legacy geometry invariants, require visibility and uniqueness, and fail honestly rather than widen to a first-match fallback.
- [In-page primary activation and trusted picker activation use different event semantics] → Keep them as explicit one-shot stages and test both direct-toggle and picker layouts.
- [A control can move after probing] → Freshly resolve at the write boundary and re-probe the same canonical Reel before reporting success.
- [Additional diagnostics could expose page data] → Log only bounded enum-like action/reason/effect tokens.
- [Old and Native tests could diverge] → Port externally meaningful fixtures and state assertions, not implementation-string assertions alone.

## Migration Plan

1. Add focused failing Native router/session and Rust orchestration tests.
2. Implement the router probes, Rust commit flow, and bounded facade diagnostics in the isolated Edge worktree.
3. Run focused Native/legacy tests, Cargo tests, protocol acceptance, full Edge tests, typecheck, and strict OpenSpec validation.
4. Rebase and fast-forward integrate Edge and control changes, then rebuild/restart the local development Native artifact.
5. Keep the existing bounded real-account acceptance as a separate final runtime gate; do not manufacture a write for validation.

Rollback is reverting the Edge commit and rebuilding the prior Native binary. There is no database or protocol migration.

## Open Questions

None.
