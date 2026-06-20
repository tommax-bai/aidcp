## ADDED Requirements

### Requirement: interaction.occurred 补 accountId（云内事件，不碰协议）

系统 SHALL 给云内事件 `interaction.occurred` 加 `accountId`，并在发射点从 `session.accountId` 填入。这 MUST 是云内类型改动，MUST NOT 改动两份 `protocol.ts`——`accountId` 已经过 `HelloPayload` 到达 `session.accountId`，并非协议新增。补齐后，按账号互动归因 SHALL 成为可能。

#### Scenario: 互动事件带上账号归因
- **WHEN** 一次互动在某账号会话中发生并发射 `interaction.occurred`
- **THEN** 事件携带从 `session.accountId` 填入的 `accountId`，且两份 `protocol.ts` 未被改动

### Requirement: undefined-accountId 显式回退到保留键并标 unattributed

由于 `accountId` 端到端可选，系统 SHALL 为缺失 `accountId` 定义显式回退：路由到保留键 `default`，**并**在投影里把该流量标为 `unattributed`。系统 MUST NOT 在缺失 `accountId` 时抛错（会打断 legacy edge 的 live 路径），MUST NOT 静默把它并入某个真名账号（静默误归因）。

#### Scenario: 缺账号的流量被标记而非误并
- **WHEN** 一个 `interaction.occurred` 到达时没有 `accountId`
- **THEN** 它被路由到保留键 `default` 并在投影里标 `unattributed`，既不抛错打断 live 路径、也不并入某个真名账号

### Requirement: 填充已声明的 noteId 并接线去重表

系统 SHALL 在发射点填充 `interaction.occurred` 上**已声明的可选** `noteId` 字段（`event-bus/types.ts:123`，无需契约改动），并把从未实例化的 `risk_interactions` 去重表接线进 live 的互动完成路径，作为按笔记互动历史的后端。

#### Scenario: 互动带笔记归因并落去重表
- **WHEN** 一次互动完成且编排已知其 `noteId`
- **THEN** `interaction.occurred` 携带 `noteId`，去重表记录 `(account, note, action)`，供按笔记历史查询

### Requirement: 归因落地前不把全局数字冒充按账号

在 `accountId` 在事件上流通之前，按账号的面板切片/聚合 MUST 被**withheld**或标为「全部账号 / 归因待补」，MUST NOT 显示为按行的按账号数字。把全局计数冒充成按账号即违反「绝不静默假成功」红线。`qualityIndex` 与平台侧内容表现无数据源，MUST 明确排除在本能力之外。

#### Scenario: 归因待补期间诚实标注
- **WHEN** 面板在 `accountId` 归因尚未流通时展示总览
- **THEN** 凡涉及按账号拆分处均标「全部账号 / 归因待补」，绝不把全局数字呈现为某账号的数字
