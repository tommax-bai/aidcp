# curated-inspiration-corpus Delta

## ADDED Requirements

### Requirement: 精选源帖类型 SHALL 拆分为图文与视频

精选层 SHALL 使用 `content_type=image_text|video|comment` 表达内容类型，其中 `image_text` 与 `video` 都属于源帖，`comment` 属于评论素材。历史 `content_type=note` 行 SHALL 在迁移时全部改写为 `image_text`，并同步更新任何包含类型字段的去重键，避免迁移后同一来源重复入库。系统 MUST NOT 在迁移历史行时猜测视频类型。

#### Scenario: 存量 note 迁为 image_text

- **WHEN** 系统升级时 `curated_content` 中存在 `content_type=note` 的历史行
- **THEN** 这些行被迁移为 `image_text`，且对应去重键同步改写为图文类型

#### Scenario: 新视频详情入库为 video

- **WHEN** 边端上报的笔记详情标识其媒体类型为视频
- **THEN** 该精选源帖若准入或由自有收藏纳入，持久化为 `content_type=video`

#### Scenario: 老边端未上报媒体类型

- **WHEN** 云端收到缺少媒体类型的历史协议 `note.detail`
- **THEN** 云端按 `image_text` 兼容处理，MUST NOT 因缺字段拒绝详情或编造为视频

### Requirement: 源帖召回 SHALL 覆盖图文与视频

需要消费精选源帖的流程（发帖创作素材、评论搜索词生成、定向评论目标来源）SHALL 把 `image_text` 与 `video` 视为同一源帖集合召回；仅当流程明确需要可洗稿的图文正文时，才限制为 `image_text`。评论素材 `comment` MUST NOT 混入源帖召回。

#### Scenario: 创作或评论搜索取源帖

- **WHEN** 系统为某账号选取精选源帖作为创作或评论搜索参考
- **THEN** 候选集合包含该账号的 `image_text` 与 `video` 行，不包含 `comment` 行

#### Scenario: 洗稿只取图文

- **WHEN** 管理员触发参照洗稿
- **THEN** 只有 `image_text` 行可作为参照，`video` 与 `comment` 行不可触发洗稿
