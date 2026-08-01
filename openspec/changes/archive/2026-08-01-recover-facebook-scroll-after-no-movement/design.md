## Context

The Native Facebook Feed path sends an 8–15 frame CDP wheel gesture and already samples the real list scroll container before and after the gesture. A successful CDP response only acknowledges input dispatch; it does not prove movement. Today the Feed loop constructs `PageMovement`, but it can return `Confirmed/PageCards` before treating `moved=false` as a failed scroll. The completed `limit-facebook-scroll-foreground-to-watchdog` change deliberately allowed `Page.bringToFront` only for `idle_recover_nudge`; this change supersedes that sole-authority rule with one tightly bounded no-movement exception.

The observed Mi Gu failure belongs to the acknowledged-but-no-movement class. Detecting a CDP request that never returns requires separate request-level timeout and outstanding-response handling and is not needed for this recovery.

## Goals / Non-Goals

**Goals:**

- Keep every ordinary Facebook list scroll background-first.
- Reuse the existing real-container movement probe instead of adding another protocol or browser channel.
- Permit exactly one foreground activation and exactly one fresh recovery wheel only after completed input has a same-document, ready, non-terminal no-movement witness.
- Prevent readable stale cards from confirming a scroll that did not move.
- Preserve watchdog behavior while counting its eager activation against the same one-activation ceiling.

**Non-Goals:**

- Add per-CDP-call timeout or recover an input RPC that never returns.
- Add JavaScript `scrollBy`, DOM wheel dispatch, configuration, Cloud fields, or retries beyond the single foreground recovery.
- Change Reels navigation fallbacks, Feed bottom evidence, browser parking, explicit operator foreground controls, packaging, or deployment.

## Decisions

### 1. Define response as measured movement, not RPC acknowledgement

The Feed executor will evaluate the existing `PageMovement` before it can return a non-empty `PageCards` batch. A completed background gesture is eligible for recovery only when the actual scroll container remains unchanged, the list is not loading, it is not near bottom, and the URL, surface, document generation, and document time origin still identify the same document.

Using the CDP method result was rejected because Mi Gu produced successful Native outcomes without visible movement. Treating card availability as movement was rejected because cards already present before the gesture can mask a stalled viewport.

### 2. Carry one activation budget through the common Feed/Reels entry

The common `page.scroll` entry will record whether `idle_recover_nudge` already called `Page.bringToFront` and pass that fact into the Feed executor. An ordinary Feed command begins with an unused activation budget. Once foreground activation occurs, the budget is consumed for the rest of the command.

This keeps the existing watchdog eager activation and prevents the adaptive path from activating the window a second time. A global session flag was rejected because activation authority and evidence belong to one command, not to later commands.

### 3. Re-probe after activation and retry one Native wheel

After an eligible miss, Native will activate the exact already-bound CDP target, immediately re-probe the list, and require the same document and list surface before any further input. It will then execute one fresh humanized wheel gesture using dimensions from that new probe. If the recovery gesture still produces no movement while non-terminal, the command returns an ambiguous `scroll_movement_unconfirmed` outcome before reporting cards.

Continuing the normal multi-round loop after a failed recovery was rejected because it would turn a one-shot recovery into repeated input. JavaScript scrolling was rejected because it bypasses the trusted Native input contract.

### 4. Leave true RPC hangs on the existing bounded command path

`CdpSession::call` currently owns the mutable WebSocket while waiting for the correlated response. Adding a short timeout raises stale-response and possible late-input/double-scroll concerns. This change therefore acts only after the wheel gesture returns and preserves the existing absolute command deadline plus later watchdog recovery for a true hang.

## Risks / Trade-offs

- [A legitimate non-moving bottom could foreground the browser] → Require the existing real-container near-bottom check to be false before activation.
- [Loading or document replacement could look like a missed wheel] → Reject loading, URL/surface/generation/time-origin drift, and re-probe after activation.
- [The first gesture moves after the settle readback] → Reuse the existing bounded Feed settle window before classifying no movement; do not introduce a shorter speculative timer.
- [A fixed overlay consumes wheel input] → Allow one foreground attempt only; a second miss returns ambiguous instead of looping.
- [The predecessor OpenSpec change is complete but unarchived] → Record that this change supersedes its watchdog-only addition; archive ordering must apply the predecessor before converting this delta to the baseline modification.

## Migration Plan

1. Add the new OpenSpec deltas and focused Native regressions.
2. Implement the activation budget, same-document eligibility predicate, and one-shot recovery in the Edge worktree.
3. Run focused Native tests, serial Native gate when required, TypeScript typecheck, and strict OpenSpec validation.
4. Integrate source only. Do not package or claim installed-client delivery without a separately authorized installer release.

Rollback is a source revert restoring watchdog-only foreground activation; no data or protocol migration is involved.

## Open Questions

None for implementation. True unreturned CDP requests remain an explicitly separate follow-up if runtime evidence shows that the existing command deadline and watchdog are insufficient.
