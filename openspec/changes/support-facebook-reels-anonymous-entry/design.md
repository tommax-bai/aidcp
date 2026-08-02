## Context

The current Reels entry executor navigates to `/reels/`, waits for page readiness, and then uses the shared 15-second card-hydration completion helper. That helper correctly refuses to report an anonymous active video, but it terminates without invoking the already implemented Native Reels navigation contract. The same session later recovers only when Cloud's generic idle nudge sends an ordinary `page.scroll` about 240 seconds later.

The existing router already distinguishes a unique active `videoKey` from a canonical Reel `noteId`. Existing Reels navigation already supports anonymous pre-states, horizontal and vertical actuators, fresh same-video rechecks, movement proof, and suppression of later writes after an observed transition. Cloud already understands the existing `page.cards` and failed scroll receipts, so this change can remain Edge-local.

## Goals / Non-Goals

**Goals:**

- Turn a unique, input-safe anonymous landing into one bounded local forward-navigation invocation after the existing hydration window expires.
- Preserve the first Reel when canonical identity becomes available before input is committed.
- Require either exact same-video canonical hydration after an ineffective actuator or a distinct active-video transition with one matching canonical Reel card before success.
- Prevent both same-command fallback writes after movement and later-command input while a prior entry transition still awaits identity.
- Keep anonymous or content-derived identities out of Reels view accounting.

**Non-Goals:**

- Change Cloud orchestration, pacing, risk quotas, protocol fields, or view semantics.
- Invent an identity from video source, poster, text, geometry, or a session-local `videoKey`.
- Add another `/reels/` navigation, JavaScript scroll fallback, unbounded retry, or automatic Cloud retry.
- Package, install, deploy, or perform a real-account action as part of this source change.

## Decisions

### Preserve hydration first, then admit only a fresh anonymous target

Entry retains the existing 15-second canonical-card hydration window. On timeout, Edge performs a fresh active-Reel and next-target readback. Bootstrap is admitted only when both observations bind the same unique `videoKey`, canonical identity is still absent, both probes explicitly report `inputSafe=true`, no blocker or document drift is present, and the command remains active with enough deadline budget. A missing safety signal is not proof of safe input.

If the same video's canonical identity appears exactly at the 15-second boundary, Edge performs one immediate card read without opening a second initial hydration window. If the active video has naturally changed, that consumes the permitted transition and starts only the post-transition read-only hydration window. Missing, equally eligible, unsafe, drifted, or disappeared observations dispatch no input and terminate with an honest entry-specific receipt.

Alternative considered: immediately advance every anonymous landing. Rejected because it would undo the 15-second slow-hydration accommodation and skip a first Reel whose canonical identity was about to appear.

### Invoke the existing bounded Reels navigator once

The entry path invokes the existing Native Reels forward-navigation contract once, using an entry admission mode that revalidates the anonymous pre-state before every possible write. The bounded invocation may use its existing fresh-probe actuator discovery when structural axis evidence is absent, but it may produce at most one active-video transition. A proven horizontal layout still starts with `ArrowRight`; a proven vertical layout still starts with `ArrowDown`. Any observed `videoKey` change suppresses every later key, wheel, or pointer fallback.

If an actuator was dispatched but the active `videoKey` remains unchanged and that same video's canonical identity finishes hydrating, Edge may report the exact current canonical card and must suppress every later actuator. This is not a fabricated moved-to view: the original video has remained active throughout the entry wait, and completion still requires the same strict canonical active-card match.

Alternative considered: add a second Cloud command or call the whole page-scroll dispatcher recursively. Rejected because Cloud would add a multi-minute delay, while recursive dispatch could fall back to Feed or lose the anonymous-entry admission boundary.

Alternative considered: permit exactly one low-level key event. Rejected because the existing safe unknown-axis contract may try `ArrowRight`, re-probe the unchanged same video, and then try `ArrowDown`; forbidding that would conflict with the completed navigation contract. The bound is one navigator invocation and at most one Reel transition.

### Canonical completion is an exact active-card match

Shared Reels completion accepts success only when a fresh active probe has both `videoKey` and a valid Facebook `/reel/<id>` identity, and `page.cards` is a ready Reels batch containing exactly one video card whose permalink identity resolves to the same Reel ID. After an ordinary canonical Reel transition, the resolved ID must also differ from the previous Reel ID; a DOM remount that changes only `videoKey` cannot be counted again. A non-Facebook host, non-Reel Facebook permalink, non-video card, non-ready batch, `content_ref`, anonymous card, mismatched card, stale previous-ID card, empty batch, or multiple-card batch remains unreportable.

This closes an existing implementation gap where the Rust completion helper accepted any non-empty card batch even though the Reels specification requires a canonical active Reel.

### Retain a session-local pending observation after an uncertain entry write

When anonymous-entry navigation dispatches input, Edge records a session-local pending Reel observation with two live phases: `AwaitingMovement` remains bound to the original `videoKey` and may adopt at most one late video change; `AwaitingIdentity` remains bound to the exact moved-to `videoKey` and rejects any second drift. A second drift permanently changes the session-local latch to `TargetChanged`, so returning to the formerly bound video cannot restore a broken observation chain. A normal Reels scroll that proves movement but cannot resolve the moved-to identity also enters `AwaitingIdentity`. Edge clears the latch only after the bound active video is reported as the one matching canonical card, the session ends, or the page leaves the Reels surface.

While the latch remains and another `page.scroll` arrives, Edge performs read-only card and active-video recovery before Feed fallback or any new Reels navigation. It MUST NOT dispatch another navigation input. If identity remains absent, it returns an ambiguous pending receipt; if the matching canonical card appears, it reports that one card and clears the latch. Surface loss clears the latch with an ambiguous receipt but does not fall through to a Feed scroll in that command.

This prevents the generic 240-second idle nudge from blindly advancing again after a transition whose identity was still hydrating.

### Preserve phase truth and existing wire shapes

Success remains `confirmed` plus one canonical `page.cards{listKind:'reels'}`. Because the entry command has already navigated to `/reels/`, cancellation or failure after that route write remains `ambiguous` even before the first actuator. Any failure after input dispatch also remains `ambiguous`; it MUST NOT become `not_started/no_target`, because Cloud may treat that phase as safe to re-enter. No protocol field is added.

## Risks / Trade-offs

- [The initial unresolved landing now holds the command for hydration plus navigation verification] → Keep both waits bounded and check cancellation/deadline with enough post-input receipt reserve before committing input.
- [A pending identity never becomes canonical] → Keep the session fail-closed and read-only on later scrolls; session restart clears the local latch rather than fabricating progress.
- [Canonical identity appears at the 15-second boundary] → Re-probe the active video and card immediately before input, suppress the write, and do not restart the initial 15-second window.
- [A navigation actuator changes the video late] → Reuse fresh same-video pre-commit checks and stop all later writes on the first observed transition.
- [Generic Feed content identity leaks into Reels accounting] → Require one permalink-kind card matching the fresh active Reel before confirmed completion.

## Migration Plan

Implement in the isolated `aidcp-edge` worktree, validate focused and full Native gates, integrate Edge source and the OpenSpec change, and do not package or replace the installed application. Rollback is a source revert; the pending observation is session-local and requires no data migration.

## Open Questions

None.
