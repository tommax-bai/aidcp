# Block③ L3 物理拆库·切换执行计划（owner-URL 翻转策略）

> 生成于 2026-07-25。用户已定策略 = **owner-URL 整体翻转**（非逐表双写）。
> 本文档是「L3 真正怎么切」的权威地图 + 排序 backlog，由一次跨 owner 依赖全量测绘（3 agent 并行扫三 owner + 综合）产出，逐处 `file:line` 核实。
> **前置**：L2 已 DONE（cloud master `653e910`，部署 dev；per-owner 池已接线、baseline 已做，见 `cloud-block3-db-split-handoff.md` §0）。

## 0. 两条改变全局的已核实事实

1. **账号从不物理删除**（migrations/scripts/src 全仓零 `DELETE FROM accounts`，account-store 不暴露任何 delete）→ 12 条 `ON DELETE CASCADE` 跨域外键**在实践中从不触发**。⇒ **降外键（0076 及新发现的 6 条 DDL FK）行为无影响、account-delete-cascade 接线可推迟到「真加删账号功能」时**。危险窗口基本消失。
2. **拓扑**：dev 与 ol **连同一台物理 PG**（PG 在 dev 机 `121.89.85.150:5432`，dev 走 `127.0.0.1`、ol 跨网络走 `121.89.85.150`；实例 id 同、账本同 73 行）。这台"dev 机"的 PG **就是生产库**。dev 机上 `sudo -u postgres` peer 认证可用 = **有超级用户 + CREATEDB**（app 角色 `aidcp` 无 CREATEDB，`rolcreatedb=f`）。
3. **可逆隔离切法**：建 owner 库 + 从 aidcp **只读**拷贝数据进新库 + **仅 dev 端**设 `AIDCP_PG_<OWNER>_URL` → **aidcp 全程零改动、ol 零风险、unset+重启即回滚**。0076 只在将来 ol 也翻转（aidcp 那份表退役）时才需要。

## 1. 翻转就绪矩阵（核心结论：没有一个 owner 现在能干净翻转）

| owner | 跨库依赖 | 读 | 写 | 跨库事务 | 已走端口 | **raw(阻塞)** | 角色 | 结论 |
|---|---|---|---|---|---|---|---|---|
| **content** | 7 | 7 | 0 | 0 | 0 | **7** | leaf（无人读它）| 修完 7 处即可**最先翻** |
| **automation** | 24 | 17 | 3 | 4 | 2 | **22** | **HUB**（api 读它 12+ 表）| 与 api 互相纠缠 |
| **api** | 27 | 21 | 1 | 5 | 1 | **26** | **HUB**（owns `accounts`）| 与 automation 互相纠缠 |

合计 58 依赖 / **55 raw**。全部跑在 local pool，只有 3 处已在端口后（automation `interaction-store.ts:1736/1819`、api `client-user-store.ts:683`，仍传 `this.pool`，翻转时把端口实现切 HTTP 即可）。

**最危险的三类（静默原子性丢失，非简单 HTTP 化能解）**：
- **4 个 config-mirror 跨库事务**：`quota-config-store.ts:243` / `pacing:181` / `session:276` / `resume:249`，各在 `pool.connect()+BEGIN` 里写自己的 automation 表 + `bumper.bumpInTx(client)` 写 **api 的 `config_mirror_version`** + `COMMIT`，**单物理连接**。注入的 bumper 只切调用点、**切不动原子性**——`config_mirror_version` 一到别的库这笔事务就断。**automation 或 api 任一翻转即触发**。修法：把 bump 移出写事务（异步 outbox / 最终一致的版本信号）或在本地复制版本计数。
- **1 处 raw 跨库写（真边界违规）**：automation `interaction-store.ts:1839` `INSERT interaction_audit_events`（api 属主）——该表被两个 owner 双写。修法：走写端口（镜像 `:1819` 的 DELETE 端已走的 `InteractionApiPurgePort`）。
- **5 处 api→automation offboard 联合提交**：`client-user-store.ts:513/619/1519/2151/2233`，经 `OffboardWritePort` 写 automation 表、但与 api 表在**同一 `BEGIN/COMMIT`** 内共提交。端口切调用点干净，**原子性在拆库时断** → 拆成两次独立提交（2-phase / outbox）。

**连接路由地雷（callout b，非表依赖、是接线 bug）**：`event_outbox`/`event_outbox_cursor`/risk 命令 outbox 属 automation，但 `emitRiskCommand`（server.ts:6052）/ `startRiskCommandConsumer`（:2442）/ `bridgeEventBusToOutbox`（:2453）/ `PanelEventReplay`（:6133）在组合根用的是 **api 的 configMirrorPool**。单库字节等价，拆库后读写错库。**修法（纯字节等价、可先做）**：把这 4 个 helper 改绑 automation 池（需把 `automationPool` 挂上 ctx，段间传递）；`ConfigMirrorRefresher`（:2886，读 api 的 `config_mirror_version`）**保持 api 池**。

## 2. 逐 owner 修法清单（每处 = file:line + 外表 + 修法）

### content（leaf，7 raw；修完最先翻，翻它不连累任何人）
| file:line | 外表(owner) | 方向 | 修法 |
|---|---|---|---|
| `curated-content-store.ts:1192` | `delegated_tasks`(automation) | 读 | **最难**。`listForClient` 的 created/uncreated 筛选：与 `curated_content` 同一 SELECT 里 `EXISTS(SELECT 1 FROM delegated_tasks dt WHERE dt.account_id=c.account_id ...)`。拆成两步：先取 curated 行，再 HTTP 问 automation 哪些 record 被触发。**改查询语义，须测行为。** |
| `facebook-publish-media-store.ts:490` | `accounts`(api) | 读 | `assertFacebookAccount` 每次媒体操作前 `SELECT platform FROM accounts`（269/274/294/330/375/412/478 都调）。走 api 读端口；热路径宜缓存/去规范化 platform。 |
| `draft-refinement.ts:226` | `publish_log`(api) | 读 | `claimNext` 的 `FOR UPDATE SKIP LOCKED` CTE 里 `EXISTS(SELECT 1 FROM publish_log pl WHERE pl.id=record_id)`。改 HTTP 存在性校验 / 移走悬挂任务守卫。 |
| `facebook-publish-media-store.ts:108` | `accounts` FK(DDL) | — | **翻转时 DROP**（运行时替代=:490）。 |
| `facebook-publish-media-store.ts:118` | `publish_log` FK(DDL, `used_by_publish_log_id`) | — | **DROP**（可空、纯审计）。 |
| `facebook-publish-media-store.ts:141` | `publish_log` FK(DDL ALTER 回填) | — | **DROP**（同上、旧库路径）。 |
| `draft-refinement.ts:52` | `publish_log` FK(DDL `ON DELETE CASCADE`) | — | **DROP**（替代=:226）。 |

自证干净：`concept-store`（concepts）、`token-usage-store`（llm_token_usage/llm_billing_price_snapshot）。

### automation（HUB，22 raw：4 tx + 1 raw 写 + 17 读）
- **4 config-mirror 跨库事务**（见 §1 最危险，架构级）。
- **raw 跨库写** `interaction-store.ts:1839` → `interaction_audit_events`（api）：走写端口。
- `pg-risk-store.ts:296/350` → `accounts`（api）：风控单写者把 `risk_state` upsert 门控在同语句内联 `SELECT ... accounts.execution_target` → 本地去规范化 execution_target 或 HTTP 预检。
- `interaction-store.ts:671/678` → `client_env_revocation_holds`/`accounts`（api）：`FOR SHARE` **跨库行锁**（不可跨库）→ 移守卫/去规范化。
- `interaction-store.ts:1320` → `accounts`（api）：写 `interaction_runtime_controls` 时内嵌 `EXISTS(accounts)` 守卫 → 去规范化/HTTP。
- `facebook-group-store.ts:471/716/763/786/825/1072/1088` → `accounts`（api）：校验/facet/覆盖读 → **把 accounts 的投影（platform/group_label）去规范化进 automation 库**。
- `facebook-group-store.ts:870/915` → `accounts`（api）：在 `claimNext`/`DELETE membership` **写路径**里 → 同库守卫（去规范化）。
- `facebook-group-store.ts:294`、`delegated-task/store.ts:33` → `accounts` FK(DDL)：**DROP**。
- `delegated-task/store.ts:515` → `accounts`（api）：`UPDATE` 认领 CTE 内 `EXISTS(accounts)` → 去规范化/本地守卫。
- 已走端口：`interaction-store.ts:1736`（`interaction_reply_configs` DELETE 经 `InteractionApiPurgePort`）、`:1819`（`interaction_audit_events` DELETE 经端口）。

### api（HUB，26 raw：5 tx + 21 读，全在 2 文件）
- **`client-auth/client-user-store.ts`**（微信环境 offboard/scope 生命周期）：14 处 raw 读 automation 表（含 `interaction_auth_state`/`interaction_offboards`/`interaction_runtime_controls`/`risk_state` 的 `FOR UPDATE` 跨库锁 + `1359/2210/2225/2254` 的 **api+automation 同查询 JOIN**，须拆两查询）；**5 处 offboard 跨库联合提交**（见 §1）；已走端口 `:683`（只写 automation 表、无 api 共写→可干净切 HTTP）。
- **`panel/panel-store.ts`**（只读看板）：**7 处 raw 读**（`400 risk_state`、`422/439/469 risk_counters`、`592 alerts`、`633 interaction_feed`、`634 interaction_target_meta`）→ **最容易的一批**，走 automation 读端口即可。

## 3. 推荐执行顺序

0. **（纯字节等价、可先做，无行为变更）** callout b 的 outbox 池改绑（automationPool 挂 ctx + 4 helper 改绑）。测 + 部署 dev。
1. **content 先翻**（leaf、7 处、不连累任何人）：路由它对外的 3 处读（`delegated_tasks`/`accounts`/`publish_log`，其中 2 处关联子查询要 2 步重写、须测行为）→ 建 aidcp_content + 拷数据（去 4 条 DDL FK）→ **dev 端设 AIDCP_PG_CONTENT_URL** 隔离验证（aidcp 不动、ol 不动）。
2. **api↔automation 是互相纠缠的双 HUB，须一起解**：先做**读端口批**（api 的 panel 7 读 + client-user 14 读；automation 侧 api 读它的风控/互动表），再攻**跨库事务/写**（4 config-mirror bump + 5 offboard 联合提交 + interaction_audit_events 双写 → 架构级最终一致重设计）。两者读干净 + 事务拆完后，才能各自翻。
3. **ol 共享翻转 + 0076**：dev 全程验证通过 → 用户在场 → **整库 pg_dump 备份** → 各 owner 表数据搬进 owner 库 → dev+ol 同设 owner URL（同值共享三库）→ 重启两端（短停机窗口）→ apply 0076 降 aidcp 的跨域 FK（此时 aidcp 那份表退役）。

## 4. 红线（不变）
- **dev 先、ol 备份先、绝不碰同机 isales、每步可回滚。**
- 跨库事务**绝不**当成「HTTP 化就行」——原子性不能跨库，必须显式改成最终一致（outbox/2-phase）并接受语义变化，且须测。
- 关联子查询/跨库 JOIN 改 2 步调用是**行为变更**，MUST 有测试覆盖、MUST 在 dev 验证，不在生产盲改。
- **本文档的每处 `file:line` 为 2026-07-25 测绘实测，fleet 活跃、动前先复核偏移。**
