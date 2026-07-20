## Context

Edge already reports an active Facebook Reel as exactly one `page.cards` item with `listKind:'reels'`, a canonical `/reel/<id>` noteId, and note-scoped like support. Cloud currently records the presentation as a view but then sends the card through the ordinary content-selection and LLM interaction path. Adding a 25% gate only at the end of that path would cover only Reels selected for deep reading, and leaving the LLM active after a missed draw would raise the effective ordinary-like rate above 25%.

The Cloud remains the owner of interaction strategy and authorization. Edge remains the owner of target location, trusted input, and platform-state verification. Existing risk, per-session budget, cooldown, duplicate-action, retry, and action-receipt accounting must remain authoritative.

## Goals / Non-Goals

**Goals:**

- Give every valid, unique active Reel presentation one ordinary like decision with probability 0.25.
- Make the random source injectable and the decision idempotent within a browsing session.
- Send a hit while the reported Reel is still active, through the existing note-scoped like command path.
- Preserve mandatory likes and all existing safety/accounting gates.
- Keep misses and blocked hits observable without claiming a platform action.

**Non-Goals:**

- Changing Reel DOM location, click verification, pacing, quotas, cooldown durations, or protocol message shapes.
- Adding a Console setting or per-account probability in this change.
- Treating a probability hit or command dispatch as a successful like.
- Applying the 25% policy to ordinary Facebook Feed posts or another platform.

## Decisions

### 1. Draw at the active-Reel presentation boundary

The handler will preserve the existing optional `listKind` on the internal `page.cards.arrived` event. For Facebook `listKind:'reels'`, RoleDispatcher accepts only a single card with a canonical Facebook `/reel/<id>` identity. It records that identity as decided before making one Bernoulli draw through the dispatcher's injectable random source.

This boundary represents every Reel actually presented by Edge and runs synchronously before the asynchronous content evaluator can navigate or advance. Drawing after `reading.done` was rejected because content evaluation can skip a visible Reel, making the denominator “selected deep reads” rather than “Reels browsed.” Drawing inside Edge was rejected because strategy and authorization belong in Cloud.

### 2. A hit sends a normal note-scoped like intent; a miss is terminal for ordinary Reel appraisal

On `random < 0.25`, Cloud checks remaining like budget, risk, and cooldown, then uses the existing `sendNoteScopedCommand('like', ...)` path and existing retry context. On `random >= 0.25`, it sends no command and logs a stable abstention reason. The identity is marked decided before gates/draw so duplicate reports cannot redraw.

A probability hit remains only an intent. Edge still requires the requested noteId to match the active Reel, clicks at most once per execution attempt, and returns `ok:true` only with a same-Reel selected-state witness. Budget and cooldown timestamps continue to update only from confirmed successful receipts.

### 3. Suppress only the later ordinary LLM decision for already-handled Reels

RoleDispatcher injects an `isInteractionHandledExternally` predicate into InteractionAppraiserRole. After the existing mandatory-like branch, the appraiser checks this predicate and emits a stable skip instead of calling the LLM. This makes the 25% draw the sole ordinary-like policy for the Reel while allowing explicit mandatory rules to force a like even when the random draw missed or a gate blocked the ordinary attempt.

This predicate is session-local and keyed by normalized Facebook post identity; it is cleared on start, restart, and end. A URL-shaped Reel not observed as `listKind:'reels'` is not automatically suppressed, avoiding cross-platform or fabricated-event inference from URL text alone.

### 4. No protocol or Edge change

`PageCardsPayload.listKind` already exists and Edge already emits `reels`; Cloud only carries that field through its internal event. The existing interaction command and receipt types are reused unchanged.

## Risks / Trade-offs

- [A random hit can still be blocked by quota, risk, cooldown, duplicate guard, stale target, or failed verification, so confirmed likes can be below 25%] → Define 25% as the ordinary intent-selection probability and keep every downstream block/failure honest in logs and receipts.
- [Content evaluation later reaches the same Reel] → The session-local handled predicate suppresses the second ordinary LLM interaction decision while leaving the read/scroll loop intact.
- [Duplicate `page.cards` delivery could inflate probability] → Normalize the Reel identity and mark it decided before drawing or dispatching.
- [A mandatory rule is discovered only after detail reading] → Mandatory appraisal remains ahead of the external-handled skip and can still force the required like; an already-liked Edge result remains an honest no-op rather than a false success.
- [Random source is shared with other dispatcher jitter] → Tests inject a deterministic source and assert the strict `< 0.25` boundary; production continues using the established dispatcher random source.

## Migration Plan

1. Add the internal event field, session-local decision set, dispatcher policy, and ordinary-appraiser bypass with focused tests.
2. Run Cloud acceptance, full tests, and typecheck; validate OpenSpec strictly.
3. Integrate to Cloud `master`, push, deploy `dev` from the eligible clean default checkout, and verify service/listener/health/Feishu/PostgreSQL.
4. Roll back the Cloud commit if needed; old Edge clients remain compatible because no wire shape or reason token is required.

## Open Questions

None. The requested probability is fixed at 25% for this change; configurability can be proposed separately if needed.
