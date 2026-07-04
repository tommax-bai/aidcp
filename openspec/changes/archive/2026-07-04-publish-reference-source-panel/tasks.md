# Tasks: 内容页展示参照洗稿来稿件

## 1. OpenSpec

- [x] 1.1 新增 `publish-reference-source-panel` proposal/design/tasks/spec deltas。
- [x] 1.2 运行 `openspec validate publish-reference-source-panel --strict`。

## 2. aidcp-cloud

- [x] 2.1 `publish_log` 加性新增 `source_reference JSONB`，初始化 SQL 与迁移文件同步。 <!-- aidcp-cloud b32acab publish_log schema + migrations/0032_publish_source_reference.sql -->
- [x] 2.2 扩展 `ReferenceNote`/触发接线，精选行参照创作携带 `curatedContentId/accountId/sourceUrl/capturedAt`，普通发布保持空。 <!-- aidcp-cloud b32acab publish-scheduler freezes reference source snapshot; normal trigger keeps sourceReference null -->
- [x] 2.3 `PublishExecutor` 从 trigger 读取参照快照，并在 pending/failed 发布记录 insert 时写入 `source_reference`。 <!-- aidcp-cloud b32acab publish-executor writes pending/failed sourceReference from trigger fallback -->
- [x] 2.4 `PanelPublish` 与 `publishedHistory` 投影新增 `sourceReference`，按账号过滤仍走 `publish_log.account_id`，不 join 当前精选池。 <!-- aidcp-cloud b32acab panel-store parses source_reference from publish_log projection only -->
- [x] 2.5 覆盖 cloud 测试：参照洗稿记录带快照、普通发布为 null、精选行删除不影响历史投影、缺来源链接不造假。 <!-- aidcp-cloud b32acab targeted tests 46/46 + acceptance 44/44 + typecheck clean after rebase -->

## 3. aidcp-console

- [x] 3.1 扩展 `PanelPublish` DTO 镜像，新增 `sourceReference` 类型。 <!-- aidcp-console eca2dff src/types/api.ts -->
- [x] 3.2 内容 tab 发布列表展示「洗稿来源」入口；点击入口打开来稿件弹窗且不触发行详情点击。 <!-- aidcp-console eca2dff ContentPage source column opens SourceReferenceModal with stopPropagation -->
- [x] 3.3 发布详情浮层展示同一来源入口；待审/已发布/失败/已否决均可查看。 <!-- aidcp-console eca2dff publish detail modal shows same source entry when sourceReference exists -->
- [x] 3.4 来稿件弹窗展示标题、作者、正文、话题、sourceId、快照时间和来源链接；缺链接不渲染死链。 <!-- aidcp-console eca2dff modal renders disabled no-link state instead of fake URL -->
- [x] 3.5 覆盖 console 测试：有来源展示并可点开、普通发布不展示、缺链接禁用、点击来源不打开发布详情。 <!-- aidcp-console eca2dff ContentPage tests; full vitest 39 passed / 1 skipped -->

## 4. 验证与收口

- [x] 4.1 cloud 相关测试与 typecheck。 <!-- aidcp-cloud b32acab: npx tsx targeted 46/46, npm run test:acceptance 44/44, npm run typecheck clean -->
- [x] 4.2 console 相关测试与 build/typecheck。 <!-- aidcp-console eca2dff: npm test 39 passed / 1 skipped, npm run typecheck clean, npm run build produced assets/index-CP7UVuSP.js -->
- [x] 4.3 更新 tasks.md 记录提交 SHA、验证结果和部署说明。 <!-- deployed 2026-07-04 22:17 CST: backups /opt/aidcp/cloud.bak.20260704-221643.tar.gz + /opt/aidcp/cloud/.env.bak.20260704-221643 + /opt/aidcp/console.bak.20260704-221643.tar.gz; cloud b32acab tar deployed + aidcp-cloud.service restart active; health 8787/8090/8088 listening, Feishu WS onReady, PG source_reference=jsonb, no recent systemd errors; console eca2dff dist deployed with assets/index-CP7UVuSP.js -->
