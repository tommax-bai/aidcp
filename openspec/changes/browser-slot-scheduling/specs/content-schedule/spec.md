## MODIFIED Requirements

### Requirement: 内容调度器按账号扇出并分钟错峰

系统 SHALL 提供一个云端单进程、每分钟心跳的内容调度器（命令式触发器，MUST NOT 进角色注册表、MUST NOT 走事件总线）。每次心跳 SHALL 遍历在线账号，对每个账号按闸序判定：排期启用 ∧ 有效且当前活跃的内容格 ∧ 当前分钟命中该账号错峰偏移 ∧ 未达日上限 ∧ 风控状态为 normal。错峰偏移 SHALL 为 `hash(accountId + 本地日期 + 动作) % 60` 得到的分钟（纯函数、无状态、可复现；逐日变化、账号间错开）。心跳 MUST 有重入护栏（上轮未完即跳过本轮），且对 `(账号, 动作, 小时格)` 幂等（同格 MUST NOT 重复触发）。

**小时格 MUST 在触发真正开始之后才被记为已消耗。** 触发若在开始前失败（edge 离线、浏览器唤醒失败、租约不可得、准入拦阻），该小时格 SHALL **保持可用**，调度器 SHALL 在该小时格剩余分钟内允许再次尝试。MUST NOT 因一次未开始的失败就把这一小时的名额烧掉——那会让浏览器停泊期与固定偏移分钟相位锁死的账号**整天一次都触发不了**。

同一 `(账号, 动作, 小时格)` 的未开始重试 SHALL **有界**：首次触发失败后最多再试 5 次。重试预算 MUST 由任务的最终 `not_started` 结果递减，包括触发入口先返回“已开跑”、稍后才异步回流 `not_started` 的路径；MUST NOT 因早期触发回执清空或重置该预算。自动重试期间的中间 `not_started` 结果 MUST NOT 逐次发送运营结果卡；预算用尽时 SHALL 只发送一张整格放弃卡。手动任务的即时结果卡不受此抑制规则影响。

#### Scenario: 命中偏移分钟才尝试
- **WHEN** 当前小时是某账号活跃内容格，但当前分钟不等于该账号的错峰偏移
- **THEN** 本分钟不触发；仅在分钟等于偏移时尝试

#### Scenario: 账号间错峰
- **WHEN** 多个账号在同一活跃小时格
- **THEN** 各账号按其 `hash(账号+日期+动作)%60` 落在不同分钟触发，绝不在同一刻齐发

#### Scenario: 同小时格不重复
- **WHEN** 同一账号在同一小时格已被成功触发过一次
- **THEN** 该小时格内 MUST NOT 再次触发（幂等键拦截）

#### Scenario: 未开始的失败不烧名额
- **WHEN** 一次排期触发在开始前失败（edge 离线 / 浏览器唤醒失败 / 租约不可得）
- **THEN** 该 `(账号, 动作, 小时格)` MUST NOT 被记为已触发，调度器可在该小时格剩余分钟内重试

#### Scenario: 唤醒中的账号可在同小时内重试
- **WHEN** 触发时该账号浏览器正在唤醒、本次未能开始
- **THEN** 名额保留，下一分钟心跳可再次尝试，直到该小时格结束

#### Scenario: 异步未开始回流仍消耗同一重试预算
- **WHEN** 自动评论触发入口先返回已开跑，而任务稍后因浏览器唤醒失败回流 `not_started`
- **THEN** 调度器在同一小时格的既有预算上递减一次，最多执行首次尝试加 5 次重试，MUST NOT 每次把剩余次数重置为 5

#### Scenario: 自动重试整格只通知一次
- **WHEN** 同一小时格内的自动评论因可恢复的接管失败连续返回 `not_started`
- **THEN** 中间重试不逐次发送结果卡；预算用尽时只发送一张整格放弃卡，并说明本小时未搜索、未选中、未发布

### Requirement: 排期评论在 edge 接管失败前如实报告未开始

排期评论在 prepare 或 commit 租约尚未取得时发生 edge acquire timeout、edge 离线、连接断开、**或浏览器唤醒失败**，SHALL 产出 `not_started` 的非成功结果。对应飞书结果卡 MUST 明确本次未搜索、未选中笔记、未发布评论，并给出可审计的接管失败原因；MUST NOT 使用"已选中笔记""发布未确认"等仅适用于已进入候选或提交阶段的措辞。该结果 MUST NOT 被记录为已评论、已发布或候选已选中。

**「浏览器停泊 / 唤醒中」SHALL 作为一个独立的、可审计的接管失败原因**，与 edge 离线区分开——前者是可恢复的，后者不是；把停泊读成离线会误导运维去查连接。

#### Scenario: prepare acquire 超时
- **WHEN** 自动排期评论在搜索候选前等待 edge acquire 超时
- **THEN** 结果卡显示浏览器未能接管且本次未搜索、未选中、未发布，零条评论业务命令被下发

#### Scenario: 浏览器唤醒失败如实区分
- **WHEN** 排期评论因目标账号浏览器停泊且唤醒失败而未开始
- **THEN** 结果卡如实说明是「浏览器唤醒失败」而非「边缘离线」，且该小时格名额保留

#### Scenario: 已进入流程后的失败保持阶段语义
- **WHEN** 排期评论已经取得租约并在候选选择、撰写或提交阶段失败
- **THEN** 系统保留对应阶段的真实失败说明，不把该失败改写成 `not_started`

## ADDED Requirements

### Requirement: 云端 SHALL 按「浏览器就绪」而非「引擎在线」派发排期任务

云端在向账号派发排期任务前 SHALL 区分「引擎在线」与「浏览器就绪」。今天的在线判定只看是否存在边缘连接，会把**停泊中（浏览器已释放）**的账号当成随时可干活。

对停泊中的账号，云端 SHALL 走**先唤醒、待其报到就绪、再下发**的两段式路径，MUST NOT 直接下发业务命令后靠失败回执兜底。

云端任务受理超时 SHALL 容得下一次浏览器冷启（默认 45 秒短于 30–90 秒的冷启）；带唤醒的请求 SHALL 使用更长的按请求超时。

#### Scenario: 停泊账号经唤醒后再派发
- **WHEN** a scheduled task targets an account whose browser is parked
- **THEN** cloud first requests a wake, waits for browser-ready, and only then dispatches the business command

#### Scenario: 受理超时容得下冷启
- **WHEN** a lease request is expected to involve a browser wake
- **THEN** cloud uses an acquire timeout long enough to cover a cold start, and MUST NOT time out at the default short bound while the wake is legitimately in progress
