## 1. aidcp — 控制仓文档与盘点范围

- [ ] 1.1 在 `docs/cloud-service-decomposition-proposal.md` §5.2「候选版本和审批不能隐式漂移」后补一段：审批授权 MUST 是 `aidcp-api` 单写的持久记录，至少含候选版本标识、决策人、决策时间、决策渠道、`envKey`、`executionTarget` 与决策本身；MUST NOT 以本机文件、本机内存或共享路径承载。
- [ ] 1.2 **降级为核对，MUST NOT 再新增条目**：本项写于定稿整合之前，§6.4 禁止清单**现已是 8 条**，第 8 条逐字为「用共享文件系统、本机路径、本机临时目录或数据库 advisory lock 传递跨服务的授权、锁或业务事实」，已覆盖本 change 的形态（并在其下以「实例一」逐点列出了审批信号文件的读写方与失效形态）。本项的义务改为：核对该条措辞确已覆盖，如有缺口再提最小增补；照原文再加一条会产出重复条目。
- [ ] 1.3 **降级为核对，MUST NOT 再新增类别**：定稿 §12 阶段 0 的「状态盘点清单」**现已是六类表**（表 / 进程内内存事实 / 本机文件信号 / 本机锁与 PG advisory lock / EventBus 事件 / 常驻定时任务），本 change 坐实的四类通道已全部在内。本项的义务改为：核对六类已覆盖，并把本 change 新坐实的实例填进对应行。
- [ ] 1.4 **仍是活任务**（定稿六类表现只有「类别 / 盘点内容 / 失效方向」三列）：在 §12 阶段 0 补一句盘点行的必填字段：引用点 `文件:行` → 拆分后归属服务 → 是否跨服务 → 替代机制 → 不替代会怎样失效（必须写出失效方向是静默还是报错）。
- [ ] 1.5 在 §12 阶段 4 与「删除对连接注册表、RiskController 和内容 Store 的直接读取」并列增一条：把审批授权的文件实现替换为持久授权记录 + `PublishApproved` 命令，并明确 edge 侧文件闸是随迁还是就地废弃。
- [ ] 1.6 在 §14 验收红线增一条：审批通过后下发侧不可用时，用户 MUST 看到明确的待下发或失败态，MUST NOT 呈现为与「待审批」不可区分的静默停滞。
- [ ] 1.7 在仓内产出阶段 0 盘点表初版（六类，至少覆盖本 change 已坐实的：审批信号文件、`interaction-env:<envKey>` advisory lock、`interaction-store.ts:409` / `:989` 两把单服务内锁、常驻定时任务）。**常驻定时任务的计数 MUST 同时给出两个数、且 MUST 在实施当天重测**：定稿 §4.6.5 / §12 阶段 0 的「14」是逐个定归属的**宿主**数（其第 13、14 项并非 `setInterval`），本稿的「24」是 `grep -rn setInterval src` 的**调用点**数（2026-07-22 实测在 23–24 之间漂动）。两者不是一回事，只写一个数会让盘点者提前收工。
- [ ] 1.8 影子写关闭后更新 `CLAUDE.md` §4 中「发布审批信号文件两端契约路径必须一致」的表述，改为「授权以持久记录为准，两端不得依赖同机路径」。

## 2. aidcp-cloud — 持久授权记录与单写出口（未来 api 域）

- [ ] 2.1 新增迁移，建 `publish_approval_decision` 表：`request_id`、`revision`、`subject_kind`、`candidate_ref`、`content_version`、`approved`、`decided_by`、`decided_via`、`decided_at`、`env_key`、`execution_target`、`frozen_payload`、`dispatch_state`、`dispatch_blocked_reason`、`dispatch_state_at`、`void_reason`；主键 `(request_id, revision)`；`CREATE UNIQUE INDEX ... (request_id) WHERE dispatch_state <> 'void'`；`execution_target` 加 `CHECK IN ('dev','ol')`。
- [ ] 2.2 新增 `src/publish-agent/publish-approval-store.ts`（或等价位置）作为该表唯一写者，暴露 `record(decision)`、`readActive(requestId)`、`listPendingDispatch(executionTarget, limit)`、`markDispatching(requestId, revision)`、`markConsumed(...)`、`void(requestId, reason)`、`setBlockedReason(requestId, reason|null)`。
- [ ] 2.3 `record()` 用 `INSERT ... ON CONFLICT (request_id) WHERE dispatch_state <> 'void' DO NOTHING RETURNING *` 实现 first-writer-wins：返回行 → `{written:true}`；返回空 → 读回活跃行 → `{alreadyDecided:<approved>}`。返回类型保持与 `ApprovalWriteResult` 同形，MUST NOT 返回 `published`。
- [ ] 2.4 `void()` 只做状态迁移（`dispatch_state='void'` + `void_reason`），MUST NOT 删行；后续同 `requestId` 的授权以 `revision+1` 插入。
- [ ] 2.5 `execution_target` 由服务端从本机 `AIDCP_DEPLOY_ENV` 注入，MUST NOT 取自请求体；缺失或非法时写入 MUST 失败并返回可区分错误。
- [ ] 2.6 把 `src/feishu/ws-receiver.ts:151` 的 `writeApprovalSignal` 改为委托到 `PublishApprovalStore.record()`，保留 `ApprovalWriteResult` 形状与 `parseApprovalActionValue` 入口不变；保留 `getApprovalSignalPath` 仅供影子写使用并标 `@deprecated`。
- [ ] 2.7 影子写：`record()` 成功后 best-effort 写同路径同格式文件，由 `AIDCP_PUBLISH_APPROVAL_LEGACY_SIGNAL_FILE`（默认 `true`）控制；写失败只记日志，MUST NOT 影响 `record()` 的返回值或抛出。
- [ ] 2.8 五个写入口全部改经同一 Store：飞书回调（`src/feishu/ws-receiver.ts:321`）、面板路由（`src/panel/panel-server.ts:1302`）、客户端内审批（`src/server.ts:2815`）、委托任务批准 / 拒绝（`src/server.ts:3991`、`:4005`）、排期 `auto_approve` 预授权。每处必须传真实 `decided_by` 与 `decided_via`，MUST NOT 用常量占位。
- [ ] 2.9 `src/panel/panel-server.ts:1246`-`:1252` 的 `requestId` 白名单保留，注释与拒因改为「记录主键与 URL 路径段的受控字符集」，删除「参与文件落盘路径拼接」的表述。

## 3. aidcp-cloud — 读侧改造与跨服务合同形状（未来 automation 域）

- [ ] 3.1 新增内部查询接口（阶段 1 用进程内适配器，形状按未来 HTTP）：`GET /internal/publish-approvals/{requestId}` 返回 `{approved, contentVersion, dispatchState, dispatchBlockedReason, envKey, executionTarget}`；不存在返回 404。
- [ ] 3.2 新增 `GET /internal/publish-approvals?dispatchState=pending_dispatch&executionTarget=<target>`，只返回本机 target 的活跃行。
- [ ] 3.3 新增 `POST /internal/publish-approvals/{requestId}/void`，reason 限枚举 `version_stale` / `edge_offline` / `preempt_exhausted` / `lease_unconfirmed`；枚举外拒绝。
- [ ] 3.4 `src/server.ts:2076` 的 `readPublishApproval`、`:2088` 的 `isPublishApproved`、`:2093` 的 `voidApprovalSignal` 三个闭包改为调用 3.1 / 3.3 的接口，删除 `readFile` / `unlink` 实现。
- [ ] 3.5 `src/publish-agent/publish-dispatcher.ts:453` 的下发前复核改读持久记录；查询超时 / 不可达 MUST 视为未授权、不下发、写 `dispatch_blocked_reason='approval_unreadable'`，MUST NOT 写任何终态。
- [ ] 3.6 `src/publish-agent/publish-dispatcher.ts:370`-`:378` 的兜底扫描改为调 3.2 批量拉取，删除「遍历 `pending_approval` id 逐个读文件」的实现。
- [ ] 3.7 `publish-dispatcher.ts:275`、`:464`、`:641` 三处作废改调 3.3，各传对应 reason。
- [ ] 3.8 `src/agents/comment-approval-gate.ts:218` 的 `isApproved` 轮询改读持久记录；查询失败 MUST 计为「未授权」继续等待到超时并 `comment.skipped{reason:'approval_timeout'}`，MUST NOT 与 `approval_rejected` 混同。
- [ ] 3.9 `src/server.ts:2720` 的 `triggerPublishDispatchOnApprove` 进程内直调改为：api 侧在 `record()` 同事务写 Outbox `PublishApproved{requestId, candidateRef, contentVersion, envKey, executionTarget}`；automation 侧 Inbox 按 `requestId+revision` 去重后触发一次 `dispatch()`。既有幂等闸（`inFlight` / status / 授权复核）保持不变。
- [ ] 3.10 `src/publish-agent/client-publish-approval.ts:91` 的 `readApproval` 改读持久记录，`already_decided` / `version_stale` 拒因语义保持不变。

## 4. aidcp-cloud — 待下发态与诚实降级

- [ ] 4.1 `record(approved=true)` 落库即置 `dispatch_state='pending_dispatch'`，同时记录 `decided_at`。
- [ ] 4.2 automation 领取执行时置 `dispatching`，序列成功后置 `consumed`；被抢占保持 `pending_dispatch` 并保留授权（对应 `publish-dispatcher.ts:610` 既有分支）。
- [ ] 4.3 把既有五类下发阻塞映射到 `dispatch_blocked_reason`：`edge_offline_waiting`（`publish-dispatcher.ts:485`）、`browser_slot_waiting`（`:638`）、`breaker_open`（`:434`）、`captcha_paused`（`:508`）、`approval_unreadable`（3.5）。阻塞解除时 MUST 清空该字段。
- [ ] 4.4 新增常驻检查：`pending_dispatch` 且 `dispatch_blocked_reason IS NULL` 超过阈值（`AIDCP_PUBLISH_PENDING_DISPATCH_ALERT_MS`，默认 15 分钟）即发飞书告警并写 `alerts`；有阻塞原因的不告警。该 worker MUST 按本机 `execution_target` 过滤。
- [ ] 4.5 `src/panel/publish-stage-lifecycle.ts:326`-`:329` 的阶段判定改用持久 `dispatch_state`，删除对进程内在途集合的依赖；`pending_approval` + `pending_dispatch` MUST 呈现为「已批准·待下发」，与「待审批」可区分。
- [ ] 4.6 面板发布队列与待审详情投影增量返回 `dispatchState`、`dispatchBlockedReason`、`decidedAt`、`waitingMs`。
- [ ] 4.7 `src/comm/protocol.ts` 的 `PublishApprovalActionResultPayload` 增量可选字段 `dispatchState?: 'pending_dispatch' | 'dispatching' | 'blocked'` 与 `dispatchBlockedReason?: string`；`state` 的既有取值 MUST NOT 变更。改动与 edge 同名文件逐字一致，并同步 `docs/protocol.md`（该消息按信封 id 应答，不进主动命令白名单）。

## 5. aidcp-cloud — advisory lock 替换

- [ ] 5.1 产出 `pg_advisory_*` 引用点盘点表：`src/client-auth/client-user-store.ts:619`、`:1468`、`:2001`、`:2128`（api）、`src/interactions/interaction-store.ts:339`（automation）、`:409`、`:989`（单服务内），每行标注 key 命名空间、归属服务、是否跨服务。
- [ ] 5.2 新增内部端点 `PUT /internal/environments/{envKey}/auth-state`，由 api 侧在事务内 `SELECT ... FROM client_environments WHERE env_key=$1 FOR UPDATE` 后写 `interaction_auth_state`。
- [ ] 5.3 `src/interactions/interaction-store.ts:333` 的 `upsertAuthStatus` 改经 5.2 的端点，删除该处 `interaction-env:` advisory lock。
- [ ] 5.4 `src/client-auth/client-user-store.ts` 四处 `interaction-env:` 改为对 `client_environments` 按 `env_key` 升序取行锁；`:1468`、`:2001` 既有的排序取锁顺序 MUST 保持不变（死锁序不回归）。
- [ ] 5.5 新增静态检查（CI 或测试）：源码中每个 advisory lock key 前缀 MUST 只被单一服务边界目录引用，跨边界引用即失败；`interaction-store.ts:409`、`:989` 两把单服务内锁在检查白名单中显式登记。

## 6. aidcp-edge — 文件闸降级与协议同步

- [ ] 6.1 `src/publish/approval-gate.ts:95` 的 `waitForPublishApproval` 增显式启用门：同时要求 `AIDCP_PUBLISH_APPROVAL_SIGNAL_DIR` 与 `AIDCP_DEV_PUBLISH=1`，否则立即返回 `{ok:false, reason:'approval_gate_disabled'}`，MUST NOT 静默通过、MUST NOT 静默等待到超时。
- [ ] 6.2 更新 `src/publish/approval-gate.ts:36`-`:41` 的注释：该闸是本机开发夹具，不是跨服务契约；生产人审在云端完成。
- [ ] 6.3 新增回归断言：生产算子表内 `publish.request` 无处理器（对照 `src/client/operation-registry.ts:104` 的墓碑与 `src/client/edge-client.ts:797` 的 `handler_unavailable` 分支）。
- [ ] 6.4 `src/comm/protocol.ts` 同步 4.7 的增量字段，与 cloud 逐字一致；`npm run typecheck` MUST 通过。
- [ ] 6.5 客户端内审批的稿件卡在收到 `dispatchState='pending_dispatch'` 时显示「已批准·待下发」；字段缺省（旧云端）时行为 MUST 与今天一致，MUST NOT 显示为失败。

## 7. aidcp-console — 待下发态呈现

- [ ] 7.1 发布队列与待审详情的 API 类型增量加 `dispatchState`、`dispatchBlockedReason`、`decidedAt`、`waitingMs`。
- [ ] 7.2 已批准待下发的行 MUST 与待审批行视觉可区分，并展示阻塞原因与等待时长；无阻塞原因且超阈值时展示告警标记。
- [ ] 7.3 字段缺省时回落为今天的呈现，MUST NOT 整页白屏（对齐 console 与 cloud 枚举漂移纪律）。

## 8. 测试与验收

- [ ] 8.1 cloud：`record()` 并发写测试——两个并发授权只有一个 `written:true`，另一个得 `alreadyDecided`，表内活跃行恰好一条。
- [ ] 8.2 cloud：作废后重新授权测试——`void()` 后同 `requestId` 可再次 `written:true`，历史轮次保留且不被活跃读接口返回。
- [ ] 8.3 cloud：授权查询不可达测试——下发前复核超时时不下发、不写终态、`dispatch_blocked_reason='approval_unreadable'`。
- [ ] 8.4 cloud：待下发告警测试——无阻塞原因超阈值发告警，有阻塞原因不发。
- [ ] 8.5 cloud：`execution_target` 隔离测试——非本机 target 的 `pending_dispatch` 行不被兜底扫描拉取。
- [ ] 8.6 cloud：advisory lock 替换后的串行测试——首次登录态写入与客户解绑对同一 `envKey` 仍观察到单一串行顺序。
- [ ] 8.7 cloud + edge：`publish-approval-contract` 验收改判据——从「同一文件路径」改为「同一 `requestId` + 同一 `contentVersion` 的授权判定」；edge 侧断言改为「生产路径无文件依赖」。`AC-PUB-*` MUST 仍全过。
- [ ] 8.8 cloud + edge：`npm run test:acceptance` → `npm test` → `npm run typecheck` 三步按序全过（协议改动的既定回归纪律）。
- [ ] 8.9 console：待下发态呈现与字段缺省回落的聚焦测试。
- [ ] 8.10 端到端（dev）：审批通过后停掉下发侧，确认界面在阈值内显示「已批准·待下发」+ 阻塞原因，阈值后收到告警；恢复下发侧后稿件正常发出，全程无重复发布。
- [ ] 8.11 关闭影子写前的验证：确认无任何读者读取 `/tmp/aidcp-publish-approve-*`，dev 与 ol 各观察满一个发布周期；关闭动作单独提交、可单独回滚。
