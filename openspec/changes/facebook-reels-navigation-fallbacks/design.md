## Context

The existing Reels driver proves movement by comparing the canonical `/reel/<id>` route and active-video identity, but it attempts only the far-right navigation button. On the first Reel, Facebook renders four same-sized header controls, a disabled previous control, and one enabled next control. The broad structural selector therefore reports ambiguity, while the two-enabled-button assumption would reject the first Reel even after header controls are excluded.

Facebook also supports trusted ArrowDown and wheel inputs. These are less coupled to localized button markup and are suitable as the primary navigation methods as long as every method remains post-condition verified.

## Goals / Non-Goals

**Goals:**

- Attempt ArrowDown, then a 70–100px downward wheel gesture, then the button fallback.
- Stop at the first method that changes the canonical Reel route or active-video identity.
- Keep every input bounded and fail closed when identity is unchanged or button targeting is ambiguous.
- Make method selection and failure visible in logs and deterministic in tests.

**Non-Goals:**

- Changing Cloud scheduling, protocol messages, risk accounting, or card parsing.
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

## Risks / Trade-offs

- **Keyboard focus can be captured by an overlay or editor.** → Verify identity; unchanged input falls through to wheel/button without claiming success.
- **A wheel delta may be ignored or coalesced.** → Use one trusted wheel gesture with a randomized bounded distance and verify before fallback.
- **Localized next labels can drift.** → Combine locale-assisted matching with a tightly scoped structural two-control fallback; unknown single controls remain fail-closed.
- **Three methods can add latency when the page is stuck.** → Give each method a short bounded verification window and stop immediately on proven movement.
- **A prior method may move late while a fallback starts.** → Re-probe immediately before every write and stop if the original identity has already changed.

## Migration Plan

1. Land the Edge-only reader and fixture tests on the latest `master`.
2. Validate focused Facebook tests, Edge acceptance/full tests, and typecheck.
3. No Cloud deployment or protocol rollout is required. The source change takes effect for development Edge runs after restart/update; do not build an installer unless explicitly requested.
4. Roll back by reverting the Edge commit; the prior button-only behavior is restored without data migration.

## Open Questions

None.
