## MODIFIED Requirements

### Requirement: 冷却闸只拦四类互动、不拦推进、不写风控终态

冷却闸 SHALL 只作用于 `{platform}.note.like` / `xiaohongshu.note.collect` / `{platform}.user.follow` / `{platform}.note.comment` 的下发判定；`{platform}.feed.scroll` / `{platform}.navigation.back` / `{platform}.note.open` / `xiaohongshu.profile.open` 等推进 / 导航指令 MUST NOT 被冷却闸拦截（避免浏览循环死锁，与既有「推进指令不被风控闸拦」同口径）。冷却闸为**附加只读兜底闸**（只防意外爆发，不表达数量策略——数量由 `RiskController` 主闸单独负责）：MUST NOT 写 `risk_state`、MUST NOT 调用 `RiskController.setQuotaLevel` / `applySignal`、MUST NOT 改变账号风控终态或档位；账号风控终态仍仅由 `RiskController` 单写。

#### Scenario: 推进指令不被冷却拦

- **WHEN** 某账号多个互动类型都处于冷却中
- **THEN** `{platform}.feed.scroll` / `{platform}.navigation.back` / `{platform}.note.open` / `xiaohongshu.profile.open` 仍正常下发，浏览循环继续，不死锁

#### Scenario: 冷却不触碰风控终态

- **WHEN** 冷却闸抑制了一次互动
- **THEN** 该账号 `risk_state`（status 与 quotaLevel）MUST NOT 被改写，`setQuotaLevel` / `applySignal` MUST NOT 被调用
