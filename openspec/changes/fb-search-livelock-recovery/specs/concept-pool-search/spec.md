# concept-pool-search — delta (fb-search-livelock-recovery)

## MODIFIED Requirements

### Requirement: 搜索前限频闸

系统 SHALL 在自治概念池搜索下发前依次经过账号 `RiskController.canDo('search')`、`SearchFrequencyLimiter`(每会话上限、每天上限)与 `budget.searches` 三道闸。任一道不通过时,SHALL 诚实跳过该次搜索——不下发 `{platform}.search.execute`(`xiaohongshu.search.execute` / `facebook.search.execute`)、不扣减 `budget.searches`、不调用 `markSearched`——并记录被拦原因(账号风险/配额原因、`session_limit` / `daily_limit` / `budget_exhausted`)。MUST NOT 在被拦时仍下发或回报为成功。

三道闸均通过且命令实际下发(`sent=true`)后,系统 SHALL 一并完成发起制记账:扣减 `budget.searches`、调用 `SearchFrequencyLimiter.recordSearch`、调用 `ConceptStore.markSearched` 将关键词标为已搜、并记 1 次账号 `search` 风险事实(幂等键 `activityId`)。失败的搜索同样占用额度与关键词——搜索失败 MUST NOT 免费,否则失败词会被反复选中、失败无限重发。Edge 终态回执 SHALL 只补写 outcome 审计,MUST NOT 二次记账。

#### Scenario: 账号搜索配额已满时拦截

- **WHEN** 账号 `RiskController.canDo('search')` 因任一窗口配额或风险状态拒绝
- **THEN** 不下发搜索、不扣 `budget.searches`、不调用 `markSearched`,并记录可诊断的风控拒因

#### Scenario: 超过每会话上限时拦截

- **WHEN** 本会话搜索次数已达 `SearchFrequencyLimiter` 的 `maxPerSession`
- **THEN** 不下发搜索、不扣 `budget.searches`,被拦原因记为 `session_limit`

#### Scenario: 搜索预算耗尽时拦截

- **WHEN** `budget.searches <= 0`
- **THEN** 不下发搜索,不静默回报成功,被拦原因记为 `budget_exhausted`

#### Scenario: 通过三道闸后发起即完成全部记账

- **WHEN** 账号预闸、限频与预算均允许,且命令成功进入下行通道
- **THEN** 下发 `{platform}.search.execute`,扣减 `budget.searches`、调用 `SearchFrequencyLimiter.recordSearch`、调用 `ConceptStore.markSearched`,并记 1 次账号 `search` 风险事实

#### Scenario: 终态失败不回滚发起记账

- **WHEN** Edge 回报 `ok=false`(无论 `actuated` 取值)
- **THEN** 发起时已完成的额度扣减、已搜标记与风险事实保持不变,终态 outcome 落审计流

### Requirement: 已搜关键词不被重复搜索

系统 SHALL 在搜索命令实际下发(`sent=true`)时调用 `ConceptStore.markSearched` 将该关键词标记为 `searched`,使其在后续会话 `loadPool()` 后落入 `known`、不再进入候选集。失败的搜索同样烧掉关键词——同词 MUST NOT 因失败被反复选中重试。未下发的搜索(被三道闸或平台准入闸拦下)MUST NOT 标为已搜。新旧 Edge 在此口径下行为一致(记账不依赖终态回执)。

#### Scenario: 已发起搜索词跨会话不重复

- **WHEN** 某关键词的搜索命令已成功下发并 `markSearched`
- **THEN** 下一会话 `loadPool()` 后该词在 `known` 中,不进入 `SearchEvaluator` 候选集

#### Scenario: 失败词不再被重复选中

- **WHEN** 某关键词的搜索以失败终态返回(含 `not_submitted`)
- **THEN** 该词维持已搜标记,后续会话不再进入候选集
