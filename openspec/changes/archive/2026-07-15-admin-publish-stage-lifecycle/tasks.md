## 1. Cloud lifecycle projection

- [x] 1.1 Add typed eight-stage lifecycle projection helpers that map running snapshots, persisted publish records, and terminal outcomes without treating arbitrary field presence as completion. <!-- aidcp-cloud: src/panel/publish-stage-lifecycle.ts maps explicit stage endpoints and persisted outcomes. -->
- [x] 1.2 Expose a read-only snapshot of dispatcher in-flight record ids and compose active/recent journeys in `GET /api/content/queue` while preserving legacy fields. <!-- aidcp-cloud: PublishDispatcher read-only in-flight snapshot + additive panel API lifecycle field; legacy status/snapshot/runs retained. -->
- [x] 1.3 Add cloud regression tests for parallel generation branches, waiting approval, dispatch in flight, failed/submitted terminal records, deduplication, and idle behavior. <!-- aidcp-cloud: lifecycle pure tests plus panel HTTP and dispatcher suites; targeted 51/51 passed. -->

## 2. Console stage presentation

- [x] 2.1 Mirror the additive lifecycle DTO and make the content page prefer cloud-projected journeys with an explicit legacy fallback. <!-- aidcp-console: ContentQueue.lifecycle DTO is optional; old five-stage status remains the rollout fallback. -->
- [x] 2.2 Replace the five-stage active-draft strip with the eight-stage active/recent presentation, honest terminal banner, richer state labels, and preserved raw snapshot disclosure. <!-- aidcp-console: ContentPage renders eight cloud stages, active/recent separation, terminal alert, and raw fields. -->
- [x] 2.3 Add responsive styles and console regression tests covering active generation, waiting approval, dispatching, failed recent result, and old-cloud fallback. <!-- aidcp-console: ContentPage targeted suite 25/25 passed; desktop 4x2 and mobile horizontal layouts added. -->

## 3. Validation and delivery

- [x] 3.1 Run relevant cloud tests, full cloud tests, and cloud typecheck; record any unrelated pre-existing failures honestly. <!-- aidcp-cloud: lifecycle 6/6; panel/dispatcher/lifecycle 51/51; acceptance 54/54 with the gated real-E2E skip; full test and typecheck passed during land-change. -->
- [x] 3.2 Run console tests and build/typecheck. <!-- aidcp-console: ContentPage 25/25; full suite 148 passed + 1 skipped; typecheck and production build passed. The existing Vite >500 kB chunk warning remains non-blocking. -->
- [x] 3.3 Run `openspec validate admin-publish-stage-lifecycle --strict` and record implementation evidence in this task list. <!-- Strict validation passed before implementation closeout and again after recording delivery evidence. -->
- [x] 3.4 Commit and push cloud/console/default control-repo changes through the matching change worktrees/default branches without including unrelated files. <!-- aidcp-cloud 8d7e214 and aidcp-console 5bafcca landed and pushed to origin/master; this archived control-repo change is committed with an explicit pathspec, excluding unrelated docs/research work. -->
- [x] 3.5 Verify the `dev` target, deploy cloud and console through the documented safe sequence, and validate the panel endpoint plus rendered lifecycle states. <!-- dev target check passed; backups cloud.bak.20260715-230528.tar.gz, cloud/.env.bak.20260715-230528, console.bak.20260715-230528.tar.gz; cloud/console rsync deployed; service active with NRestarts=0; :8787/:8090/:8088 healthy; PG query ok; Feishu WS onReady; live authenticated queue returned 1 active + 5 recent with eight stages; new console assets returned 200. -->
