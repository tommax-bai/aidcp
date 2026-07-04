# publish-pipeline Delta

## ADDED Requirements

### Requirement: 参照洗稿发布记录持久化来稿快照

当发布触发输入含有人工或阅读旁路指定的单条 `referenceNote` 时，系统 SHALL 将该参照来稿作为发布记录的来源血缘快照持久化到 `publish_log`。快照 SHALL 至少包含来源类型、精选行 id（若来自精选池）、执行账号、源笔记 `sourceId`、标题、正文、作者、话题、来源链接与触发时刻。普通发布或仅抽样素材参与的发布 SHALL 将该字段置空，MUST NOT 编造来源。

该快照 MUST 以触发时输入为准，MUST NOT 在内容页展示时再依赖当前 `curated_content` 行；精选行后续被删除、清空或更新时，历史发布记录仍 SHALL 展示当时的来稿件。来稿快照只用于审计与面板展示，MUST NOT 改变参照洗稿的 prompt 红线、人审闸、发布下发、配图收口或失败判定。

#### Scenario: 参照洗稿记录带来稿快照

- **WHEN** 运营从精选页对一条正文非空的精选图文触发参照洗稿，并生成一条 `pending_approval` 或 `failed` 发布记录
- **THEN** 该发布记录持久化一个 `sourceReference` 快照，包含该精选行触发时的标题、正文、作者、话题、sourceId、sourceUrl 与触发时刻

#### Scenario: 普通发布不编造来源

- **WHEN** 发布由普通 `/publish`、自动发布或抽样精选素材触发，且没有单条 `referenceNote`
- **THEN** 发布记录的来源快照为空，面板不展示「洗稿来源」

#### Scenario: 来源行删除后历史仍可查看

- **WHEN** 一条参照洗稿发布记录已持久化来源快照，之后对应 `curated_content` 行被删除或正文被清理
- **THEN** 内容页仍能从 `publish_log` 快照查看当时来稿件，MUST NOT 因当前精选行缺失而显示断链或伪造空态

#### Scenario: 来源快照不改变发布行为

- **WHEN** 系统为参照洗稿记录写入来源快照
- **THEN** 生成、质量评分、人审、下发与失败处理语义保持不变；该字段只读展示，不参与是否发布的判定
