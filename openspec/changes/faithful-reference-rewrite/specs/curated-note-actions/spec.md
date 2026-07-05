# curated-note-actions Specification Delta

## MODIFIED Requirements

### Requirement: 参照洗稿创作——参照注入完整发布链、人审闸不短路

参照创作 SHALL 将该行的标题、正文（截断至有界长度）与话题装配为参照笔记注入发布输入，并走完整既有发布链路（保真改写→配图→人审→下发），MUST NOT 绕过或简化任何一环（含 AC-PUB 三重人审闸）。参照洗稿 SHALL 仅执行**保真改写**：系统 MUST 保留原稿的核心事实、论点、结构与叙事边界，MUST NOT 主动新增原稿没有的实测数据、个人经历、身份背书、时间线、结论或案例；MUST NOT 把参照稿改成解读二创或借题重写。正文为空的壳行 MUST 以 `empty_body` 拒绝，MUST NOT 以空参照触发。发布链路占用中 SHALL 诚实返回未触发（原因如 `publish_busy`/`skipped`），MUST NOT 排队假装成功。

参照创作触发时还 SHALL 把该精选行的展示/审计血缘随 `referenceNote` 传入发布链，至少包括精选行 id、行归属账号、sourceId、sourceUrl、标题、正文、作者、话题和触发时刻。该血缘用于发布记录持久化与内容页「来稿件」展示；MUST 以触发时快照为准，MUST NOT 在历史展示时要求当前精选行仍存在。

#### Scenario: 参照创作生成草稿并送人审

- **WHEN** 对一条正文非空的精选笔记触发参照创作且发布链空闲
- **THEN** 以该笔记为参照生成保真改写草稿、落待审状态并发送人审卡；审核通过前绝不发布

#### Scenario: 参照保真而非借题重写

- **WHEN** 装配含参照笔记的保真改写链路
- **THEN** 系统先抽取原稿事实/论点/结构，再按该边界改写；成稿不得新增原稿没有的实测、个人经历、身份或结论

#### Scenario: 空正文壳行诚实拒绝

- **WHEN** 对 admit_reason 为 bot_collect(content_missing) 等正文为空的行触发参照创作
- **THEN** 触发即以 empty_body 拒绝，不进入发布链

#### Scenario: 发布占用中诚实返回未触发

- **WHEN** 发布链路正在为任一账号生成草稿时触发参照创作
- **THEN** 返回未触发与占用原因，MUST NOT 静默排队或谎报已触发

#### Scenario: 触发时携带来稿展示血缘

- **WHEN** 管理员从精选页触发参照洗稿
- **THEN** 发布链输入携带该精选行触发时的展示血缘，后续发布记录可据此展示来稿件，即使当前精选行之后被删除

