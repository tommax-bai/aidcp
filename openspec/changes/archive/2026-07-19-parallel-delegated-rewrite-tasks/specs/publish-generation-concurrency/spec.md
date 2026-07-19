## ADDED Requirements

### Requirement: 委托入口不得重新串行化跨来源洗稿

结构化 Edge、console 或 API 洗稿先进入统一委托层时，委托层 MUST 保留发布生成段的输入身份并发语义：参照洗稿以 `(accountId, sourceId)` 为单飞 lane，不同稳定 `sourceId` SHALL 能并行进入 PublishScheduler，且继续受账号在途帽与全局生成帽约束。委托层 MUST NOT 以同账号 `actionFamily=publish` 的粗粒度 ownership 把跨来源洗稿重新串行化。

参照洗稿完成生成、候选已持久化并进入 `waiting_approval` 后，该任务 MUST NOT 继续占用参照洗稿生成 lane；同源串行重洗与跨来源新洗稿均可继续按容量帽准入。无参照稿的自主发布仍按账号单飞。

#### Scenario: 三条 Edge 洗稿委托同时进入生成

- **WHEN** 同一账号从 Edge 连续提交三条不同稳定 `sourceId` 的洗稿委托，账号与全局容量均空闲
- **THEN** 三条任务 SHALL 能同时进入发布生成段
- **AND** MUST NOT 因另一条同账号发布任务处于 planning 或 executing 而得到 `delegated_ownership_busy`

#### Scenario: 待审批洗稿不阻塞另一来源

- **WHEN** 一条参照洗稿已生成候选并处于 `waiting_approval`，同账号另一 `sourceId` 的洗稿委托到达
- **THEN** 新任务 SHALL 可立即申请发布生成 claim
- **AND** MUST NOT 等待前一候选被批准、驳回或下发终结

#### Scenario: 普通稿仍保持账号单飞

- **WHEN** 同账号已有一条无参照稿的自主发布委托处于生成或既有 ownership 保护期
- **THEN** 第二条自主发布委托 SHALL 等待
- **AND** MUST NOT 因委托 worker 支持并发而同时生成相似普通稿
