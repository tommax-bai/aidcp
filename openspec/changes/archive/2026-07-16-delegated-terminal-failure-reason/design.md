## Context

飞书委托发帖失败卡只有一句预算记账（「已达到最大尝试次数；真实完成 0/1。」），不含任何失败原因。

**原因数据一路都在，只在最后一跳被丢**：

| 环节 | 位置 | 状态 |
| --- | --- | --- |
| 编排器产出原因 | `publish-orchestrator.ts:117`（`Pipeline aborted by <role>: <err>` / 超时 / `选题判定不发布：<reason>`） | 有 |
| scheduler 透传 | `publish-scheduler.ts:574` → `failureReason` | 有 |
| 执行器接住并写入 attempt | `executors.ts:153` → `finishAttempt({reason})` | 有 |
| **持久化** | `delegated_task_attempts.reason TEXT`（DDL `store.ts:92`，写入 `store.ts:452-455`；memory 实现同构 `store.ts:720-733`） | **有** |
| 终态拼 message | `worker.ts:263-270` `finishBudget` | **丢** |
| 卡片渲染 | `notification.ts:41` → `server.ts:3550` → `cards.ts:172` | 忠实转发那句空话 |

`finishBudget` 的入参只有 `task` / `token` / 字面 reason，作用域内关于「为什么」的全部信息 = 4 个裸计数器（`types.ts:31-36`）。attempt 的 `reason` 写入后**没有任何路径把它投影回 task**：`DelegatedTask` 无 `lastError` / `lastReason` 字段（`types.ts:46-85`），`currentStep` 还被 `complete()` 置 NULL。

**对照组坐实这是能力缺口而非数据缺失**：老的同步 `/publish` 命令打印 `原因：${o.failureReason}`（`server.ts:1623`）。

**约束**：
- `buildCommandResultCard`（`cards.ts:153-175`）**不是行可扩展的**——`elements[]` 是硬编码单元素数组，另有 8 个调用点（server.ts 多处、`publish-executor.ts:411`、`ws-receiver.ts:248`）。改模板形状 = 波及全产品所有指令回执。
- `CommandResult.card?` 逃生舱（`types.ts:157`）**在此路径无效**——只有 `ws-receiver.ts:248` 认，委托失败路径直调 builder。
- store 唯一的 attempt 列举方法 `listUnsettledAttempts` 按构造 `WHERE status IN ('prepared','dispatched')`，对已 settle 的 failed / skipped **恒返回 `[]`**——恰好排除掉要读的那些。
- 云端测试在**镜像 `test/` 树**（grep `src/` 找测试是假阴性）。

## Goals / Non-Goals

**Goals:**

- 预算耗尽的零成功终态在飞书卡上说清「为什么没成」，而非只说「为什么停」。
- 区分「尝试后失败」与「从未真正开始」——后者是本投诉的实型，且最易被误读成「已经发过了」。
- 机器码翻人话，但**未知码原样透传**：宁可让运营看见 `publish_needs_review`，也不给一句听着专业却是编的话。
- 零渲染层形状改动、零 DDL、零协议改动、不碰热点文件。

**Non-Goals:**

- **不**抬高失败精度天花板。FB 派发期分步失败（`command-sequencer` 的 `failedAt {seq,kind,error}`）从不落库，`publish-log-store.updateStatus` 只写状态枚举（`publish-log-store.ts:281-283`）→ 本变更上限是「派发阶段失败」+ recordId。落库是后继 change。
- **不**修 `executors.ts:133` 的死判断（本投诉第一放大器，见 proposal）——须动 `publish-scheduler.ts` 热点文件，串行做。
- **不**做原因聚类 / 统计 / 结构化原因列表。
- **不**改卡片模板形状、不改评论家族的通知语义。

## Decisions

### D1：注入点 = `terminalOutcome.message` 尾巴，不是卡上新增结构化行

**选择**：`finishBudget` 在既有 message 后追加原因，前缀原样保留。

**理由**：`message` 是自由 lark_md 且位于卡正文末尾（`cards.ts:172`），内含 `\n` 天然渲染多行（既有调用者已这么用）。零渲染层改动，`notification.ts:41` 已把它整段转发。

**否决 A：`DelegatedTerminalOutcome` 加 `attemptReasons[]` + 卡上新增「原因」独立行。**
① 卡模板不是行可扩展的，改它波及另外 8 个调用点的全部指令回执；② 加了也**看不见**——渲染端只读 `.message`（`notification.ts:41,52`、`delegated-task-card.ts:94-95`）；③ 评论家族 `max_attempts` 根本不发委托层卡（`notification.ts:48-51`），结构化字段在那边不可见；④ 动 fingerprint。收益 = 一条 message 尾巴，代价 = 三个热点文件 + 全产品卡模板。

### D2：数据源 = attempt 表，新增 `listAttempts`

**选择**：store 接口加 `listAttempts(taskId): Promise<DelegatedTaskAttempt[]>`（PG `ORDER BY ordinal`，走现有索引 `idx_delegated_task_attempts_reconcile(task_id,status,prepared_at)`；memory 同构）。**不动** `listUnsettledAttempts`。

**理由**：attempt 表是**唯一双实现同构、且真带 reason** 的源。`reason` 是一等 TEXT 列，已存在 → 零 DDL。读频 = 每任务终态 1 次。

**否决 B：从 `delegated_task_events.detail` jsonb 反查**——src 全仓无任何 events SELECT，且 memory store 根本没有 events 表 → 砍断单测路径。同理 `releaseClaim` 的 `reason` 只进 PG events（`store.ts:400`），memory 实现签名里连 `reason` 参数都没有（`store.ts:666`）→ 不可作数据源。

**否决 C：task 行加 `lastFailureReason` 列，attempt settle 时投影**——需 DDL + 迁移（本仓 schema 启动自建、**无迁移器**，新增列不会自动 ALTER），且是新增单写状态、要维护一致性。

### D3：四支判定，靠计数器补集而非白名单

`finishBudget` 读 attempts 后按下表拼尾巴：

| 局面 | 判据 | 追加文案 |
| --- | --- | --- |
| 从未真正开始 | `failureCount === 0 && skippedCount === attemptCount && attemptCount > 0` | `；<N> 次均未真正开始：<人话>` |
| 尝试后失败 | 存在 `failed` attempt，且非上一支 | `；最后一次未成原因：<人话>` |
| 混合 | 既有 `failed` 又有 `skipped` | `；最后一次未成原因：<人话>（共 <N> 次尝试）` |
| 无原因可取 | 无 settle 且 reason 非空的 attempt | 保持现状，不补话 |

**「从未真正开始」这一支的依据（已实证）**：`markAttemptDispatched` 在 `executor.execute()` **之前**无条件跑（`worker.ts:145` vs `:150`），而它正是 `attemptCount++` 处（PG `store.ts:433`、memory `store.ts:701-711`）→ **每一次 executor 返回的 `deferred` 都永久烧掉一个 attempt**，并 settle 成 `skipped`（`worker.ts:166-168`，`failureCount` 保持 0）。NL 发帖默认 `maxAttempts = max(target, target*2) = 2`（`parser.ts:60-63`）→ `warned` 账号两次 `risk_status(warned)` 即终结，**从未接触边缘**。若与真实失败同文表述，运营会误以为系统已在平台上动过手 —— 这是红线落点，不是文案偏好。

### D4：人话化 = 白名单 + 原样透传，独立纯函数文件

**选择**：新文件 `src/delegated-task/reason-humanize.ts`，导出纯函数 `humanizeAttemptReason(reason: string): string`。

**理由**：无副作用、纯单测、**避开全部热点文件**，可与 fleet 其他 change 并行。

同一 `reason: string` 字段混装三种语域，无判别字段：

- **(a) 机器码 snake_case**（会原样打进飞书卡）：`needs_persona_setup`(`executors.ts:305`)、`risk_status(<s>)`(`publish-scheduler.ts:397`)、`risk_denied(status=<s>)`(`:398`)、`candidate_record_missing`(`executors.ts:143`)、`today_inspiration_unavailable`、`candidate_terminal_<status>`(`executors.ts:379`)、`candidate_missing_during_reconcile`(`:377`)、`publish_<status>`(`:153`)、`executor_exception:<msg>`(`worker.ts:153`)、`duplicate_target`(`:139`)。
- **(b) 中文人话句**（直接透传）：`稿件已提交但平台发布结果未确认`、`已有一轮发帖编排在运行中，本次未触发（already_running）`、`选题判定不发布：<reason>` 等。
- **(c) 裸英文异常文本**：`Pipeline aborted by <role>: <err>`、`Pipeline timed out after <ms>ms`。

策略：白名单命中即翻译（含三个前缀式：`risk_status(` / `risk_denied(` / `executor_exception:`）；未命中**原样透传**；超长裁到 ~120 字符并保留原文可辨识片段。

### D5：顺手 additive —— 卡上补平台名

`server.ts:3550-3557` 从不传 `platformName`，但 `task.platform` 就在手边，`cards.ts:161` 的 `platformLine` 是现成条件片段 → 1 行、零回归。（`task.id` / `terminalOutcome.code` 同样在手边被丢，运营拿不到 task id 去 `/cancel` 或查证——本变更不扩，登记备选。）

## Risks / Trade-offs

- **[假精度：把 `candidate_terminal_failed` 渲染成具体边缘原因]** → spec 已写死上限为「派发阶段失败」+ recordId；数据根本不存在（D 的 Non-Goals），实装时 humanize 白名单对该码只给阶段级表述。
- **[假诊断：未知码被美化成听着像原因的句子]** → 未命中一律原样透传，单测覆盖「未知码原样出现」。
- **[误读：让开被读成已发过]** → D3 第一支专治，单测覆盖 `failureCount===0 && skippedCount===attemptCount`。
- **[既有测试断言被打破]** → `test/delegated-task/notification.test.ts:52-62` 断言 `/已达到最大尝试次数/`、`worker.test.ts` 断言诚实部分完成，均为**子串匹配**；本变更**追加而非替换**前缀 → 应仍通过。实装后跑 `test:acceptance` + 全量 `test` + `typecheck` 验证。
- **[fingerprint 变化]** → `delegatedTaskNotificationFingerprint`（`notification.ts:3-12`）`JSON.stringify` 整个 `terminalOutcome` → message 变化即指纹变化。属期望行为：终态只发一次，无重复发卡风险。
- **[放大器仍在：`already_running` 2 秒烧光预算]** → 本变更**只让它可见、不修它**。可见即价值（运营终于知道是撞车而非平台问题），但卡仍会出现。已登记为后继 change，proposal 显式记账，**不静默留着**。
- **[fleet 并发]** → `delegated-executor-operator-authority-parity` 已于 `cd185df` 归档 → `notification.ts` / `server.ts` onTaskUpdated 现无主。`worker.ts` / delegated `store.ts` 无主。同批新建的 `facebook-write-action-visibility` 尚为空壳，若落到 `publish-log-store` / dispatcher 则与本变更互补（它抬天花板、本变更修管道），须在其成文后对账。
- **[归档序]** → 本 change MODIFY `user-delegated-tasks`；若届时另有 change 同改该 capability，归档须串行（见 memory「OpenSpec archive batch mechanics」）。

## Migration Plan

无数据迁移：`reason` 列已存在、`terminal_outcome` 是 JSONB（旧行只是缺 key）。纯 cloud 部署，按标准安全序列走 dev（备份 → rsync → restart → healthcheck → 失败回滚）。回滚 = 恢复上一个 `cloud.bak.<ts>.tar.gz`；行为回退到「只有预算记账」，无数据残留。

## Open Questions

- 是否把 `task.id` 也补进失败卡（便于运营 `/cancel` 与查证）？倾向不扩本变更范围，先看运营是否真需要。
