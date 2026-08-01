## 1. Structured Login Flow

- [x] 1.1 Add coordinator coverage and a callback for structurally confirmed automatic login progress without inferring from credential presence or logs.
- [x] 1.2 Emit generation-scoped automatic-progress, manual-required, and terminal-failure lifecycle events from Facebook startup authentication.

## 2. Electron Status Projection

- [x] 2.1 Project one mutually exclusive login-flow state in Electron and clear or replace it on automatic progress, manual requirement, identity establishment, restart, pause, close, and child exit.
- [x] 2.2 Preserve a current-generation terminal authentication failure across child exit and prevent an older binding stop reason from collapsing it to ordinary offline state.

## 3. Client Presentation

- [x] 3.1 Map automatic login to `登录中` in the existing `启动中` group without changing automation intent or task-ready truth.
- [x] 3.2 Keep explicit manual login and terminal authentication failure in `需要处理`, with stable detail text and rail refresh inputs.

## 4. Validation And Delivery

- [x] 4.1 Add focused coordinator, lifecycle IPC, rail, and health-view regressions for automatic, manual, resumed, terminal-failure, and stopped transitions.
- [x] 4.2 Run focused Edge tests, typecheck, and strict OpenSpec validation.
  <!-- Edge: focused auth/UI/lifecycle 96/96; post-rebase fleet/renderer 195/195; acceptance 31/31 with gated live E2E not exercised; full 2914 passed, 0 failed, 1 skipped; typecheck passed; native fmt/clippy/test passed (179 library tests plus integration suites); OpenSpec strict validation passed; git diff --check passed. -->
- [x] 4.3 Record commits, validation evidence, integration/push status, and the no-package/no-live-account boundary.
  <!-- Edge commit 8bdb3af was rebased onto c4d8929, pushed as the fast-forward master head, and fast-forwarded into the canonical checkout. This control change records the contract and evidence. No DEV/OL deployment, installer packaging, installed-client update, or live-account action was performed. -->
