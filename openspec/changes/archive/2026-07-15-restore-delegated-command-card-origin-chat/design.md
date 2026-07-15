## Context

飞书命令的执行路径在两次演进后发生了回归：

1. `route-publish-approval-to-command-chat`（2026-07-06 归档）给**直接**发帖路径接了「审批卡回命令来源会话」：命令带 `sourceChatId` → `PublishScheduler.triggerManual(manualApprovalChatId)` → 审批卡目标解析 `resolveApprovalCardTarget` 命中 `manual_source`。
2. `delegated task orchestration`（后续）把委托任务层插到每一条 `/publish` 前面：`CommandRouter.handle` 里 `case 'publish'` 只要 `actions.delegate` 存在就走 `runDelegated`（`src/feishu/commands.ts:336-337`）。生产装配里 `delegate` 永远接线（`server.ts:1549`），所以直接路径 `runPublish`（连同它带 `sourceChatId` 的审批路由）成了**死代码**。

委托路径不带来源会话：`triggerDelegated`（`publish-scheduler.ts:387-394`）把 `manualApprovalChatId` 位参写死 `undefined`；命令的 `context.chatId` 只被存进 `sourceRef`（`server.ts:1551`，取 `messageId ?? chatId`、参与去重键），从不被读回做路由。于是：

- **审批卡**回落 `botChatStore.getDefaultChat()`（默认管理群）——违反 `publish-pipeline` 既有要求；
- **终态失败卡**（`delegatedPublishOutcomeReceipt`）走 `resolveAccountChatId(task.accountId)`（账号→团队群，`server.ts:3500`）——per-team 路由，与审批卡不同群。

净效果：私聊 `/publish` 的两张卡分别落默认管理群与账号团队群，都不在私聊。（三个对抗性校验 agent 均 CONFIRMED；完备性 agent 结论「无遗漏的回私聊路径」。）

## Goals / Non-Goals

**Goals:**
- 命令触发的委托发帖，其**审批卡 + 终态失败卡**投递到下命令的那个会话（私聊→私聊、群→那个群），恢复并扩展既有「回命令会话」语义到委托路径。
- 自动 / 排期 / 面板 / 边缘等**无来源命令会话**的发帖流量，路由**逐字不变**（审批卡走默认群、业务结果卡走账号团队群）。
- 保持诚实红线：投递失败绝不当成功。

**Non-Goals:**
- 不改手动 `/comment` 终态结果卡的路由（现仍走 per-team 团队群）——同形问题、不同代码路径（`CommentScheduler.postResultCard`），登记为后续对齐项，避免写出宽于实现的 spec。
- 不动边缘（纯云端变更）。
- 不改 per-team 路由对自动流量的既有行为，也不改审批卡「面向运营方、不按账号团队路由」的分类。

## Decisions

**D1：新增独立字段 `originChatId`，不复用 `sourceRef`。**
`sourceRef` 取 `messageId ?? chatId` 且参与 `delegatedTaskDedupeKey`；把它改成 chatId 既会改去重语义，也会把「审计引用」与「路由目标」两种职责搅在一起。新增 `DelegatedTask.originChatId`（可空）专职路由，语义单一、零去重副作用。
备选：复用 `sourceRef` —— 否决（职责耦合 + 去重回归风险）。

**D2：来源会话必须持久化（DB 一列），不能用内存映射。**
委托 worker 5s 轮询异步执行，审批卡与失败卡在命令之后、甚至进程重启之后才发出。内存态在重启后丢失。故在 `delegated_tasks` 加一列 `origin_chat_id TEXT`（可空）。无迁移器、schema 启动自建，用幂等 `ALTER TABLE delegated_tasks ADD COLUMN IF NOT EXISTS origin_chat_id TEXT;` 追加在建表 SQL 后。旧行该列为 NULL = 回落既有路由，零回归。
备选：内存 `Map<taskId, chatId>` —— 否决（重启即丢，正是异步终态卡最需要它的时候）。

**D3：审批卡走既有 `manual_source` 通道，不新增解析分支。**
`resolveApprovalCardTarget`（`publish-executor.ts:544-548`）已是「有 `manualApprovalChatId` 用它，否则默认群」。只需让委托路径把 `originChatId` 一路透传成 `input.manualApprovalChatId`：`executors.ts:300` 的 `DelegatedPublishPort.triggerDelegated` 增 `manualApprovalChatId` 入参 → `PublishScheduler.triggerDelegated` 透传给 `doTrigger`（替换写死的 `undefined`）。审批卡目标解析代码一行不改。

**D4：失败卡在委托 worker 出口按「优先来源会话、否则团队群」取址。**
`server.ts:3500` 改为 `const chatId = task.originChatId?.trim() || await resolveAccountChatId(task.accountId);`。补集式判定：只有拿到非空来源会话才覆盖团队路由，其余一切（自动任务、旧行、trim 后为空）都走既有 `resolveAccountChatId`，天然零回归。发送日志标明所选 sink（`origin` / `account_team`）便于运营核对。

**D5：来源会话只在命令入口（`server.ts:1551`）从 `context.chatId` 采集。**
`context.chatId` 即 `im.message.receive_v1` 的 `message.chat_id`——私聊是 p2p 会话 id、群聊是群 id，都可直接 `sendCard`。console / api / edge 等非飞书入口没有 chatId → `originChatId` 为空 → 回落既有路由。

## Risks / Trade-offs

- [手动发帖失败卡不再进团队群，客户团队看不到该次失败] → 这是用户显式选择的策略（操作员触发、操作员收结果）。自动 / 排期发帖的团队可见性完全不变；手动触发本就是运营内部动作。
- [publish 与 comment 手动结果卡路由不一致（前者回来源、后者仍团队群）] → 已在 proposal / spec 显式登记为后续对齐项，非隐藏漂移；spec 只声明已实现的 publish 范围，不写宽于代码的要求。
- [`ADD COLUMN IF NOT EXISTS` 在启动自建 schema 上运行] → PostgreSQL 原生幂等；与既有建表 SQL 同批执行，与并发部署方共库时不冲突（纯 additive，不改约束）。
- [来源会话可能是已解散 / 不可达的私聊] → 命中既有诚实红线：`sendCard` 失败记日志、不当成功；审批卡失败保持诚实待审态。

## Migration Plan

1. 部署即随启动 schema 自建执行 `ADD COLUMN IF NOT EXISTS`，无独立迁移步骤。
2. 回滚：字段可空、旧代码不读它 → 直接回滚代码即可，DB 列留存无害（下次前滚复用）。env 无新开关（行为由数据是否带 `origin_chat_id` 自然决定）。
3. 验收：dev 上从**私聊**下 `/publish <昵称>`，确认审批卡与终态卡都回到该私聊；从**管理群**下同一命令，确认回该群；确认自动 / 排期发帖结果卡仍进账号团队群（真机项，登记 backlog）。

## Open Questions

- 手动 `/comment` 终态结果卡是否也要回来源会话（与 publish 对齐）？本变更不做，留作后续；届时需同样把 `originChatId` 透传进 `CommentScheduler.postResultCard` 的取址。
