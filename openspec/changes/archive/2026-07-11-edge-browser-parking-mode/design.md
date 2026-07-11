## Context

The desktop edge app currently starts an AdsPower or self Chrome browser in a normal visible foreground window. This keeps the browser headful, which is preferred by the anti-detection guidance, but it interrupts the operator's desktop. Minimizing or headless mode would reduce interruption but can make `document.hidden` observable and create page-visibility/timer-throttling risk.

The current AdsPower provider already passes launch arguments such as `--window-size=1440,980` through `browser/start`. The edge core also owns a CDP connection after `attachToPage`, which can issue `Browser.getWindowForTarget` and `Browser.setWindowBounds`.

## Goals / Non-Goals

**Goals:**

- Add three operator-selectable parking modes in the Electron settings drawer.
- Keep the driven browser headful and sized for the existing desktop layout assumptions.
- Reduce first-launch foreground disruption with launch-position hints where possible.
- Re-apply and verify the parking bounds after CDP attach.
- Fail or degrade honestly if a selected parking mode cannot preserve a visible page and valid viewport.
- Provide a recovery path to bring/reset the browser window.

**Non-Goals:**

- Do not create OS-level virtual displays from AIDCP.
- Do not install display drivers or third-party display tools.
- Do not use headless or minimized mode as the default answer to foreground disruption.
- Do not change cloud protocol, risk authority, or browser command semantics.

## Decisions

### D1. Three modes, with recoverable default

The persisted setting is `browserParkingMode` with values:

- `parking-display`: target a non-primary display when Electron can detect one.
- `edge-strip`: park the window mostly outside the primary display while leaving a small visible strip.
- `offscreen`: move the window fully outside the primary display after verification.

Default: `edge-strip`. This materially reduces interruption while preserving a visible recovery handle and avoiding a hidden/minimized page. `parking-display` is best when available but cannot be assumed on most operator machines. `offscreen` is an advanced mode because OS window managers can clamp offscreen windows or page visibility can become abnormal.

### D2. Electron computes geometry, edge core applies it

Electron main process has reliable access to display geometry via Electron's `screen` module. It computes:

- mode requested by the user;
- chosen effective mode after fallback;
- bounds `{ left, top, width, height }`;
- optional early `--window-position=x,y` launch hint.

The core process receives this via environment variables. The core remains responsible for applying the bounds over CDP after it attaches to the target page. This keeps display enumeration out of the pure edge core while still letting CDP correct AdsPower/Chrome window memory.

### D3. Launch hint plus CDP correction

AdsPower mode gets early `launch_args` position hints to reduce the initial foreground flash. CDP correction after attach is still authoritative because Chrome/AdsPower may restore or clamp previous positions. Self mode can use the same CDP correction, with any Electron Chrome launcher position hint treated as best effort.

### D4. Verification before continuing

After applying bounds, the core evaluates a visibility probe:

```js
({
  hidden: document.hidden,
  visibility: document.visibilityState,
  w: window.innerWidth,
  h: window.innerHeight
})
```

The core only treats parking as successful when the page remains visible and the viewport stays near the required desktop size. If `parking-display` cannot be resolved or fails verification, Electron/core use `edge-strip`. If `offscreen` fails verification, the core resets to `edge-strip` instead of continuing in a hidden state.

### D5. Recovery is explicit

The desktop client adds recovery controls:

- "显示浏览器": move/reset the browser window to a normal visible location.
- "重置浏览器位置": restore default parking coordinates on the next application of the selected mode.

These are honest operational controls, not health-state substitutions. If recovery cannot be applied because no CDP window is available, the UI reports that fact.

## Risks / Trade-offs

- [Risk] Some OS/window-manager combinations clamp offscreen coordinates back onto the visible display. -> Mitigation: apply CDP correction, verify final state, and report/degrade honestly.
- [Risk] Fully offscreen windows could still make the page hidden or render-throttled on some systems. -> Mitigation: make `offscreen` an advanced option and require visibility/viewport verification.
- [Risk] First-launch flash may still occur before CDP attach. -> Mitigation: include launch-position hints for AdsPower and self where available, then correct via CDP.
- [Risk] Parking may conflict with window positions remembered by AdsPower profiles. -> Mitigation: CDP correction is applied each startup and can be re-applied via recovery controls.
- [Risk] Leaving a visible strip is slightly less hidden than a virtual display. -> Mitigation: use it as the default because it is recoverable and stable on single-display machines.

## Migration Plan

1. Add the setting with default `edge-strip`; old settings files load through defaults.
2. Add UI controls in the existing settings drawer.
3. Apply env injection and edge-core CDP parking.
4. Add tests for setting persistence/env injection, renderer controls, provider launch args, geometry computation, and CDP parking fallback.
5. Validate in `aidcp-edge` with typecheck and targeted/unit tests.

Rollback: remove the setting/env usage and skip CDP parking. Existing settings files containing `browserParkingMode` remain harmless unknown JSON fields.
