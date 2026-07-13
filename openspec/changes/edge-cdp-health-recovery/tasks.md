## 1. Protocol and task-acquisition truthfulness

- [x] 1.1 Add `cdp_unhealthy` as an edge task release reason in edge/cloud protocol definitions and `docs/protocol.md`. <!-- edge 1b636df; cloud e668476 -->
- [x] 1.2 Gate edge task acquisition on CDP control readiness and emit the explicit negative acknowledgement without creating ownership. <!-- edge 1b636df -->
- [x] 1.3 Make cloud reject a pending lease immediately on `cdp_unhealthy` and map it to a distinct publish requeue/Feishu notice. <!-- cloud e668476 -->
- [x] 1.4 Add edge/cloud protocol and lease/dispatcher regression coverage for the negative acknowledgement path. <!-- edge 1b636df; cloud e668476 -->

## 2. Edge CDP control-health recovery

- [x] 2.1 Add CDP input latency classification, timeout diagnostics, and a bounded connected-stall recovery trigger without replaying commands. <!-- edge 1b636df -->
- [x] 2.2 Pause browse command admission during recovery or unavailable control, re-report current state after safe soft recovery, and preserve timeout uncertainty for external browsers. <!-- edge 1b636df -->
- [x] 2.3 Route exhausted owned-browser control-stall recovery through the existing unrecoverable/recycle lifecycle; keep external/reused browser handling non-destructive. <!-- edge 1b636df -->
- [x] 2.4 Add focused CDP client, browse-session, and task-coordinator tests for timeout, slow-input recovery, pause, rejection, and ownership boundaries. <!-- edge 1b636df -->

## 3. Verification and delivery

- [x] 3.1 Run edge/cloud acceptance suites, affected unit suites, full tests, and type checks; record exact outcomes. <!-- edge: typecheck pass; test:acceptance 18 pass; focused 102 then post-change BrowseSession 83 pass; full runner 1,132 pass/0 fail (its temporary-worktree cleanup wrapper exited nonzero only because zsh reserves the variable name `status`, then link was removed). cloud: typecheck pass; test:acceptance 49 pass; focused 23 pass; npm test 1,916 pass/0 fail. -->
- [x] 3.2 Run strict OpenSpec validation, update this task log with commits and dev deployment evidence, and commit/push the isolated worktrees. <!-- strict validation passed; edge 1b636df and cloud e668476 committed and pushed from isolated worktrees; this control change is committed and pushed with this task record. -->
- [x] 3.3 Fast-forward merge verified Edge and Cloud changes to `master`, deploy cloud to `dev`, and verify service, panel, database, Feishu, and unrelated service health. <!-- edge master 1b636df; cloud master e668476; dev backup 20260713-151401; source-only rsync (4 changed runtime files); restarted 2026-07-13 15:14:44 CST; active, 8787, panel 8090, PostgreSQL select 1, Feishu WSClient onReady, and all isales services verified. -->
- [x] 3.4 Record the required desktop-client release handoff; do not build an installer unless explicitly authorized. <!-- No installer was built, per default policy. Operators need an explicitly authorized desktop release/update containing edge master 1b636df before their local client receives the control-health recovery. -->
