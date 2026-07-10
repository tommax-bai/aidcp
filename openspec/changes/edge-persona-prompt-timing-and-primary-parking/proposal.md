## Why

Two operator-facing rough edges on the edge companion, both reported from real use:

- The persona setup prompt fires on the wrong signal timing. Right after an environment becomes logged-in + cloud-connected there is a short window where the authoritative "persona is bound" signal (sent sticky-true, only when bound, on a subsequent cloud tick) has not yet arrived. The client currently reads that window as "unbound" and immediately pops the persona dialog (and pushes the in-page reminder). Accounts that already have a persona get prompted anyway — the timing point of the persona check is wrong.
- Window parking "does not take effect". The shipping default modes ask the OS to place the driven window ~98.75% off the right edge (edge-strip) or fully off-screen (offscreen); single-monitor OSes clamp the window back on-screen, so it never tucks away. There is no reliable "put it on the primary screen" mode, clicking an environment's avatar never moves its browser, and the selected environment's highlight is easy to miss.

## What Changes

- Persona prompt/notice timing: introduce a grace window after an environment first becomes logged-in + cloud-connected. During the grace the client MUST NOT treat "not yet bound" as "unbound" — it neither auto-opens the persona dialog, emits a notification, nor pushes the in-page reminder. Only after the grace elapses with the account still unbound does it prompt. Accounts whose persona-bound signal arrives within the grace are never prompted. Applies to both surfaces (Electron dialog + controlled-page reminder). A re-evaluation timer guarantees a genuinely-unbound account is still prompted after the grace even without further status pushes.
- New `primary-screen` parking mode, made the default: the driven window is placed at a fully-on-primary "background slot" the OS honors, keeping the browser rendering and not stealing focus. The old edge-strip / offscreen / parking-display modes remain selectable.
- Environment-avatar 3-state toggle: first click selects the environment (distinct red highlight); a second click raises that environment's browser to the primary screen and focuses it; a third click sends it back to its parked slot. Reuses the existing per-environment show / re-park control channel; honest failures (browser not ready) do not advance the phase.
- Robustness: the "show" action now raises/focuses the window (best-effort); the parking-visibility fallback targets a reliably-visible centered position instead of the clamped edge strip; a parking-apply failure at startup can no longer disable the show/re-park control channel; the parking-display no-secondary fallback stays consistent with the default mode.

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `edge-companion-ui`: Add a grace window to persona prompting/notice so already-bound accounts are not prompted during the pre-`personaBound` window; add primary-screen default parking with reliable placement; add the environment-avatar select → show-on-primary → re-park toggle with a distinct selected highlight.

## Impact

- Code: `../aidcp-edge/src/electron/browser-parking.cjs`, `../aidcp-edge/src/cdp/browser-window.ts`, `../aidcp-edge/src/main.ts`, `../aidcp-edge/src/electron/main.cjs`, `../aidcp-edge/src/electron/renderer/{renderer.js,index.html,styles.css}`, and focused tests under `../aidcp-edge/test/`.
- Protocol: no edge-cloud message type changes; reuses the existing Electron-to-core stdin control channel (`browser.show` / `browser.park` / `browser.personaNotice`). No CLAUDE.md §7 hot file (protocol.ts, command-bridge, role registry, risk state machine) is touched.
- Deployment: edge-only; no cloud runtime / ECS deployment. Takes effect for newly launched browsers; requires the edge client to be rebuilt/repackaged to reach operators.
- Relation to the concurrent `edge-browser-parking-mode` change: additive — this change adds a further mode and makes it the default; it does not restate that change's mode-set or recovery-control requirements.
