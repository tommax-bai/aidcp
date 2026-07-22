## MODIFIED Requirements

### Requirement: 搜索前限频闸

系统 SHALL 在自治概念池搜索下发前依次经过账号 `RiskController.canDo('search')`、`SearchFrequencyLimiter`（每会话上限、每天上限）与 `budget.searches` 三道闸。任一道不通过时，SHALL 诚实跳过该次搜索——不下发 `search.execute`、不扣减 `budget.searches`、不调用 `markSearched`——并记录被拦原因（账号风险/配额原因、`session_limit` / `daily_limit` / `budget_exhausted`）。MUST NOT 在被拦时仍下发或回报为成功。

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
- **THEN** 下发 `search.execute`，扣减 `budget.searches` 并调用 `SearchFrequencyLimiter.recordSearch`
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

