## Context

### 现状（每条断言给 file:line）

**风控状态的读写路径**

- `RiskController.create()` 读一次库、回放一次计数：`aidcp-cloud/src/risk/risk-controller.ts:140-149`（`loadState` + `loadCounters(now - WINDOW_MS.day)`）。
- 之后状态只在内存变更，写回是全列 upsert、无版本列、无条件谓词：`aidcp-cloud/src/risk/pg-risk-store.ts:191-204`（`ON CONFLICT (account_id) DO UPDATE SET` 七列全覆盖）。
- 进程内并发写已被串行化，但只在进程内：`aidcp-cloud/src/risk/risk-controller.ts:123`（`mutationChain`）、`:234-241`（`enqueue`）。三个写入口 `applySignal:243-249`、`recoverRestricted:255-280`、`setQuotaLevel:286-292` 都经它。
- 注册表的 controller Map 无 delete / TTL / 失效：`aidcp-cloud/src/risk/risk-controller-registry.ts:29`（`new Map`）、`:49-56`（`getController` 只增不删）。注释 `:22-27` 声称「绝不出现两个内存 controller 写同一 risk_state」，该断言只在单进程内成立。
- 注册表注释 `:9-12` 进一步声称「Map 永不驱逐从坑变成不再相关的事实」——那只对养号配置（已改同步现读）成立，对 `state` 与 `counter` 不成立。

**配额计数的判定路径**

- 准入判定读的是内存计数：`aidcp-cloud/src/risk/risk-controller.ts:160-172`（`explain` 逐窗口 `this.counter.count`）。
- 记账只累加本进程自己的那一笔：`aidcp-cloud/src/risk/risk-controller.ts:221-227`（`counter.record` + `store.appendCounter`）。
- 库侧已有现成聚合口，但准入路径从不调用它们：`aidcp-cloud/src/risk/pg-risk-store.ts:138-158`（`todayTotalsForAccount` / `totalsForAccountSince`）。
- 计数按上海自然日与滑动窗剪枝：`aidcp-cloud/src/risk/sliding-window-counter.ts:10-14`。

**跨进程冲突（今天就在发生）**

- dev 与 ol 共用同一个 PostgreSQL、只靠 `account_id` 区分：`docs/deployment-environments.md:62-64`。
- `risk_state` / `risk_counters` 无 target 维度：`aidcp-cloud/src/risk/pg-risk-store.ts:29-51`。
- `accounts` 表无 target 维度：`aidcp-cloud/src/account-store.ts:34-49`。
- 面板首页汇总为库里全部账号物化并永久缓存 controller：`aidcp-cloud/src/panel/panel-store.ts:471-474`（`listAccounts` 无过滤）→ `aidcp-cloud/src/panel/panel-server.ts:711-720`（`riskRegistry.getController(entry.accountId)`）。
- 两个整行盲写口：`aidcp-cloud/src/panel/panel-server.ts:1628-1636`（`/risk/signal` → `applySignal`）、`:1655-1656`（`/risk/quota` → `setQuotaLevel`）。

**跨重启丢账**

- 边缘回执 → 事件 → 记账是 fire-and-forget，异常只 `console.warn`：`aidcp-cloud/src/server.ts:1592-1612`；搜索侧同形：`aidcp-cloud/src/server.ts:1677-1687`。
- 事件的发射点在回执处理里，发完即返回、不等待落库：`aidcp-cloud/src/comm/handler.ts:735-750`（`emit('interaction.occurred', …)`）、`:1026`（`risk.record` 通道，边缘未接线）。
- 这条链上没有任何持久中间态：`grep -i outbox aidcp-cloud/src` 只命中协议注释 `aidcp-cloud/src/comm/protocol.ts:123,133`（那是 **Edge 侧**互动结果的 outbox，与云端记账无关）。

**仓内可照抄的正例**

- 委托任务：`aidcp-cloud/src/delegated-task/store.ts:493-516`（`claimNext`：`FOR UPDATE SKIP LOCKED` + `claim_token` + `claim_expires_at` + `execution_target` 过滤）、`:418-475`（`recoverInterruptedClaims`：启动回收被中断的认领并留事件）、`:29`（`execution_target` 列 + CHECK）、`:87-94`（target 打头的去重与认领索引）。
- 内容排期小时格：`aidcp-cloud/src/config/content-schedule-store.ts:268-276`（表带 `execution_target`）、`:426-450`（条件 upsert 原子占位，同格返回 false）。
- 部署目标解析 fail-closed：`aidcp-cloud/src/deployment-target.ts:6-11`、`aidcp-cloud/src/server.ts:503`。

**必须单实例的既有组件（内存态即权威）**

- 发布下发器：`aidcp-cloud/src/publish-agent/publish-dispatcher.ts:145`（`inFlight`）、`:147`（`accountTail`）、`:151`（`openBreakers`）——`publish_log` 无 dispatch 级认领。
- 验证码协助：`aidcp-cloud/src/comm/captcha-assist.ts:153`（`incidents`）、`:159`（`recoveryLeases`）；协助链接必须指向签发进程本身，见 `docs/deployment-environments.md:116`。
- 连接运行时注册表：`aidcp-cloud/src/orchestrator/connection-runtime.ts:81-82`（`bySession` Map），WebSocket 连接天然进程本地。

### 约束

- dev / ol 共库期间**禁止破坏性 DDL**（`docs/deployment-environments.md` 2026-07-11 状态段）：本变更全部 DDL 必须是 `ADD COLUMN IF NOT EXISTS` / `CREATE TABLE IF NOT EXISTS` 级别的 additive。
- 本仓无迁移执行器，schema 靠各 store `init()` 里的幂等 SQL 自愈（`aidcp-cloud/src/risk/pg-risk-store.ts:28-82` 即范式）。迁移文件与 `init()` SQL 必须同时给出。
- `risk-state-machine.ts` 是 `CLAUDE.md` §7 明列的热点单写文件，本变更需与其它 change 串行。

## Goals / Non-Goals

**Goals**

- 让「风控单写」成为一条能被测试和运维验证的不变量，而不是一句在多进程下自动通过的形容。
- 消除今天 dev / ol 之间真实存在的配额翻倍与状态倒退窗口。
- 让边缘确认的真实动作在任何崩溃点都不丢账，或至少不静默丢账。
- 为拆出 `aidcp-automation` 预先定死它的实例模型，不把这个决定留到迁移期。

**Non-Goals**

- 不改风控状态机的迁移规则（`risk-state-machine.ts` 的 `transition` / `nextStatus` 逐字不动）。
- 不改配额数字、慢启动曲线、节奏系数。
- 不改边云协议：不新增消息类型、不动两份 `protocol.ts`、不动命令桥动作映射、不动主动命令白名单、不动 `action.completed.action` 归一表。
- 不把风控做成独立服务或独立仓（方案 §15 明确当前不新增 `aidcp-risk`）。
- 不引入分布式事务、不引入消息中间件。

## Decisions

### D1. 选定路线 A（单实例），不选路线 B（去单实例依赖）

**路线 A**：承载风控写的进程对每个 `executionTarget` 单实例；部署形态保持 stop→start；禁止滚动 / 蓝绿。
**路线 B**：`risk_state` 加 `version` 列 + 乐观并发条件写；准入判定从内存滑动窗改为按需从 `risk_counters` 聚合（加缓存 TTL）；注册表 controller 缓存加失效机制。

**选 A。三条理由，按权重排序：**

1. **B 买不到它要买的东西。** B 的全部收益是「风控写可以多实例」。但风控写在目标架构里落在 `aidcp-automation`，而同一个进程里还坐着三个同样以内存为权威的组件：发布下发器（`publish-dispatcher.ts:145,147,151`）、验证码协助（`captcha-assist.ts:153,159`）、连接运行时注册表（`connection-runtime.ts:81-82`）。把风控一项改造成多实例安全，automation 仍然必须单实例——只是把「四个理由」减成「三个理由」。付一个数量级的成本换零部署自由度。
2. **automation 的负载轴不是水平扩容轴。** 方案 §12 阶段 3 之所以先提取 content，正因为 AI / FFmpeg / ASR / GPU 是真正的负载源（`docs/cloud-service-decomposition-proposal.md` 阶段 3 四条理由）。automation 的并发上界是同时在线的边缘连接数，而边缘连接数由客户手上的指纹浏览器环境数封顶——那是个几十量级、且受浏览器槽位内存约束的量。为一个不会水平扩的层做去单实例改造属于超前抽象。
3. **A 的成本已经支付过了。** 现状 `systemctl restart aidcp-cloud.service` 就是 stop→start，重叠窗口为零；`CLAUDE.md` §5 的部署安全序列本来就没有滚动 / 蓝绿这一步。A 需要新增的只有「把这个既成事实写成硬约束 + 加一道机械闸」。

**A 的代价必须明说**：从此 automation 的部署有一段（当前实测秒级的）不可用窗口，且不可能通过多副本消除。这不是遗憾，是这类控制面的固有属性——它持有真实平台副作用的准入权，两个副本同时持有该权限本身就是缺陷。

**明确不做 B 的哪几件事**（防止实施期悄悄漂移回去）：不给 `risk_state` 加乐观并发版本列；不把 `explain` 的准入判定改成按需聚合查询（它是同步热路径，浏览闭环每个动作都调，见 `risk/types.ts:33-38` 对同步零 IO 的契约要求）；不给 controller 缓存加 TTL 失效。

### D2. 单实例不能只靠文档，要靠一把机械锁

路线 A 的失效模式是「有人某天为了扩容起了第二个实例，或某个部署脚本改成了滚动」。文档纪律抓不住这个——CLAUDE.md 已经写了三年部署纪律，仍然出过 canonical checkout 被切到发布分支停 24 小时的事故。

**决定**：进程启动时用 PostgreSQL 会话级 advisory lock 按 target 抢一把「自动化写者锁」：

```sql
SELECT pg_try_advisory_lock(hashtext('aidcp_automation_writer'), hashtext($1));  -- $1 = 'dev' | 'ol'
```

- 锁必须挂在一条**专用的长连接**上（不能用 pool，pool 连接会被回收、锁随之释放）。
- 抢不到锁：在有界等待（默认 60s，可配）内重试；仍抢不到即**拒绝启用风控写路径**并写 P1 告警，进程以非零码退出，绝不降级为「无锁照写」。
- 连接断开即释放锁，因此 stop→start 天然可接管；滚动部署的第二个实例会在启动阶段响亮失败，而不是安静地开始双写。
- 已知边界：老进程被 `kill -9` 且 TCP 未被回收时，新进程可能要等到 keepalive 超时。这属于「拒绝启动」而不是「静默双写」，方向正确；运维手册给出显式的强制释放步骤。

`executionTarget` 缺失或非法时，按方案 §8 第 4 条 fail-closed：不抢锁、不启用风控写路径、不启动 outbox worker（现状 `server.ts:503` 已解析 target，`deployment-target.ts:6-11` 已 fail-closed 返回 null）。

### D3. 跨 target 的单写靠「账号归属」，不靠给风控表加 target 列

单实例 per target 只解决同一 target 内的多写者。dev 与 ol 是两个 target、两个进程、一个库，仍然是两个写者。

**否决的做法：给 `risk_state` / `risk_counters` 加 `execution_target` 作为分区键。** 那样同一账号在两个 target 下各有一份独立状态和独立配额——正好把「配额合计翻倍」从 bug 固化成 schema。平台不关心是我们哪个进程点的赞；一个账号在平台眼里只有一份活动预算。

**选定的做法：账号归属唯一。** 新增 `accounts.execution_target`，语义是「该账号当前由哪个 target 的自动化驱动」，服务端注入，禁止从客户端请求、`envKey`、自然语言或边缘上报推导（与方案 §8 第 2 条同一条规则）。由此：

- **握手准入**：`connection-runtime.ts` 的 `onHandshake` 增加一道与既有 `platform_mismatch`（`:148-152`）对称的闸——账号归属非本 target 即拒绝，拒绝码 `execution_target_mismatch`，走同一个 `onConfigError` 通道。
- **首次归属自证占位**：`accounts.execution_target` 允许为 NULL（迁移刻意**不回填默认值**——回填 `'dev'` 会把 ol 的生产账号静默划给 dev）。某账号在本 target 上首次握手成功且归属为 NULL 时，以条件 UPDATE 原子占位（`WHERE account_id=$1 AND execution_target IS NULL`）；占位竞争落败方转为只读并告警，不重试抢占。这条路径照抄内容排期小时格的条件 upsert 占位（`content-schedule-store.ts:438-449`）。
- **归属变更是显式运维动作**：需要该账号在旧属主上无活跃边缘会话，否则诚实拒绝。变更后旧属主的缓存 controller 不需要被同步通知——它的下一次写会被 D4 的条件写谓词挡住并触发驱逐。

### D4. `risk_state` 改条件写，0 行即诚实拒绝

`saveState` 改成带属主谓词的单语句，属主事实唯一权威是 `accounts.execution_target`（不在 `risk_state` 复制一份，避免两处漂移）：

```sql
WITH owner AS (
  SELECT 1 FROM accounts WHERE account_id = $1 AND execution_target = $8
)
INSERT INTO risk_state (account_id, status, quota_level, signal_count, last_signal_at, status_since, updated_at)
SELECT $1, $2, $3, $4, …, …, … WHERE EXISTS (SELECT 1 FROM owner)
ON CONFLICT (account_id) DO UPDATE SET …
RETURNING account_id
```

- `rowCount = 0` 有三种含义：账号不存在、归属为空、归属是别人。三种都必须是**显式失败**（抛 `risk_state_not_owned`，附带真实归属值），MUST NOT 返回成功。
- 失败的处理是**驱逐本地缓存 controller + 告警**，MUST NOT 重试、MUST NOT 改谓词绕过。
- 顺带收掉一个既有隐患：今天 `saveState` 的裸 upsert 能为不存在的账号造幽灵 `risk_state` 行，面板靠应用层 `assertAccountExists`（`panel-server.ts:1627`）挡住；改条件写后这道保护变成结构性的。

`risk_counters` **不加属主谓词**。它是 append-only、无读改写，不存在丢更新；而且「哪个进程记的」不该改变「这次动作是否算数」——归属刚变更时飞在半路的回执仍然要记进同一本账。这是「记账不按 target 分裂」与「状态写按 target 排他」的分工，两者不冲突：分裂的是写权限，不分裂的是事实。

### D5. 记账走 outbox：先落库，再推进

现状是回执处理里 `emit` 完就返回，记账在事件订阅者里异步做、异常吞掉（`server.ts:1592-1612`）。任何在「回执已到、`appendCounter` 未提交」之间的崩溃都静默丢账。

**新表 `risk_counter_outbox`**（照抄委托任务的认领字段形状）：

| 列 | 说明 |
| --- | --- |
| `id` | `BIGSERIAL` 主键，兼作 apply 的幂等键 |
| `account_id` / `action` / `occurred_at` | 既成事实三元组 |
| `execution_target` | `dev` / `ol`，服务端注入；worker 只认本 target |
| `dedupe_key` | `${envelopeId}:${action}`，边缘重发同一信封即天然去重 |
| `status` | `pending` / `applied` / `dead` |
| `attempts` / `last_error` | 有界重试与诚实失败原因 |
| `claim_token` / `claim_expires_at` | 认领令牌 + 租约，同 `delegated_tasks:56-57` |

索引：`UNIQUE (execution_target, dedupe_key)`；`(execution_target, status, claim_expires_at, id)` 供认领扫描（同 `delegated_task` 的 target 打头认领索引 `store.ts:90-91`）。

**写侧顺序**：回执处理在 `emit('interaction.occurred')` 之前先**同步提交** outbox 行；提交失败即视为本次记账失败——告警，并对该账号 fail-closed 暂停后续自动互动下发，MUST NOT 当作无事发生继续浏览闭环。

**apply 侧**：worker 按 `execution_target` 认领（`FOR UPDATE SKIP LOCKED`），在**单个事务**里做两件事——`INSERT INTO risk_counters(..., outbox_id) … ON CONFLICT (outbox_id) DO NOTHING` 与 `UPDATE risk_counter_outbox SET status='applied'`。`risk_counters.outbox_id` 上的唯一索引把 exactly-once 交给数据库，而不是交给内存去重。

**内存计数只在 apply 成功后递增**，只此一条路径，杜绝「emit 时加一次、apply 时又加一次」的双计。为把窗口压到不可观测：入队提交后在**同进程内立即触发一次 apply**，轮询只作为崩溃恢复的兜底，不作为常规路径。

**启动回收**：进程启动时按本 target 回收租约过期的 `pending` 行并记录条数（对齐 `interactionStore.recoverableAttemptIds()` 在 `server.ts:1527-1531` 的启动自检形态）。

**死信**：`attempts` 超限转 `dead` + P1 告警。积压量与死信量必须可读——这是「已经知道自己丢了什么」与「不知道自己丢了什么」的分界。

**判定值的取法不变**：节奏告警依据的 `explain` 判定仍在入队前同步取（`server.ts:1598` 的既有语义逐字保留），outbox 只承载事实、不承载判定。

### D6. 计数对账：让偏差可检出

单写者成立时内存计数是对的；它出错的方式是「有别的东西往库里写了行而我不知道」（归属变更、运维手工 SQL、另一 target 的历史遗留行）。

**决定**：周期（默认 5 分钟）对当前已物化的 controller 做一次当日总量对账——用现成的 `totalsForAccountSince`（`pg-risk-store.ts:149-158`）取库内当日总量，与内存 `counts()` 比对。偏差非零即告警并**以库为准重放重建**该账号计数。不加 TTL 缓存、不改准入路径的同步性质。

判据是「偏差是否为零」，不是「偏差是否超过阈值」——一旦允许阈值，这个信号就退化成噪声。

### D7. 面板：只读投影与可写控制器分家

- `panel-server.ts:711-720` 的首页汇总改为**不物化可写 controller**：非本 target 归属的账号只回库内只读投影（状态取自 `risk_state` 直读，配额上限取自配置计算），拿不到就诚实缺省——保持 `:717-719` 既有的「拿不到就不带上限」诚实回落语义。
- `/risk/signal`（`:1628-1636`）与 `/risk/quota`（`:1655-1656`）在非属主时返回可区分拒绝（HTTP 409 + `risk_state_not_owned` + 真实归属 target），MUST NOT 返回 200。
- 注册表增加 `getReadOnlyState(accountId)` 与 `getWritableController(accountId)` 两个口，让「读投影」与「取写权」在类型层面分开，避免调用点靠注释约束。

## Risks / Trade-offs

- **[归属强制上线后，跨 target 的既有连接会被拒]** → 两阶段发布：先以观察模式上线（`AIDCP_RISK_OWNERSHIP_ENFORCE=false`，只占位、只告警、不拒绝），在 dev 与 ol 各观察一段时间确认零跨 target 争用，再翻开强制。观察模式不是静默：每一次本会被拒的握手都必须留告警。
- **[advisory lock 抢不到导致进程起不来]** → 这是设计意图（拒绝启动优于静默双写）。缓解：有界等待 + 明确的运维手册强制释放步骤 + 告警文案直接说出「另一个实例正持有 <target> 写者锁」。
- **[outbox 引入的记账延迟]** → 入队后同进程立即 apply，轮询只兜底；且 apply 延迟必须可观测（积压量指标）。若延迟不可接受，暴露的是 apply 路径故障而不是设计缺陷。
- **[入队失败导致浏览闭环 fail-closed]** → 这是对「禁止静默假成功」的正确表达：数据库写不进去时，继续驱动真实平台动作而不记账，等于主动制造配额超发。
- **[对账把 5 分钟一次的库查询加到每个已物化账号上]** → 只查当日总量（走 `idx_risk_counters_account_action_time`），且只对已物化 controller 做；账号量级为几十。
- **[单实例约束限制未来扩容]** → 已在 D1 明确接受。若某天 automation 真的需要水平扩，正确的下一步是把「按账号分片 + 分片归属租约」做成显式设计，而不是让两个副本共享一张表赌运气。

## Migration Plan

1. **迁移 `0057`（additive）**：`accounts.execution_target`（可空 + CHECK，不回填）、`risk_counter_outbox`、`risk_counters.outbox_id` + 部分唯一索引。同步在 `PgRiskStore.init()` / `AccountStore.init()` 的幂等 SQL 里补齐（本仓无迁移执行器）。
2. **只读上线**：写者锁 + outbox 写入与 apply + 对账，归属强制关闭。此时行为与今天逐位一致，只是多了持久记账与告警。
3. **观察**：在 dev 与 ol 各观察，确认 (a) 无跨 target 归属争用告警，(b) outbox 积压恒为 0、死信为 0，(c) 对账偏差恒为 0。
4. **翻开归属强制**：条件写谓词生效、握手拒绝生效、面板写口拒绝生效。
5. **回滚**：`AIDCP_RISK_OWNERSHIP_ENFORCE=false` 秒级回到观察模式；outbox 与写者锁可分别用独立旗标关闭。DDL 为 additive，无需数据库回退。

## Open Questions

- `docs/deployment-environments.md` 的长期方向是给 ol 独立 PostgreSQL 边界（spec `deployment-environments` 的 "Dev and ol runtime state must be isolated"）。库真分开后，本变更的归属机制退化为每库一个 target、恒定自证成立，不需要拆除——它同时也是拆库之前唯一能止血的手段。拆库时机不在本变更范围。
- `deployment-environments` 这份 spec 全文为英文，本变更对它的 delta 沿用英文以与被合并文件保持一致；其余两份 delta 为中文，与各自 spec 一致。
