## Context

The Electron supervisor currently pauses an environment by sending `SIGTERM` to its edge core. The core has one terminal shutdown path: it stops watchers and browsing, closes the cloud and CDP connections, calls the owned browser handle's close-and-confirm operation, and exits. This correctly avoids orphan browsers on shutdown and recycle, but it makes temporary pause indistinguishable from final close.

Browser lifecycle ownership is intentionally kept in the edge core. The Electron-side AdsPower clients are read-only for lifecycle endpoints, so adding a supervisor-side `browser/stop` call would create a second writer and a race with the core. Multi-environment operation also requires every lifecycle command and status transition to remain keyed by `envId`.

## Goals / Non-Goals

**Goals:**

- Pause automation, monitoring, and cloud participation cleanly without closing the owned browser.
- Preserve a single browser-lifecycle writer and allow a later explicit close to use the original owned-browser handle.
- Expose separate paused and closed states with unambiguous resume/start/close controls.
- Preserve final-close behavior for application exit, environment removal, fatal recycle, and ordinary restart paths.
- Keep rapid or repeated lifecycle actions bounded and honest.

**Non-Goals:**

- No new cloud command, cloud persistence field, or cross-machine browser takeover behavior.
- No change to risk-state ownership or automatic browser recovery after a genuine browser crash.
- No attempt to make an externally reused browser owned by the edge process.

## Decisions

### Keep a paused core as a lightweight lifecycle owner

The Electron supervisor will spawn each core with a Node IPC channel. A local `lifecycle.pause` message asks the core to deactivate browsing, watchers, cloud connectivity, and CDP activity but retain the browser handle and remain alive in a parked state. The core acknowledges `lifecycle.paused` only after deactivation completes.

This keeps the only process allowed to close the browser alive, so a subsequent `lifecycle.close` can call the existing close-and-confirm path. It avoids adding a second AdsPower lifecycle writer in Electron and avoids a close-only helper process that would need to reconstruct ownership after the fact.

Alternatives considered:

- Killing the core while skipping browser cleanup leaves no owner available for a later explicit close.
- Calling `browser/stop` from Electron violates the existing single-writer boundary and can race a still-running core.
- Keeping the full automation session live and merely stopping the browse loop leaves cloud commands, publishers, and monitors reachable unless many independent gates are added.

### Resume by exiting the parked owner without closing the browser

`lifecycle.resume` tells a parked core to exit after deactivation while preserving the browser. The Electron supervisor then starts a fresh core for the same environment. The provider's existing start/attach behavior reuses the already-active profile and obtains its current CDP endpoint; no second profile window is created.

A parked core is deliberately not rehydrated in place. Rebuilding the existing main function's client, monitor, identity, and browse graph in the same process would add a second initialization lifecycle and increase stale-state risk.

### Make close an explicit final transition

The renderer shows a secondary `关闭` control when an environment is paused. Closing sends `lifecycle.close`; the core runs the existing final browser close-and-confirm behavior and exits. The supervisor projects `session=closed` only after the core exits from this explicit close intent. In the closed state the primary control is `启动`.

Final system intents remain final: application quit, environment removal, fatal recycle, and non-pause termination continue to close an owned browser. Closing a reused external browser remains forbidden by the existing ownership rule.

### Track lifecycle intent per environment

Each Electron environment handle gains explicit parked/close intent flags. Child IPC messages are handled on that exact handle, and exit classification treats parked/closing exits as intentional. Bulk pause skips already-paused environments; bulk start resumes paused environments and starts closed/offline environments. Lifecycle message delivery failure is surfaced as an error and MUST NOT silently fall back to `SIGTERM`, because that fallback would close the browser while claiming to pause.

### Keep status compatibility additive

`closed` is added to the local session status vocabulary. Older renderers receiving it already fall back to a string value in detail rows, while the updated renderer supplies the human label `已关闭`, a static presence message, a closed rail label, and a `启动` primary action. No existing status field is removed.

## Risks / Trade-offs

- [A parked core consumes a small process slot per paused environment] → The parked core closes cloud/CDP connections and stops monitors, retaining only the lifecycle owner and IPC channel.
- [Rapid pause/resume/close clicks can overlap] → Serialize lifecycle transitions per environment, disable relevant controls while a command is pending, and make core deactivation/finalization idempotent.
- [IPC delivery fails or an old core lacks lifecycle support] → Report the failure and keep the current running state; never use a browser-closing signal as a pause fallback.
- [The retained browser closes externally while paused] → Resume follows the existing provider startup/identity gates and reports the real failure; the client does not fabricate successful reuse.
- [Application quit while paused could leave the browser open] → OS termination signals always use final-close semantics, even from the parked state.

## Migration Plan

1. Ship the core lifecycle IPC handling and Electron supervisor changes in the same desktop package.
2. Add renderer and pure-state tests, plus core lifecycle tests for pause retention, resume preservation, close confirmation, and terminal signal behavior.
3. Build and publish the next dev desktop package; update the console download metadata and verify the public artifacts.
4. Rollback is a package rollback to the previous desktop version; no cloud or data migration is required.

## Open Questions

None.
