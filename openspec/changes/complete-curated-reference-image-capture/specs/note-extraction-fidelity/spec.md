## ADDED Requirements

### Requirement: 翻图后回传完整图片快照

边端在执行 `note.browse_images` 并真实浏览到轮播图片后，SHALL 重新从当前笔记详情作用域抽取图片引用，并把更新后的有界图片快照回传给云端。该回传 MUST 复用既有图片抽取规则：按页面顺序、去重、过滤头像/emoji/重复 swiper clone/`blob:`/`data:`/空 URL，数量上限 MUST NOT 超过 9。

翻图后的图片快照回传 MUST NOT 被计为新的浏览动作；云端可用显式刷新标记或等价机制区分首次 `note.detail` 与图片刷新详情。若 `note.browse_images` 失败、未找到轮播或刷新抽取失败，边端 MUST 诚实保留原 action 回执并不得编造图片 URL。

#### Scenario: 翻图后补传新加载图片
- **WHEN** 笔记打开时只观测到部分图片，随后 `note.browse_images` 成功翻到更多轮播图片
- **THEN** 边端重新抽取详情图片，并回传包含新观测图片的有界快照

#### Scenario: 图片刷新不增加浏览计数
- **WHEN** 边端为翻图后的图片快照再次发送详情数据
- **THEN** 云端不得把该刷新当作新的 `view` 互动计数

#### Scenario: 翻图失败不伪造图片
- **WHEN** `note.browse_images` 返回 `no_target` 或执行失败
- **THEN** 边端不生成假图片快照，云端不因失败刷新覆盖已有非空图片

