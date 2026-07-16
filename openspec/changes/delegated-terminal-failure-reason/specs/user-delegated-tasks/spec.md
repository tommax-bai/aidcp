## ADDED Requirements

### Requirement: 预算耗尽的零成功终态必须携带真实失败原因

预算耗尽（`max_attempts` / `deadline`）而零成功的终态，其 `terminalOutcome.message` MUST 在既有预算记账之后追加**真实失败原因**，取自该任务已 settle 且 `reason` 非空的最后一条 attempt。

「已达到最大尝试次数」「已到截止时间」是**为什么停**的记账，不是**为什么没成**的原因。只给记账等同于静默失败——卡发出来了，但运营无法判断该重试、该改配置、还是该等。原因在 attempt settle 时即已持久化，终态 MUST 读它，MUST NOT 凭空另拼一句只含记账的模板。

既有前缀 SHALL 原样保留（追加而非替换），既有的诚实部分完成语义不受影响。

#### Scenario: 尝试后失败的终态带上最后一次原因

- **WHEN** 一个委托发帖任务耗尽 `maxAttempts`，其最后一条 settle 的 attempt 状态为 `failed`、`reason` 非空
- **THEN** `terminalOutcome.message` SHALL 保留 `已达到最大尝试次数；真实完成 0/1。` 前缀
- **AND** SHALL 追加该 attempt 的原因（经人话化）
- **AND** 该原因 SHALL 出现在飞书终态失败卡正文中

#### Scenario: 无原因可取时保持现状而非编造

- **WHEN** 预算耗尽终态下，该任务不存在任何 settle 且 `reason` 非空的 attempt
- **THEN** `terminalOutcome.message` SHALL 与本变更前逐字一致
- **AND** MUST NOT 补一句「原因未知，可能是……」之类的推测

#### Scenario: 到期终态同样带原因

- **WHEN** 一个委托任务因 `deadlineAt` 到期而零成功终结，且存在带原因的已 settle attempt
- **THEN** `terminalOutcome.message` SHALL 在 `已到截止时间；真实完成 N/M。` 之后追加该原因

### Requirement: 终态必须区分「尝试后失败」与「从未真正开始」

预算耗尽的零成功终态 MUST 区分两种截然不同的局面，MUST NOT 让二者产出同一句话：

- **尝试后失败**（存在 `failed` attempt）：SHALL 表述为最后一次未成的原因。
- **从未真正开始**（`failureCount === 0` 且 `skippedCount === attemptCount`——每一次 attempt 都在动作真正发生前就被让开、settle 成 `skipped`）：SHALL 明说 N 次均未真正开始及其原因，MUST NOT 使用任何可被读成「已经发过 / 已经动过手」的措辞。

此区分为红线「绝不静默假成功」在终态回执上的落点：让开（deferred → `skipped`）同样消耗尝试预算，若与真实失败同文表述，运营会误以为系统已在平台上动过手。

#### Scenario: 全程被让开而耗尽预算

- **WHEN** 一个委托发帖任务的 2 次 attempt 全部因执行前闸（风控状态、并发占用等）被让开，settle 为 `skipped`，`failureCount` 为 0
- **THEN** `terminalOutcome.message` SHALL 表述为「2 次均未真正开始」并带上原因
- **AND** MUST NOT 表述为「最后一次未成原因」或任何暗示已发生平台写入的措辞

#### Scenario: 混合局面只报最后一次并标注总次数

- **WHEN** 一个任务的多次 attempt 中既有 `failed` 也有 `skipped`，原因各异
- **THEN** `terminalOutcome.message` SHALL 报最后一次未成的原因并标注总尝试次数
- **AND** MUST NOT 做原因聚类统计（超出本变更范围）

### Requirement: 原因人话化必须只翻译已知码、未知码原样透传

原因字符串在同一字段内混装三种语域（机器码 snake_case、中文人话句、上游抛出的英文异常文本），无判别字段。人话化 SHALL 按白名单把已知机器码翻成中文；**未命中白名单的 MUST 原样透传**，MUST NOT 猜测其含义、MUST NOT 美化成听着像诊断而实际是编造的句子。超长文本 SHALL 裁剪并保留可辨识的原文片段。

#### Scenario: 已知码翻成人话

- **WHEN** 最后一条 attempt 的 `reason` 为白名单内的机器码（如风控状态类、人设未配置类）
- **THEN** 终态 message 中 SHALL 出现对应中文表述

#### Scenario: 未知码原样出现在卡上

- **WHEN** 最后一条 attempt 的 `reason` 是白名单未覆盖的字符串
- **THEN** 该字符串 SHALL 原样出现在终态 message 中
- **AND** MUST NOT 被替换成任何未经证据支持的表述

### Requirement: 失败原因的精度不得超过已落库的证据

终态回执的原因精度 SHALL 以**已持久化的证据**为上限。发布派发阶段的分步失败细节（定位失败、内容超长、配图全失败等）当前未落库，仅塌成一个状态枚举——因此该类失败的终态回执 SHALL 表述到「稿件在发布派发阶段失败」这一层并携带可追证据引用，**MUST NOT** 渲染成具体的边缘失败原因。

抬高该精度天花板（把分步失败落库）属独立变更，MUST NOT 在本变更中以推测填补。

#### Scenario: 派发期失败只说到阶段

- **WHEN** 一个委托发帖任务的 attempt 因发布派发阶段失败而 settle，DB 中仅有状态枚举、无分步细节
- **THEN** 终态 message SHALL 说明失败发生在发布派发阶段并带上稿件记录引用
- **AND** MUST NOT 声称具体是哪一步、哪个控件或哪条平台文案导致失败
