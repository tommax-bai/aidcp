## Why

私聊里下 `/publish` 命令后，内容审批卡落到了默认管理群、失败结果卡落到了账号团队群——两张卡分到两个不同的群，都没回到下命令的私聊。根因是委托任务层（现在挡在每一条 `/publish` 前面）把「命令来自哪个会话」这个信息丢了：来源会话只被存成一个从不被读回的审计字段。这既**违反了 `publish-pipeline` 已合入的既有要求**「手动飞书发帖审批卡投递到触发命令的会话」（该要求原本由已成死代码的直接触发路径满足），也让操作员对自己手动触发的任务失去了「在哪下、结果回哪」的可预期性。

## What Changes

- 委托任务新增一等**来源会话**字段（`originChatId`，取命令事件的真实 `chatId`，与偏向 messageId、参与去重键的 `sourceRef` 解耦），随任务持久化。
- **审批卡回来源会话（恢复既有要求）**：命令触发的委托发帖，其内容审批卡投递到下命令的那个会话（私聊→私聊，群→那个群）；无来源会话的自动 / 排期 / 面板 / 边缘触发继续走默认审批群解析，**行为不变**。
- **发帖终态失败卡回来源会话（本变更的新策略，覆盖 per-team 路由）**：命令触发的委托发帖，其终态失败 / 部分完成结果卡投递到来源会话，而非账号团队群；**无来源会话**的自动 / 排期发帖结果卡仍按账号→团队群路由，**行为不变**。
- 诚实红线不动：投递失败绝不当成功（审批卡发送失败照旧记日志 + 保持诚实待审态）。
- **范围**：仅发帖（本次报障的两张卡）。手动 `/comment` 的终态结果卡目前仍按 per-team 路由（`feishu-notification-routing` 现有要求），本变更**不改**，作为已登记的后续对齐项（同形问题、不同代码路径 `CommentScheduler.postResultCard`）。
- **仅云端**（`aidcp-cloud`），边缘不动。

## Capabilities

### New Capabilities
<!-- 无新增能力，均为既有能力的要求修改 -->

### Modified Capabilities
- `user-delegated-tasks`: 新增要求——命令触发的委托任务 MUST 捕获并持久化来源会话，并把该会话作为其操作员向卡（审批卡、终态结果卡）的投递目标；无来源会话时回落既有默认 / 团队路由。
- `publish-pipeline`: 既有「手动飞书发帖审批卡投递到触发会话」要求**扩展到委托路径**——经委托任务触发的 `/publish`，其审批卡同样 MUST 投递到命令来源会话（补一条委托路径的回归场景，堵住本次这类回归）。
- `feishu-notification-routing`: 修改「账号维度业务结果卡走团队群」要求——**命令触发的发帖终态结果卡** MUST 改投来源会话（操作员触发、操作员收结果）；自动 / 排期等**无来源命令会话**的业务结果卡仍走账号→团队群，逐字不变。

## Impact

- 代码（`aidcp-cloud`）：`src/delegated-task/{types,parser,service,store}.ts`（新增 `originChatId` 字段 + `ALTER TABLE delegated_tasks ADD COLUMN IF NOT EXISTS origin_chat_id TEXT`）、`src/server.ts`（1551 捕获 `context.chatId`；3500 失败卡优先 `originChatId`）、`src/delegated-task/executors.ts`（`DelegatedPublishPort.triggerDelegated` 增 `manualApprovalChatId` + 调用点透传）、`src/publish-agent/publish-scheduler.ts`（`triggerDelegated` 透传，去掉写死的 `undefined`）。审批卡目标解析 `publish-executor.ts` 的 `resolveApprovalCardTarget` 不改（已支持 `manual_source`）。
- 数据：`delegated_tasks` 增一列 `origin_chat_id`（可空、幂等 `ADD COLUMN IF NOT EXISTS`，无迁移器、启动自建 schema）。旧任务该列为空 = 回落既有路由，零回归。
- 行为面：手动命令触发者的可预期性提升；per-team 路由对**自动**流量完全不变。外部客户群仍只收该账号入站通知与自动业务结果，MUST NOT 收到审批卡（审批卡本就不按账号路由）。
- 测试：委托 store 往返 `origin_chat_id`；`triggerDelegated` 把 `manualApprovalChatId` 透传到审批卡（`manual_source`）；`onTaskUpdated` 失败卡优先 `originChatId`。安全红线 `AC-PUB-*` / `AC-PROTO-*` 不受影响。
