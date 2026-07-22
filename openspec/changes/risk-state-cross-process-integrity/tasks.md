## 0. 串行前置

- [x] 0.1 确认本 change 独占风控热点文件：`aidcp-cloud/src/risk/pg-risk-store.ts`、`risk-controller.ts`、`risk-controller-registry.ts`、`risk-state-machine.ts`（后者只读、不改）。开工前 `openspec list` 确认无其它活跃 change 声明要动这四个文件；有则等对方 land 后再开始，不并行。 <!-- 主控已确认独占：并行的 cloud-schema-migration-executor 被指示跳过 pg-risk-store.ts；config-mirror-cross-process-invalidation 只被允许动 risk-controller.ts 的 resolveNurtureAnchor 一个函数且排在本 change 之后 rebase。risk-state-machine.ts 全程只读、逐字未动。 -->
- [x] 0.2 确认本 change **不触碰**协议五处同步点：两份 `src/comm/protocol.ts`、`aidcp-cloud/src/comm/command-bridge.ts` 动作映射、`aidcp-edge/src/client/edge-client.ts` 主动命令白名单、`FB_COMMAND_ACTION_NAMES` / `LEGACY_ACTION_COMPLETION_ALIASES` 两张动作名表。实施中如发现必须改，停手先与用户确认（会改变本 change 的串行范围）。 <!-- 全程未触碰协议五处同步点：两份 protocol.ts / command-bridge.ts / edge 主动命令白名单 / FB_COMMAND_ACTION_NAMES / LEGACY_ACTION_COMPLETION_ALIASES 均零 diff。握手拒绝走既有 hello→error 应答形态，与 platform_mismatch 同形。 -->

## 1. aidcp-cloud — 迁移与 schema（全部 additive）

- [x] 1.1 新增 `migrations/0057_risk_writer_ownership_and_outbox.sql`：`ALTER TABLE accounts ADD COLUMN IF NOT EXISTS execution_target TEXT`，并用幂等 `DO $$` 块补 `CHECK (execution_target IS NULL OR execution_target IN ('dev','ol'))`。**MUST NOT 回填默认值**（回填 `'dev'` 会把 ol 生产账号静默划给 dev），文件头注释写清这条理由。 <!-- aidcp-cloud 419e0f9 偏离：文件名用 0061_ 而非 tasks 写的 0057_——0057 已被 publish_draft_refinement_jobs 占用，且主控为并行 change 预留 0058-0060。未回填默认值，理由写在文件头。 -->
- [x] 1.2 同文件新增 `risk_counter_outbox` 表：`id BIGSERIAL PK`、`account_id`、`action`（CHECK 复用 `risk_counters` 的十个动作全集）、`occurred_at TIMESTAMPTZ`、`execution_target TEXT NOT NULL CHECK IN ('dev','ol')`、`dedupe_key TEXT NOT NULL`、`status TEXT NOT NULL DEFAULT 'pending' CHECK IN ('pending','applied','dead')`、`attempts INTEGER NOT NULL DEFAULT 0`、`claim_token TEXT`、`claim_expires_at TIMESTAMPTZ`、`last_error TEXT`、`created_at`、`updated_at`。 <!-- aidcp-cloud 419e0f9 -->
- [x] 1.3 同文件新增索引：`UNIQUE (execution_target, dedupe_key)`；`(execution_target, status, claim_expires_at, id)`（认领扫描，target 打头，对齐 `delegated-task/store.ts:90-91`）。 <!-- aidcp-cloud 419e0f9 -->
- [x] 1.4 同文件 `ALTER TABLE risk_counters ADD COLUMN IF NOT EXISTS outbox_id BIGINT` + `CREATE UNIQUE INDEX IF NOT EXISTS uq_risk_counters_outbox ON risk_counters (outbox_id) WHERE outbox_id IS NOT NULL`（exactly-once 交给数据库）。 <!-- aidcp-cloud 419e0f9 -->
- [x] 1.5 把 1.1–1.4 的等价幂等 SQL 补进 `src/risk/pg-risk-store.ts` 的 `RISK_SCHEMA_SQL`（`:28-82`）与 `src/account-store.ts` 的建表 SQL（`:34-54` 的自愈式 ALTER 段）——本仓无迁移执行器，`init()` 里的幂等 SQL 才是实际生效路径。 <!-- aidcp-cloud 419e0f9 accounts 侧进 ACCOUNTS_SCHEMA_SQL，outbox + outbox_id 进 RISK_SCHEMA_SQL -->
- [x] 1.6 在 dev ECS 上先只跑迁移、不改代码，确认 `\d risk_counters`、`\d accounts` 新列到位且既有查询零回归（本批 DDL 全 additive，ol 侧只是多出忽略的列）。
  <!-- 2026-07-23 deployed 偏离：**没有**分两步（先只跑迁移、再上代码）。本仓无迁移执行器，0061 的等价幂等 DDL 就写在 `src/account-store.ts` 的 `ACCOUNTS_SCHEMA_SQL` 与 `src/risk/pg-risk-store.ts` 的 `RISK_SCHEMA_SQL` 的 init() 里（迁移文件头已注明「init() 里那份才是实际生效路径」），代码与 schema 天然同批。实测确认：`accounts.execution_target`、`risk_counters.outbox_id` 两列到位，`risk_counter_outbox` 建表成功，`accounts` 36 行全部保持 NULL 未被回填。零回归的证据仅为「服务启动零 error + PG ping + 归属分布查询正常」，**未**做既有查询的逐条回归——完整回归留给真机验收簇。 -->

## 2. aidcp-cloud — 每 target 单实例写者锁

- [x] 2.1 新增 `src/risk/writer-lock.ts`：用一条**专用 `pg.Client` 长连接**（不走 pool）执行 `SELECT pg_try_advisory_lock(hashtext('aidcp_automation_writer'), hashtext($1))`，`$1` 为 `executionTarget`。暴露 `acquire(timeoutMs)` / `isHeld()` / `release()`。 <!-- aidcp-cloud 419e0f9 src/risk/writer-lock.ts，连接经 connect 工厂注入以便桩验 -->
  <!-- aidcp-cloud aef96c4 修正：defaultConnect 曾直读 process.env.PGHOST/PGPORT/... —— 全进程唯一绕开统一回落链的 DB 客户端，未配 PG* 的部署上连不上会让整个云端 exit(1)（不是风控降级）。现连接参数由 server.ts 显式注入（与 PgRiskCounterOutboxStore 同形），缺项回落 pgRiskConfigFromEnv。 -->
- [x] 2.2 抢锁失败按有界重试（默认 60s，`AIDCP_RISK_WRITER_LOCK_WAIT_MS` 可配）；超时后写 P1 告警（`alerts` 表，文案直接写「另一个实例正持有 <target> 的自动化写者锁」）并让进程以非零码退出。**MUST NOT 降级为无锁继续运行**，MUST NOT 只打 `console.warn` 后继续。 <!-- aidcp-cloud 8178574 有界等待 AIDCP_RISK_WRITER_LOCK_WAIT_MS 默认 60s；失败写 P1 到 alerts（临时连接，此时 alertStore 尚未构造）后 process.exit(1) -->
- [x] 2.3 在 `src/server.ts` 的 `main()` 里，于 `RiskControllerRegistry` 构造（`:1442`）之前抢锁；`parseDeploymentTarget`（`:503`）返回 null 时不抢锁、不启用风控写路径、不启动 outbox worker（fail-closed，对齐方案 §8 第 4 条）。 <!-- aidcp-cloud 8178574 抢锁点在 PgRiskStore 构造之前（即 registry 之前）；target 为 null 时不抢锁、归属模式恒 off、不启动 outbox worker -->
- [x] 2.4 锁连接断开（`error` / `end` 事件）时视为写权丢失：立即停止下发新的互动命令、写 P1 告警。**MUST NOT 静默继续写 `risk_state`**。 <!-- aidcp-cloud 8178574 onLost → writerAuthorityLost 全局闸 → 每账号 explain 拒绝一切互动动作（浏览仍放行）+ P1 告警。outbox apply 刻意不停：既成事实账本停了就是丢账。 -->
- [x] 2.5 单测：两个 store 实例对同一 target 抢锁，第二个必须失败；对不同 target 抢锁必须都成功；释放后可被重新抢到。 <!-- aidcp-cloud 0ac891e test/risk-writer-lock.test.ts 4 例（同 target 第二个失败 / 不同 target 各自成功 / 释放后可重抢 / 连接断开即失权） -->

## 3. aidcp-cloud — 账号归属 target

- [x] 3.1 `src/account-store.ts` 增加 `getExecutionTarget(accountId)` 与 `claimExecutionTarget(accountId, target)`；后者用条件 UPDATE 原子占位：`UPDATE accounts SET execution_target=$2 WHERE account_id=$1 AND execution_target IS NULL RETURNING execution_target`，返回 `claimed` / `already_owned_by(target)` 两种诚实结果，MUST NOT 在已被占位时覆盖。 <!-- aidcp-cloud 419e0f9 getExecutionTarget / claimExecutionTarget / setExecutionTarget 落 PgAccountStore（accounts 单写方） -->
- [x] 3.1b **跨边界写入登记（MUST 与 3.1 / 3.2 一并读）**：`accounts` 表按拆分方案 §5.1 由 `aidcp-api` **单写**，而 `src/account-store.ts` 归 api、`src/orchestrator/connection-runtime.ts` 归 automation（方案 §4.7）。因此 3.2 在握手路径上调 3.1 占位，拆分后属 **automation 写 api 的表**。二选一并在实施时写死：① 收口为「automation 握手调 api 的窄内部接口占位、api 单写 `accounts`」（与 §5.1 `client_environments` 行同形，为首选）；② 在 change `cloud-service-boundary-gates` 的表写入豁免清单里为该写入留一条具名条目并填 `eliminatedBy`。**MUST NOT 两条都不做**——`AC-OWN-02` 上线当天该写入即判违规。 <!-- aidcp-cloud 419e0f9 选①：新增窄口 AccountOwnershipPort（src/risk/ownership.ts），实现方是 account-store（api 侧），automation 侧只持接口、绝不自拼 accounts 的 SQL。与定稿 §5.1 accounts 行「MUST 经 api 的窄内部接口完成」一致；拆进程时换成一次内部 HTTP 即可，调用点不改。 -->
- [x] 3.2 `src/orchestrator/connection-runtime.ts` 的 `onHandshake` 在既有 `platform_mismatch` 闸（`:148-152`）之后增加对称的归属闸：归属为 NULL → 调 3.1 占位；归属为本 target → 放行；归属为对方 target → 走同一个 `this.deps.onConfigError` 通道拒绝，返回 `{ ok:false, code:'execution_target_mismatch', message }`，message 里写清真实归属 target 与「请先在 <owner> 停止该账号自动化再改归属」。 <!-- aidcp-cloud 419e0f9+8178574 connection-runtime.resolveOwnership，紧接 platform_mismatch 之后，走同一 onConfigError 通道 -->
- [x] 3.3 强制开关 `AIDCP_RISK_OWNERSHIP_ENFORCE`（默认 `false` = 观察模式）：观察模式下 3.2 的拒绝分支只写告警不拒绝，占位照做。**观察模式 MUST NOT 静默**——每一次本会被拒的握手都必须留一条可检索的告警。 <!-- aidcp-cloud 8178574 默认 observe：占位照做、每次本会被拒的握手都写一条可检索告警（risk_owner_mismatch_observed），不拒绝 -->
- [x] 3.4 新增运维口 `POST /api/accounts/:accountId/risk-owner`（面板，JWT 守卫同既有风控口）：改归属前必须校验该账号在旧属主上无活跃边缘会话，否则返回 409 + `owner_change_blocked_by_active_session`，MUST NOT 强改。 <!-- aidcp-cloud 12e3a84 POST /api/accounts/:id/risk-owner；旧属主是对方 target 时一律拒（本进程看不见对方会话，看不见≠没有） -->
- [x] 3.5 单测：占位竞争（两次并发 claim 只有一次成功）、归属冲突握手被拒且带真实归属、观察模式不拒绝但留告警、活跃会话时改归属被拒。 <!-- aidcp-cloud 0ac891e test/risk-ownership.test.ts（占位竞争落败 / 归属冲突被拒带真实归属 / 观察模式不拒但留告警）+ test/panel-risk-ownership.test.ts（活跃会话时改归属被拒） -->

## 4. aidcp-cloud — `risk_state` 条件写与缓存驱逐

- [x] 4.1 `src/risk/pg-risk-store.ts` 的 `saveState`（`:191-204`）改为带属主谓词的单语句：`WITH owner AS (SELECT 1 FROM accounts WHERE account_id=$1 AND execution_target=$8) INSERT … SELECT … WHERE EXISTS (SELECT 1 FROM owner) ON CONFLICT (account_id) DO UPDATE SET … RETURNING account_id`。属主事实唯一权威是 `accounts.execution_target`，**MUST NOT 在 `risk_state` 复制一份属主列**。 <!-- aidcp-cloud 419e0f9 属主事实唯一权威是 accounts.execution_target，risk_state 未复制属主列 -->
- [x] 4.2 `rowCount === 0` 时抛 `RiskStateNotOwnedError`（带 accountId + 期望 target + 真实归属），MUST NOT 返回成功、MUST NOT 重试、MUST NOT 换谓词绕过。三种触发原因（账号不存在 / 归属为空 / 归属是别人）必须能从错误里区分。 <!-- aidcp-cloud 419e0f9 RiskStateNotOwnedError 带 accountId/expectedTarget/actualTarget/cause2，三种原因可区分；enforce 抛后绝不回落无谓词写 -->
- [x] 4.3 `src/risk/risk-controller-registry.ts` 捕获 `RiskStateNotOwnedError` → 从 `controllers` Map（`:29`）中 **delete 该账号**并写 P1 告警。这是该 Map 的第一个失效路径；同时把 `:9-12` 与 `:22-27` 那两段「Map 永不驱逐已不再相关」「绝不出现两个内存 controller」的注释改写为与新事实一致的表述。 <!-- aidcp-cloud 419e0f9 handleNotOwned 驱逐 + P1；registry 头部两段注释已改写为「只在单进程内成立」+「本 Map 现在有失效路径」 -->
  <!-- aidcp-cloud aef96c4 修正：419e0f9 只写了 handleNotOwned 方法、生产侧零调用方（唯一实调是 test/risk-ownership.test.ts 手工喂错误），真实链路上 saveState 抛出的错被 captcha-coordinator 吞成一行日志 ⇒ 无驱逐无告警。现改由 RiskController.persistState（三个写入口的唯一落库出口）回调 registry.handleNotOwned，并补一条从 store 抛错走到驱逐+告警的端到端断言。 -->
- [x] 4.4 注册表拆两个口：`getWritableController(accountId)`（校验本 target 归属，非属主直接抛）与 `getReadOnlyState(accountId)`（直读 `risk_state` 投影，不物化 controller）。既有 `getController` 的 14 个调用点（`server.ts` 9 处、`panel/panel-server.ts` 2 处、`panel/types.ts:226`、`orchestrator/connection-runtime.ts:62,167`）逐个归位到其中之一。 <!-- aidcp-cloud 419e0f9+8178574+12e3a84 拆成 getWritableController / getReadOnlyState，另加 getControllerForAccounting（记账刻意不过归属闸，见 design D4「分裂的是写权限不分裂的是事实」）。getController 保留为 getWritableController 的薄别名。调用点归位：握手→可写；面板两个写口→可写（前置 409 闸）；首页汇总→非属主不物化；记账三处→记账口；listStates→只读投影。 -->
- [x] 4.5 单测：非属主 `saveState` 影响 0 行并抛错、错误后 controller 被驱逐、驱逐后重新解析读到库内最新状态（模拟「另一 target 写过 restricted」）、属主写正常成功且逐位与今天一致。 <!-- aidcp-cloud 0ac891e test/risk-ownership.test.ts。「非属主 saveState 影响 0 行」本身是数据库给的保证，桩只能验 0 行之后的分支——已登记真机验收项 5。 -->
  <!-- aidcp-cloud aef96c4 补一例走真实链路的断言（store.saveState 抛 → controller → registry 驱逐 + 告警 + 照常抛给发起方）；原有那条只是手工构造错误直接喂 handleNotOwned，验的是它自己。 -->

## 5. aidcp-cloud — 记账 outbox

- [x] 5.1 新增 `src/risk/risk-counter-outbox-store.ts`：`enqueue({accountId, action, occurredAt, dedupeKey})`（`ON CONFLICT (execution_target, dedupe_key) DO NOTHING`）、`claimBatch({workerId, leaseMs, limit})`（`FOR UPDATE SKIP LOCKED` + `execution_target=$local`，照抄 `delegated-task/store.ts:493-516`）、`applyClaimed(rows)`、`recoverExpiredClaims()`（照抄 `store.ts:418-475`）、`backlogCounts()`。 <!-- aidcp-cloud 419e0f9 src/risk/risk-counter-outbox-store.ts -->
- [x] 5.2 `applyClaimed` 必须在**单事务**里完成 `INSERT INTO risk_counters(account_id, action, count, occurred_at, outbox_id) … ON CONFLICT (outbox_id) DO NOTHING` 与 `UPDATE risk_counter_outbox SET status='applied'`；exactly-once 由 1.4 的唯一索引保证，MUST NOT 用内存 Set 去重。 <!-- aidcp-cloud 419e0f9 单事务 BEGIN/INSERT ON CONFLICT (outbox_id) DO NOTHING/UPDATE ... AND claim_token/COMMIT；认领失效即整笔 ROLLBACK -->
- [x] 5.3 `src/comm/handler.ts` 的回执分支（`:715-750`）：在 `emit('interaction.occurred', …)` **之前**同步 `await` outbox 入队，`dedupeKey = \`${env.id}:${result.action}\``。入队失败 MUST 抛出到调用方并触发 5.4，MUST NOT 吞掉后照常 emit。 <!-- aidcp-cloud 8178574 handler.enqueueRiskFact 在两处 emit 之前 await；失败刻意不 catch，由 ws 层兜成 error 帧。search 侧去重键用 activityId（每次搜索唯一）。 -->
- [x] 5.4 入队失败的处理：写 P1 告警 + 该账号进入 fail-closed（暂停继续下发自动互动命令，直到人工或下一次成功入队解除）。**MUST NOT 静默继续浏览闭环**——那等于明知记不上账还继续制造真实平台动作。 <!-- aidcp-cloud 8178574 入队失败 → P1 + 该账号进 blocked 集合；闸接在 RiskController.explain（全部自动路径的公共必经点，覆盖是结构性的），reason=accounting:blocked，浏览仍放行 -->
- [x] 5.5 `src/server.ts` 的 `interaction.occurred` 订阅（`:1592-1612`）改造：删掉其中的 `await c.record(evt.action)`，改为「取写入前判定 `explain`（`:1598` 语义逐字保留，供 `pacingAlerter`）→ 触发一次立即 apply」。`search.occurred` 订阅（`:1677-1687`）同样改造。**内存计数只在 apply 成功时递增，全系统只此一条路径**。 <!-- aidcp-cloud 8178574 两个订阅都改成「取写入前判定 → applyNow()」；:1598 的 explain 语义逐字保留（判定仍取自 apply 之前）。漏斗未启用时回落 controller.record，行为逐位一致。 -->
  <!-- aidcp-cloud aef96c4 修正两处：① 8178574 的订阅者只 applyNow()，而 view 从未在任何地方入队（它是唯一没有 action.completed 回执的动作）⇒ 浏览配额三个窗口全部失效、面板浏览数与首发引导进度恒 0，且对账检不出。现 handler 的三个 view 发射点先 enqueue 再 emit。② 「行为逐位一致」当时是假陈述，见 5.6。 -->
- [x] 5.6 `RiskController.record`（`:221-227`）拆成两半：`recordFact(action, occurredAt)`（仅递增内存计数，由 apply 驱动）与保留的判定取值；`store.appendCounter` 的直接调用从 controller 移出，改由 outbox apply 承担。注释里那段「求值顺序不可换」的不变量必须保留并更新到新路径。 <!-- aidcp-cloud 419e0f9+8178574 record 拆成 recordFact（仅递增内存）+ 判定取值；appendCounter 调用已从 controller 移出。「求值顺序不可换」的不变量原文保留并迁到 RiskAccounting.record 的 JSDoc。生产侧全部 7 个 record 调用点（interaction/search 订阅、publish、两处 contact comment、互动域评论与私信、保留通道 risk.record）已收口到同一漏斗。 -->
  <!-- aidcp-cloud aef96c4 修正：把 appendCounter 从 record() 里整个摘掉，使它全仓零调用方，于是三处「漏斗未启用即回落改动前记账、行为逐位一致」的降级分支实际一行都不落库（重启即把当日已消耗配额清零，且对账检不出）。现 record() 恢复 appendCounter：漏斗启用时它不被生产路径调用（无双计），未启用时它才是那条真正逐位一致的降级路径。 -->
- [x] 5.7 outbox worker：入队后同进程立即触发一次 apply；轮询（默认 5s）只作崩溃恢复兜底。启动时 `recoverExpiredClaims()` 并把回收条数写进启动日志（对齐 `server.ts:1527-1531` 的形态）。 <!-- aidcp-cloud 8178574 入队后同进程立即 applyNow；轮询默认 5s 只兜底；启动 recoverExpiredClaims 条数写进启动日志 -->
  <!-- aidcp-cloud aef96c4 修正：applyNow 的并发折叠直接复用飞行中的那一次 apply，而那一次可能早在本次入队前就做完了 claimBatch ⇒ 「入队后立即 apply」对并发账号整个落空、退化成 5s 轮询，期间准入判定偏松。现改为排队一轮后续 apply（最多一轮）。 -->
- [x] 5.8 死信：`attempts` 超限（默认 5）转 `status='dead'` + P1 告警，MUST NOT 静默丢弃。积压量与死信量落 `alerts` 或指标口，必须可被面板读到。 <!-- aidcp-cloud 419e0f9+8178574 attempts 超限（默认 5）转 dead + P1；backlog() 暴露 pending/dead/staleClaims/blockedAccounts -->
  <!-- aidcp-cloud aef96c4 修正：failClaimed 的 WHERE 缺 status='pending' 守卫，会把一条已 applied 的行改回 pending 或标 dead，并发一条「该动作没进账本」的假 P1（它其实已经在账本里），死信数还会污染上线判据。已补守卫；同时把「落账已 COMMIT 之后的失败」与之前的失败在 applyOnce 里分开——前者不回写 outbox，交由对账以库为准重建。 -->
- [x] 5.9 单测：崩在 emit 与 apply 之间后重启能补记（模拟：入队成功、不 apply、重建 store、跑 recover + apply，计数只 +1）；同 `dedupeKey` 重复入队只产生一行；同一 outbox 行 apply 两次 `risk_counters` 只增一行；`attempts` 超限进 dead 且有告警。 <!-- aidcp-cloud 0ac891e test/risk-counter-outbox.test.ts 6 例（崩溃点补记只 +1 / 同 dedupeKey 一行 / 同行 apply 两次一行 / 内存只跟 apply 走 / 超限进死信 / 入队失败 fail-closed）。FOR UPDATE SKIP LOCKED 的真实互斥与真事务原子性桩验不了 → 真机验收项 6。 -->
  <!-- aidcp-cloud aef96c4 补 test/risk-accounting-gaps.test.ts 5 例（view 入队 / view 端到端到 risk_counters+内存 / 降级 record 同时落库 / 飞行中入队不被推迟到轮询 / failClaimed 只动 pending），其中 4 例在本次修复前为红。 -->

## 6. aidcp-cloud — 计数与库内事实对账

- [x] 6.1 新增周期对账（默认 5 分钟，`AIDCP_RISK_RECONCILE_INTERVAL_MS` 可配）：对已物化的每个 controller，用 `PgRiskStore.totalsForAccountSince`（`:149-158`）取当日总量，与 `RiskController.counts()`（`:413-415`）比对。 <!-- aidcp-cloud 419e0f9+8178574 src/risk/risk-counter-reconciler.ts，AIDCP_RISK_RECONCILE_INTERVAL_MS 默认 5min，只对已物化 controller -->
- [x] 6.2 判据是**偏差是否为零**，MUST NOT 引入容忍阈值。偏差非零 → 写告警（带 accountId / action / 内存值 / 库值）并**以库为准重建**该账号计数（重放 `loadCounters`）。 <!-- aidcp-cloud 419e0f9 逐项相等即通过、无阈值；偏差 → 告警 + controller.reloadCounters() 整段以库重建。窗口口径取 shanghaiDayStartMs 与内存 day 窗严格一致（取错口径会制造恒定假偏差）。 -->
- [x] 6.3 归属占位成功、归属变更后重新解析 controller 时，MUST 强制重放一次计数（不复用可能陈旧的内存值）。 <!-- aidcp-cloud 8178574 占位成功经 ownership.onClaimed → peek 到已物化 controller 即 reloadCounters；归属变更经面板则直接 evict（下次解析必从库重建） -->
- [x] 6.4 单测：库里被外部插入一行后，对账能检出偏差、发告警、重建后内存值等于库值。 <!-- aidcp-cloud 0ac891e test/risk-counter-outbox.test.ts 末两例（外部插入被检出并重建 / 偏差 1 也算偏差） -->

## 7. aidcp-cloud — 面板读写口归位

- [x] 7.1 `src/panel/panel-server.ts:711-720` 的首页汇总改用 4.4 的只读口：非本 target 归属账号 MUST NOT 物化可写 controller；保留 `:717-719` 既有的「拿不到就不带上限」诚实缺省。 <!-- aidcp-cloud 12e3a84 非属主账号 early-return 原 entry，:717-719 的「拿不到就不带上限」诚实缺省逐字保留 -->
- [x] 7.2 `/risk/signal`（`:1628-1636`）与 `/risk/quota`（`:1655-1656`）在非属主时返回 409 + `risk_state_not_owned` + 真实归属 target，MUST NOT 返回 200、MUST NOT 返回看起来成功的 `changed:false`。 <!-- aidcp-cloud 12e3a84 偏离：真实路由是 /risk/status（不是 change 文档写的 /risk/signal），以代码为准。两口都在 assertAccountExists 之后加 assertRiskWritable，409 + risk_state_not_owned + owner + executionTarget + 人话说明，且响应体不含 changed 字段。 -->
  <!-- aidcp-cloud aef96c4 修正：12e3a84 在 observe 模式下也 409，与 design Migration Plan 第 2 步「只读上线…行为与今天逐位一致」/第 4 步「面板写口拒绝生效」冲突；迁移刻意不回填归属 ⇒ 上线瞬间全部账号 execution_target=NULL、风控写口集体锁死，没有边缘在线的账号永远拿不到归属。现 assertRiskWritable 与 panel-store 的 riskWritable 都只在 enforce 收紧，observe 只留告警。 -->
- [x] 7.3 面板账号 DTO 增加 `executionTarget`（可为 null=未归属）与 `riskWritable: boolean`；服务端权威，MUST NOT 让 Console 自己推断。 <!-- aidcp-cloud 12e3a84 PanelAccount 加 executionTarget / riskWritable，服务端算；panel/version.ts 的 PANEL_ACCOUNT_FIELDS 同步（该断言使 console 字段漂移在 cloud typecheck 阶段暴露） -->
- [x] 7.4 单测：非属主账号的两个写口返回 409、首页汇总对非属主账号不物化 controller。 <!-- aidcp-cloud 0ac891e test/panel-risk-ownership.test.ts 6 例 -->
  <!-- aidcp-cloud aef96c4 补第 7 例：observe 模式下非属主与未归属账号的写口 MUST 照常 200（原实现在 observe 也 409，见 7.2 的修正说明）。 -->

## 8. aidcp-console — 归属可见性与非属主只读

- [x] 8.1 账号相关 API 类型补 `executionTarget` / `riskWritable`（与 cloud 同源，避免枚举/字段漂移）。 <!-- aidcp-console c73b6bc PanelAccount 加 executionTarget / riskWritable（可选，滚动升级旧 Cloud 缺字段时按可写处理、零回归） -->
- [x] 8.2 账号列表与风控操作区：非属主账号的「风控信号 / 配额档位」写操作禁用，并显示真实归属 target 与「请在 <owner> 后台操作」。未归属（null）显示为「未归属」而不是伪装成本 target。 <!-- aidcp-console c73b6bc 非属主两个控件渲染为只读，归属直接显示在行上（不只挂 hover），未归属显示「未归属」 -->
  <!-- aidcp-cloud aef96c4 生效范围收窄（console 代码无需改动）：riskWritable 现在只在 enforce 模式下才会为 false，observe 期间恒 true。理由见 7.2 的修正说明——observe 也变灰＝上线当天全车队锁死。 -->
- [x] 8.3 收到 409 `risk_state_not_owned` / `owner_change_blocked_by_active_session` 时，MUST 显示可区分的失败态，MUST NOT 显示成功或静默无反应。 <!-- aidcp-console c73b6bc ApiError 新增 serverMessage（与机器码 message 分列），409 归属拒绝原样上屏服务端说明；其余失败仍走通用文案 -->
- [x] 8.4 补少量聚焦测试：非属主行的写按钮禁用、409 的失败态渲染。 <!-- aidcp-console c73b6bc src/components/RiskControls.ownership.test.tsx 5 例 -->

## 9. aidcp-edge — 拒绝码诚实呈现

- [x] 9.1 客户端把握手拒绝码 `execution_target_mismatch` 如实呈现（文案含真实归属 target 与处理办法），MUST NOT 渲染成通用「云端离线 / 连接失败」。不新增协议消息类型、不动主动命令白名单。 <!-- aidcp-edge 22a9c31 新增 CloudHandshakeRejectedError（拒绝 ≠ 连不上）；main.ts 原样打印拒绝码与云端说明并对 execution_target_mismatch 追加处理办法；外壳 fleet.isFailureShapedLine 认「云端拒绝」、main.cjs 单列一条在场感分支（先于断连规则匹配） -->
- [x] 9.2 确认该拒绝走的是既有 `onConfigError` 通道形态，与 `platform_mismatch` / `missing_account_id` 一致，不新增分支语义。 <!-- aidcp-edge 22a9c31 确认：走的仍是既有 hello→error 应答形态，与 platform_mismatch / missing_account_id 逐字同形；未新增消息类型、未动主动命令白名单、未动两张动作名表 -->

## 10. aidcp（控制仓）— 文档

- [ ] 10.1 `docs/cloud-service-decomposition-proposal.md` **§14.1 红线表 `AC-DECOMP-09` 行**（该文档不存在 §14.9，顶层编号 §1–§17 冻结，**MUST NOT 新增 §14.x 小节**）：在「红线」列补入可验收句式「对任一 `accountId`、任一时刻，`risk_state` 的写入者唯一，且配额判定所依据的计数与库内事实一致」；在「验收方式」列补写者锁与部署约束（每 target 单实例、stop→start、禁止滚动 / 蓝绿）。注意该行的「验收方式」列已按分两段兑现改写（阶段 2 凭据 + 静态门禁 / 子目标 B 后 GRANT），本项 MUST 在其上追加，MUST NOT 覆盖。
  <!-- BLOCKED: 中控仓文档为 5 个并行 change 的共享写点，本 session 只读。精确编辑已写进 scratchpad/docpatch-risk-state-cross-process-integrity.md（§14.1 AC-DECOMP-09 行），由主控串行套用。 -->
- [ ] 10.2 §12 阶段 2「验证各进程独立停止、重启和回滚」旁补「单实例 / 可多实例」组件分类表（内容见本 change 的 spec delta），并写明新增后台组件必须先归类。
  <!-- BLOCKED: 中控仓文档为 5 个并行 change 的共享写点，本 session 只读。精确编辑已写进 scratchpad/docpatch-risk-state-cross-process-integrity.md（§12 阶段 2 单实例分类表），由主控串行套用。 -->
- [ ] 10.3 §5.1 单一写入者表的「最终风险状态」行补一句：写权按 `accounts.execution_target` 排他，`risk_counters` 作为既成事实账本不按 target 分裂。
  <!-- BLOCKED: 中控仓文档为 5 个并行 change 的共享写点，本 session 只读。精确编辑已写进 scratchpad/docpatch-risk-state-cross-process-integrity.md（§5.1 最终风险状态行），由主控串行套用。 -->
- [ ] 10.4 §11 故障表补一行「自动化写者锁不可获得」：应保持可用=客户数据与内容服务；允许受影响=该 target 的自动化整体不启动（诚实失败，不降级为无锁运行）。
  <!-- BLOCKED: 中控仓文档为 5 个并行 change 的共享写点，本 session 只读。精确编辑已写进 scratchpad/docpatch-risk-state-cross-process-integrity.md（§11 故障表新增一行），由主控串行套用。 -->
- [ ] 10.5 `docs/risk-control.md` 补跨进程单写、outbox 记账链路、对账机制三节。
  <!-- BLOCKED: 中控仓文档为 5 个并行 change 的共享写点，本 session 只读。精确编辑已写进 scratchpad/docpatch-risk-state-cross-process-integrity.md（docs/risk-control.md §7.4–§7.6），由主控串行套用。 -->
- [ ] 10.6 `docs/deployment-environments.md` 补写者锁运维段：如何确认锁持有者、`kill -9` 后如何强制释放、为什么禁止滚动 / 蓝绿。
  <!-- BLOCKED: 中控仓文档为 5 个并行 change 的共享写点，本 session 只读。精确编辑已写进 scratchpad/docpatch-risk-state-cross-process-integrity.md（docs/deployment-environments.md 写者锁运维段），由主控串行套用。 -->

## 11. 验证与交付

- [x] 11.1 cloud：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全过；`AC-RISK-*` 必须全绿（本变更直接改风控写路径）。 <!-- aidcp-cloud 0ac891e 实测：test:acceptance 68 passing / 0 failing（含 AC-RISK-* 全绿）；npm test 2940 tests, 2932 pass, 0 fail, 8 skipped（skip 为既有 gated 真机用例）；typecheck 无输出 -->
- [x] 11.2 edge：`npm run typecheck` + `npm test`（本变更对 edge 只有文案层改动，但握手拒绝路径有回归面）。 <!-- aidcp-edge 22a9c31 实测：typecheck 无输出；npm test 2252 passing / 0 failing；test:acceptance 29 passing -->
- [x] 11.3 console：`npm run typecheck` + `npm run build` + 聚焦测试。 <!-- aidcp-console c73b6bc 实测：typecheck 无输出；vitest 38 files / 260 passed / 1 skipped；npm run build 成功（built in 5.40s） -->
- [x] 11.4 `openspec validate risk-state-cross-process-integrity --strict` 通过。 <!-- 实测：openspec validate risk-state-cross-process-integrity --strict → "Change ... is valid" -->
- [x] 11.5 部署 dev（观察模式：`AIDCP_RISK_OWNERSHIP_ENFORCE=false`），按 `CLAUDE.md` §5 安全序列走；部署后验证写者锁已持有、outbox 积压为 0、对账偏差为 0、账号归属自证占位符合预期。
  <!-- 2026-07-23 deployed 主控串行执行：备份 cloud.bak.20260722-185821Z.tar.gz + .env.bak.20260722-185821Z → 从 git archive HEAD 干净快照 rsync（--exclude .env/node_modules/.git）→ restart → healthcheck。部署 sha d9c550e（含本 change 全部 5 个提交）。实测四项：① 日志「自动化写者锁已持有（target=dev）」；② `select status,count(*) from risk_counter_outbox` 返回空集（零行、零积压），启动日志「启动回收在途行=0」；③ 对账器已启动、15 分钟内零偏差告警；④ 归属模式 = observe，`accounts.execution_target` 36 行全 NULL（迁移刻意不回填，等运行时首次真实握手自证占位）。零 error 日志。 -->
- [ ] 11.6 观察期结束后单独提交一次「翻开 `AIDCP_RISK_OWNERSHIP_ENFORCE=true`」的变更，并在 tasks 里记录观察期实测的跨 target 争用次数（预期 0；非 0 则先查清归属再翻）。
  <!-- BLOCKED: 依赖 11.5 的观察期数据。翻 AIDCP_RISK_OWNERSHIP_ENFORCE=true 须单独提交，且先统计 alerts 里 risk_owner_mismatch_observed / risk_state_not_owned 条数（预期 0）。 -->
- [ ] 11.7 真机验收项（双 target 同时驱动同一账号被拒、滚动部署第二实例启动失败、崩溃点补记）登记进 `docs/real-machine-acceptance-backlog.md`，按共享真机环境归簇。
  <!-- BLOCKED: docs/real-machine-acceptance-backlog.md 是中控仓共享文档，本 session 只读。8 条真机项已写进 scratchpad/docpatch-risk-state-cross-process-integrity.md 的附录，由主控串行登记。 -->
