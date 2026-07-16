## Why

委托任务终态失败卡只会说「为什么停」，从不说「为什么没成」。运营在飞书收到的原文是：

> ❌ 发帖任务未成
> **指令**：`发帖`　**账号**：Dennis Scott
> 已达到最大尝试次数；真实完成 0/1。

「已达到最大尝试次数」是**预算耗尽的记账**，不是失败原因。运营据此无法判断该重试、该改配置、还是该等——只能来问工程。

**原因其实一直存在，只是终态那句话从不去读它**：每次尝试的原因（编排器 `failureReason` / 风控 `risk_status(...)` / 「已有一轮发帖编排在运行中」等）在尝试 settle 时就写进了 `delegated_task_attempts.reason` 列（`store.ts:92` DDL、`store.ts:452-455` 写入），双实现（PG / memory）同构。但 `worker.ts:263-270` 的 `finishBudget` 入参只有 `task` / `token` / 字面 reason，作用域内关于「为什么」的全部信息 = 4 个裸计数器（`types.ts:31-36`），**零 reason 字符串**——它凭空另拼了一句模板，卡片（`notification.ts:41` → `server.ts:3550` → `cards.ts:172`）只是忠实转发。

**这是委托层的能力缺口，不是原因不存在**——对照组：老的同步 `/publish` 命令路径打印 `原因：${o.failureReason}`（`server.ts:1623`）。同一个失败，走老命令看得见原因，走委托任务只剩一句空话。这违反「绝不静默失败」红线的精神：卡发出来了，但等于没说。

## What Changes

- 委托任务**终态失败的 `terminalOutcome.message` 追加真实原因**（取最后一条已 settle 且 reason 非空的 attempt），覆盖 `max_attempts` / `deadline` 两支预算终态。前缀 `已达到最大尝试次数；真实完成 0/1。` 原样保留（不破既有语义与测试）。
- **区分「失败了」与「压根没开始」**：`deferred` 结果同样烧尝试次数（`markAttemptDispatched` 在 `execute()` 之前无条件跑，`worker.ts:145` vs `:150`，且它就是 `attemptCount++` 处），settle 成 `skipped` 而非 `failed`。因此 `failureCount === 0 && skippedCount === attemptCount` 这一支 MUST 明说「N 次均未真正开始：<原因>」，MUST NOT 让人以为发过了。
- 新增纯函数 `humanizeAttemptReason`：机器码→人话白名单（含 `risk_status(...)` / `risk_denied(...)` / `executor_exception:` 三个前缀式）；中文原样透传；**未命中原样透传**（绝不猜、绝不美化成听着像诊断其实是编的话）；超长裁剪并保留原文尾。
- store 接口加 `listAttempts(taskId)` + PG / memory 两实现（既有 `listUnsettledAttempts` 按构造只返回 `prepared`/`dispatched`，对已 settle 的 failed / skipped 恒返回 `[]`，恰好排除掉要读的那些）。**不动** `listUnsettledAttempts`。
- 顺带 additive：失败卡补 `platformName`（`task.platform` 就在调用点手边，`cards.ts:161` 的 platformLine 是现成条件片段）。

**诚实边界（写进 spec，不是备注）**：Facebook 派发期的细节失败（`editor_not_found` / composer 失败 / `content_too_long` / `all_images_failed`）**在 DB 里就已经塌成一个 status 枚举**——`command-sequencer` 的 `failedAt {seq,kind,error}` 从不落库，`publish-log-store.updateStatus` 只写状态（`publish-log-store.ts:281-283`）。本变更能给到的上限是「稿件在发布派发阶段失败」+ recordId，**MUST NOT** 在卡上渲染成具体边缘原因。抬高这个天花板是另一件事（见 Impact 的后继项）。

**不做（显式切走）**：`executors.ts:133` 那条**永不命中的判断**——它想把 `publish_capacity` / `publish_busy` / `already_running` 归为「稍后重试」，但检查的是 `outcome.result === 'blocked'`，而这三者由 `tryClaim` 产出、被 scheduler 包成 `result:'triggered'` + `status:'skipped'`（`publish-scheduler.ts:504-514`），**从不是 `blocked`**。后果：并发抢占落到 `executors.ts:153` 被判 `failed(retryable:true)` → `worker.ts:258-260` 以 `now+1_000` 热重试 → **默认 `maxAttempts=2`（`parser.ts:61`）约 2 秒烧光 → 就是本投诉那张卡**。作者本意显然是 defer。它是本投诉的**第一放大器**，但要动的 `publish-scheduler.ts` 属热点文件、按并行纪律须串行——登记为后继 change，**不静默留着**。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `user-delegated-tasks`: 「所有任务必须有有界尝试、截止时间与诚实部分完成」增补——零成功终态 MUST 携带真实失败原因而非仅预算记账；且 MUST 区分「尝试后失败」与「从未真正开始」；未知原因码 MUST 原样透传、MUST NOT 编造或美化。

## Impact

- **`aidcp-cloud`**（唯一代码仓）
  - `src/delegated-task/worker.ts`：`finishBudget` 读 attempts 并追加原因尾巴。
  - `src/delegated-task/store.ts`：接口 + PG + memory 加 `listAttempts`。**零 DDL / 零迁移**（`reason` 列已存在；`terminal_outcome` 是 JSONB）。
  - `src/delegated-task/reason-humanize.ts`：**新文件**，纯函数、无副作用、纯单测，避开全部热点文件。
  - `src/server.ts`：失败卡调用点补 `platformName`（1 行 additive）。
  - 测试：`test/delegated-task/{notification,worker}.test.ts` 现有断言为子串匹配（`/已达到最大尝试次数/`），本变更是**追加而非替换**，应仍通过；新增 humanize 与 finishBudget 四支用例。
- **不碰**：边云协议、风控状态机、角色注册、`publish-scheduler.ts`、`cards.ts` 卡模板形状（`buildCommandResultCard` 的 `elements[]` 是硬编码单元素，另有 8 个调用点，改形状会波及全产品所有指令回执）。
- **注意 `delegatedTaskNotificationFingerprint`**（`notification.ts:3-12`）`JSON.stringify` 整个 `terminalOutcome` → message 变化即指纹变化，属期望行为（终态只发一次，无重复风险）。
- **fleet 并发**：`delegated-executor-operator-authority-parity` 已于 `cd185df` 归档 → `notification.ts` / `server.ts` onTaskUpdated 现无主。同批新建的 `facebook-write-action-visibility` 尚为空壳，若其落到 `publish-log-store` / dispatcher 落库，则与本变更**互补**（它抬天花板、本变更修管道），需在其成文后对账。

### 后继 change（登记，勿静默）

1. **`already_running` 类误判为可重试**（第一放大器，见上）：`executors.ts:133` 死判断 + `publish-scheduler.ts` 形状，须串行。
2. **`failedAt` 落库**：`publish-log-store` + dispatcher——抬高失败精度天花板的真活。
3. **`approvalCard.error` 从不被读**（`executors.ts:131-154`）：审批卡发送失败的稿件会在 `waiting_approval` 静默躺到 deadline（`notification.ts` 对该态返回 null，委托层也不发卡）。
