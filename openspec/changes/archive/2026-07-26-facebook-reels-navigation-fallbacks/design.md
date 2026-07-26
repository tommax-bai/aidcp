## Context

The existing Reels driver proves movement by comparing the canonical `/reel/<id>` route and active-video identity, but it attempts only the far-right navigation button. On the first Reel, Facebook renders four same-sized header controls, a disabled previous control, and one enabled next control. The broad structural selector therefore reports ambiguity, while the two-enabled-button assumption would reject the first Reel even after header controls are excluded.

Facebook also supports trusted ArrowDown and wheel inputs. These are less coupled to localized button markup and are suitable as the primary navigation methods as long as every method remains post-condition verified.

## Goals / Non-Goals

**Goals:**

- Attempt ArrowDown, then a 70–100px downward wheel gesture, then the button fallback.
- Stop at the first method that changes the canonical Reel route or active-video identity.
- Keep every input bounded and fail closed when identity is unchanged or button targeting is ambiguous.
- Make method selection and failure visible in logs and deterministic in tests.
- Count each Reel that was actually presented as one view, regardless of whether the content selector chooses it for deeper reading.
- Avoid double-counting when a selected Reel subsequently produces `note.detail` for quality/interaction appraisal.

**Non-Goals:**

- Changing protocol messages, other-platform accounting, or the rule that likes require content/interaction appraisal.
- Using DOM `scrollBy`, synthetic page JavaScript events, or unverified success.
- Adding backward navigation to the current forward-only browse loop.
- Packaging an Edge installer.

## Decisions

1. **Use trusted CDP input in an ordered ladder.** `Input.dispatchKeyEvent` sends ArrowDown first. If the same route/video remains after a bounded verification window, `Input.dispatchMouseEvent` sends one positive wheel delta. Only if that also fails is the button probed and clicked. This preserves human-like platform inputs while retaining the existing trusted-input boundary.

2. **Generate one inclusive integer wheel delta per navigation attempt.** Inject a random source into `FacebookReelsReader`; production defaults to `Math.random`, while tests inject fixed values. Clamp the derived distance to the inclusive 70–100px range so configuration or test doubles cannot escape the contract.

3. **Verify after each method against the same original identity.** A method succeeds only when the canonical route or stable active-video element/content key differs from the pre-navigation observation. The key is assigned through a page-scoped `WeakMap`; viewport coordinates are excluded because the same video moves during the Reel transition animation. A failed method does not replace the baseline, preventing transient probes from weakening the proof.

4. **Use a short method-level verification window.** Reuse the active-Reel probe with a bounded, sub-second polling cadence instead of the longer initial-entry settle window. This keeps the worst-case three-method ladder bounded without declaring success early.

5. **Keep Reels deduplication route-and-video scoped.** Facebook can switch the active video before the address bar hydrates. The session therefore deduplicates Reels with `canonical route + stable video key`, while feed cards retain their existing post-id deduplication. This lets a proven new video enter the next evaluation round without treating coordinate-only animation as new content.

6. **Constrain the final button fallback to the Reel navigation rail.** Exclude the page header by requiring a control inside the active video's middle vertical band and to the far right of the video. Prefer a unique localized next-label match; otherwise choose the lower control only from a credible two-control rail. Accept a single enabled, semantically next-labeled control on the first Reel. Ambiguity produces no click.

7. **Keep protocol failure compatibility.** The reader logs `keyboard_unchanged`, `wheel_unchanged`, `button_no_target`, `button_ambiguous`, or `button_unchanged`; the session continues to return the existing protocol-level `scroll/no_target` when all methods fail.

8. **Account a visible Reel at the `page.cards` ingress.** A non-empty `page.cards` payload with `listKind='reels'` means Edge has already resolved and presented the active video. Cloud records one `interaction.occurred{action:'view'}` for that arrival before content selection. This prevents content-language or persona mismatch from turning real watching into `view:0` and an unbounded scroll loop.

9. **Suppress only the matching follow-up detail view.** Cloud remembers the currently visible Reel note id on the connection. If content selection later opens that same Reel and Edge reports `note.detail`, the detail still drives quality and interaction appraisal but does not emit a second view. A normal feed detail, a different note id, or a later feed list keeps the existing detail-based accounting.

10. **Enforce the view gate at the shared scroll exit.** Recording views alone does not stop a run whose content evaluator skips every card: the legacy view check guarded `open_note`, while `content.no_valuable → scroll` bypassed it. `sendScrollCommand` now asks the existing view decision before dispatching any next-page scroll and enters the existing bounded quota sleep when denied. Already-sleeping calls still pass through the suppressed-command logger so the pause remains observable.

## Risks / Trade-offs

- **Keyboard focus can be captured by an overlay or editor.** → Verify identity; unchanged input falls through to wheel/button without claiming success.
- **A wheel delta may be ignored or coalesced.** → Use one trusted wheel gesture with a randomized bounded distance and verify before fallback.
- **Localized next labels can drift.** → Combine locale-assisted matching with a tightly scoped structural two-control fallback; unknown single controls remain fail-closed.
- **Three methods can add latency when the page is stuck.** → Give each method a short bounded verification window and stop immediately on proven movement.
- **A prior method may move late while a fallback starts.** → Re-probe immediately before every write and stop if the original identity has already changed.
- **A selected Reel can also produce `note.detail`.** → Track the current Reel view fact on the Edge session and skip only its matching detail-side view emission.
- **Reel content can be irrelevant to the persona.** → Count the view as an observed fact, but preserve the existing quality/appraisal gates; viewing a Reel does not force a like.
- **Every Reel can be rejected by the content selector.** → Put the view quota check at the common scroll-command exit so the skip-only path cannot roll forever.

## Migration Plan

1. Land the Edge-only reader and fixture tests on the latest `master`.
2. Validate focused Facebook tests, Edge acceptance/full tests, and typecheck.
3. Deploy the Cloud accounting follow-up to `dev` after its default-branch integration; no protocol rollout or database migration is required.
4. The Edge source change takes effect for development runs after restart/update; do not build an installer unless explicitly requested.
5. Roll back by reverting the Edge navigation and Cloud accounting commits; no data migration is required.

## Open Questions

None.
