# 库级作用域机制清单（Database-Scope Inventory）

> change `cloud-schema-migration-executor`（design.md D8）。机器可读副本在
> `aidcp-cloud/test/schema/database-scope-inventory.json`，由 `npx tsx scripts/generate-db-scope-inventory.ts --write` 生成；
> 验收用例 `AC-SCHEMA-DB-SCOPE`（`aidcp-cloud/test/acceptance/schema-db-scope.test.ts`）断言两者一致，
> **新增未登记条目即失败**。只写文档不加测试等于没做。
>
> 数据为 2026-07-22 在 `aidcp-cloud` master + 本 change 分支上的实测。

## 0. 先纠正一个容易被误读的点

`pg_advisory_lock` 与外键都是**数据库级**作用域，与 schema 无关。

- 把表搬进新 schema：锁**照常互斥**，外键**照常生效**。不需要为「搬 schema」改动任何一条。
- 真正拆成两个数据库：锁**不再互斥**、外键**根本不存在**。
- 而且这两种失效都是**静默的**——不报错、业务照跑，数据慢慢分叉。这正是本项目第一红线禁止的形态，
  所以这份清单必须由源码扫描用例锁死，而不是靠人眼评审。

把「拆 schema」和「拆库」混为一谈的代价是双向的：以为搬 schema 就得先换掉这些锁 → 做一次完全没必要、
风险更高的改造；以为拆库跟搬 schema 一样安全 → 悄悄失去全部互斥与引用完整性。

## 1. advisory lock（8 处）

| 机制 | 位置 file:line | 当前作用域 | 拆 schema 后 | 拆库后 | 拆库替代方案 |
| --- | --- | --- | --- | --- | --- |
| `pg_advisory_xact_lock(hashtext(...))`，key 为收件箱批次幂等键 | `aidcp-cloud/src/interactions/interaction-store.ts:430` | 数据库级，事务生命周期 | 仍互斥 | **静默失去互斥** | 对权威表行 `SELECT … FOR UPDATE`，或持久命令 + Inbox 去重 |
| `pg_advisory_xact_lock(hashtext('interaction-send|<accountId>'))` | `aidcp-cloud/src/interactions/interaction-store.ts:1011` | 同上 | 仍互斥 | **静默失去互斥** | 同上 |
| `pg_advisory_xact_lock(hashtextextended('offboard-admission-command|<target>|<commandId>',0))` | `aidcp-cloud/src/client-auth/offboard-admission-ledger.ts` | API owner 数据库级，事务生命周期；只串行化同一 command receipt 与 owner-local ledger 副作用 | 仍互斥 | 随 API owner 表迁移后仍在同一 API 库互斥；若错误拆到别库则**静默失去幂等串行化** | 保持锁与 `client_env_admission_command_receipts` 同库；或改为先建 command row 再 `FOR UPDATE` |
| `pg_advisory_xact_lock(hashtextextended('offboard-admission-capability|<target>|<capability>',0))` | `aidcp-cloud/src/client-auth/offboard-admission-ledger.ts` | API owner 数据库级，事务生命周期；串行化 complete snapshot 的首次 cursor 建立与替换 | 仍互斥 | 随 API owner snapshot/hold 表迁移后仍在同一 API 库互斥；若错误拆到别库则**静默失去 snapshot 顺序** | 保持锁与 `client_env_admission_snapshot_state` 同库；或引入可先占位的 owner row lock |
| `pg_try_advisory_lock(hashtext('aidcp_automation_writer'), hashtext(<target>))` 风控单写者锁 | `aidcp-cloud/src/risk/writer-lock.ts:143` | 数据库级，**会话**生命周期（专用长连接，MUST NOT 走 pool） | 仍互斥 | **静默失去互斥**（两个自动化进程会同时自认写者） | 对 `risk_state` 权威行 `FOR UPDATE`，或把写者选举挪到进程外协调 |
| `pg_advisory_unlock(...)` 释放上一条 | `aidcp-cloud/src/risk/writer-lock.ts:205` | 同上 | — | — | 同上 |
| `pg_try_advisory_lock(<固定 key>)` 迁移执行器整批互斥 | `aidcp-cloud/scripts/migrate.ts:148` | 数据库级，会话生命周期 | 仍互斥 | 拆库后每个库各有自己的账本与锁，**这是正确的**（一个库一条版本序列） | 无需替代 |
| `pg_advisory_unlock(<固定 key>)` 释放上一条 | `aidcp-cloud/scripts/migrate.ts:209` | 同上 | — | — | 无需替代 |

**历史修正（重要）**：design.md D8 与 tasks 9.2 记的是「7 处，含 `interaction-env:<envKey>` 命名空间被 client-auth
与 interactions 两域共用」。那 3 处 `client-user-store.ts` 的 `interaction-env:` 锁**已在 change
`publish-approval-signal-to-database` 中被消除**，改为 `client_environments` 的行锁
（`aidcp-cloud/src/db/environment-row-lock.ts`），并由验收用例 `AC-LOCK-01` 断言它不再出现。
本清单记录的是**当前事实**，不是提案时的快照。

## 2. 跨域外键

### 2.1 源码里的外键（17 处，全部在存储的 DDL 常量里）

| 目标 | 处数 | 引用点 |
| --- | --- | --- |
| `accounts(account_id)` | 5 | `src/comment-agent/facebook-group-store.ts:396`、`src/config/approval-policy-store.ts:29`、`src/config/persona-store.ts:60`、`src/delegated-task/store.ts:36`、`src/onboarding/first-post-onboarding-store.ts:28` |
| `client_users(user_id)` | 3 | `src/client-auth/client-user-store.ts:183`、`:273`、`src/config/persona-auto-fill-store.ts:52` |
| `facebook_group_target(group_url)` | 2 | `src/comment-agent/facebook-group-store.ts:367`、`:397` |
| `delegated_tasks(id)` | 2 | `src/delegated-task/store.ts:112`、`:123` |
| `account_facebook_publish_image(id)` | 2 | `src/publish-agent/facebook-publish-media-store.ts:115`、`:126` |
| `account_facebook_publish_image_set(id)` | 1 | `src/publish-agent/facebook-publish-media-store.ts:107` |
| `client_environments(env_key)` | 1 | `src/client-auth/client-user-store.ts:245` |
| `persona_auto_fill_runs(run_id)` | 1 | `src/config/persona-auto-fill-store.ts:66` |

### 2.2 迁移目录里的外键（按目标表计数）

`accounts` 21 · `client_users` 4 · `publish_log` 3 · `interaction_reply_config_scopes` 3 ·
`delegated_tasks` 2 · `facebook_group_target` 2 · `account_facebook_publish_image` 2 ·
`account_facebook_publish_image_set` 1 · `client_environments` 7 · `facebook_consumption_progress` 2 ·
`facebook_consumption_action` 1 · `persona_auto_fill_runs` 1 · `interaction_messages` 1 ·
`interaction_reply_jobs` 1 · `interaction_threads` 1。

本 change 新增三条 `client_environments` 外键，来自
`facebook_operation_policy.env_key`、`facebook_operation_policy_audit.env_key` 与
`facebook_environment_slow_start_completion.env_key`；配置、审计、按执行目标隔离的慢启动毕业事实
与环境台账均属 `aidcp-api`，物理拆库时 MUST 保持同库迁移。该毕业事实即使按
`execution_target` 分行，外键仍是数据库级约束：拆 schema 后成立，拆库后不成立。
`facebook_consumption_view_fact`、`facebook_consumption_action` 对
`facebook_consumption_progress` 的两条外键，以及 action result 对
`facebook_consumption_action` 的一条外键，均处于 `aidcp-automation` 运行事实域，也 MUST 同库。
若未来拆分这些属主内表，必须先改为持久命令/应用层存在性校验，并让孤儿引用 fail-closed。

**指向 `accounts(account_id)` 合计 26 处**（迁移 21 + 源码 5），与 design.md 的总数一致。
分项变化来自 ① 本 change 第 3 节补齐的迁移把两条既有外键写进迁移目录；② 源码旧盘点曾把
`src/client-auth/client-user-store.ts` 注释里的反例说明「故意不写 REFERENCES accounts」误算成真实
外键；③ publish media 的运行时 DDL 已不再直接引用 `accounts`。扫描器因此 MUST 先剥注释。

**作用域结论（全部外键共用）**：拆 schema 后仍生效（外键是数据库级、可跨 schema）；
拆库后**外键根本不存在**，脏引用无人拦、且无任何错误。

**拆库替代方案**：应用层校验 + 读侧 fail-closed。范式已存在于
`aidcp-cloud/src/client-auth/client-user-store.ts:123-127` 与 `:1803`——`client_environments.account_id`
因启动顺序被迫放弃外键，完整性改由读侧每次 JOIN `accounts` 承担，悬空绑定读时归入 `binding_unknown`
而不是当成「未绑定」。这条先例正好是拆库后的可复用形态。

## 3. 跨多表单事务清理（1 处）

| 机制 | 位置 | 当前作用域 | 拆 schema 后 | 拆库后 | 替代方案 |
| --- | --- | --- | --- | --- | --- |
| `purgeDueOffboards` 在**一个事务**里清 11 张表 | `aidcp-cloud/src/interactions/interaction-store.ts:1634-1686` | 数据库级事务 | **仍原子** | **不再原子**：部分表清掉、部分没清，且不报错 | 改为可重入的分表 saga，每张表的清理独立幂等，进度落库 |

## 4. 硬编码 schema 名的形状探测（7 处）

| 位置 | 字面量 |
| --- | --- |
| `aidcp-cloud/src/interactions/interaction-store.ts:301` | `public.interaction_threads` |
| `aidcp-cloud/src/interactions/interaction-store.ts:302` | `public.interaction_reply_configs` |
| `aidcp-cloud/src/interactions/interaction-store.ts:303` | `public.interaction_offboards` |
| `aidcp-cloud/src/interactions/reply-config-scope-store.ts:130` | `public.interaction_reply_config_scopes` |
| `aidcp-cloud/src/interactions/reply-config-scope-store.ts:131` | `public.interaction_reply_scope_versions` |
| `aidcp-cloud/src/interactions/reply-config-store.ts:72` | `public.interaction_reply_configs` |
| `aidcp-cloud/src/interactions/reply-config-store.ts:73` | `public.reply_templates` |

**改 `search_path` 救不了这些**：schema 名写死在字面量里，搬 schema 后 `to_regclass('public.xxx')`
会指向一个已经不在那里的对象，探测结果是「表不存在」，而调用方会把它当成「schema 缺失」处理。

**收口进度**：第 8 处（`src/cache/curated-content-store.ts:365`）已在本 change 收口到唯一解析点
`aidcp-cloud/src/schema/schema-name.ts` 的 `qualifiedObjectName()`，行为不变（默认仍是 `public`）。
剩余 7 处全在 `src/interactions/**`，属互动域单写者的热点文件，**未在本 change 内改动**——
互动域下一批改动时收口（本 change 未授权改动这三个文件），`AC-SCHEMA-DB-SCOPE` 会盯住它们不再增加。
