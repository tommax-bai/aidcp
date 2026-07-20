## 1. Isolated implementation setup

- [x] 1.1 Create matching clean `codex/xhs-approval-peak-time-shortcuts` worktrees for control, Cloud, and Edge from their latest default branches, with physical dependencies in each app worktree.

## 2. Cloud occupied-hour truth

- [x] 2.1 Add an account-scoped `PublishLogStore` query for Xiaohongshu `scheduled` targets in the Cloud-owned future 14-day window, returning only target timestamps.
- [x] 2.2 Add the customer-auth occupied-hours route with server-side environment ownership/account binding and an explicit timestamp-only DTO.
- [x] 2.3 Cover store scoping/range SQL and customer-auth ownership, response allowlist, and failure behavior with focused tests.
  <!-- aidcp-cloud focused: 55 passed; `npm run typecheck` passed. -->

## 3. Edge peak-time selection

- [x] 3.1 Add pure Shanghai-time helpers for `08:00 / 12:00 / 18:00`, current-selection cursor behavior, hour keys, occupied-slot skipping, cross-day behavior, and 14-day bounds.
- [x] 3.2 Add a named Electron main/preload IPC that reads the occupied-hours customer endpoint without accepting renderer account or network authority.
- [x] 3.3 Load Cloud occupied truth independently, merge per-environment session reservations after successful scheduled approval acceptance, and fail closed when availability is unknown.

## 4. Approval-page interaction and design

- [x] 4.1 Ensure single-draft and multi-draft Xiaohongshu details render the same scheduling controls.
- [x] 4.2 Add compact “下个热门时段” and “下个空闲时段” secondary buttons that only update the datetime input, preserve scroll position, and explain the fixed hours / explicit approval boundary.
- [x] 4.3 Add renderer regressions for single-draft visibility, no approval RPC on shortcut click, hour-level skipping (`08:15 → 12:00`), session reservation, and unavailable-truth disabling.
  <!-- aidcp-edge focused: 86 passed; `npm run typecheck` passed. -->

## 5. Validation and delivery

- [x] 5.1 Run focused Cloud and Edge tests, both repositories' full tests and typechecks, and `openspec validate xhs-approval-peak-time-shortcuts --strict`.
  <!-- Cloud: focused 55, acceptance 60, full 2677 passed / 8 gated skips, typecheck passed. Edge after latest-default rebase: focused 86, acceptance 26, full 2032 passed, typecheck passed. OpenSpec strict passed after rebase. -->
- [x] 5.2 Record repo SHAs, validation, deviations, and deployment status in this checklist; commit the control/Cloud/Edge changes.
  <!-- aidcp 9561c86: proposal/design/spec/tasks after latest-main rebase, strict validation passed. aidcp-cloud 1347891: occupied scheduled-hour store/API + focused/acceptance/full/typecheck pass. aidcp-edge 93c3017: single/multi approval shortcuts after latest-master rebase + acceptance/full/typecheck pass. Deviations: none. Deployment pending task 5.3. -->
- [ ] 5.3 Rebase/integrate through clean default checkouts, push current default branches, and deploy the runtime Cloud change to `dev` after target precheck and documented health checks; do not package an Edge installer.
