## Context

The pre-Native Facebook executor added lazy-load-aware exhaustion evidence after real accounts repeatedly refreshed too early. The first Native cutover collapsed that stateful behavior into a one-shot scroll, and the later parity repair restored height, near-bottom, and consecutive-round checks. Two gaps remain:

- Feed settling can return after two unchanged card samples roughly 500 ms apart because document height is not part of the stability key.
- After eight rounds, Native returns `feed_exhausted` whenever any card was observed, even if height grew or the page never reached the bottom.

The embedded router already observes localized explicit-empty text, but ordinary Feed exhaustion does not consume a distinct end-of-feed observation. Cloud also treats fallback authorization as idempotent for the whole active session; once readable Reels confirm it, a later return to a non-empty Feed does not start a new authorization epoch.

The repair spans Edge and Cloud but does not change the protocol envelope or add a configuration knob.

## Goals / Non-Goals

**Goals:**

- Report `feed_exhausted` only from stable explicit terminal evidence or the established structural proof.
- Observe delayed document growth inside the existing bounded in-place settle budget.
- Continue browsing promptly when one bounded Edge command cannot prove either progress or exhaustion.
- Preserve duplicate suppression while allowing a new fallback after readable Reels have been left and a non-empty Feed is authoritative again.
- Cover the negative paths that the Native parity suite previously missed.

**Non-Goals:**

- Change Facebook content selection, pacing values, view quotas, interaction policy, or session budgets.
- Add an unbounded wait, periodic retry timer, compatibility fallback, database state, or operator setting.
- Change search/group exhaustion into Reels selection.
- Package or release a desktop installer, deploy OL, or execute a Facebook write action for validation.

## Decisions

### 1. Separate explicit end-of-feed evidence from explicit empty-home evidence

The embedded router will expose an internal `explicitEnd` observation when a visible, bounded Feed-scoped text node matches the established localized terminal phrases. `explicitEmpty` remains the stronger empty-home observation that also requires the existing empty-home hint.

Rust will accept `explicitEnd` as terminal evidence only on the canonical home surface near the bottom and after consecutive observations. This avoids treating a matching phrase in search, a group, or an off-screen mounted subtree as Feed exhaustion.

Alternative considered: reuse `explicitEmpty` for both meanings. Rejected because an empty homepage and the end of a previously non-empty Feed drive different state transitions and require different surrounding evidence.

### 2. Confirm a bottom candidate within the existing in-place wait budget

The ordinary scroll path will include document height in its settle identity. When a round has no new canonical card, no observed growth, and is near the bottom, Native will use the existing 3.5-second in-place budget to poll for:

- a new canonical card;
- document-height growth;
- loading or surface/generation invalidation;
- consecutive explicit terminal observations; or
- a structurally stable bottom candidate for the complete window.

Only two consecutive structurally stable candidate rounds, or stable explicit terminal evidence, produce `feed_exhausted`. Growth, loading, a new card, or leaving the home Feed resets the candidate count.

Alternative considered: make all eight scroll rounds sleep for the full 3.5 seconds. Rejected because it spends nearly the whole command deadline even when a new card becomes available immediately.

### 3. Round exhaustion without terminal evidence remains non-terminal and observable

If eight bounded rounds finish after seeing only recycled cards but never establish terminal evidence, Edge will return `feed_continuation_unconfirmed`. Cloud will map that reason to another ordinary gated scroll command, using the existing view-quota, pause, comment-hold, dwell, and command serialization gates.

This is an observed recovery path, not an unbounded Edge retry: each Edge command remains bounded, the reason is logged, and Cloud retains session-level termination and quota authority. Returning generic `no_target` was rejected because the current dispatcher intentionally does not recover scroll failures and would reproduce the 240-second idle-watchdog pause.

### 4. Scope fallback idempotency to a confirmed Feed/Reels epoch

`pending` remains unchanged until readable Reels cards arrive or bounded handshake recovery fails. `confirmed` suppresses duplicate empty/exhausted evidence while Reels remains active. A later non-empty `page.cards` batch with `listKind:'feed'` while the dispatcher is on its ordinary Feed source proves Feed re-entry and resets the fallback state to `idle`.

Empty batches, search context, and batches arriving while the handshake is still `pending` do not reset the state. The next truthful Feed terminal observation may then authorize exactly one new fallback.

Alternative considered: reset when Cloud sends a back/scroll command. Rejected because command dispatch is not platform readback and could reopen authorization while the page is still on Reels.

## Risks / Trade-offs

- [Localized terminal text drifts] → Keep the marker internal, bounded, visible, home-scoped, near-bottom, and consecutively observed; structural evidence remains authoritative when the marker is absent.
- [A virtualized Feed keeps a constant document height while replacing cards] → Canonical-card identity changes and new-card extraction take precedence over exhaustion.
- [Repeated unresolved continuation consumes actions] → The existing eight-round Edge bound, Cloud command gates, view quota, pacing, and session monitor remain active; the reason is explicit in logs.
- [A late Feed batch arrives during a pending Reels handshake] → Only `confirmed` can reset on Feed re-entry; `pending` retains its current bounded recovery behavior.
- [Source and deployed Native artifacts diverge] → Validate Cargo tests, rebuild the canonical source-run artifact, and report installer scope separately.

## Migration Plan

1. Implement and validate Edge in an isolated worktree, including Native router/probe changes and focused Rust regressions.
2. Implement and validate Cloud in an isolated worktree, including continuation and fallback-epoch integration tests.
3. Validate the OpenSpec change strictly, integrate by fast-forward to the default branches, and push.
4. Rebuild the local Native Page Engine artifact used by source execution without packaging an installer.
5. Run the DEV deployment preflight, deploy Cloud to DEV, restart only the documented AIDCP service, and verify listener, health, service logs, and the Nancy browse path when safely observable.

Rollback is a revert of the Edge and Cloud commits, restoration of the preceding Native artifact, and the documented DEV Cloud rollback. There is no database or protocol migration.

## Open Questions

None.
