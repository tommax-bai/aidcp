# Tasks — restore-delegated-command-card-origin-chat

> 仅云端（`aidcp-cloud`），边缘不动。实装在 worktree，进度按 sub-repo 分节回写。

## 1. aidcp-cloud — 委托任务携带来源会话

- [ ] 1.1 `src/delegated-task/types.ts`：`DelegatedTaskIntent` 增 `originChatId?: string`；`DelegatedTask` 增 `originChatId: string | null`。
- [ ] 1.2 `src/delegated-task/store.ts`：建表 SQL 后追加幂等 `ALTER TABLE delegated_tasks ADD COLUMN IF NOT EXISTS origin_chat_id TEXT;`；`TaskRow` 增 `origin_chat_id: string | null`；rowToTask 映射 `originChatId: r.origin_chat_id`；`createDraft` INSERT 增列与参数（`input.originChatId ?? null`）。
- [ ] 1.3 `src/delegated-task/parser.ts`：把 `opts.originChatId` 透传进构建出的 intent（与 `sourceRef` 并列，仅在有值时带上）。
- [ ] 1.4 `src/delegated-task/service.ts`：`createFromText(text, opts?: { sourceRef?; originChatId? })` 接收并传入 `parseDelegatedText` / intent；`createDraft` 携带 `originChatId` 落库。
- [ ] 1.5 `src/server.ts:1551`：`createFromText(text, { sourceRef: context?.messageId ?? context?.chatId, originChatId: context?.chatId })`（来源会话专取 `chatId`，不掺 messageId）。

## 2. aidcp-cloud — 审批卡回来源会话（走既有 manual_source）

- [ ] 2.1 `src/delegated-task/executors.ts`：`DelegatedPublishPort.triggerDelegated` opts 增 `manualApprovalChatId?: string`；调用点（`:300`）传 `task.originChatId ?? undefined`。
- [ ] 2.2 `src/publish-agent/publish-scheduler.ts`：`triggerDelegated` opts 增 `manualApprovalChatId?`；透传给 `doTrigger`（替换写死的 `undefined` 第 5 位参）。`resolveApprovalCardTarget`（`publish-executor.ts`）**不改**——已支持 `manual_source`。

## 3. aidcp-cloud — 终态失败卡优先来源会话

- [ ] 3.1 `src/server.ts:3500`（`DelegatedTaskWorker.onTaskUpdated`）：`const chatId = task.originChatId?.trim() || await resolveAccountChatId(task.accountId);`（补集式：非空才覆盖团队路由）。发送日志标明 sink（`origin` / `account_team`）。

## 4. aidcp-cloud — 测试与校验

- [ ] 4.1 委托 store 单测：`createDraft` 带 `originChatId` → `get` 往返回来同值；缺省为 `null`。
- [ ] 4.2 executor / scheduler 单测：`triggerDelegated` 收到非空 `manualApprovalChatId` 时透传到 `doTrigger` → 审批卡目标解析为 `manual_source`；缺省仍 `default_chat`。
- [ ] 4.3 失败卡取址单测：任务持 `originChatId` → 失败卡投递到该会话；`originChatId` 为空 → 回落 `resolveAccountChatId`（团队群），零回归。
- [ ] 4.4 `npm run test:acceptance` → `npm test` → `npm run typecheck` 全过；安全红线 `AC-PUB-*` / `AC-PROTO-*` / `AC-RISK-*` 不回归。

## 5. 集成 / 部署 / 归档（主 checkout）

- [ ] 5.1 worktree 内提交；fetch + rebase 最新 `master`；ff 合并回 `aidcp-cloud` master；push。
- [ ] 5.2 部署 dev（安全序列：`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck）；schema `ADD COLUMN` 随启动自建生效。
- [ ] 5.3 真机验收项登记 `docs/real-machine-acceptance-backlog.md`：私聊 `/publish` 审批卡 + 终态卡回私聊；管理群 `/publish` 回该群；自动 / 排期发帖结果卡仍进账号团队群。
- [ ] 5.4 `openspec validate restore-delegated-command-card-origin-chat --strict` → 攒批归档时并入主 spec。
- [ ] 5.5 后续对齐项登记：手动 `/comment` 终态结果卡回来源会话（同 `originChatId` 透传进 `CommentScheduler.postResultCard` 取址）。
