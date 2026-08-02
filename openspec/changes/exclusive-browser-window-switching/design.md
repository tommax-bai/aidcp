## Context

The renderer currently owns a `shownEnv` toggle and interprets the environment row as `select -> show -> park`. A physical double-click on an unselected row performs only the first phase because the second click is discarded, while `selectEnv()` clears `shownEnv` without issuing `browser.park` to the previously shown child. Electron main can correlate only `browser.show`; `browser.park` is fire-and-forget, so it cannot establish that other windows reached their per-environment parking bounds before completing a switch.

The existing geometry and control boundaries remain useful: each child already owns its resolved parking plan, correlated show already moves the target to bounds centered behind the live AIDCP window, and guided-login/recovery calls intentionally retain browser-foreground behavior.

## Goals / Non-Goals

**Goals:**

- Make single-click selection and double-click browser recall independent gestures.
- Treat avatar recall as an exclusive main-process operation across currently controllable environment browsers.
- Apply every non-target child's existing `browser.park` plan, then place the target behind AIDCP.
- Keep the final layout deterministic under rapid consecutive double-clicks.
- Distinguish target-show failure, superseded requests, and partial non-target parking failure.

**Non-Goals:**

- Do not start stopped environments merely to park them, close browsers, change parking configuration, or bypass browser-slot/identity gates.
- Do not change guided login, tray, settings recovery, platform automation, Cloud protocol, or packaging.
- Do not claim that macOS can permanently guarantee window Z-order after unrelated user/system focus changes.

## Decisions

### 1. Single click only selects; avatar double-click always recalls

The row's ordinary click handler schedules selection after the same short double-click discrimination window already used by nickname editing and is otherwise a no-op. A dedicated double-click handler on the avatar cancels that pending selection, selects the environment if necessary, and requests exclusive recall. The bounded delay keeps the original avatar DOM alive across both physical clicks; otherwise the first click's immediate rail re-render can replace the target before the browser emits `dblclick`. The second physical click therefore cannot toggle the target back to parking. Repeating the gesture for the same environment reruns the same recall intent and never becomes a park toggle.

Keeping the three-phase row toggle was rejected because its phase depends on previous selection and cannot make a double-click on another environment a complete switch. Immediate single-click re-rendering was rejected because it can replace the avatar between the two physical clicks and make the explicit double-click unreliable.

### 2. Electron main is the exclusive-window authority

Renderer sends one explicit target `envId`; main resolves that exact handle, snapshots other live/parking-ready handles, and sends each a correlated `browser.park`. Each child applies its already-resolved parking configuration, so primary-screen, parking-display, edge-strip, offscreen, fallbacks, and per-environment cascade remain authoritative. Main does not compute substitute parking bounds and does not wake absent browsers.

Renderer-side fan-out was rejected because renderer status is only a projection and cannot safely decide which child process is currently controllable. Parking only the previous `shownEnv` was rejected because prior UI state can already be stale and other browser windows may have been exposed through recovery/manual paths.

### 3. Extend the existing correlation channel to parking

`browser.park` accepts the same optional request id as `browser.show` and emits a completion only after `applyBrowserParking()` succeeds or fails. Uncorrelated reset/recovery calls preserve their existing behavior. Electron generalizes its pending reply table so show and park use the same bounded correlation mechanism while still validating the replying `envId`.

Treating stdin write acceptance as completion was rejected because it recreates the current false-exclusive state: the UI could mark the target shown while another window never moved.

### 4. Serialize recalls and coalesce stale queued requests

Main owns a monotonic recall generation and a single promise tail. A new double-click becomes the latest generation. Operations execute serially so a late show from an older request cannot overtake a newer parking/show sequence; a queued operation checks the generation before doing work and returns a structured `superseded` result if a newer gesture already exists. The latest operation always finishes with target show after all of its park attempts, so its target is the final browser immediately below AIDCP.

Fully concurrent operations were rejected because cross-child CDP commands can complete in either order and leave an older target visible. Canceling already-written child commands was rejected because stdin/CDP has no trustworthy cancellation boundary.

### 5. Partial parking failure remains useful but explicit

Other-browser parks run in parallel and are bounded as a group. If the target show succeeds, renderer marks that target shown. When one or more non-target parks fail, the result is `ok: true` with a bounded failure summary and the UI reports that the target was recalled but exclusive parking was incomplete. If target show fails, `ok: false` and renderer does not advance `shownEnv`. A superseded request produces no user-facing failure because a newer operator intent is already responsible for the final state.

Failing the target recall solely because an unrelated browser could not be parked was rejected because it would make the requested environment unavailable while providing no safer final layout. Silently ignoring those failures was rejected because it would falsely claim exclusivity.

## Risks / Trade-offs

- [One unresponsive child adds latency] → Park children concurrently under the existing bounded completion timeout and report only the failed environment labels.
- [An older operation is already in flight when a newer gesture arrives] → Serialize operations; the newer request runs afterward and establishes the final layout.
- [A browser becomes ready after the non-target snapshot] → It is outside this operation's controllable snapshot and retains normal startup parking; a later recall re-snapshots current handles.
- [Renderer is re-rendered between click and double-click] → Bind the double-click directly to the avatar and route by stable `envId`; nickname/persona controls continue stopping propagation.
- [Installed clients still exhibit the old behavior] → Source validation is separate from packaging/installation; this change does not build or install a client.

## Migration Plan

1. Land the Edge source and focused renderer/main/core tests.
2. Validate the full Edge suite, typecheck, and strict OpenSpec change.
3. Integrate the default branches without packaging or installation.
4. A later explicitly authorized desktop release can verify real macOS multi-window focus/parking behavior.

Rollback restores the old renderer gesture and removes the exclusive IPC/correlated park path; existing uncorrelated `browser.show` and `browser.park` remain compatible throughout.

## Open Questions

None. The user confirmed that double-click recalls one environment and parks all other windows according to the configured parking parameters.
