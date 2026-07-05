# note-extraction-fidelity Specification (delta)

## ADDED Requirements

### Requirement: 笔记详情上报有界图片引用

边端在打开小红书笔记详情并上报 `note.detail` 时 SHALL 尝试在详情页作用域内抽取图文轮播图片引用，并以可选 `images` 数组随详情一起上报。图片引用 MUST 保持页面视觉顺序、去重、限量，并且只包含可远程引用的图片 URL。抽取不到图片时 MUST 诚实上报空数组或省略字段，MUST NOT 因无图阻断标题/正文/计数详情上报，MUST NOT 编造图片 URL。

边端 MUST 优先抽取真实轮播图片，避免把头像、emoji、重复 swiper clone、视频封面控制层或页面其它图片混入。URL 解析 SHOULD 优先 `currentSrc` / `src`，再退 `srcset` / `data-src`；`blob:`、`data:`、空串和重复 URL MUST 被过滤。图片数量 MUST 有上限，且该上限 MUST NOT 超过平台图文硬上限 9。

由于 `note.detail` 是 edge -> cloud 协议，新增图片字段时 MUST 同步两份 `src/comm/protocol.ts`、云端事件类型/映射和 `docs/protocol.md`，并保持旧端/旧云对缺失字段向后兼容。

#### Scenario: 多图笔记按顺序上报图片引用

- **WHEN** 详情页轮播中有多张真实图片
- **THEN** `note.detail.images` 包含按页面顺序排列的图片引用，且每项至少包含 `index` 与 `url`

#### Scenario: 重复 swiper clone 被去重

- **WHEN** 详情页 DOM 中含 `.swiper-slide-duplicate` 或相同图片 URL 的重复节点
- **THEN** 上报数组中同一 URL 只出现一次，顺序以真实图片第一次出现为准

#### Scenario: 无图或抽取失败不阻断详情

- **WHEN** 详情页没有可抽取图片，或图片选择器失效
- **THEN** 边端仍上报标题/正文/计数等 `note.detail`，图片字段为空或省略，MUST NOT 把无图伪造成一张占位图

#### Scenario: 协议双份同步

- **WHEN** `NoteDetailPayload.images` 字段加入 edge 协议
- **THEN** cloud 协议、事件类型/映射和协议文档同步更新，类型检查与协议漂移守护通过

#### Scenario: 红线反例 - 把头像或假 URL 当原笔记图片

- **WHEN** 有实现从整个 document 粗扫 `img`，导致作者头像/导航图/emoji 混入，或在抽不到图片时拼接假 URL
- **THEN** MUST 视为违规，不予合入；图片抽取 MUST 限定详情作用域、诚实置空
