## 1. Protocol and Contract

- [x] 1.1 Add synchronized Cloud/Edge `interaction.browser.control` payload types, validators, negotiated capability, fixtures, and active-command routing.
- [x] 1.2 Document browser foreground control, acceptance-only semantics, and auth-status truth in `docs/protocol.md`.

## 2. Cloud Control Path

- [x] 2.1 Add the ownership-scoped idempotent customer browser-control API and Electron-facing response envelope without treating delivery as execution success.
- [x] 2.2 Route open/close commands only to the uniquely matched compatible online Edge and cover unavailable, scope, ownership, and duplicate-request cases.

## 3. Edge Browser Lifecycle

- [x] 3.1 Implement serialized active-session browser open/close control in the video-channel auth coordinator and Connector while preserving the encrypted API session and identity binding.
- [x] 3.2 Keep manually opened sidecars visible until explicit close or lifecycle cleanup, and make repeated actions and failure states truthful.
- [x] 3.3 Close manually opened sidecars during pause, stop, offboard, and runtime destruction without affecting another environment.

## 4. Electron Workspace

- [x] 4.1 Add minimal preload/main IPC for the environment-scoped browser-control customer API.
- [x] 4.2 Show “打开浏览器”, “转入后台”, transitional labels, and acceptance-only notices from the selected environment's auth/browser projection while keeping reauth and client logout distinct.

## 5. Validation and Delivery

- [x] 5.1 Add focused Cloud, Edge auth/runtime, Electron IPC/workspace, protocol fixture, and lifecycle regression tests.
- [x] 5.2 Run Cloud and Edge acceptance suites, full tests, typechecks, builds required by the touched paths, and `openspec validate wechat-channels-browser-foreground-control --strict`.
  <!-- Edge: 1540 passed; Cloud: 2305 passed, 6 real-environment gates skipped; both typecheck/build passed; OpenSpec strict validation passed. -->
- [ ] 5.3 Commit and push Edge/Cloud/control changes, record SHAs and validation evidence here, and do not build an Edge installer.
- [ ] 5.4 Deploy the clean Cloud default branch to `dev`, verify service/listeners/health/Feishu/PostgreSQL and the acceptance-only control path, and record the honest live-validation boundary.
- [ ] 5.5 Archive the completed OpenSpec change, validate all specs strictly, and remove obsolete worktrees/branches.
