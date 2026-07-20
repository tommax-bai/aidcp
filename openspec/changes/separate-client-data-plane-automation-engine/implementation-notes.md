## Admission

- Preflight: passed on 2026-07-20.
- Control worktree: `/Users/baitianxing/codes/aidcp.wt/separate-client-data-plane-automation-engine`, start `739f8e1088b2d1435886726e6e2c0cb7490955e4`.
- Edge worktree: `/Users/baitianxing/codes/aidcp-edge.wt/separate-client-data-plane-automation-engine`, start `857d3324a2cba8888330cbb55c3ae76691c6dbed`.
- Cloud worktree: `/Users/baitianxing/codes/aidcp-cloud.wt/separate-client-data-plane-automation-engine`, start `f57bfb7`.
- Canonical branches matched origin; control `output/` and `tmp/` were pre-existing and preserved. Edge/Cloud worktrees have independent physical `node_modules` from `npm ci --prefer-offline`.

## Pre-change path inventory

| Operation group | Current entry/transport | Browser dependency | Target contract |
|---|---|---|---|
| settings, environment nickname, notification surface | renderer → named Electron IPC/local | forbidden | `local`; unchanged |
| persona read/generate/persist | renderer → named IPC → Electron customer-auth HTTP | forbidden | `cloud_data`; no engine/WS gate |
| publish approval/reject and draft image removal | renderer → named IPC → Electron customer-auth HTTP | forbidden | `cloud_data`; accepted receipt remains distinct from platform success |
| interaction workspace reads/config | renderer → named IPC → Electron customer-auth HTTP | forbidden | `cloud_data`; no engine/WS gate |
| UI snapshot compatibility, pacing, interaction ACK/control, ping/pong | Cloud ↔ Edge WebSocket | forbidden | new clients only receive automation projection; legacy customer-data snapshot fields are compatibility-only |
| interaction sync/reply/reconcile/offboard | Cloud ↔ Edge WebSocket → local platform API | forbidden except explicit reauth | `platform_api_automation`; only while ordinary automation engine is enabled, except restricted cleanup |
| auth reopen and remote browser control | Cloud ↔ Edge WebSocket or local browser IPC | on demand | `browser_lifecycle`; explicit human/recovery purpose |
| browse, page interaction, publish, task lease, captcha | Cloud ↔ Edge WebSocket → CDP | required | `page_automation`; full slot/identity/lease gates |

Electron lifecycle inventory:

- `proceedAfterAuth()` and periodic roster maintenance currently call `bootstrapOwnedClientCores()`; this creates browser-absent ordinary Edge children after login.
- `edge:start` currently wakes a browser-absent child or queues a full browser start.
- `pauseEdge()` sends `lifecycle.pause` but intentionally keeps the child/WebSocket alive.
- `resumeEdge()` resumes the existing child or queues a new start.
- `closeEdge()` currently means browser standby, not full engine/browser close; `browser:close` aliases it.
- `lifecycleAxes()` projects `coreState`, `cloudState`, `automationState` and `browserState`; renderer and `ui-logic.js` still make core/Cloud primary.
- Restricted offboard cleanup already uses a separate customer-auth bootstrap and must remain the only login-time browserless worker exception.

Implemented lifecycle outcome: ordinary engines now start only from explicit automation intent; pause uses `lifecycle.pause_and_exit`, releases the engine-owned browser/CDP/slot, and does not respawn; resume reacquires resources automatically. Cloud additionally filters `ui.snapshot` for the new capability at both service and transport boundaries so ordinary customer data cannot be pushed through the automation channel.

## Capability and compatibility matrix

| Edge hello | Cloud welcome | Behavior |
|---|---|---|
| neither capability | legacy/no split | Existing legacy lifecycle; Cloud sends only legacy-compatible commands |
| `client_core_browser_executor_v1` only | echoes v1 | Existing browserless-core semantics remain for already shipped clients |
| `client_data_plane_automation_engine_v1` | echoes v2 | Client data uses HTTP; ordinary Edge child is on-demand automation engine; new operation names/state projection apply |
| v2 offered, Cloud does not echo | no v2 | Edge fails back to compatible command wire names but MUST NOT make HTTP data management depend on engine/browser; diagnostics record capability downgrade |
| Cloud supports v2, Edge does not offer | no v2 echo | Cloud retains legacy adapters and MUST NOT send v2-only active commands or state fields |

Protocol migration rules:

- New capability and fields are optional; no MessageType removal in this change.
- Cloud domain methods remain single writer; HTTP and legacy WS adapters share idempotency/CAS and audit gates.
- Unknown active command classification remains `operation_unclassified` fail-closed.
- New renderer consumes `automationState`, `browserState` and diagnostic `engineLinkState`; `coreState`/`cloudState` remain compatibility-only until a later removal change.
