## ADDED Requirements

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
