## 0. 串行前置

- [ ] 0.1 确认本 change 独占风控热点文件：`aidcp-cloud/src/risk/pg-risk-store.ts`、`risk-controller.ts`、`risk-controller-registry.ts`、`risk-state-machine.ts`（后者只读、不改）。开工前 `openspec list` 确认无其它活跃 change 声明要动这四个文件；有则等对方 land 后再开始，不并行。
- [ ] 0.2 确认本 change **不触碰**协议五处同步点：两份 `src/comm/protocol.ts`、`aidcp-cloud/src/comm/command-bridge.ts` 动作映射、`aidcp-edge/src/client/edge-client.ts` 主动命令白名单、`FB_COMMAND_ACTION_NAMES` / `LEGACY_ACTION_COMPLETION_ALIASES` 两张动作名表。实施中如发现必须改，停手先与用户确认（会改变本 change 的串行范围）。

## 1. aidcp-cloud — 迁移与 schema（全部 additive）

- [ ] 1.1 新增 `migrations/0057_risk_writer_ownership_and_outbox.sql`：`ALTER TABLE accounts ADD COLUMN IF NOT EXISTS execution_target TEXT`，并用幂等 `DO $$` 块补 `CHECK (execution_target IS NULL OR execution_target IN ('dev','ol'))`。**MUST NOT 回填默认值**（回填 `'dev'` 会把 ol 生产账号静默划给 dev），文件头注释写清这条理由。
- [ ] 1.2 同文件新增 `risk_counter_outbox` 表：`id BIGSERIAL PK`、`account_id`、`action`（CHECK 复用 `risk_counters` 的十个动作全集）、`occurred_at TIMESTAMPTZ`、`execution_target TEXT NOT NULL CHECK IN ('dev','ol')`、`dedupe_key TEXT NOT NULL`、`status TEXT NOT NULL DEFAULT 'pending' CHECK IN ('pending','applied','dead')`、`attempts INTEGER NOT NULL DEFAULT 0`、`claim_token TEXT`、`claim_expires_at TIMESTAMPTZ`、`last_error TEXT`、`created_at`、`updated_at`。
- [ ] 1.3 同文件新增索引：`UNIQUE (execution_target, dedupe_key)`；`(execution_target, status, claim_expires_at, id)`（认领扫描，target 打头，对齐 `delegated-task/store.ts:90-91`）。
- [ ] 1.4 同文件 `ALTER TABLE risk_counters ADD COLUMN IF NOT EXISTS outbox_id BIGINT` + `CREATE UNIQUE INDEX IF NOT EXISTS uq_risk_counters_outbox ON risk_counters (outbox_id) WHERE outbox_id IS NOT NULL`（exactly-once 交给数据库）。
- [ ] 1.5 把 1.1–1.4 的等价幂等 SQL 补进 `src/risk/pg-risk-store.ts` 的 `RISK_SCHEMA_SQL`（`:28-82`）与 `src/account-store.ts` 的建表 SQL（`:34-54` 的自愈式 ALTER 段）——本仓无迁移执行器，`init()` 里的幂等 SQL 才是实际生效路径。
- [ ] 1.6 在 dev ECS 上先只跑迁移、不改代码，确认 `\d risk_counters`、`\d accounts` 新列到位且既有查询零回归（本批 DDL 全 additive，ol 侧只是多出忽略的列）。

## 2. aidcp-cloud — 每 target 单实例写者锁

- [ ] 2.1 新增 `src/risk/writer-lock.ts`：用一条**专用 `pg.Client` 长连接**（不走 pool）执行 `SELECT pg_try_advisory_lock(hashtext('aidcp_automation_writer'), hashtext($1))`，`$1` 为 `executionTarget`。暴露 `acquire(timeoutMs)` / `isHeld()` / `release()`。
- [ ] 2.2 抢锁失败按有界重试（默认 60s，`AIDCP_RISK_WRITER_LOCK_WAIT_MS` 可配）；超时后写 P1 告警（`alerts` 表，文案直接写「另一个实例正持有 <target> 的自动化写者锁」）并让进程以非零码退出。**MUST NOT 降级为无锁继续运行**，MUST NOT 只打 `console.warn` 后继续。
- [ ] 2.3 在 `src/server.ts` 的 `main()` 里，于 `RiskControllerRegistry` 构造（`:1442`）之前抢锁；`parseDeploymentTarget`（`:503`）返回 null 时不抢锁、不启用风控写路径、不启动 outbox worker（fail-closed，对齐方案 §8 第 4 条）。
- [ ] 2.4 锁连接断开（`error` / `end` 事件）时视为写权丢失：立即停止下发新的互动命令、写 P1 告警。**MUST NOT 静默继续写 `risk_state`**。
- [ ] 2.5 单测：两个 store 实例对同一 target 抢锁，第二个必须失败；对不同 target 抢锁必须都成功；释放后可被重新抢到。

## 3. aidcp-cloud — 账号归属 target

- [ ] 3.1 `src/account-store.ts` 增加 `getExecutionTarget(accountId)` 与 `claimExecutionTarget(accountId, target)`；后者用条件 UPDATE 原子占位：`UPDATE accounts SET execution_target=$2 WHERE account_id=$1 AND execution_target IS NULL RETURNING execution_target`，返回 `claimed` / `already_owned_by(target)` 两种诚实结果，MUST NOT 在已被占位时覆盖。
- [ ] 3.1b **跨边界写入登记（MUST 与 3.1 / 3.2 一并读）**：`accounts` 表按拆分方案 §5.1 由 `aidcp-api` **单写**，而 `src/account-store.ts` 归 api、`src/orchestrator/connection-runtime.ts` 归 automation（方案 §4.7）。因此 3.2 在握手路径上调 3.1 占位，拆分后属 **automation 写 api 的表**。二选一并在实施时写死：① 收口为「automation 握手调 api 的窄内部接口占位、api 单写 `accounts`」（与 §5.1 `client_environments` 行同形，为首选）；② 在 change `cloud-service-boundary-gates` 的表写入豁免清单里为该写入留一条具名条目并填 `eliminatedBy`。**MUST NOT 两条都不做**——`AC-OWN-02` 上线当天该写入即判违规。
- [ ] 3.2 `src/orchestrator/connection-runtime.ts` 的 `onHandshake` 在既有 `platform_mismatch` 闸（`:148-152`）之后增加对称的归属闸：归属为 NULL → 调 3.1 占位；归属为本 target → 放行；归属为对方 target → 走同一个 `this.deps.onConfigError` 通道拒绝，返回 `{ ok:false, code:'execution_target_mismatch', message }`，message 里写清真实归属 target 与「请先在 <owner> 停止该账号自动化再改归属」。
- [ ] 3.3 强制开关 `AIDCP_RISK_OWNERSHIP_ENFORCE`（默认 `false` = 观察模式）：观察模式下 3.2 的拒绝分支只写告警不拒绝，占位照做。**观察模式 MUST NOT 静默**——每一次本会被拒的握手都必须留一条可检索的告警。
- [ ] 3.4 新增运维口 `POST /api/accounts/:accountId/risk-owner`（面板，JWT 守卫同既有风控口）：改归属前必须校验该账号在旧属主上无活跃边缘会话，否则返回 409 + `owner_change_blocked_by_active_session`，MUST NOT 强改。
- [ ] 3.5 单测：占位竞争（两次并发 claim 只有一次成功）、归属冲突握手被拒且带真实归属、观察模式不拒绝但留告警、活跃会话时改归属被拒。

## 4. aidcp-cloud — `risk_state` 条件写与缓存驱逐

- [ ] 4.1 `src/risk/pg-risk-store.ts` 的 `saveState`（`:191-204`）改为带属主谓词的单语句：`WITH owner AS (SELECT 1 FROM accounts WHERE account_id=$1 AND execution_target=$8) INSERT … SELECT … WHERE EXISTS (SELECT 1 FROM owner) ON CONFLICT (account_id) DO UPDATE SET … RETURNING account_id`。属主事实唯一权威是 `accounts.execution_target`，**MUST NOT 在 `risk_state` 复制一份属主列**。
- [ ] 4.2 `rowCount === 0` 时抛 `RiskStateNotOwnedError`（带 accountId + 期望 target + 真实归属），MUST NOT 返回成功、MUST NOT 重试、MUST NOT 换谓词绕过。三种触发原因（账号不存在 / 归属为空 / 归属是别人）必须能从错误里区分。
- [ ] 4.3 `src/risk/risk-controller-registry.ts` 捕获 `RiskStateNotOwnedError` → 从 `controllers` Map（`:29`）中 **delete 该账号**并写 P1 告警。这是该 Map 的第一个失效路径；同时把 `:9-12` 与 `:22-27` 那两段「Map 永不驱逐已不再相关」「绝不出现两个内存 controller」的注释改写为与新事实一致的表述。
- [ ] 4.4 注册表拆两个口：`getWritableController(accountId)`（校验本 target 归属，非属主直接抛）与 `getReadOnlyState(accountId)`（直读 `risk_state` 投影，不物化 controller）。既有 `getController` 的 14 个调用点（`server.ts` 9 处、`panel/panel-server.ts` 2 处、`panel/types.ts:226`、`orchestrator/connection-runtime.ts:62,167`）逐个归位到其中之一。
- [ ] 4.5 单测：非属主 `saveState` 影响 0 行并抛错、错误后 controller 被驱逐、驱逐后重新解析读到库内最新状态（模拟「另一 target 写过 restricted」）、属主写正常成功且逐位与今天一致。

## 5. aidcp-cloud — 记账 outbox

- [ ] 5.1 新增 `src/risk/risk-counter-outbox-store.ts`：`enqueue({accountId, action, occurredAt, dedupeKey})`（`ON CONFLICT (execution_target, dedupe_key) DO NOTHING`）、`claimBatch({workerId, leaseMs, limit})`（`FOR UPDATE SKIP LOCKED` + `execution_target=$local`，照抄 `delegated-task/store.ts:493-516`）、`applyClaimed(rows)`、`recoverExpiredClaims()`（照抄 `store.ts:418-475`）、`backlogCounts()`。
- [ ] 5.2 `applyClaimed` 必须在**单事务**里完成 `INSERT INTO risk_counters(account_id, action, count, occurred_at, outbox_id) … ON CONFLICT (outbox_id) DO NOTHING` 与 `UPDATE risk_counter_outbox SET status='applied'`；exactly-once 由 1.4 的唯一索引保证，MUST NOT 用内存 Set 去重。
- [ ] 5.3 `src/comm/handler.ts` 的回执分支（`:715-750`）：在 `emit('interaction.occurred', …)` **之前**同步 `await` outbox 入队，`dedupeKey = \`${env.id}:${result.action}\``。入队失败 MUST 抛出到调用方并触发 5.4，MUST NOT 吞掉后照常 emit。
- [ ] 5.4 入队失败的处理：写 P1 告警 + 该账号进入 fail-closed（暂停继续下发自动互动命令，直到人工或下一次成功入队解除）。**MUST NOT 静默继续浏览闭环**——那等于明知记不上账还继续制造真实平台动作。
- [ ] 5.5 `src/server.ts` 的 `interaction.occurred` 订阅（`:1592-1612`）改造：删掉其中的 `await c.record(evt.action)`，改为「取写入前判定 `explain`（`:1598` 语义逐字保留，供 `pacingAlerter`）→ 触发一次立即 apply」。`search.occurred` 订阅（`:1677-1687`）同样改造。**内存计数只在 apply 成功时递增，全系统只此一条路径**。
- [ ] 5.6 `RiskController.record`（`:221-227`）拆成两半：`recordFact(action, occurredAt)`（仅递增内存计数，由 apply 驱动）与保留的判定取值；`store.appendCounter` 的直接调用从 controller 移出，改由 outbox apply 承担。注释里那段「求值顺序不可换」的不变量必须保留并更新到新路径。
- [ ] 5.7 outbox worker：入队后同进程立即触发一次 apply；轮询（默认 5s）只作崩溃恢复兜底。启动时 `recoverExpiredClaims()` 并把回收条数写进启动日志（对齐 `server.ts:1527-1531` 的形态）。
- [ ] 5.8 死信：`attempts` 超限（默认 5）转 `status='dead'` + P1 告警，MUST NOT 静默丢弃。积压量与死信量落 `alerts` 或指标口，必须可被面板读到。
- [ ] 5.9 单测：崩在 emit 与 apply 之间后重启能补记（模拟：入队成功、不 apply、重建 store、跑 recover + apply，计数只 +1）；同 `dedupeKey` 重复入队只产生一行；同一 outbox 行 apply 两次 `risk_counters` 只增一行；`attempts` 超限进 dead 且有告警。

## 6. aidcp-cloud — 计数与库内事实对账

- [ ] 6.1 新增周期对账（默认 5 分钟，`AIDCP_RISK_RECONCILE_INTERVAL_MS` 可配）：对已物化的每个 controller，用 `PgRiskStore.totalsForAccountSince`（`:149-158`）取当日总量，与 `RiskController.counts()`（`:413-415`）比对。
- [ ] 6.2 判据是**偏差是否为零**，MUST NOT 引入容忍阈值。偏差非零 → 写告警（带 accountId / action / 内存值 / 库值）并**以库为准重建**该账号计数（重放 `loadCounters`）。
- [ ] 6.3 归属占位成功、归属变更后重新解析 controller 时，MUST 强制重放一次计数（不复用可能陈旧的内存值）。
- [ ] 6.4 单测：库里被外部插入一行后，对账能检出偏差、发告警、重建后内存值等于库值。

## 7. aidcp-cloud — 面板读写口归位

- [ ] 7.1 `src/panel/panel-server.ts:711-720` 的首页汇总改用 4.4 的只读口：非本 target 归属账号 MUST NOT 物化可写 controller；保留 `:717-719` 既有的「拿不到就不带上限」诚实缺省。
- [ ] 7.2 `/risk/signal`（`:1628-1636`）与 `/risk/quota`（`:1655-1656`）在非属主时返回 409 + `risk_state_not_owned` + 真实归属 target，MUST NOT 返回 200、MUST NOT 返回看起来成功的 `changed:false`。
- [ ] 7.3 面板账号 DTO 增加 `executionTarget`（可为 null=未归属）与 `riskWritable: boolean`；服务端权威，MUST NOT 让 Console 自己推断。
- [ ] 7.4 单测：非属主账号的两个写口返回 409、首页汇总对非属主账号不物化 controller。

## 8. aidcp-console — 归属可见性与非属主只读

- [ ] 8.1 账号相关 API 类型补 `executionTarget` / `riskWritable`（与 cloud 同源，避免枚举/字段漂移）。
- [ ] 8.2 账号列表与风控操作区：非属主账号的「风控信号 / 配额档位」写操作禁用，并显示真实归属 target 与「请在 <owner> 后台操作」。未归属（null）显示为「未归属」而不是伪装成本 target。
- [ ] 8.3 收到 409 `risk_state_not_owned` / `owner_change_blocked_by_active_session` 时，MUST 显示可区分的失败态，MUST NOT 显示成功或静默无反应。
- [ ] 8.4 补少量聚焦测试：非属主行的写按钮禁用、409 的失败态渲染。

## 9. aidcp-edge — 拒绝码诚实呈现

- [ ] 9.1 客户端把握手拒绝码 `execution_target_mismatch` 如实呈现（文案含真实归属 target 与处理办法），MUST NOT 渲染成通用「云端离线 / 连接失败」。不新增协议消息类型、不动主动命令白名单。
- [ ] 9.2 确认该拒绝走的是既有 `onConfigError` 通道形态，与 `platform_mismatch` / `missing_account_id` 一致，不新增分支语义。

## 10. aidcp（控制仓）— 文档

- [ ] 10.1 `docs/cloud-service-decomposition-proposal.md` **§14.1 红线表 `AC-DECOMP-09` 行**（该文档不存在 §14.9，顶层编号 §1–§17 冻结，**MUST NOT 新增 §14.x 小节**）：在「红线」列补入可验收句式「对任一 `accountId`、任一时刻，`risk_state` 的写入者唯一，且配额判定所依据的计数与库内事实一致」；在「验收方式」列补写者锁与部署约束（每 target 单实例、stop→start、禁止滚动 / 蓝绿）。注意该行的「验收方式」列已按分两段兑现改写（阶段 2 凭据 + 静态门禁 / 子目标 B 后 GRANT），本项 MUST 在其上追加，MUST NOT 覆盖。
- [ ] 10.2 §12 阶段 2「验证各进程独立停止、重启和回滚」旁补「单实例 / 可多实例」组件分类表（内容见本 change 的 spec delta），并写明新增后台组件必须先归类。
- [ ] 10.3 §5.1 单一写入者表的「最终风险状态」行补一句：写权按 `accounts.execution_target` 排他，`risk_counters` 作为既成事实账本不按 target 分裂。
- [ ] 10.4 §11 故障表补一行「自动化写者锁不可获得」：应保持可用=客户数据与内容服务；允许受影响=该 target 的自动化整体不启动（诚实失败，不降级为无锁运行）。
- [ ] 10.5 `docs/risk-control.md` 补跨进程单写、outbox 记账链路、对账机制三节。
- [ ] 10.6 `docs/deployment-environments.md` 补写者锁运维段：如何确认锁持有者、`kill -9` 后如何强制释放、为什么禁止滚动 / 蓝绿。

## 11. 验证与交付

- [ ] 11.1 cloud：`npm run test:acceptance` → `npm test` → `npm run typecheck` 全过；`AC-RISK-*` 必须全绿（本变更直接改风控写路径）。
- [ ] 11.2 edge：`npm run typecheck` + `npm test`（本变更对 edge 只有文案层改动，但握手拒绝路径有回归面）。
- [ ] 11.3 console：`npm run typecheck` + `npm run build` + 聚焦测试。
- [ ] 11.4 `openspec validate risk-state-cross-process-integrity --strict` 通过。
- [ ] 11.5 部署 dev（观察模式：`AIDCP_RISK_OWNERSHIP_ENFORCE=false`），按 `CLAUDE.md` §5 安全序列走；部署后验证写者锁已持有、outbox 积压为 0、对账偏差为 0、账号归属自证占位符合预期。
- [ ] 11.6 观察期结束后单独提交一次「翻开 `AIDCP_RISK_OWNERSHIP_ENFORCE=true`」的变更，并在 tasks 里记录观察期实测的跨 target 争用次数（预期 0；非 0 则先查清归属再翻）。
- [ ] 11.7 真机验收项（双 target 同时驱动同一账号被拒、滚动部署第二实例启动失败、崩溃点补记）登记进 `docs/real-machine-acceptance-backlog.md`，按共享真机环境归簇。
