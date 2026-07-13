## 1. Protocol and edge coordination

- [x] 1.1 Add the optional acquire wait duration to both protocol definitions and `docs/protocol.md`. <!-- aidcp-edge c29f8ac; aidcp-cloud b2de46b; control docs committed with this change. -->
- [x] 1.2 Expire queued acquire requests locally on edge and clear their timers through acquire, release, reset, and grant paths. <!-- aidcp-edge c29f8ac -->
- [x] 1.3 Add edge coordinator tests for bounded queued acquire behavior. <!-- aidcp-edge c29f8ac -->

## 2. Cloud recovery and scheduled-comment truthfulness

- [x] 2.1 Send an idempotent release when cloud acquire times out and retry it after a late acquired reply. <!-- aidcp-cloud b2de46b -->
- [x] 2.2 Report edge lease acquisition failure as scheduled-comment `not_started`, without claiming a selected note or post attempt. <!-- aidcp-cloud b2de46b -->
- [x] 2.3 Add cloud tests for timeout cancellation, late acquired cleanup, and the `not_started` receipt. <!-- aidcp-cloud b2de46b -->

## 3. Verification and delivery

- [x] 3.1 Run protocol/acceptance and focused unit tests, then the required type checks. <!-- edge: acceptance + typecheck + 1096 full tests; cloud: acceptance + typecheck + 86 affected-suite tests. -->
- [x] 3.2 Update this task log with implementation commits and deployment evidence. <!-- edge c29f8ac and cloud b2de46b; dev backup cloud.bak.20260713-120611.tar.gz; service/8787/8090/PG/Feishu/isales health checks passed. -->
- [x] 3.3 Validate the OpenSpec change strictly, commit, push, merge to default branches, and deploy cloud to dev. <!-- strict validation passed; edge/cloud fast-forwarded to origin/master; cloud b2de46b deployed to dev. -->
