# curated-note-actions Delta

## MODIFIED Requirements

### Requirement: 参照洗稿创作——参照注入完整发布链、人审闸不短路

参照创作 SHALL 将该行的标题、正文（截断至有界长度）与话题装配为参照笔记注入创作输入，并走完整既有发布链路（生成→配图→人审→下发），MUST NOT 绕过或简化任何一环（含 AC-PUB 三重人审闸）。创作提示中参照笔记 SHALL 使用独立条件块，MUST NOT 混入既有抽样素材块；参照块 SHALL 要求借选题/结构/要点、以账号人设口吻重新创作，MUST 禁止逐句照抄或近似同义替换。正文为空的壳行 MUST 以 empty_body 拒绝，MUST NOT 以空参照触发。发布链路占用中 SHALL 诚实返回未触发（原因如 publish_busy/skipped），MUST NOT 排队假装成功。

参照创作触发时还 SHALL 把该精选行的展示/审计血缘随 `referenceNote` 传入发布链，至少包括精选行 id、行归属账号、sourceId、sourceUrl、标题、正文、作者、话题和触发时刻。该血缘用于发布记录持久化与内容页「来稿件」展示；MUST 以触发时快照为准，MUST NOT 在历史展示时要求当前精选行仍存在。

#### Scenario: 参照创作生成草稿并送人审

- **WHEN** 对一条正文非空的精选笔记触发参照创作且发布链空闲
- **THEN** 以该笔记为参照生成草稿、落待审状态并发送人审卡；审核通过前绝不发布

#### Scenario: 参照块独立于素材块且带非照抄红线

- **WHEN** 装配含参照笔记的创作提示
- **THEN** 参照笔记以独立条件块注入（含禁止逐句照抄、须有可辨识表达差异的红线），既有抽样素材块及其「仅作灵感、严禁照抄」护栏原样保留

#### Scenario: 空正文壳行诚实拒绝

- **WHEN** 对 admit_reason 为 bot_collect(content_missing) 等正文为空的行触发参照创作
- **THEN** 触发即以 empty_body 拒绝，不进入发布链

#### Scenario: 发布占用中诚实返回未触发

- **WHEN** 发布链路正在为任一账号生成草稿时触发参照创作
- **THEN** 返回未触发与占用原因，MUST NOT 静默排队或谎报已触发

#### Scenario: 触发时携带来稿展示血缘

- **WHEN** 管理员从精选页触发参照洗稿
- **THEN** 发布链输入携带该精选行触发时的展示血缘，后续发布记录可据此展示来稿件，即使当前精选行之后被删除
