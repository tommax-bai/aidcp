## 2026-07-20 implementation inventory

### Starting points

- `aidcp-edge` worktree: `/Users/baitianxing/codes/aidcp-edge.wt/separate-client-core-browser-executor`, start `0a0b6c55f600076bac3289c681992db13bc251e7`.
- `aidcp-cloud` worktree: `/Users/baitianxing/codes/aidcp-cloud.wt/separate-client-core-browser-executor`, start `5b31064f2098332d46702f7cf88220dc3d48fa12`.
- Both `browser-slot-cloud-presence` repo heads are ancestors of current default branches (`aidcp-edge` `4e0671e3f71910b30dd36d29b3b5b5d3675a78d5`; `aidcp-cloud` `19cf0eb645708abfa45456cc778324f01a588ea1`). Its browser-absent core, persistent-binding bootstrap, in-place wake and Cloud handling are reusable current behavior.
- `browser-slot-scheduling` remains in progress only for its own measurement/rotation/idle-release backlog. This change does not alter FIFO, memory admission, task lease or cold-standby safety gates; it changes which operations enter that domain.

### Current coupling inventory

| Surface | Current mechanism | Classification | Required change |
|---|---|---|---|
| Customer login / roster refresh | `proceedAfterAuth()` only calls `syncEnvHandles()` and renders “点启动”; no core starts | `cloud` bootstrap | Automatically call browser-absent core bootstrap for trustworthy roster handles with a core-only concurrency budget |
| Normal environment start | `queueStartEnv()` enters AdsPower/browser preparation first; `startBrowserAbsentCore()` is reached only when the start queue or slot rejects | `browser_lifecycle` + `page_automation` | Keep this path only for explicit automation/browser intent; make `startBrowserAbsentCore()` the normal post-login path |
| Persona get/generate/persist | Already implemented as named Electron-main customer-auth requests; legacy WS handlers remain | `cloud` | Preserve and include persona truth in independent core/browser tests; no new transport |
| Publish approve/reject | `publish:approval` calls `sendPublishApprovalCommand()`, which requires `handle.child` | `cloud` decision, followed by `page_automation` dispatch | Submit decision through customer-auth using authoritative env binding; keep legacy WS handler and distinguish accepted from published |
| Draft image removal | `publish:image-remove` calls `sendPublishClientCommand()`, which requires `handle.child` | `cloud` | Submit through customer-auth and reuse the same Cloud CAS handler |
| Interaction list/detail/draft/config/notify | Named Electron-main customer-auth bridge already exists | `cloud` | Preserve; explicitly classify and assert it never enters browser scheduling |
| WeChat sync/reply/reconcile | Edge runtime owns encrypted platform API session; Cloud sends `interaction.sync.request`, `interaction.reply.send`, `interaction.reply.reconcile` | `platform_api` | Keep core-local; browser remains closed unless a separate auth-reopen/browser-control command is received |
| Auth reopen / visible sidecar | `interaction.auth.reopen`, `interaction.browser.control`, local `interaction:browser:open-local` | `browser_lifecycle` | Keep explicit and slot-backed; never use as a generic prerequisite for Cloud operations |
| XHS/FB browse, publish, interaction, captcha and edge task commands | Existing `EdgeClient` allowlists plus cold-standby wake and task coordinator | `page_automation` | Route through centralized classification; preserve slot, CDP, real identity and lease gates |
| Cloud selection | `cloud:restartAll` SIGTERMs every core and calls `queueStartEnv()`, which may start AdsPower/browser | `cloud` transport lifecycle | Add local parent-child rebind intent and keep browser state/slot ownership unchanged |
| Offboard recovery | `syncEnvHandles()` calls `queueStartEnv()` for cleanup-only handles | restricted `platform_api` cleanup | Replace normal start with signed, purpose-scoped cleanup bootstrap and a browser-absent restricted session |
| Local settings/nickname/notifications | Electron main/local stores; some save flows reuse restart helpers | `local` | Keep local writes browser-free and split settings that truly require transport rebind from browser lifecycle |

### Operation registry contract

The registry covers active operations, not request/response envelopes already correlated by id.

- `local`: named Electron-only settings, UI state, notifications and nickname operations.
- `cloud`: customer-auth persona, pending-draft reads/writes, approval decisions, configuration and control transport state.
- `platform_api`: WeChat sync, reply, reconcile, runtime controls and restricted offboard cleanup.
- `browser_lifecycle`: explicit open/close/show/hide, auth reopen and browser-control transitions.
- `page_automation`: plan/browse/navigation/page interaction, captcha assist, edge task acquire/release and publish execution.

Unregistered active Cloud→Edge messages are rejected/logged as `operation_unclassified`; they are never defaulted into a browser wake or a browser-free route.

### Protocol and compatibility delta

- No new protocol v2 `MessageType` is required. Customer Cloud operations use additive customer-auth HTTP routes; Electron renderer receives only narrow IPC DTOs.
- Add optional hello/welcome capability `client_core_browser_executor_v1`. New Cloud echoes it only when offered; old Cloud omits it and the Edge remains compatible. Existing `browser_absent_v1` remains during the compatibility window but is no longer the product-level lifecycle label.
- Cloud→Edge active-command classification is mirrored in Edge code/tests and documented in `docs/protocol.md`; existing payloads and command mappings stay byte-compatible.
- Legacy WS persona, publish approval and draft-image handlers remain available for older Edge builds and reuse the same Cloud domain handlers.
- Cloud is deployed first because all new HTTP/capability handling is additive; Edge activation follows only after Cloud compatibility tests pass.
