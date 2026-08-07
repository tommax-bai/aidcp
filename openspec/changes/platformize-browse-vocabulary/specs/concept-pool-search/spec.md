## MODIFIED Requirements

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
