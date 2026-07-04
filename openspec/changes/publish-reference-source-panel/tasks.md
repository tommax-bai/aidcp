# Tasks: 内容页展示参照洗稿来稿件

## 1. OpenSpec

- [x] 1.1 新增 `publish-reference-source-panel` proposal/design/tasks/spec deltas。
- [x] 1.2 运行 `openspec validate publish-reference-source-panel --strict`。

## 2. aidcp-cloud

- [ ] 2.1 `publish_log` 加性新增 `source_reference JSONB`，初始化 SQL 与迁移文件同步。
- [ ] 2.2 扩展 `ReferenceNote`/触发接线，精选行参照创作携带 `curatedContentId/accountId/sourceUrl/capturedAt`，普通发布保持空。
- [ ] 2.3 `PublishExecutor` 从 trigger 读取参照快照，并在 pending/failed 发布记录 insert 时写入 `source_reference`。
- [ ] 2.4 `PanelPublish` 与 `publishedHistory` 投影新增 `sourceReference`，按账号过滤仍走 `publish_log.account_id`，不 join 当前精选池。
- [ ] 2.5 覆盖 cloud 测试：参照洗稿记录带快照、普通发布为 null、精选行删除不影响历史投影、缺来源链接不造假。

## 3. aidcp-console

- [ ] 3.1 扩展 `PanelPublish` DTO 镜像，新增 `sourceReference` 类型。
- [ ] 3.2 内容 tab 发布列表展示「洗稿来源」入口；点击入口打开来稿件弹窗且不触发行详情点击。
- [ ] 3.3 发布详情浮层展示同一来源入口；待审/已发布/失败/已否决均可查看。
- [ ] 3.4 来稿件弹窗展示标题、作者、正文、话题、sourceId、快照时间和来源链接；缺链接不渲染死链。
- [ ] 3.5 覆盖 console 测试：有来源展示并可点开、普通发布不展示、缺链接禁用、点击来源不打开发布详情。

## 4. 验证与收口

- [ ] 4.1 cloud 相关测试与 typecheck。
- [ ] 4.2 console 相关测试与 build/typecheck。
- [ ] 4.3 更新 tasks.md 记录提交 SHA、验证结果和部署说明。
