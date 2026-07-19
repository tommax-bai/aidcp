## 1. Cloud read model

- [x] 1.1 Extend delegated-task list filters through service and PostgreSQL/in-memory stores so action-family and status filtering happens before limit.
  <!-- aidcp-cloud 7f2cdd6: DelegatedTaskListFilter is shared by service and stores; both stores filter action family/status before sorting and limiting. -->
- [x] 1.2 Add validated `actionFamily` and `statuses` query parameters to `GET /api/delegated-tasks` while preserving existing requests.
  <!-- aidcp-cloud 7f2cdd6: panel API validates both enums; legacy unfiltered requests retain their original query shape. -->
- [x] 1.3 Cover filtered list and compatibility behavior with focused Cloud tests and typecheck.
  <!-- Validation: focused 27/27 passed; Cloud typecheck passed; acceptance suite passed (57 pass, 1 gated deployment E2E skip); full test command exited 0. -->

## 2. Console queue column

- [x] 2.1 Add the filtered delegated-task query and mirror the task evidence fields needed by the queue view.
  <!-- aidcp-console b418d70: 10-second filtered query plus additive backward-compatible task evidence fields. -->
- [x] 2.2 Render the responsive queued-task column with honest loading, error, empty and queued/planning/deferred states without duplicating lifecycle items.
  <!-- aidcp-console b418d70: desktop summary uses two columns, <=1024px stacks to one column; old Cloud responses are filtered fail-closed in the client. -->
- [x] 2.3 Add focused ContentPage tests for visible queued tasks, excluded states and query failure isolation; run Console typecheck.
  <!-- Validation: focused ContentPage 28/28 passed; full Console 183 passed and 1 skipped; typecheck and production build passed. -->

## 3. Integration and closeout

- [x] 3.1 Run strict OpenSpec validation and record repository commits plus validation evidence.
  <!-- `openspec validate show-queued-publish-tasks --strict` passed. Browser QA covered desktop and 760px stacked layout with zero console errors. -->
- [x] 3.2 Integrate Cloud and Console changes through their isolated worktrees, deploy the runtime change to `dev`, verify health, and update the change record with outcomes or deviations.
  <!-- Landed to origin/master: aidcp-cloud 7f2cdd6; aidcp-console b418d70. Deployed dev on 2026-07-19 with backups cloud.bak.20260719-105512.tar.gz, cloud/.env.bak.20260719-105512, and console.bak.20260719-105512.tar.gz. Health: service active, NRestarts=0, listeners 8787/8090/8088, panel health ok, Console HTTP 200, PostgreSQL select 1, Feishu WS ready. Deviation: local Windows had no rsync binary, so committed Cloud files and the clean Console build were uploaded as checksummed archives; remote rsync checksum dry-run showed only the intended files, and staged/deployed SHA-256 values matched before restart. -->
