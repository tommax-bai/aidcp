## ADDED Requirements

### Requirement: 详情确认命中的强制点赞不再由普通选择性判定二次否决

选卡角色 SHALL 在账号存在 `mandatory_interactions` 时优先打开可能命中规则的真实卡片；详情粗筛 SHALL 以全文作唯一语义确认，并输出合法 `mandatoryRuleId`。规则命中 MUST 服从全局品牌安全：品牌安全禁区仍 close；LLM 错误、解析错误或未知 rule id MUST fail-closed，MUST NOT 伪造命中。

当详情确认命中的规则包含 `like` 时，mandatory context MUST 沿 `quality.pass → reading.* → reading.done` 的 typed payload 逐跳透传；`InteractionAppraiserRole` MUST 跳过普通点赞 LLM、会话 likes 软预算与点赞冷却，确定性 emit 一次 `interaction.completed{actions:['like']}`。该意图仍 MUST 经过账号 `RiskController.canDo('like')`，且只有 edge 对目标帖回报真实 `ok:true` 才计数 / 扣可用预算 / 落冷却；被硬风控拦截或 edge 失败 MUST 如实记录非成功，MUST NOT 伪报“已点赞”。

#### Scenario: 低热度规则命中帖仍产生点赞意图
- **WHEN** 一篇低热度但全文确认命中账号强制规则的帖子进入 `reading.done`，且普通点赞 LLM原本会 pass、会话 likes 软预算为 0、点赞仍在冷却
- **THEN** 系统不调用普通点赞判定，确定性产生一次目标帖 like 意图，并跳过软预算与冷却

#### Scenario: 强制点赞仍受硬风控与真实回执约束
- **WHEN** mandatory like 意图被 `RiskController` 拒绝，或 edge 返回 `no_target` / `blocked_by_captcha` / `state_unchanged`
- **THEN** 系统如实记录拦截或失败，不记点赞成功、不扣成功配额，MUST NOT 因“强制”伪造成功

#### Scenario: mandatory context 不依赖同级共享集合
- **WHEN** `quality.pass` 在同步 EventBus 内触发深读并嵌套推进到 `reading.done`
- **THEN** 规则上下文随因果 payload 可见于点赞判定，MUST NOT 依赖另一个同级订阅者稍后写入的 Set 而丢失
