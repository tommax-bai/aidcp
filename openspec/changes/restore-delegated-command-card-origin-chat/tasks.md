# Tasks — restore-delegated-command-card-origin-chat

> 仅云端（`aidcp-cloud`），边缘不动。实装在 worktree，进度按 sub-repo 分节回写。
> 全部代码任务落于 cloud `f248a1e`（合 master + push）。dev 部署 2026-07-15、healthcheck 全过。

## 1. aidcp-cloud — 委托任务携带来源会话

- [x] 1.1 `src/delegated-task/types.ts`：`DelegatedTaskIntent` 增 `originChatId?: string`；`DelegatedTask` 增 `originChatId: string | null`。 <!-- aidcp-cloud f248a1e -->
- [x] 1.2 `src/delegated-task/store.ts`：建表 SQL 后追加幂等 `ALTER TABLE delegated_tasks ADD COLUMN IF NOT EXISTS origin_chat_id TEXT;`；`TaskRow` 增 `origin_chat_id`；`mapTask` 映射 `originChatId`；PG `createDraft` INSERT 增列 `$19` + `MemoryDelegatedTaskStore` 同步。 <!-- aidcp-cloud f248a1e --> <!-- 2026-07-15 deployed dev：origin_chat_id 列已在 delegated_tasks 上（schema 启动自建） -->
- [x] 1.3 `src/delegated-task/parser.ts`：`ParseDelegatedTextOptions` 增 `originChatId`；`baseIntent` 透传（所有 intent 经此，含 legacy_command）。 <!-- aidcp-cloud f248a1e -->
- [x] 1.4 `src/delegated-task/service.ts`：`createFromText(text, { sourceRef?, originChatId? })` 接收并传入 `parseDelegatedText`。 <!-- aidcp-cloud f248a1e -->
- [x] 1.5 `src/server.ts:1551`：`createFromText(text, { sourceRef: messageId ?? chatId, originChatId: context?.chatId })`。 <!-- aidcp-cloud f248a1e -->

## 2. aidcp-cloud — 审批卡回来源会话（走既有 manual_source）

- [x] 2.1 `src/delegated-task/executors.ts`：`DelegatedPublishPort.triggerDelegated` opts 增 `manualApprovalChatId?`；调用点传 `task.originChatId ?? undefined`。 <!-- aidcp-cloud f248a1e -->
- [x] 2.2 `src/publish-agent/publish-scheduler.ts`：`triggerDelegated` opts 增 `manualApprovalChatId?`；透传给 `doTrigger`（替换写死的 `undefined`）。`resolveApprovalCardTarget` 未改（已支持 `manual_source`）。 <!-- aidcp-cloud f248a1e -->

## 3. aidcp-cloud — 终态失败卡优先来源会话

- [x] 3.1 `src/server.ts`（`onTaskUpdated`）：`const chatId = task.originChatId?.trim() || await resolveAccountChatId(task.accountId);`；发送日志标明 sink（`origin` / `account_team`）。 <!-- aidcp-cloud f248a1e -->

## 4. aidcp-cloud — 测试与校验

- [x] 4.1 委托 service 单测：`createFromText` 带 `originChatId` → 任务 + store 往返回同值，且与 `sourceRef` 解耦；非命令任务 `originChatId=null`。 <!-- aidcp-cloud f248a1e test/delegated-task/service.test.ts -->
- [x] 4.2 executor 单测：`triggerDelegated` 收到 `manualApprovalChatId=originChatId` 透传；`originChatId` 空时省略该字段。 <!-- aidcp-cloud f248a1e test/delegated-task/executors.test.ts -->
- [ ] 4.3 失败卡取址（`onTaskUpdated` 内联闭包）——用真机验收覆盖（登记 5.3），不为 `a?.trim() || b` 一行硬起 server 全量测试桩（避免过度设计）。 <!-- 代码级由 typecheck + 逻辑显然性保证 -->
- [x] 4.4 `npm run test:acceptance`（54/54）→ `npm test`（2271 pass / 0 fail / 5 skip）→ `npm run typecheck`（clean）全过；`AC-PUB-*` / `AC-PROTO-*` / `AC-RISK-*` 无回归。 <!-- aidcp-cloud f248a1e -->

## 5. 集成 / 部署 / 归档

- [x] 5.1 worktree 提交 `f248a1e`；fetch + rebase（0 behind）；ff 合并回 `aidcp-cloud` master；push。 <!-- aidcp-cloud f248a1e -->
- [x] 5.2 部署 dev（clean `git archive` 快照 rsync，避开脏 checkout；备份 `cloud.bak.20260715-235312.tar.gz` + `.env.bak`；restart；healthcheck：active + 8787 + 飞书长连接 + PG select 1 + `origin_chat_id` 列已建）。 <!-- 2026-07-15 deployed dev -->
- [x] 5.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md` 簇 86（86.14–86.18：私聊/群 `/publish` 卡回来源会话、自动不受影响、`/comment` 对齐为后续项）。 <!-- 2026-07-15 registered -->
- [x] 5.4 `openspec validate restore-delegated-command-card-origin-chat --strict`（已过）→ 归档并入主 spec（`publish-pipeline` / `feishu-notification-routing` MODIFIED、`user-delegated-tasks` ADDED）。 <!-- 2026-07-15 archived -->
- [x] 5.5 后续对齐项：手动 `/comment` 终态结果卡回来源会话——已在 proposal / spec / backlog 86.18 显式登记。 <!-- registered -->
- [ ] 5.4 `openspec validate restore-delegated-command-card-origin-chat --strict`（已过）→ 归档并入主 spec。
- [ ] 5.5 后续对齐项：手动 `/comment` 终态结果卡回来源会话（同 `originChatId` 透传进 `CommentScheduler.postResultCard` 取址）——已在 proposal / spec / backlog 显式登记。
