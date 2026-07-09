# curated-note-actions Delta

## MODIFIED Requirements

### Requirement: 参照洗稿创作——参照注入完整发布链、人审闸不短路

参照创作 SHALL 将该行的标题、正文（截断至有界长度）与话题装配为参照笔记注入发布输入，并走完整既有发布链路（保真改写→配图→人审→下发），MUST NOT 绕过或简化任何一环（含 AC-PUB 三重人审闸）。参照洗稿 SHALL 仅执行**保真改写**：系统 MUST 保留原稿的核心事实、论点、结构与叙事边界，MUST NOT 主动新增原稿没有的实测数据、个人经历、身份背书、时间线、结论或案例；MUST NOT 把参照稿改成解读二创或借题重写。正文为空的壳行 MUST 以 `empty_body` 拒绝，MUST NOT 以空参照触发。

并发语义（见 `publish-generation-concurrency`）：同账号对**不同**参照笔记的触发 SHALL 并行放行（受容量帽约束）；同账号对**同一**参照笔记的并发触发 SHALL 以 `duplicate_source` 同步拒绝；账号在途帽满 SHALL 以 `publish_capacity` 拒绝；全局并发帽满 SHALL 以 `publish_busy`（语义=并发已满）拒绝。全部拒绝 MUST 诚实返回未触发，MUST NOT 排队假装成功。

参照创作触发时还 SHALL 把该精选行的展示/审计血缘随 `referenceNote` 传入发布链，至少包括精选行 id、行归属账号、sourceId、sourceUrl、标题、正文、作者、话题和触发时刻。该血缘用于发布记录持久化与内容页「来稿件」展示；MUST 以触发时快照为准，MUST NOT 在历史展示时要求当前精选行仍存在。

#### Scenario: 参照创作生成草稿并送人审

- **WHEN** 对一条正文非空的精选笔记触发参照创作且容量帽未满
- **THEN** 以该笔记为参照生成保真改写草稿、落待审状态并发送人审卡；审核通过前绝不发布

#### Scenario: 同账号连续洗两篇不同笔记并行推进

- **WHEN** 运营对同一账号先后触发两篇不同精选笔记的参照创作
- **THEN** 两轮并行生成、各自落待审草稿各发人审卡，第二次触发 MUST NOT 因第一轮在跑而被拒

#### Scenario: 参照保真而非借题重写

- **WHEN** 装配含参照笔记的保真改写链路
- **THEN** 系统先抽取原稿事实/论点/结构，再按该边界改写；成稿不得新增原稿没有的实测、个人经历、身份或结论

#### Scenario: 空正文壳行诚实拒绝

- **WHEN** 对 admit_reason 为 bot_collect(content_missing) 等正文为空的行触发参照创作
- **THEN** 触发即以 empty_body 拒绝，不进入发布链

#### Scenario: 并发帽满诚实返回未触发

- **WHEN** 账号在途帽或全局并发帽已满时触发参照创作
- **THEN** 返回未触发与对应原因码（`publish_capacity` / `publish_busy`），MUST NOT 静默排队或谎报已触发

#### Scenario: 触发时携带来稿展示血缘

- **WHEN** 管理员从精选页触发参照洗稿
- **THEN** 发布链输入携带该精选行触发时的展示血缘，后续发布记录可据此展示来稿件，即使当前精选行之后被删除

### Requirement: 触发态回执与终态结果分离——诚实三态

动作端点的响应为触发态回执（triggered 与机器原因码），MUST NOT 把域内拒绝或未触发表达为成功。终态结果沿既有渠道呈现：参照创作=内容页待审草稿+飞书人审卡；定向评论=飞书人审卡+既有三态终态结果卡（成功绿/未产出黄/失败红），终态卡 SHALL 可辨识为定向来源。同账号多轮洗稿并行时，参照创作的异步结果通知 SHALL 携带参照稿标识（标题或 sourceId），使运营能分辨是哪一篇的结果，MUST NOT 只报账号名致多轮结果不可区分。console SHALL 按 triggered 真值分支提示（成功=引导去飞书审核；拒绝=中文原因；异常=错误提示），MUST NOT 对拒绝染绿。

#### Scenario: 触发成功提示走飞书人审

- **WHEN** 动作端点返回 triggered=true
- **THEN** console 提示任务已触发并引导到飞书完成人审；不宣称动作已完成

#### Scenario: 域内拒绝以原因码透传

- **WHEN** 动作因 empty_body/note_only/already_commented/group_code_missing/publish_busy/publish_capacity/duplicate_source/边端离线等被拒
- **THEN** 端点返回 triggered=false 与稳定机器原因码，console 映射为中文提示且不染绿；console 对未知码保持原样兜底

#### Scenario: 并行多轮结果可区分

- **WHEN** 同账号两轮洗稿并行、其中一轮以 skipped 或 failed 收敛
- **THEN** 异步结果卡标明该轮的参照稿标识，运营可对应到具体是哪篇笔记的洗稿结果

#### Scenario: 终态不由触发回执谎报

- **WHEN** 任务触发成功但终态失败（如 note_not_found、发布失败）
- **THEN** 终态经既有渠道如实呈现（黄/红），触发回执不被追溯性当作成功依据
