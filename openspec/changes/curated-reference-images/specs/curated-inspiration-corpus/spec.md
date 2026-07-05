# curated-inspiration-corpus Specification (delta)

## ADDED Requirements

### Requirement: 精选笔记保存有界图片参考快照

精选语料中的笔记行 SHALL 支持保存原笔记图片参考快照，用于人工指定参照洗稿时的视觉参考。图片快照 SHALL 仅属于 `content_type='note'` 行，并与正文、作者、来源链接、赞藏计数一样按账号隔离、按精选保留上限治理。评论行 MUST NOT 被强行补图片。

图片快照 MUST 是有界数组，保留原始页面顺序，并记录每张图的来源 URL、可选 OSS 稳定 URL、宽高/alt 等可得元数据、捕获状态与捕获时间。图片来源不可用、下载失败、OSS 未配置或不支持时 MUST 诚实记录状态并保留可见诊断，MUST NOT 伪造 `ossUrl` 或把不可访问 URL 标为稳定可用。

精选准入路径与自有收藏自动纳入路径都 SHALL 合并图片快照：模型准入的笔记使用 `note.detail.images`；机器人自有收藏若需补建精选行，使用同访问最近观测到的图片快照。后续观测更新 MAY 刷新图片快照；机器人动作标记 MUST NOT 擦掉已有图片。

#### Scenario: 过准入笔记落库时保存图片快照

- **WHEN** 一篇带图片引用的笔记通过精选准入
- **THEN** `curated_content.reference_images` 保存有界、有序、规范化后的图片快照

#### Scenario: 自有收藏补建行携带图片

- **WHEN** 机器人收藏一篇此前未入精选但本访问已观测到图片的笔记
- **THEN** 自动纳入的精选行包含该次观测到的图片快照

#### Scenario: OSS 转存成功写稳定 URL

- **WHEN** 云端能下载某张原笔记图片并成功转存 OSS
- **THEN** 对应图片项记录 `captureStatus='stored'` 与 `ossUrl`，后续后台和参照生成优先使用 `ossUrl`

#### Scenario: OSS 或下载失败诚实降级

- **WHEN** 图片下载失败、防盗链、OSS 未配置或上传失败
- **THEN** 对应图片项记录 `fetch_failed` 或 `url_only` 等状态，MUST NOT 写入伪造稳定 URL，精选正文入库不因此失败

#### Scenario: 评论行不支持图片参考

- **WHEN** `content_type='comment'` 的精选行被读取
- **THEN** 图片快照为空，后台不开放洗稿参照动作

#### Scenario: 红线反例 - 直接把原图作为发布素材

- **WHEN** 有实现把 `reference_images` 中的原图 URL 直接下发给发布上传指令作为最终帖子图片
- **THEN** MUST 视为违规，不予合入；原笔记图片只能作为生成新图的参考，不得直接发布
