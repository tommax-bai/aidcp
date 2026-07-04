# panel-curated-content Delta

## ADDED Requirements

### Requirement: 精选面板 SHALL 按图文 / 视频 / 评论展示与筛选

面板精选内容列表与 facets SHALL 使用图文、视频、评论三类展示 `content_type`，并支持按 `image_text`、`video`、`comment` 精确筛选。为兼容过渡期调用，旧查询参数 `contentType=note` MAY 被解释为源帖集合（`image_text|video`），但响应行 MUST 返回真实的新类型。facets SHOULD 提供图文数、视频数、评论数；若保留旧 `noteCount` 字段，则其值 MUST 等于图文数与视频数之和。

#### Scenario: 按视频筛选

- **WHEN** 管理员在精选面板选择视频筛选
- **THEN** 列表只返回该账号 `content_type=video` 的行，total 与 facets 不跨账号

#### Scenario: 旧 note 查询兼容

- **WHEN** 过渡期客户端请求 `contentType=note`
- **THEN** 服务端返回图文与视频两类源帖行，且每行的 `contentType` 仍为 `image_text` 或 `video`

#### Scenario: 面板标签反映真实类型

- **WHEN** 列表中同时存在图文、视频和评论
- **THEN** 前端分别以「图文」「视频」「评论」呈现，MUST NOT 再把源帖统称为「笔记」
