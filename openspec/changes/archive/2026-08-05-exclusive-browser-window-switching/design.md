## Context

The renderer owns a `shownEnv` projection. The first exclusive-recall implementation made every avatar double-click a recall, including a repeated double-click on the target already shown behind AIDCP. That removed the operator's direct way to restore the shown browser to its configured parking position. The older `resetBrowserParking` IPC remains fire-and-forget, so it cannot safely clear `shownEnv`: command acceptance does not establish that the operating system actually moved the window.

The existing geometry and control boundaries remain useful: each child already owns its resolved parking plan, correlated show already moves the target to bounds centered behind the live AIDCP window, and guided-login/recovery calls intentionally retain browser-foreground behavior.

## Goals / Non-Goals

**Goals:**

- Make single-click selection and double-click browser recall independent gestures.
- Let a repeated double-click on the currently shown target restore that exact browser to its configured parking position.
- Treat avatar recall as an exclusive main-process operation across currently controllable environment browsers.
- Apply every non-target child's existing `browser.park` plan, then place the target behind AIDCP.
- Keep the final layout deterministic under rapid consecutive double-clicks.
- Distinguish target-show failure, superseded requests, and partial non-target parking failure.

**Non-Goals:**

- Do not start stopped environments merely to park them, close browsers, change parking configuration, or bypass browser-slot/identity gates.
- Do not change guided login, tray, settings recovery, platform automation, Cloud protocol, or packaging.
- Do not claim that macOS can permanently guarantee window Z-order after unrelated user/system focus changes.

## Decisions

### 1. Single click selects; avatar double-click toggles the shown target

The row's ordinary click handler schedules selection after the same short double-click discrimination window already used by nickname editing and is otherwise a no-op. A dedicated double-click handler on the avatar cancels that pending selection. If the exact environment is not `shownEnv`, the gesture selects it if necessary and requests exclusive recall. If it is already `shownEnv`, the gesture requests a correlated restore to that environment's configured parking position and clears `shownEnv` only after successful completion. The bounded delay keeps the original avatar DOM alive across both physical clicks; otherwise the first click's immediate rail re-render can replace the target before the browser emits `dblclick`.

Keeping the old three-click row control was rejected because its phase depends on previous selection and cannot make a double-click on another environment a complete switch. Making repeated double-click permanently idempotent was rejected because it leaves no direct restore gesture. Immediate single-click re-rendering was rejected because it can replace the avatar between the two physical clicks and make the explicit double-click unreliable.

### 2. Electron main is the exclusive-window authority

Renderer sends one explicit target `envId`; main resolves that exact handle, snapshots other live/parking-ready handles, and sends each a correlated `browser.park`. Each child applies its already-resolved parking configuration, so primary-screen, parking-display, edge-strip, offscreen, fallbacks, and per-environment cascade remain authoritative. Main does not compute substitute parking bounds and does not wake absent browsers.

Renderer-side fan-out was rejected because renderer status is only a projection and cannot safely decide which child process is currently controllable. Parking only the previous `shownEnv` was rejected because prior UI state can already be stale and other browser windows may have been exposed through recovery/manual paths.

### 3. Extend the existing correlation channel to parking

`browser.park` accepts the same optional request id as `browser.show` and emits a completion only after `applyBrowserParking()` succeeds or fails. Uncorrelated reset/recovery calls preserve their existing behavior. Electron generalizes its pending reply table so show and park use the same bounded correlation mechanism while still validating the replying `envId`.

Treating stdin write acceptance as completion was rejected because it recreates the current false-exclusive state: the UI could mark the target shown while another window never moved.

### 4. Serialize recalls and restores and coalesce stale queued requests

Main owns a monotonic window-intent generation and a single promise tail shared by recall and restore. A new double-click becomes the latest generation. Operations execute serially so a late show from an older recall cannot overtake a newer restore, and a late restore cannot override a newer recall. A queued operation checks the generation before doing work and returns a structured `superseded` result if a newer gesture already exists. The latest operation establishes the final shown-or-parked state.

Fully concurrent operations were rejected because cross-child CDP commands can complete in either order and leave an older target visible. Canceling already-written child commands was rejected because stdin/CDP has no trustworthy cancellation boundary.

### 5. Parking and recall failures remain explicit

Other-browser parks run in parallel and are bounded as a group. If the target show succeeds, renderer marks that target shown. When one or more non-target parks fail, the result is `ok: true` with a bounded failure summary and the UI reports that the target was recalled but exclusive parking was incomplete. If target show fails, `ok: false` and renderer does not advance `shownEnv`. A superseded request produces no user-facing failure because a newer operator intent is already responsible for the final state.

Failing the target recall solely because an unrelated browser could not be parked was rejected because it would make the requested environment unavailable while providing no safer final layout. Silently ignoring those failures was rejected because it would falsely claim exclusivity.

Restoring the currently shown target uses the correlated `browser.park` path. A failed or timed-out restore keeps `shownEnv` and reports the failure; renderer never clears the shown projection from fire-and-forget command acceptance.

## Risks / Trade-offs

- [One unresponsive child adds latency] → Park children concurrently under the existing bounded completion timeout and report only the failed environment labels.
- [An older recall or restore is already in flight when a newer gesture arrives] → Serialize both operations; the newer request runs afterward and establishes the final layout.
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

None. The user confirmed that double-click recalls an unshown environment and repeated double-click on the shown target restores it according to configured parking parameters.
