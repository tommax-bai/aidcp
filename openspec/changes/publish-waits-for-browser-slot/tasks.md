## 1. Cloud publish slot waiting

- [x] 1.1 Classify pre-sequence `browser_wake_failed` as recoverable: preserve the approval and pending draft, skip breaker accounting, and let the existing approved-draft scan retry. <!-- aidcp-cloud worktree: PublishDispatcher retains approval only for browser_wake_failed -->
- [x] 1.2 Add bounded per-record slot-wait notification deduplication and clear it when dispatch acquires the lease or the draft is no longer dispatchable. <!-- aidcp-cloud worktree: browserSlotWaitingNotified lifecycle -->
- [x] 1.3 Add the truthful `browser_slot_waiting` operator notice while preserving offline, CDP-unhealthy, acquire-timeout, and post-sequence wording. <!-- aidcp-cloud worktree: server Feishu copy -->
- [x] 1.4 Add focused Cloud regression coverage for retained authorization, scan-driven retry, notification deduplication, and unchanged negative paths. <!-- focused publish-dispatcher 24/24 -->

## 2. Edge safe-idle standby re-evaluation

- [x] 2.1 Add an optional task-coordinator safe-idle callback that fires only after queued/active tasks and publish writers have settled and browse recovery reaches a safe boundary. <!-- aidcp-edge worktree: EdgeTaskCoordinator onIdle after resumeAfterTask -->
- [x] 2.2 Forward safe idle through private lifecycle IPC and reapply only the environment's latest standby hint in Electron, without adding a protocol message or direct-close bypass. <!-- lifecycle.task_idle is private core/Electron IPC; Electron calls the existing applyBrowserStandbyHint gate -->
- [x] 2.3 Add focused Edge regression coverage for release-triggered re-evaluation, no-hint no-op, and active/new-task safety. <!-- focused coordinator/lifecycle contract tests 36/36 -->

## 3. Verification

- [x] 3.1 Run focused Cloud and Edge tests, then each owning repository's acceptance suite, full tests, and typecheck. <!-- Cloud focused 24/24, acceptance 59/59, full exit 0, typecheck pass; Edge focused 36/36, acceptance 25/25, full 1865/1865, typecheck pass -->
- [x] 3.2 Run `openspec validate publish-waits-for-browser-slot --strict` and record concise validation evidence. <!-- strict validation passed 2026-07-19 -->
- [x] 3.3 Record the 6-environment / 5-slot real-machine acceptance scenario as pending unless a safe dev account and installed Edge build are explicitly available. <!-- docs/real-machine-acceptance-backlog.md cluster 107; no real publish claimed -->

## 4. Delivery

- [ ] 4.1 Commit and push the Cloud, Edge, and control-repository changes with validation evidence in this task file.
- [ ] 4.2 Rebase and serially fast-forward the sibling changes to their default branches; do not build an Edge installer.
- [ ] 4.3 Deploy the integrated Cloud default branch to `dev` and verify service, listeners, health, PostgreSQL, Feishu, and unrelated `isales` services.
