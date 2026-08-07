# concept-pool-search Specification

## Purpose
TBD - created by archiving change wire-concept-pool-search-intelligence. Update Purpose after archive.
## Requirements
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

### Requirement: 搜索关键词来自概念池而非仅写死种子词

`SearchEvaluator` 在挑选搜索关键词时，候选集 SHALL 为「`soul.yaml` 的 `seed_keywords`」与「概念池 candidates（本会话已 `loadPool` 的 PG 概念）」的并集，并排除本会话/已知（`known`/已搜）的关键词。当并集去重后为空时，SHALL 诚实跳过搜索而非编造关键词。

#### Scenario: 概念池有候选词时优先可选

- **WHEN** `search.needed` 触发，概念池存在未搜过的 candidate 关键词
- **THEN** 该 candidate 进入 `SearchEvaluator` 的可选关键词集合，可被选中下发搜索

#### Scenario: 候选集为空时诚实跳过

- **WHEN** `seed_keywords ∪ candidates` 去掉已搜词后为空
- **THEN** `SearchEvaluator` 不下发搜索（skip），不重复搜已搜过的词

### Requirement: 搜索指令如实标注关键词来源

下发 `{platform}.search.execute`（`xiaohongshu.search.execute` / `facebook.search.execute`）时，`SearchExecutePayload.source` SHALL 被如实填充，反映该关键词的真实来源（概念池抽取得到的 candidate → `new_concept`；来自 `seed_keywords` → `random_from_interests`；来自点赞内容抽取 → `extract_from_liked`）。MUST NOT 留空或填与实际来源不符的值。

#### Scenario: 概念池候选词下发时标注 new_concept

- **WHEN** 选中的关键词来自概念池 candidate
- **THEN** `{platform}.search.execute` 的 `source` 字段为 `new_concept`

#### Scenario: 种子词下发时标注来源

- **WHEN** 选中的关键词来自 `seed_keywords`
- **THEN** `{platform}.search.execute` 的 `source` 字段为 `random_from_interests`

### Requirement: 搜索前限频闸

系统 SHALL 在自治概念池搜索下发前依次经过账号 `RiskController.canDo('search')`、`SearchFrequencyLimiter`（每会话上限、每天上限）与 `budget.searches` 三道闸。任一道不通过时，SHALL 诚实跳过该次搜索——不下发 `{platform}.search.execute`（`xiaohongshu.search.execute` / `facebook.search.execute`）、不扣减 `budget.searches`、不调用 `markSearched`——并记录被拦原因（账号风险/配额原因、`session_limit` / `daily_limit` / `budget_exhausted`）。MUST NOT 在被拦时仍下发或回报为成功。

三道闸均通过且命令实际下发后，系统 SHALL 扣减 `budget.searches` 并调用 `SearchFrequencyLimiter.recordSearch`，将其作为防止在途重复的**尝试账**；对支持 `search_activity_receipt_v1` 的 Edge，MUST NOT 此时调用 `ConceptStore.markSearched` 或增加账号 `search` 风险事实。只有 Edge 终态证明 `actuated=true` 后，系统才 SHALL 分别写入概念词已搜状态与账号搜索事实。

#### Scenario: 账号搜索配额已满时拦截

- **WHEN** 账号 `RiskController.canDo('search')` 因任一窗口配额或风险状态拒绝
- **THEN** 不下发搜索、不扣 `budget.searches`、不调用 `markSearched`，并记录可诊断的风控拒因

#### Scenario: 超过每会话上限时拦截

- **WHEN** 本会话搜索次数已达 `SearchFrequencyLimiter` 的 `maxPerSession`
- **THEN** 不下发搜索、不扣 `budget.searches`，被拦原因记为 `session_limit`

#### Scenario: 搜索预算耗尽时拦截

- **WHEN** `budget.searches <= 0`
- **THEN** 不下发搜索，不静默回报成功，被拦原因记为 `budget_exhausted`

#### Scenario: 通过三道闸后只记录尝试

- **WHEN** 账号预闸、限频与预算均允许，且命令成功进入下行通道
- **THEN** 下发 `{platform}.search.execute`，扣减 `budget.searches` 并调用 `SearchFrequencyLimiter.recordSearch`
- **AND** 在 Edge 终态前不调用 `ConceptStore.markSearched`、不新增账号 search 风险事实

#### Scenario: 提交后失败仍完成事实记账

- **WHEN** Edge 回报 `ok=false, actuated=true, searchOutcome=failed_after_submit`
- **THEN** 系统调用 `ConceptStore.markSearched` 并记录一次账号 search 风险事实，因为平台动作已经发生

### Requirement: 已搜关键词不被重复搜索

对支持 `search_activity_receipt_v1` 的 Edge，系统 SHALL 在搜索终态证明 `actuated=true` 后调用 `ConceptStore.markSearched` 将该关键词标记为 `searched`，使其在后续会话 `loadPool()` 后落入 `known`、不再进入候选集。仅有命令下发、`page.cards` 或 `actuated=false` 的终态 MUST NOT 将关键词标为已搜。未声明新能力的旧 Edge MAY 保持下发成功后标记的兼容行为，但系统 MUST NOT 把该兼容标记解释为新搜索事实。

#### Scenario: 已执行搜索词跨会话不重复

- **WHEN** 某关键词收到 `actuated=true` 的终态并已 `markSearched`
- **THEN** 下一会话 `loadPool()` 后该词在 `known` 中，不进入 `SearchEvaluator` 候选集

#### Scenario: 未提交搜索词仍可重试

- **WHEN** 某关键词命令已下发但 Edge 终态为 `actuated=false, searchOutcome=not_submitted`
- **THEN** 系统不调用 `markSearched`，该词在后续会话仍可作为候选词

### Requirement: 首页转搜索的触发更耐心

浏览闭环在首页连续多屏无可点内容后才转入搜索。该「连续无收获屏数」阈值 MUST 为 20（可由 env 覆盖，默认 20），使账号更长时间地留在首页浏览、不因短暂的低命中就急于离开首页去搜索。真正打开一篇内容 MUST 重置该连续计数（只有连着无收获才累积）。

#### Scenario: 首页连续无收获未达阈值时继续翻页
- **WHEN** 首页连续无可点内容的屏数尚未达到阈值
- **THEN** 浏览闭环 SHALL 继续在首页翻页，MUST NOT 触发搜索

#### Scenario: 首页连续无收获达阈值时才转搜索
- **WHEN** 首页连续无可点内容的屏数达到阈值
- **THEN** 浏览闭环 SHALL 触发一次搜索决策，并重置该连续计数

### Requirement: 当前列表页型据真实导航追踪，而非自指默认值

云端 MUST 依据「真实下发了搜索指令」来把当前列表页型标记为搜索页，而 MUST NOT 让页型状态自指（写回等于读出、永远停在首页）。被限频或预算闸拦下、并未下发的搜索 MUST NOT 翻转页型——只有实际导航到搜索结果页那一刻才标记为搜索页。回到首页时 MUST 标回首页。

由此，搜索结果页 MUST 由搜索翻页逻辑驱动（而非被当作首页处理），且搜索结果卡 MUST NOT 计入首页浏览深度。

#### Scenario: 实际下发搜索后页型为搜索页
- **WHEN** 一次搜索通过两道闸并真正下发了搜索指令
- **THEN** 当前列表页型 SHALL 标记为搜索页
- **AND** 后续该页上报的可见卡 MUST NOT 计入首页浏览深度

#### Scenario: 被闸拦下的搜索不翻转页型
- **WHEN** 一次搜索被会话搜索预算或关键词限频闸拦下、未下发
- **THEN** 当前列表页型 MUST NOT 被翻转为搜索页

### Requirement: 搜索行程累计到有界卡数后回到首页

一次搜索行程 MUST 是有界的：在搜索结果页累计浏览到有界数量的不重复卡片后（阈值可由 env 覆盖，默认 20），浏览闭环 MUST 回到首页，而 MUST NOT 无限期停留在搜索页。计数 MUST 按不重复新卡差分累计，从而「搜索页一篇都点不开」的空转场景同样计入卡数、同样在达阈值时回首页（绝不卡死在搜索页）。

回首页 MUST 复用既有的「刷新回顶换首页」能力，MUST NOT 新增协议消息类型或主动命令。平台不支持刷新时，MUST 诚实降级（不回首页），MUST NOT 因此卡死加剧或伪造已回首页。

#### Scenario: 搜索页累计达阈值回首页
- **WHEN** 搜索结果页累计浏览的不重复卡片数达到阈值
- **THEN** 浏览闭环 SHALL 发出一次回首页指令，并把当前列表页型标回首页
- **AND** 随后按首页浏览闭环继续

#### Scenario: 搜索页空转也在达阈值时回首页
- **WHEN** 搜索结果页一篇都点不开、只是持续下滑
- **THEN** 划过的不重复卡片数 SHALL 照常累计
- **AND** 达阈值时 SHALL 回首页，MUST NOT 永久停留在搜索页

