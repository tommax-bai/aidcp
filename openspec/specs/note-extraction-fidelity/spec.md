# note-extraction-fidelity Specification

## Purpose
TBD - created by archiving change fix-browse-loop-resilience. Update Purpose after archive.
## Requirements
### Requirement: 文本笔记正文须跨布局变体被抽到

详情页正文抽取 SHALL 在正文位于 `#detail-desc` 或 `note-scroller`/`note-content` 等布局变体容器时均抽到非空正文；MUST NOT 因选择器过窄而对真·文本笔记产生空正文（假阴性），同时 MUST NOT 回退到会把「标题+发布时间(刚刚)」拼进正文的裸 `.note-content`/`[class*=content]` 选择器（假阳性）。

#### Scenario: 正文位于 #detail-desc
- **WHEN** 笔记正文渲染在 `#detail-desc` 容器内
- **THEN** 抽取得到非空正文，且不含标题/发布时间拼接

#### Scenario: 正文位于布局变体容器
- **WHEN** 笔记正文位于 `note-scroller` / `note-content` 内的文本节点而页面无字面 `#detail-desc`
- **THEN** 抽取仍得到非空正文（命中共享选择器列表中的变体候选）

#### Scenario: 真·纯图文/视频笔记如实记录
- **WHEN** 笔记确无正文容器（纯图文/视频）
- **THEN** 正文上报为空，且日志 MUST 区分「真·纯图文/视频」与「布局变体未命中（疑似需补选择器）」，MUST NOT 把后者谎报为前者

### Requirement: 渲染门与抽取器须共用同一份正文选择器

`waitForNoteBody`（渲染门）与 `extractNoteContent`（抽取器）MUST 使用同一份共享的正文容器选择器列表，避免门通过但抽取器未命中（或反之）的漂移；门的超时窗口 SHALL 足以覆盖长文 + 懒加载（~5-6s 量级）。

#### Scenario: 门与抽取器口径一致
- **WHEN** 渲染门在某容器上判定正文已就绪
- **THEN** 抽取器从同一组容器选择器中抽取，二者不因选择器集合不同而结果矛盾

### Requirement: 点赞数在 feed 卡与详情页须口径一致

点赞数抽取 SHALL 使用非贪婪选择器，使同一笔记的点赞数在 feed 卡与详情页口径一致（数量级一致）；MUST NOT 使用会抓到无关计数（收藏/评论/分享）的泛化 `[class*=count]` 末位兜底。

#### Scenario: feed 卡与详情点赞数一致
- **WHEN** 同一笔记分别在 feed 卡与详情页抽取点赞数
- **THEN** 两处点赞数口径一致（不出现 feed `👍11` vs detail `👍1` 这类因选择器不同导致的矛盾）

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

