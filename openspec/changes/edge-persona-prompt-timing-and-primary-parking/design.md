## Context

Both fixes are edge-only UI/UX refinements on already-landed features (persona notice, browser parking). They ride the existing Electron-shell ↔ core stdin control channel and the per-environment status projection; no edge-cloud protocol change.

## Decision 1 — Persona prompt grace window

The client cannot distinguish "genuinely unbound" from "personaBound not yet arrived": cloud sends `personaBound` sticky-true only when bound, never false, and it lands on a cloud tick after the initial connect. A single transient "unbound" read therefore is not authoritative.

- Add a grace window (`PERSONA_PROMPT_GRACE_MS`, default 6s) measured from the moment an environment first observes `auth='logged in' && cloud='connected'`.
- Within the grace, "not yet bound" is treated as unresolved-but-unknown: no dialog, no notification, no in-page reminder.
- A one-shot re-evaluation timer (renderer) / recheck timer (main) guarantees a still-unbound account is prompted after the grace even if no further status push arrives. The timer re-runs the same gate, which prompts only if the account is still current + still unbound.
- If `personaBound=true` (or local persist success) arrives during the grace, the account is cleared and never prompted.
- The grace is applied on both surfaces with the same rationale: the renderer companion dialog (`maybePromptPersonaSetup`) and the controlled-page reminder (`syncBrowserPersonaNotice`).
- The renderer grace is overridable via a `personaPromptGraceMs` setting (default 6s) so it can be unit-tested deterministically with a short value; production leaves it at the default.

Rejected: a purely count-based gate (prompt after N ready pushes) has the same false-positive risk as a too-short timer, since a bound account can also produce several pushes before `personaBound` arrives.

## Decision 2 — primary-screen parking + avatar toggle

- `primary-screen` bounds = full render size clamped to the display, right-aligned but fully within the primary work-area (a "background slot"), so the OS honors it and the page keeps rendering. This deterministically fixes "parking never takes effect" on single-monitor setups, where off-screen positions are clamped back.
- "Show" (raise) uses a centered on-primary position plus `Page.bringToFront`; "park" re-applies the background slot. The position + focus difference makes the toggle observable.
- Parked ≠ shown is by position and by focus/raise, so even where the two rects coincide (screen no wider than the window) the raise still distinguishes them.
- Multi-environment cascade: the existing per-env cascade offset can push a right-aligned slot past the right edge for higher indices; the OS clamps those back on-screen so they stack. This is acceptable — parked windows are background, and the avatar "show" is how an operator brings a specific one forward. (Real-machine note: confirm stacking is acceptable with several concurrent environments.)
- Avatar 3-state lives in the rail row click handler, not `selectEnv` (which is shared by persona-open and snapshot adoption and early-returns on the already-selected env). Per-env `shownEnv` sub-state drives the third visual state; it is cleared on env switch and when the shown env stops running. Honest failure ({ok:false}) never advances the phase.
- Startup hardening: `applyBrowserParking` is wrapped so a visibility-probe failure can no longer skip installing the stdin control listener (which would permanently disable show/re-park — a silent dead-end).

## Risks / trade-offs

- Genuinely-unbound accounts are prompted ~grace-late (≤6s). Acceptable: a short delay on a setup prompt is far better than a false flash on already-set accounts.
- Adding `primary-screen` as a distinct requirement while the concurrent `edge-browser-parking-mode` change still owns the base mode-set requirement leaves two parking requirements in the merged spec until a future consolidation. Chosen over blocking on cross-session ordering.
