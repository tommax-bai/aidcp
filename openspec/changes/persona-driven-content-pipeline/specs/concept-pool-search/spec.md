## MODIFIED Requirements

### Requirement: 概念从浏览内容中抽取并持久化

系统 SHALL 在浏览到笔记详情（`note.detail.arrived`，含真实 title/content）时，用 LLM 抽取其中**可作搜索词的领域/话题概念关键词**（话题中立、不限技术领域），并以 `status='candidate'` 写入 PG `concepts` 表（`ConceptStore.addCandidate`），来源记为该笔记标题。抽取 SHALL 跨会话累积（启动时 `loadPool()` 载入）。抽取 prompt MUST NOT 将可抽概念限定为技术领域（如仅工具/方法名词），亦 MUST NOT 因笔记非技术内容而一律返回空。

系统 MUST NOT 在抽不到关键词时编造或填充占位词——抽取结果为空则不写入任何记录（红线：不静默假成功）。

#### Scenario: 从笔记详情抽到新概念

- **WHEN** 收到 `note.detail.arrived`，其 content 含一个 `concepts` 表中尚不存在的、可作搜索词的领域/话题概念
- **THEN** 该关键词以 `status='candidate'`、`source_note=<笔记标题>` 写入 `concepts` 表，并可被后续会话 `loadPool()` 读到

#### Scenario: 非技术领域笔记同样可抽概念

- **WHEN** 收到 `note.detail.arrived`，其内容属于非技术领域（如美食、旅行、穿搭）但含可作搜索词的领域/话题概念
- **THEN** 系统抽取该领域概念并写库，不因「非技术」而一律返回空

#### Scenario: 抽不到概念时不写库

- **WHEN** 收到 `note.detail.arrived`，但 LLM 未能从中抽出任何可作搜索词的领域/话题概念（如纯情绪/无信息内容）
- **THEN** 不向 `concepts` 表写入任何行，也不下发任何搜索，不产生占位/编造关键词

#### Scenario: 重复概念不重复入库

- **WHEN** 抽到的关键词在 `concepts` 表中已存在（任意 status）
- **THEN** 通过 `ON CONFLICT DO NOTHING` 保留原记录，不覆盖其既有 status
