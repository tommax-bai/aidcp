## Context

Electron computes display geometry before spawning each edge core. Today the same final parking coordinate is passed as the browser launch hint, while both providers also pass `--start-maximized`. AdsPower creates the native window before returning its dynamic debug port, so CDP cannot correct a visible first frame during that interval. The maximized-state request can also compete with the position hint.

The environment rail's show phase uses `browser.show`; the core moves the window and calls `Page.bringToFront`. Electron currently treats writing that stdin command as success, so the browser is left above the AIDCP client. Guided login and explicit recovery still need the browser itself in front; only the environment-avatar inspection gesture needs AIDCP restored above it.

## Goals / Non-Goals

**Goals:**

- Start parked headful browsers at a best-effort coordinate to the right of every known display, before CDP is available.
- Avoid the conflicting maximized launch state when a staging coordinate is present, while keeping the fixed desktop size and post-attach viewport proof.
- Keep the operator-selected parking bounds independent from the startup staging coordinate.
- For the environment-avatar show gesture, center the browser on the AIDCP client's current outer bounds, establish it immediately below the client in window order, and only advance the UI phase after the placement completes.
- Preserve browser-foreground behavior for guided login and explicit recovery controls.

**Non-Goals:**

- Do not promise that macOS or another window manager will honor a fully off-screen first position.
- Do not switch to headless, minimized, OS-hidden, or a virtual display.
- Do not change cloud protocol, browser-slot scheduling, identity gates, or package an installer.

## Decisions

### 1. Separate startup staging from final parking

Electron derives `launchPosition` from the union of all current display work areas: its left edge is placed beyond the right-most known display plus a fixed gap, while its top follows the primary work area. `bounds`, `visibleBounds`, and fallbacks continue to represent final operator-facing placements. Per-environment cascade may offset both values without coupling them again.

Using the selected final bounds as the launch hint was rejected because `primary-screen` is intentionally visible and therefore cannot hide a cold-start first frame. Relying on the AdsPower GUI's local setting was rejected because the public CLI/API does not expose a global writer and API launch arguments take precedence over profile-stored values.

### 2. Maximize only when no staging coordinate exists

AdsPower and self Chrome omit `--start-maximized` when `BrowserLaunchOptions.windowPosition` is present. They retain `--window-size=1440,980`; after attach, `Browser.setWindowBounds` remains authoritative and the existing visibility/desktop-viewport probe runs before automation. Standalone launches without Electron parking geometry retain the historical maximize fallback, so a raw provider start does not regress to a remembered narrow profile.

Removing the fixed desktop size was rejected because responsive Facebook/XHS layouts depend on it. Removing post-attach correction was rejected because launch hints remain best-effort and window managers may clamp them.

### 3. Center the avatar-shown browser on the live AIDCP window frame

Electron reads `mainWindow.getBounds()` at the moment of the avatar gesture and selects the matching display. It preserves the fixed browser desktop size, centers that browser rectangle on the AIDCP outer window rectangle, and clamps only to the matching display work area when the client is itself near an edge. The resulting bounds travel in the correlated `browser.show` payload and replace the static primary-screen inspection bounds for this avatar-only path.

Using the startup-time `visibleBounds` was rejected because it is centered on the primary display and may also carry a per-environment cascade offset. That creates the observed lower-right exposure when AIDCP is large or has moved. Resizing the browser to exactly match AIDCP was rejected because it could cross the fixed desktop viewport boundary and trigger responsive platform layouts.

### 4. Use a correlated show completion before restoring AIDCP foreground

The rail-avatar path sends `browser.show` with a correlation id, the client-centered target bounds, and a client-foreground policy. The core performs the requested bounds move and browser raise, then emits a structured completion line carrying that id. Electron waits for that bounded completion, raises/focuses its own `mainWindow`, and only then returns success to the renderer. This ordering places the driven browser immediately below AIDCP rather than racing two independent focus calls.

Uncorrelated `browser.show` calls from guided login, tray, and explicit recovery keep the current browser-foreground behavior. A simple fixed delay was rejected because AdsPower/CDP timing varies by machine and could still let a late `Page.bringToFront` cover AIDCP. Skipping `Page.bringToFront` was rejected because the browser could remain behind unrelated windows instead of directly below AIDCP.

### 5. Completion remains honest and bounded

Electron stores only short-lived correlation ids. A core error, child loss, or completion timeout returns `{ok:false}` and the rail does not enter the shown phase. Successful completion proves the core finished the requested move and Electron issued its own foreground call; it still does not claim the OS can guarantee focus indefinitely against later user/system actions.

## Risks / Trade-offs

- [The OS clamps the staging coordinate onto a display] → Keep staging explicitly best-effort, record final proof only after CDP correction, and validate cold starts on real macOS hardware.
- [A transient off-screen page reports hidden] → No automation starts before final parking and the existing post-placement visibility probe passes; hidden final state still fails/degrades honestly.
- [Foreground acknowledgement is lost in stdout processing] → Use a narrow structured prefix, bounded timeout, and focused parsing tests; never advance the rail phase on timeout.
- [AIDCP focus call itself is denied by the OS] → Do not claim permanent topmost status; preserve visible bounds and honest failure for missing windows/cores.
- [AIDCP is partly outside the work area or on another display] → Derive geometry from the matching display and clamp the browser rectangle to that work area while keeping its fixed size.

## Migration Plan

1. Land the Edge-only source and regression tests.
2. Validate cold starts and avatar show ordering on a macOS development machine with the current AdsPower runtime.
3. Rebuild/publish the desktop client only in a separately authorized release flow.

Rollback removes the separate staging coordinate and correlated client-foreground show path, restoring the previous launch hint and browser-foreground behavior.

## Open Questions

- Real-machine acceptance must establish how often macOS clamps the initial off-screen coordinate and whether any visible focus flash remains after maximization is omitted.
