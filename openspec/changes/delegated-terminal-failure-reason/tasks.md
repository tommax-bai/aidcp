# Tasks — delegated-terminal-failure-reason

> 单仓变更：全部落 `aidcp-cloud`（`../aidcp-cloud`，默认分支 `master`）。中控仓只回写本文件。
> 实装前先 `ls -d ../aidcp-cloud` 确认 sub-repo 存在（CLAUDE.md §0）。

## 1. aidcp-cloud — store 读路径

- [ ] 1.1 `src/delegated-task/store.ts` 的 `DelegatedTaskStore` 接口加 `listAttempts(taskId: string): Promise<DelegatedTaskAttempt[]>`（放在 `listUnsettledAttempts` 旁；**不动**后者）
- [ ] 1.2 PG 实现：`SELECT * FROM delegated_task_attempts WHERE task_id=$1 ORDER BY ordinal`，复用 `mapAttempt`（走现有索引 `idx_delegated_task_attempts_reconcile`）
- [ ] 1.3 memory 实现：按 `taskId` 过滤、按 `ordinal` 排序、`structuredClone` 返回（与既有方法同构）
- [ ] 1.4 单测：两实现对同一任务返回同序、同内容；已 settle 的 `failed`/`skipped` 都在结果里（对照 `listUnsettledAttempts` 对其返回 `[]`）

## 2. aidcp-cloud — 原因人话化（新文件、纯函数、无热点）

- [ ] 2.1 新建 `src/delegated-task/reason-humanize.ts`，导出 `humanizeAttemptReason(reason: string): string`
- [ ] 2.2 精确码白名单：`needs_persona_setup` / `candidate_record_missing` / `today_inspiration_unavailable` / `candidate_missing_during_reconcile` / `duplicate_target` / `empty_body` / `account_required`
- [ ] 2.3 前缀式白名单：`risk_status(` / `risk_denied(` / `executor_exception:`（保留括号内状态值与异常原文）
- [ ] 2.4 阶段级码（**精度上限，勿超**）：`candidate_terminal_<status>` / `publish_<status>` → 只表述到「稿件在发布派发阶段失败」层级，MUST NOT 渲染成具体边缘原因（spec「失败原因的精度不得超过已落库的证据」）
- [ ] 2.5 未命中一律**原样透传**；超长裁到 ~120 字符并保留原文可辨识片段
- [ ] 2.6 单测：已知码翻中文；中文句原样；未知码原样（红线用例）；`risk_status(warned)` 带出状态值；超长裁剪后仍可辨识

## 3. aidcp-cloud — finishBudget 追加原因

- [ ] 3.1 `src/delegated-task/worker.ts` 的 `finishBudget` 改为 `async` 读 `store.listAttempts`，取最后一条已 settle 且 `reason` 非空的 attempt
- [ ] 3.2 四支拼接（design D3）：从未真正开始（`failureCount===0 && skippedCount===attemptCount && attemptCount>0`）→ `；<N> 次均未真正开始：<人话>`；尝试后失败 → `；最后一次未成原因：<人话>`；混合 → `；最后一次未成原因：<人话>（共 <N> 次尝试）`；无原因可取 → **保持现状不补话**
- [ ] 3.3 既有前缀 `已达到最大尝试次数 / 已到截止时间；真实完成 N/M。` **原样保留**（追加而非替换）
- [ ] 3.4 `expireDueTasks` 的 deadline 终态（`worker.ts:286-289`）同样接入（它走 `complete(id, null, ...)` 无 token 路径，勿漏）
- [ ] 3.5 `finishCancelled` **不接**（用户主动取消、自知原因），确认无回归
- [ ] 3.6 单测：四支各一例；「全 deferred 耗尽」用例 MUST 断言文案不含任何暗示已发生平台写入的措辞（红线）

## 4. aidcp-cloud — 卡片顺手 additive

- [ ] 4.1 `src/server.ts` 的 `onTaskUpdated` 失败卡调用点（约 `:3550-3557`）补 `platformName: task.platform`（`cards.ts:161` platformLine 是现成条件片段）
- [ ] 4.2 确认 `delegatedTaskFailureReceipt`（`notification.ts:41`）无需改动——它已整段转发 `terminalOutcome.message`

## 5. 回归与验证

- [ ] 5.1 `cd ../aidcp-cloud && npm run test:acceptance`（先跑；安全红线 `AC-PUB-*` / `AC-RISK-*` 必须全过）
- [ ] 5.2 `npm test` 全量（重点核 `test/delegated-task/notification.test.ts:52-62` 与 `worker.test.ts` 的既有子串断言仍通过——本变更是追加）
- [ ] 5.3 `npm run typecheck`
- [ ] 5.4 用 `/verify` 或等价手段在本地驱一次委托发帖终态（memory store + 桩执行器返回 deferred/failed），肉眼确认 message 尾巴符合四支

## 6. 集成与部署

- [ ] 6.1 cloud 改动提交 + push `master`（commit message 末尾带 Co-Authored-By）
- [ ] 6.2 部署前先探 ECS 真实现状（并发方也在改同机；memory「Verify ECS state before deploy」）
- [ ] 6.3 `scripts/deploy-target dev --check` → 按 CLAUDE.md §5 安全序列部署 dev（备份 → rsync → restart → healthcheck → 失败回滚）。**绝不碰同机 isales**
- [ ] 6.4 回写本文件：每个 task 标 `[x]` + `<!-- <repo> <commit-sha> 备注 -->`，部署后追加 `<!-- <date> deployed -->`（sha 必须取自**已推送**提交，判据 `git merge-base --is-ancestor`）

## 7. 真机验收与收口

- [ ] 7.1 真机项登记 `docs/real-machine-acceptance-backlog.md`：dev 上触发一次注定失败的委托发帖（如占用中 / 风控非 normal 账号），确认飞书卡带出原因且措辞不误导
- [ ] 7.2 后继 change 登记（**勿静默**）：① `already_running` 类被误判可重试、1 秒热重试 2 秒烧光预算（`executors.ts:133` 死判断 + `publish-scheduler.ts` 形状，须串行）；② `failedAt` 落库抬精度天花板（`publish-log-store` + dispatcher）；③ `approvalCard.error` 从不被读致 `waiting_approval` 静默躺到 deadline
- [ ] 7.3 与并发 change `facebook-write-action-visibility` 对账（若其落到 `publish-log-store` / dispatcher 则与本变更互补，避免重复造）
- [ ] 7.4 `openspec validate delegated-terminal-failure-reason --strict` → archive（MODIFY `user-delegated-tasks`，若同期另有 change 同改该 capability，归档须串行）
