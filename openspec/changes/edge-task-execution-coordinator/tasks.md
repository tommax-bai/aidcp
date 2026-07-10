## 1. Protocol and contracts

- [x] 1.1 Add task acquire/acquired/release/released payloads and taskId command ownership fields to cloud and edge protocol v2 definitions
- [x] 1.2 Update protocol contract tests, command routing, and `docs/protocol.md` message tables/examples/counts

## 2. Edge execution coordination

- [x] 2.1 Implement `EdgeTaskCoordinator` priority/FIFO queue, idempotent acquire/release, lease deadlines, and ownership validation
- [x] 2.2 Add `BrowseSession` quiesce/resume support that waits for the active command boundary and cancels queued ordinary browse commands
- [x] 2.3 Route edge task control messages and enforce current task ownership for browse/comment and publish command paths
- [x] 2.4 Add edge unit/integration tests for in-flight browse quiescence, stale queue cancellation, task FIFO/priority, lease mismatch, expiry, and single resume

## 3. Cloud lease orchestration

- [x] 3.1 Implement `EdgeTaskLeaseClient` acquired/released correlation, push/offline/timeout handling, and `withLease` finally release
- [x] 3.2 Wire task acknowledgements through the message handler and invalidate edge leases on disconnect/reconnect
- [x] 3.3 Add cloud unit tests for no business command before acquired, release idempotence, offline/timeout honesty, priority metadata, and disconnect cleanup

## 4. Publish integration

- [x] 4.1 Acquire one publish task lease after account FIFO selection and hold it across the complete command sequence
- [x] 4.2 Carry taskId through `CommandSequencer` and every `publish.command`; return honest mismatch failures from edge
- [x] 4.3 Add regression tests proving an in-flight `navigation.back` finishes before `navigate_entry` and two publishes never interleave atoms

## 5. Comment integration

- [x] 5.1 Refactor xhs comment runner into prepare snapshot, cloud-only compose/approval, and commit phases
- [x] 5.2 Acquire/release separate comment prepare/commit leases and make all edge steps carry taskId
- [x] 5.3 Reopen and revalidate stable noteId plus dedup state in commit; do not acquire commit after rejection/timeout
- [x] 5.4 Add manual, scheduled, targeted, current-note and post/comment contention tests, including browser availability during human approval

## 6. Remaining task classes and recovery

- [x] 6.1 Route notification excursions and group joins through task leases with manual/automatic priority derived from trigger source
- [x] 6.2 Treat navigation-writing captcha/identity recovery as system-recovery tasks while preserving read-only watcher behavior
- [x] 6.3 Replace unconditional per-feature browse resume with coordinator-owned queue-drain resume and add overlap regressions

## 7. Validation and delivery

- [x] 7.1 Run edge acceptance tests, full tests, and typecheck <!-- edge after rebase onto 0.3.4: acceptance 16/16, full 859/859, typecheck passed; commits 359563a, c8ec185 -->
- [x] 7.2 Run cloud acceptance tests, full tests, and typecheck <!-- cloud: acceptance 47/47, final full 1715/1715, typecheck passed; commits 0e4eec6, 97c0310 -->
- [x] 7.3 Run strict OpenSpec validation and record implementation/validation commit SHAs in this checklist <!-- openspec validate edge-task-execution-coordinator --strict passed; aidcp f654994; console f16237c; console tests 87 passed, 1 skipped, production build passed -->
- [ ] 7.4 Rebase/fast-forward integrate, push default branches, deploy cloud to dev, publish the edge desktop package/download path, and verify dev runtime health
- [ ] 7.5 Record dev verification and deployment notes, archive the OpenSpec change, and remove obsolete worktrees/branches
