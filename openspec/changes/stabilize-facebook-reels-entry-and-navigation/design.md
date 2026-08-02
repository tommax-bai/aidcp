## Context

The Native Reels continuation path currently requires the embedded router to produce one structural `axis` before any keyboard input. The observed `/reel/` layout had one active video, a disabled in-video `Next items` control, and an enabled viewport-scale `Next Card` overlay. Both controls were counted as semantic next controls, so the single-overlay rule produced no axis and Native returned `not_started/no_target` before sending `ArrowRight`. Cloud exhausted two fallback handshakes and released the account idle.

The configured-primary entry uses the existing `page.scroll` wire command. Native currently maps the entry reason directly to `Page.navigate('/reels/')`, readiness wait, and canonical-card polling. The companion command diagnostic nevertheless renders every `page.scroll` as “页面滚动 / 滚动当前页面”. A successful first navigation must remain background-safe; only bounded proof that the entry did not take effect authorizes a foreground recovery.

The completed `fix-native-facebook-primary-reels-routing` change remains the prerequisite that classifies `facebook_reels_primary` and `empty_feed_reels_fallback` as entry reasons. This change does not edit that prerequisite or broaden Cloud authority.

## Goals / Non-Goals

**Goals:**

- Let verified keyboard navigation discover the working Reels direction even when DOM structure cannot classify an axis.
- Ensure one late transition suppresses every later key, wheel, or pointer write.
- Preserve exact-target and canonical-identity success proof.
- Recover one confirmed ineffective Reels entry with one exact-target foreground activation and at most one fresh navigation retry.
- Make the local command diagnostic name Reels entry intent without claiming execution or platform success.

**Non-Goals:**

- Treat key dispatch, `Page.bringToFront`, route acknowledgement, coordinates, or document scroll as Reel progress.
- Send both keys without a bounded same-Reel re-probe between them.
- Add JavaScript scrolling, horizontal wheel input, blind overlay clicks, protocol fields, Cloud policy, configuration, or unbounded retries.
- Package or install the Edge client, deploy Cloud/Console, or perform real-account actions.

## Decisions

### Treat the working key as a verified actuator result, not a structural prerequisite

Native will first bind one unique active Reel by `videoKey` and optional canonical `noteId`. Router topology remains an optional ordering hint and a safe pointer-fallback locator. The command will choose a deterministic keyboard order: a fresh unique structural hint first, otherwise the last session-local verified key when available, otherwise `ArrowRight` then `ArrowDown`. Each direction may be dispatched at most once per command.

After every key, Native will use the existing bounded active-video transition probe. A transition immediately ends active probing and enters canonical-card hydration; it is both the axis evidence and the requested scroll action, so Native must not send another input. If no transition is observed, Native must freshly prove that the original Reel and document context remain unchanged before dispatching the other key. If the context drifted or a transition appeared late, the second key is suppressed.

The implementation may remember the last verified working key only as a session-local preference. A miss invalidates its authority for that command, and every later command still requires identity-changing postconditions. Calling this value a preferred key rather than a permanent layout classification avoids claiming that every future Reel shares one visual axis.

Alternative considered: extend the DOM classifier for the observed `Next items + Next Card` combination only. Rejected as the sole fix because another Facebook control variant would recreate the same pre-dispatch stall. The classifier may still be corrected for ordering and pointer evidence, but it is no longer keyboard admission authority.

### Preserve bounded fallbacks after active key probing

When both keyboard directions leave the same Reel unchanged, Native may use the existing wheel or button fallback only if a fresh router probe now proves the corresponding structural axis and safe target. The vertical wheel remains vertical-only; horizontal wheel remains forbidden; viewport-scale overlays remain non-clickable. If no structural fallback is safe, the command returns one ambiguous `reels_navigation_unconfirmed` receipt because input was dispatched.

This keeps the existing trusted-input ladder available without allowing missing DOM structure to block keyboard discovery or allowing pointer ambiguity to become a blind click.

### Recover only a proven ineffective Reels entry

The first entry attempt remains background-first: issue `Page.navigate('/reels/')`, wait for readiness, and prove that the bound page changed onto a Reels route/surface. If that surface-transition postcondition succeeds, Native does not call `Page.bringToFront`; missing or still-hydrating canonical Reel cards are handled honestly after entry and do not authorize foreground activation.

If bounded readback proves the exact target did not enter a ready Reels surface, Native may consume one per-command recovery budget. It calls `Page.bringToFront` once on that already-bound target, re-probes before writing, accepts any late successful surface transition without another navigation, and otherwise issues one fresh `Page.navigate('/reels/')`. The retry uses the same readiness and Reels-surface postcondition before canonical-card hydration proceeds. Target/document drift, login, challenge, consent, or another blocker returns the existing honest result without foreground retry. `Page.bringToFront` acknowledgement is never success evidence.

Alternative considered: bring every Reels entry to the foreground before navigation. Rejected because the user explicitly requires foreground activation only after the initial navigation is shown ineffective and routine background entry should remain non-disruptive.

### Derive companion wording from the safe reason whitelist

The command-diagnostic builder already receives the decoded command payload before renderer projection. It will map `page.scroll{reason:'facebook_reels_primary'}` and `page.scroll{reason:'empty_feed_reels_fallback'}` to the title “进入 Reels” with distinct fixed summaries. Other `page.scroll` commands retain “页面滚动 / 滚动当前页面”. No raw payload, URL, account identity, or new field reaches the renderer, and the diagnostic stage remains received/rejected/dispatched rather than success.

## Risks / Trade-offs

- [The wrong first key seeks media or changes focus without navigating] → Only active-Reel identity change counts; prefer fresh structural or cached evidence, gate unsafe editor/dialog focus, and re-probe before the second key.
- [The first key moves late and the second key double-advances] → Fresh same-Reel pre-commit probing suppresses every later write after any observed transition.
- [Both keys work on one Facebook layout] → The first verified transition completes the command; store only the working key used, not a universal visual-layout claim.
- [Foreground recovery steals focus for a transient load] → Require bounded proof that the first navigation was ineffective, one exact target, no blocker, and a one-activation budget.
- [A foregrounded first attempt completes before the retry] → Re-probe after activation and accept the late entry without a second navigation.
- [UI wording implies completion] → Change only the command intent title/summary; preserve “已交给执行器” and the explicit success disclaimer.

## Migration Plan

1. Add OpenSpec deltas and focused regressions for active key probing, late-movement suppression, entry recovery ordering, and reason-aware diagnostic wording.
2. Implement in an isolated `aidcp-edge` worktree, run focused Native/router/UI tests, the serial Native gate when required, and TypeScript typecheck.
3. Integrate and push source plus OpenSpec evidence. Do not package or replace `/Applications/AIDCP.app` without separate authorization.

Rollback is a source revert restoring structure-gated keyboard navigation, single-attempt background Reels entry, and generic `page.scroll` wording. There is no data or protocol migration.

## Open Questions

None.
