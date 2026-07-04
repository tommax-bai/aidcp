# console-panel-api Delta

## ADDED Requirements

### Requirement: 已发布投影展示参照洗稿来稿件

只读接口 `GET /api/content/published` SHALL 在既有发布记录投影上加性返回 `sourceReference` 字段。该字段在参照洗稿记录上为触发时来稿快照，在普通发布记录上为 `null`。接口 MUST 复用既有端点、既有账号过滤和既有排序，MUST NOT 为展示来源而 join 当前 `curated_content` 或退化为全表扫描。

管理后台「内容」tab SHALL 在发布内容列表或标题副信息中标识参照洗稿来源，并允许运营点击查看来稿件详情。发布详情浮层中 SHALL 提供同一入口。来稿件详情 SHALL 展示来源标题、正文、作者、话题、sourceId、快照时间与来源链接；来源链接缺失时 SHALL 诚实显示「无链接」或禁用按钮，MUST NOT 渲染死链。

#### Scenario: 参照洗稿行展示可点击来源

- **WHEN** `GET /api/content/published` 返回某行 `sourceReference != null`
- **THEN** 内容 tab 在该发布记录上展示「洗稿来源」入口，点击后打开来稿件详情，而非只打开发布稿详情

#### Scenario: 普通发布不展示来源入口

- **WHEN** 某发布记录 `sourceReference == null`
- **THEN** 内容 tab 不展示洗稿来源入口，也不暗示该记录由来稿触发

#### Scenario: 来稿件详情使用快照且链接诚实

- **WHEN** 运营打开参照洗稿记录的来稿件详情
- **THEN** 页面展示 `sourceReference` 快照中的标题、正文、作者、话题、sourceId 和快照时间；若 `sourceUrl` 存在则新标签打开，若为空则显示无链接且不渲染死链

#### Scenario: 账号过滤保持索引友好

- **WHEN** 请求 `GET /api/content/published?accountId=A`
- **THEN** 接口仍按 `publish_log.account_id` 过滤并返回该账号记录及其 `sourceReference`，MUST NOT 为来源展示跨账号读取当前精选池
