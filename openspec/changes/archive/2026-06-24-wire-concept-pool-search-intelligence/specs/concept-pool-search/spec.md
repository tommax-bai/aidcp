## ADDED Requirements

### Requirement: 概念从浏览内容中抽取并持久化

系统 SHALL 在浏览到笔记详情（`note.detail.arrived`，含真实 title/content）时，用 LLM 抽取其中的技术概念关键词，并以 `status='candidate'` 写入 PG `concepts` 表（`ConceptStore.addCandidate`），来源记为该笔记标题。抽取 SHALL 跨会话累积（启动时 `loadPool()` 载入）。

系统 MUST NOT 在抽不到关键词时编造或填充占位词——抽取结果为空则不写入任何记录（红线：不静默假成功）。

#### Scenario: 从笔记详情抽到新概念

- **WHEN** 收到 `note.detail.arrived`，其 content 含一个 `concepts` 表中尚不存在的技术概念
- **THEN** 该关键词以 `status='candidate'`、`source_note=<笔记标题>` 写入 `concepts` 表，并可被后续会话 `loadPool()` 读到

#### Scenario: 抽不到概念时不写库

- **WHEN** 收到 `note.detail.arrived`，但 LLM 未能从中抽出任何技术概念关键词
- **THEN** 不向 `concepts` 表写入任何行，也不下发任何搜索，不产生占位/编造关键词

#### Scenario: 重复概念不重复入库

- **WHEN** 抽到的关键词在 `concepts` 表中已存在（任意 status）
- **THEN** 通过 `ON CONFLICT DO NOTHING` 保留原记录，不覆盖其既有 status

### Requirement: 搜索关键词来自概念池而非仅写死种子词

`SearchEvaluator` 在挑选搜索关键词时，候选集 SHALL 为「`soul.yaml` 的 `seed_keywords`」与「概念池 candidates（本会话已 `loadPool` 的 PG 概念）」的并集，并排除本会话/已知（`known`/已搜）的关键词。当并集去重后为空时，SHALL 诚实跳过搜索而非编造关键词。

#### Scenario: 概念池有候选词时优先可选

- **WHEN** `search.needed` 触发，概念池存在未搜过的 candidate 关键词
- **THEN** 该 candidate 进入 `SearchEvaluator` 的可选关键词集合，可被选中下发搜索

#### Scenario: 候选集为空时诚实跳过

- **WHEN** `seed_keywords ∪ candidates` 去掉已搜词后为空
- **THEN** `SearchEvaluator` 不下发搜索（skip），不重复搜已搜过的词

### Requirement: 搜索指令如实标注关键词来源

下发 `search.execute` 时，`SearchExecutePayload.source` SHALL 被如实填充，反映该关键词的真实来源（概念池抽取得到的 candidate → `new_concept`；来自 `seed_keywords` → `random_from_interests`；来自点赞内容抽取 → `extract_from_liked`）。MUST NOT 留空或填与实际来源不符的值。

#### Scenario: 概念池候选词下发时标注 new_concept

- **WHEN** 选中的关键词来自概念池 candidate
- **THEN** `search.execute` 的 `source` 字段为 `new_concept`

#### Scenario: 种子词下发时标注来源

- **WHEN** 选中的关键词来自 `seed_keywords`
- **THEN** `search.execute` 的 `source` 字段为 `random_from_interests`

### Requirement: 搜索前限频闸

系统 SHALL 在下发搜索前经过 `SearchFrequencyLimiter`（每会话上限、每天上限）与 `budget.searches` 两道闸。任一道不通过时，SHALL 诚实跳过该次搜索——不下发 `search.execute`、不扣减 `budget.searches`、不调用 `markSearched`——并记录被拦原因（`session_limit` / `daily_limit` / `budget_exhausted`）。MUST NOT 在被拦时仍下发或回报为成功。

#### Scenario: 超过每会话上限时拦截

- **WHEN** 本会话搜索次数已达 `SearchFrequencyLimiter` 的 `maxPerSession`
- **THEN** 不下发搜索、不扣 `budget.searches`，被拦原因记为 `session_limit`

#### Scenario: 搜索预算耗尽时拦截

- **WHEN** `budget.searches <= 0`
- **THEN** 不下发搜索，不静默回报成功，被拦原因记为 `budget_exhausted`

#### Scenario: 通过两道闸后正常下发并记账

- **WHEN** 限频与预算均允许
- **THEN** 下发 `search.execute`，扣减 `budget.searches`，并对该关键词调用 `ConceptStore.markSearched` 与 `SearchFrequencyLimiter.recordSearch`

### Requirement: 已搜关键词不被重复搜索

下发搜索成功后，系统 SHALL 调用 `ConceptStore.markSearched` 将该关键词标记为 `searched`，使其在后续会话 `loadPool()` 后落入 `known`、不再进入候选集。

#### Scenario: 已搜词跨会话不重复

- **WHEN** 某关键词上一会话已 `markSearched`
- **THEN** 下一会话 `loadPool()` 后该词在 `known` 中，不进入 `SearchEvaluator` 候选集
