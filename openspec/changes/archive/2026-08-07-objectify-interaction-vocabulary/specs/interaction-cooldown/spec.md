## MODIFIED Requirements

### Requirement: 未到冷却点的互动诚实抑制——不下发、不计数、不假成功

当冷却闸判定某互动未到点时，系统 MUST 诚实跳过：MUST NOT 下发该互动指令、MUST NOT 扣减每会话预算、MUST NOT 触发风控计数、MUST NOT 以任何方式记录/上报为成功互动。被抑制 MUST 以可观测的中性原因（如 `cooldown`）记录，便于区分「按冷却跳过」与「找不到目标 / 被风控拒」，且日志 MUST NOT 写成「失败」。该语义为红线「MUST NOT 静默假成功」的延伸。

**丢弃语义的条件式不变量**：冷却抑制**直接丢弃该次意图、不排队、不补发**。这是可接受代价，**当且仅当**冷却取值可证明不削主闸的任一窗口配额（见上一要求的不变量）。若某次变更使冷却在任一窗口成为 binding 者，则「丢弃而不排队」将**永久吃掉合法互动意图**、使面板配额无法被逼近——该变更 MUST 被视为违规，或 MUST 同批把丢弃改为排队。

#### Scenario: 被冷却抑制不下发不扣预算

- **WHEN** 某 `collect` 意图被冷却闸判定未到点
- **THEN** 系统 MUST NOT 下发 `xiaohongshu.note.collect`、MUST NOT 扣减 collect 预算、MUST NOT 计数，并以原因 `cooldown` 如实记录

#### Scenario: 红线反例——被冷却却假报成功（禁止）

- **WHEN** 有实现在冷却未到点时仍记一次成功互动 / 仍扣预算 / 仍下发指令
- **THEN** MUST 视为违规、不予合入；被冷却抑制 MUST 等价于一次诚实跳过

#### Scenario: 冷却成为 binding 者时丢弃语义即不再可接受

- **WHEN** 某次变更把某动作的冷却调大到在任一窗口比主闸紧（即削掉了该窗口的配额）
- **THEN** MUST 视为违规、不予合入——因为「丢弃不排队」会把合法互动意图永久吃掉，使面板配额无法被逼近，且无日志无告警

### Requirement: 冷却闸只拦四类互动、不拦推进、不写风控终态

冷却闸 SHALL 只作用于 `{platform}.note.like` / `xiaohongshu.note.collect` / `{platform}.user.follow` / `{platform}.note.comment` 的下发判定；`{platform}.feed.scroll` / `navigation.back` / `{platform}.note.open` / `xiaohongshu.profile.open` 等推进 / 导航指令 MUST NOT 被冷却闸拦截（避免浏览循环死锁，与既有「推进指令不被风控闸拦」同口径）。冷却闸为**附加只读兜底闸**（只防意外爆发，不表达数量策略——数量由 `RiskController` 主闸单独负责）：MUST NOT 写 `risk_state`、MUST NOT 调用 `RiskController.setQuotaLevel` / `applySignal`、MUST NOT 改变账号风控终态或档位；账号风控终态仍仅由 `RiskController` 单写。

#### Scenario: 推进指令不被冷却拦

- **WHEN** 某账号多个互动类型都处于冷却中
- **THEN** `{platform}.feed.scroll` / `navigation.back` / `{platform}.note.open` / `xiaohongshu.profile.open` 仍正常下发，浏览循环继续，不死锁

#### Scenario: 冷却不触碰风控终态

- **WHEN** 冷却闸抑制了一次互动
- **THEN** 该账号 `risk_state`（status 与 quotaLevel）MUST NOT 被改写，`setQuotaLevel` / `applySignal` MUST NOT 被调用
