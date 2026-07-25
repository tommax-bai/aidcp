# Block③ L3 物理拆库·切换执行计划（owner-URL 翻转策略）

> 生成于 2026-07-25。用户已定策略 = **owner-URL 整体翻转**（非逐表双写）。
> 本文档是「L3 真正怎么切」的权威地图 + 排序 backlog，由一次跨 owner 依赖全量测绘（3 agent 并行扫三 owner + 综合）产出，逐处 `file:line` 核实。
> **前置**：L2 已 DONE（cloud master `653e910`，部署 dev；per-owner 池已接线、baseline 已做，见 `cloud-block3-db-split-handoff.md` §0）。

## 进展与方法更正（2026-07-25）

**架构原则（2026-07-25 定，此前一版取巧被撤）**：最终目标是**三个真正独立的服务**（各自进程、各自库、只走接口）。铁律 = **一个域绝不直连另一个域的数据库**。跨域读**一律走「拥有那张表的域」的接口**：接口定义在 **kernel**，**属主域用它自己的连接实现**，消费方只依赖接口、从不碰别人的库/表结构。同进程期接口 = 进程内直调属主域实现（跑在属主池上）；拆进程后同一接口换 HTTP 客户端，接口不变。
> ⚠️ **被撤的取巧**：曾有一版把 api/automation 的池**直接注入 content**、让 content「在正确的池上跑查询」。那物理上分了库，但 content 仍**直连别人的库、仍知道别人的表结构**——反模式，与「系统间解耦」相悖，已撤销、重做为接口。
>
> **唯二不因接口化解决的**（无论同进程/拆进程都要架构级改）：① 跨库**事务**（一笔 tx 不能横跨两个库）——4 个 config-mirror bump + 5 个 offboard 联合提交，须改最终一致（outbox/2-phase）；② 跨库**写**（interaction_audit_events 双写）须收口到单写者的写接口。

**已完成**：
- **step0**（`f8651f0`，部署 dev）：outbox helper 池改绑 automation（见 §1 callout b）。
- **content 三处运行时跨库读全解——经接口，content 零跨库直连**（半连接改写 `e0d353c` → 接口重做 `5cbb6b1`，部署 dev）：
  - `curated-content-store.listForClient` created/uncreated：不再关联 `EXISTS(delegated_tasks)`——经 **kernel 接口 `TriggeredPublishRefsReader`** 向 automation 域要「已触发发帖」的 curatedId/sourceId 引用集（**属主 = `PgDelegatedTaskStore.triggeredPublishRefs`，跑在 automation 自己的池**），主查询本地 `id = ANY(...)`，排序/COUNT OVER/分页 SQL 结构逐字不变。**dev 真实数据验证等价**：94 条 publish_post 任务下新旧「已创作」集 31==31、双向差 0。缺读端口 / delegated_tasks 42P01 → fail-closed。
  - `facebook-publish-media-store.assertFacebookAccount`：经 **kernel 接口 `AccountPlatformReader`** 向 api 域要平台（**属主 = `PgAccountStore.getPlatformOrNull`，跑在 api 自己的池**，缺账号返 null 保留 account_not_found 区分）。
  - `draft-refinement.claimNext`：移除 **vestigial** `EXISTS(publish_log)` 守卫（publish_log 全仓从不 DELETE、任务 record_id 建时即合法 → 恒真、never excluded；移除逐字节等价，且直接消除该跨域读）。
  - 组合根用惰性 thunk 把接口接到属主 store（属主构造在后）。**还减了一条耦合边**（media→platform/index，frozenTotal 101→100）。tsc0 / acc0 / 全量 3194·0。
  - ⇒ **content 现在 0 处运行时跨库直连、也 0 处跨库直读**（全经接口）。只剩 **4 条跨 owner DDL FK**（facebook-publish-media→accounts、→publish_log ×2；draft→publish_log），**翻转时降**（schema-ensure 建 aidcp_content 空表时须去掉；共库期不动）。**content runtime-read 已解耦。**
- **api HUB 的面板批读全解——经接口，面板零跨库直读**（`cf32544`，部署 dev + healthcheck 绿）：
  - `panel/panel-store.ts`（api 属主）历史直读 automation 的 risk_counters / risk_state / alerts / interaction_feed / interaction_target_meta（§2 api 列的 7 处 raw 读）。改经 **新 kernel 端口 `PanelAutomationReader`**（今日计数聚合 / 批量风控态 / 告警 / 互动流）取投影，**属主实现 `PgPanelAutomationRead`（`src/risk/`，跑在 automation 池上）**，SQL 从面板逐字迁来。
  - 原 `accounts LEFT JOIN risk_state` 拆为「本地读 accounts（api 池）+ 端口批量取风控态 + 本地按 accountId 合入」，逐字等价「缺风控行=null」LEFT JOIN 语义；listAlerts/listInteractions 的 42P01 缺表降级保留在面板层。
  - 面板自己的 api 属主读（accounts/persona_config/publish_log）改用 **apiPool**（server ctx 新增字段），与 automation 端口**分池** ⇒ 面板整体 flip-ready。
  - 组合根按运行模式接线：monolith/core=automation 池本地实现（现网单进程即此路，逐字节等价）；**api 模式=fail-closed**（HTTP 客户端待 Block② 进程拆分时补，automation 内部读 API 增面板端点），镜像同段 publishStatusLocal 的 api 模式 reject 先例，api 模式未部署 ⇒ 不改现网。
  - 边界：新 kernel 文件入花名册（kernel-non-members.kernelRoster + ownership-rules fileOverride）；automation 新文件继承 src/risk/；**跨层 import 边零新增（仍 100）**。tsc0 / acc105·0 / 全量 3195·0。
  - ⇒ **api HUB 的 raw 跨库读从 26 降到 19**（21 读→14 读，已走端口 1→8）；剩 client-user-store 的 14 读（含跨库锁 / api+automation JOIN，须拆两查询）+ 5 tx 未解。

- **api `client-user-store.ts` 的「真纯读」批全解——6/14 处经接口**（`6796488`，部署 dev + healthcheck 绿 + **dev 真实数据等价核对通过**）：
  - 先对该文件 14 处 automation 读做了**逐处归类**（两路独立测绘 + 一道对抗性复核，结论一致）：**6 处真纯读**（顶层 `this.pool.query`、无行锁、不在事务内）+ **8 处须监督**（事务内 / 带跨库行锁）。本刀**只动前 6 处**，后 8 处原样保留并登记在下面 §2.1。
  - 新 kernel 端口 **`ClientEnvAutomationReader`**（单条离场记录 / 未清除微信离场记录 / 微信绑定环境键 / 账号→环境键 / 批量风控态），属主实现 **`PgClientEnvAutomationRead`（`src/interactions/`，跑在 automation 池）**——与同目录 `offboard-write-adapter.ts`（离场表单写者）读写配对。SQL 逐字迁来。
  - 解耦的 4 个方法：`getOffboard`（整条读经端口，归属过滤下推属主侧）；`hasPendingRevocationHold`（原 auth_state JOIN holds 拆两步）；`reconcileRevocationHolds` **候选扫描**（本地按序取 hold + 端口问哪些已绑定 + 本地截断；方法内那条事务内 `FOR UPDATE` 联查仍属须监督批、未动）；`listAllEnvironments`（原横跨两域的巨型聚合拆三步：端口取离场投影 → 本地只聚合 api 属主表 → 端口批量取风控态本地合入）。
  - **等价性有机械依据**：`interaction_auth_state` 有 `UNIQUE(platform, env_key)` + `PRIMARY KEY(platform, account_id)`、`interaction_offboards` 在未清除态上有 `UNIQUE(platform, env_key)`、`risk_state` 以 `account_id` 为主键 ⇒ 被拆掉的四处 JOIN **全是 1:1**，不放大行数、不改 LIMIT 选中集，「缺行 = null / 无回执」语义逐字保留。
  - **dev 真实数据核对（新旧双跑 deep-equal）**：`listAllEnvironments` 45==45 **逐字段全等**（其中 4 行真的走了离场回执路径、9 行真的走了风控态合入路径）；`hasPendingRevocationHold` 对全部 5 个微信绑定账号新旧一致；`getOffboard` 取真实记录读回正确且**错配 userId 返 null**（归属闸有效）。⚠️ 撤权 hold 相关路径当前库内**存量为 0**（hold 回执 0 / reconcile 候选 0），真实数据只证了「空集下一致」，**行为覆盖靠单测**，已登记真机 backlog。
  - 失败方向显式钉死：`hasPendingRevocationHold` 的消费方拿 `false` 当放行条件（互动读/回复/私信闸），故该方法**不 catch 任何错误**——跨域读失败必须抛，吞成 `false` 等于给正被撤权的环境重开互动写。端口未注入时跨域读**当场抛具名错**，绝不假空集。
  - 组合根按模式接线（monolith/core/automation/content = automation 池本地实现；api 模式 fail-closed）。边界：kernel 新文件入花名册；`src/interactions/` 为逐文件裁决目录，属主实现另加 fileOverride。跨层 import 边**零新增**（仍 100）。tsc0 / acc105·0 / 全量 3204·0（新增 9 用例）。
  - ⇒ **api HUB raw 跨库读从 19 降到 13**（读 14→8，已走端口 8→13）。

- **互动域属主 store 补接属主池**（`92a2196` + 修 `7f5232a` + 属主纠正 `b46708b`，部署 dev + healthcheck 绿）：解掉 §1 callout c 的主体。三个构造点显式绑各自**表的**属主池——`InteractionStore` → `automationPool`；**`ReplyConfigStore` / `ReplyConfigScopeStore` → `apiPool`**（它们住在 `src/interactions/` 但碰的表全是 api 属主：`interaction_reply_configs` / `_config_versions` / `_config_scopes` / `_scope_versions` / `_scope_audit` / `reply_templates` / `reply_rules` / `account_reply_profiles` / `interaction_audit_events` / `accounts`）。⚠️ **`92a2196` 曾把这两个也绑成 `automationPool`**——按目录猜属主，等于把同一个 split-brain 反向埋一遍；`b46708b` 已纠正。**教训：目录位置不是属主判据，`boundaries/table-ownership.json` 才是。****今天逐字节等价且不依赖任何 env 组合**——这三个 store 本就跑在 `resolveEnvPgConfig()` 上，而 `resolveOwnerPgConfig('automation')` 在 owner URL 未设时回落的 `resolveSharedPgConfig` 与它是同一套 env 名 / 同一 DEFAULT 兜底 / 同样 `DATABASE_URL` 优先，故**不存在** L2 那批 HOST-param store「接池后开始认 `DATABASE_URL`」的口径漂移。连接数亦降（三个私有池 → 复用共享池）。
  - ⚠️ **同刀发现并修掉一个自己引入的真 bug（`7f5232a`）**：三个 store 的 `close()` 是 `this.pool.end()`，而组合根的互动域构造被 `try/catch` 包着（schema / 迁移未就位时整域降级不启用），**失败分支正好会调这三个 `close()`**。绑共享池之后，那一下会 end 掉被本域十几个 store 共用的 `automationPool`，把一次**局部**子系统失败升级成进程级瘫痪（其余 automation store 全部「Cannot use a pool after calling end」）。修法 = `ownsPool = options.pool === undefined`，`close()` 只 end 自己建的池；加 2 条回归用例钉住。
  - **同类潜在形态仍存在**（已登记、本刀不扩面）：多数被注入属主池的 store 的 `close()` 也会 end 共享池，只是**当前无人调用**（`server.ts` 里 `.close()` 仅三处：`tokenUsageStore` 用专用小池、启动期 `raiseStandaloneAlert` 用自建池、以及本次修的互动域 catch）。将来给任何 store 加 close 调用前先看 `ownsPool`。
- **「假跨域」的 cleanup-grant 一对收回属主域**（`7c2f6e3`，部署 dev + healthcheck 绿 + dev 只读冒烟通过）：`registerOffboardCleanupGrant` / `consumeOffboardCleanupGrant` 原本由 api 侧 `BEGIN` 出 **api 池**连接、再把句柄递给 automation 写适配器，但这两笔事务碰的表**全是 automation 属主**、一张 api 表都没有 ⇒ 整体收回属主域（新 kernel 端口 `OffboardCleanupGrantOperations`，方法**不接调用方句柄、自成一笔事务**；属主实现 `PgOffboardCleanupGrantOps`，`src/interactions/`，持 automation 池）。`OffboardWritePort` 由 6 方法缩到 3。⇒ **§2.1 的须监督读从 8 降到 7**（第 9 行 `:719` 已解）。
  - 这一对是残余离场写里**唯一不与任何 api 写共事务**的两个 —— 这正是「这一刀干净」的判据（对照 `enqueueOffboard` / `enqueueProvisionedUnboundOffboard` / `revokeInteractionAccess` 确实夹在 `client_users FOR UPDATE` + `lockEnvironmentRow` + `client_env_scope FOR UPDATE OF s,e` 与两条 api 写之间，**不能用同一手法**）。
  - **逐字保留的五条不变量**（写进 kernel 端口文件头，并用 4 条新用例钉住）：① 五档失败判定顺序即优先级；② 失败路径 `COMMIT` 而非 `ROLLBACK`（拒绝审计要留痕）；③ 行不存在时不写审计（绝不编造 accountId/envKey）；④ 取行的 `FOR UPDATE` 与烧票、写审计**同一事务同一连接**——烧票那条 `UPDATE` 不查影响行数，拆开即「0 行也返回成功」= **静默假成功**；⑤ `now` 为可注入判定时钟。
  - **这两个方法搬迁前 SQL 层零覆盖**（`offboard-cleanup-grant.test.ts` 只测签票/验签纯函数、`client-auth-server.test.ts` 用内存假 store 测路由契约），即「零语义变化」当时的测试套件根本验不了 —— 随刀补齐。
  - 诚实登记一处**非生产**差异：改动前 consume 对不存在的 offboardId 会在完全不触达端口的情况下返 `not_found`；现在一进门就要端口，未注入时抛具名错。生产组合根恒注入 ⇒ 现网无影响。

- **`alerts` 写端并入 automation 池**（`3f86c6c`，部署 dev + healthcheck 绿）：读端（面板 `listAlerts`）自 `cf32544` 起已在 automation 池，写端两处却仍是裸 HOST-param 自建池 ⇒ 翻转后**写旧库、面板读新库、告警列表永久为空且零报错**。两处修法**故意不同**：常规 `alertStore` 注入 `automationPool`（其 `close()` 全仓无调用方）；启动期 `raiseStandaloneAlert` **仍自建专用小池**、只换配置来源为 `resolveOwnerPgConfig('automation')`——因为它 `finally` 里调 `close()`，注入共享池会 end 掉整个 automation 池（与 `7f5232a` 同形）。dev 实测 `.env` 无 `DATABASE_URL` / 无 owner URL（只核变量名）⇒ 逐字节等价。

**下一步（同样一律走接口，不得直连别人的库）**：
0. **⛔ 翻转前置的剩余部分**（`PgAlertStore` 已于 `3f86c6c` 解掉；完整名单与修法要点见 §1 callout c 表）：剩 `PgRiskStore`、`PgRiskCounterOutboxStore`、**`AutomationWriterLock`**（最严重：advisory lock 按库，翻转后**静默双写 `risk_state`**）、`runSchemaContractGate` 的账本 Client。**前三项属活跃 change `risk-state-cross-process-integrity` 独占范围（§7 单写者纪律）⇒ 待其归档后另起一刀**；账本 Client 须先裁决「账本一份还是每库一份」。
1. **api `client-user-store.ts` 余下 7 处须监督读**（见 §2.1）：跨库行锁 + 事务内联查，**接口化解决不了**，须最终一致重设计。**用户在场做。**
2. **automation 侧 api 读**（automation → api 的 `accounts` 等）：多为**写事务内嵌的守卫读**（execution_target 内联 / `EXISTS(accounts)` / `FOR SHARE` 行锁），接口化不干净，需**去规范化**（把 accounts 投影冷备进 automation 库）或移守卫——性质更接近下面的事务批，非纯读。
3. 再攻 **9 处跨库事务 + 1 处跨库写**（架构级最终一致，改的是风控/环境注销关键路径，**须监督**）。之后才谈建库/拷数据/翻 URL。

## 0. 两条改变全局的已核实事实

1. **账号从不物理删除**（migrations/scripts/src 全仓零 `DELETE FROM accounts`，account-store 不暴露任何 delete）→ 12 条 `ON DELETE CASCADE` 跨域外键**在实践中从不触发**。⇒ **降外键（0076 及新发现的 6 条 DDL FK）行为无影响、account-delete-cascade 接线可推迟到「真加删账号功能」时**。危险窗口基本消失。
2. **拓扑**：dev 与 ol **连同一台物理 PG**（PG 在 dev 机 `121.89.85.150:5432`，dev 走 `127.0.0.1`、ol 跨网络走 `121.89.85.150`；实例 id 同、账本同 73 行）。这台"dev 机"的 PG **就是生产库**。dev 机上 `sudo -u postgres` peer 认证可用 = **有超级用户 + CREATEDB**（app 角色 `aidcp` 无 CREATEDB，`rolcreatedb=f`）。
3. **可逆隔离切法**：建 owner 库 + 从 aidcp **只读**拷贝数据进新库 + **仅 dev 端**设 `AIDCP_PG_<OWNER>_URL` → **aidcp 全程零改动、ol 零风险、unset+重启即回滚**。0076 只在将来 ol 也翻转（aidcp 那份表退役）时才需要。

## 1. 翻转就绪矩阵（核心结论：没有一个 owner 现在能干净翻转）

| owner | 跨库依赖 | 读 | 写 | 跨库事务 | 已走端口 | **raw(阻塞)** | 角色 | 结论 |
|---|---|---|---|---|---|---|---|---|
| **content** | 7 | 7 | 0 | 0 | 0 | ~~7~~ **0** ✅ | leaf（无人读它）| runtime-read 已全解（`5cbb6b1`），只剩 4 DDL FK 翻转时降 |
| **automation** | 24 | 17 | 3 | 4 | 2 | **22** | **HUB**（api 读它 12+ 表）| 与 api 互相纠缠 |
| **api** | 27 | ~~21~~ ~~14~~ ~~8~~ **7** | 1 | 5 | ~~1~~ ~~8~~ ~~13~~ **14** | ~~26~~ ~~19~~ ~~13~~ **12** | **HUB**（owns `accounts`）| 面板 7 读（`cf32544`）+ client-user 真纯读 6（`6796488`）+ cleanup-grant 一对收回属主域（`7c2f6e3`）已解；剩 client-user **7 处须监督读** + 5 tx |

合计 58 依赖 / **48 raw**。全部跑在 local pool，只有 3 处已在端口后（automation `interaction-store.ts:1736/1819`、api `client-user-store.ts:683`，仍传 `this.pool`，翻转时把端口实现切 HTTP 即可）。

**最危险的三类（静默原子性丢失，非简单 HTTP 化能解）**：
- **4 个 config-mirror 跨库事务**：`quota-config-store.ts:243` / `pacing:181` / `session:276` / `resume:249`，各在 `pool.connect()+BEGIN` 里写自己的 automation 表 + `bumper.bumpInTx(client)` 写 **api 的 `config_mirror_version`** + `COMMIT`，**单物理连接**。注入的 bumper 只切调用点、**切不动原子性**——`config_mirror_version` 一到别的库这笔事务就断。**automation 或 api 任一翻转即触发**。修法：把 bump 移出写事务（异步 outbox / 最终一致的版本信号）或在本地复制版本计数。
- **1 处 raw 跨库写（真边界违规）**：automation `interaction-store.ts:1839` `INSERT interaction_audit_events`（api 属主）——该表被两个 owner 双写。修法：走写端口（镜像 `:1819` 的 DELETE 端已走的 `InteractionApiPurgePort`）。
- **5 处 api→automation offboard 联合提交**：`client-user-store.ts:513/619/1519/2151/2233`，经 `OffboardWritePort` 写 automation 表、但与 api 表在**同一 `BEGIN/COMMIT`** 内共提交。端口切调用点干净，**原子性在拆库时断** → 拆成两次独立提交（2-phase / outbox）。

**属主 store 没接属主池（callout c，2026-07-25 新发现，翻转前置、byte-equivalent 可先做）**：
`InteractionStore`（`src/interactions/interaction-store.ts:302`）/ `ReplyConfigStore` / `ReplyConfigScopeStore`
在组合根构造时**不传 `pool`**（`server.ts:2617/2621/2622`），故各自 `new Pool(resolveEnvPgConfig())` —— 回落的是
**共享库配置**，不是 `automationPool`。而它们正是 `interaction_offboards` / `interaction_auth_state` /
`interaction_runtime_controls` / `interaction_feed` / `interaction_reply_configs` 这些 automation 属主表的**单写者**。
后果：一旦设 `AIDCP_PG_AUTOMATION_URL`，**属主继续读写旧共享库**，而本批已解耦的读端口读**新 automation 库** ⇒
split brain（读端看到空库或陈旧副本，写端的离场 / 授权状态改动读端永远看不见）。今天三 URL 全未设 ⇒ 零影响。
**修法**：组合根把 `automationPool` 传给这三个 store（与 callout b 同形、同为纯字节等价）。**✅ 已做（`92a2196` + 修 `7f5232a`，部署 dev）** —— 见上「已完成」。
> **⛔ 本 callout 尚未全解**：`PgAlertStore`（`alerts`，automation 属主，`server.ts` 两处构造）仍走 HOST-param 自建池；它与已迁到 automation 池的读端（`PgPanelAutomationRead` 读 `alerts`）**已构成一对 split-brain**。注意它有两处构造且性质不同：常规 `alertStore` 可直接注入属主池；启动期 `raiseStandaloneAlert` 那一处**必须继续自建池**（它 `finally` 里调 `store.close()`，注入共享池会把 automationPool end 掉——与上面修掉的那个 bug 同形），只应把它的**配置来源**从 HOST-param 换成 `resolveOwnerPgConfig('automation')`。`PgRiskStore` / `PgRiskCounterOutboxStore` 同样漏接，但 `src/risk/` 属活跃 change `risk-state-cross-process-integrity` 独占范围（§7 单写者纪律）⇒ 待其归档后另起一刀。
> ⚠️ **排查方法本身有盲区（务必知道）**：`grep -rn "new Pool(resolveEnvPgConfig())" src/` **只命中自建池的一种写法**。
> 另一种写法 `new Pool({ host: options.host ?? DEFAULT_PG_CONFIG.host, ... })` 完全绕过该 grep ——
> `PgRiskStore` / `PgRiskCounterOutboxStore` / `PgAlertStore` 都是这种，因此第一版 callout c 名单**漏了它们**。
> 正确的排查口径是**枚举 `new Pool(` 与 `new Client(` 全部出现点**，再逐个看组合根有没有注入 pool。
>
> **一次全量审计（2026-07-25）后的完整漏接名单**，除上面三个已修的之外还有：
> | 组件 | 文件 | 属主 | 翻转后的失效形态 |
> |---|---|---|---|
> | `PgRiskStore` | `src/risk/pg-risk-store.ts` | automation（`risk_state` / `risk_counters` / `risk_interactions`）| 风控权威态写旧库、面板经已迁的读端口从新库读 ⇒ **面板永远看到空 / 陈旧风控态，零报错** |
> | `PgRiskCounterOutboxStore` | `src/risk/risk-counter-outbox-store.ts` | automation（`risk_counter_outbox` / `risk_counters`）| 记账 exactly-once 靠唯一索引，与 `PgRiskStore` 的 `risk_counters` **必须同库**；一个翻一个不翻 ⇒ **exactly-once 直接失效** |
> | ~~`PgAlertStore`（两处构造）~~ **✅ 已解（`3f86c6c`，部署 dev）** | `src/alerts/alert-store.ts` | automation（`alerts`）| ~~写旧库、面板读新库 ⇒ 后台告警列表永久为空且零报错~~ |
> | **`AutomationWriterLock`** | `src/risk/writer-lock.ts` | automation（无表；`pg_try_advisory_lock` 保护 `risk_state` 单写）| **最隐蔽、最严重**：advisory lock 是**按库**的。锁留在旧共享库、写落到新 automation 库 ⇒ 两个进程各自「抢到同一把锁」却互不排斥 = **静默双写 `risk_state`**，正是这把锁存在的唯一目的 |
> | `runSchemaContractGate` 的一次性 `Client` | `src/schema/schema-gate.ts` | automation（`schema_migrations`）| 校验的是旧共享库的账本、业务表已分散三库 ⇒ enforce 模式下**假绿** |
>
> **两条修法上的要点，照抄会出事**：
> 1. **`AutomationWriterLock` MUST NOT 注入池**——advisory lock 是会话级的，池回收连接即释放锁（该文件头注释已写明）。
>    修法是让它的**连接配置**跟随 `resolveOwnerPgConfig('automation')`，而不是给它一个共享池。
> 2. **`PgAlertStore` 的两处构造性质不同**：常规 `alertStore` 可注入属主池；启动期 `raiseStandaloneAlert`
>    那一处 `finally` 里调 `store.close()`（= `pool.end()`），**注入共享池会把 automationPool 整个 end 掉**
>    —— 与 `7f5232a` 修掉的那个 bug 同形。那一处只应把**配置来源**换成 owner resolver、继续自建池。
> 3. **`src/risk/` 属活跃 change `risk-state-cross-process-integrity` 的独占范围**（§7 热点单写者纪律）⇒
>    上表的 risk 三项**不与之并行动**，待其归档后另起一刀。
>
> **附带发现的耦合点**：`InteractionApiWrites`（`src/interactions/interaction-api-writes.ts`）自身不持池，
> 方法签名接调用方句柄，写的却是 **api 属主**表（`reply_templates` / `reply_rules` / `account_reply_profiles` /
> `interaction_reply_config*` / `interaction_audit_events`）。它由 `InteractionStore` 注入调用 ⇒
> `InteractionStore` 绑 automationPool 之后，这些 api 表的写**确定地**跑在 automation 连接上（此前只是「碰巧同库」）。
> 翻转时它会响亮失败（表不在 automation 库），属既有的跨库写清单（§2 automation 段 `interaction-store.ts:1839`
> 同族），**必须与任何 automation 翻转同批解决**。

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

### api（HUB，原 26 raw：5 tx + 21 读，全在 2 文件；**面板 7 读已解 → 现 19 raw**）
- **`client-auth/client-user-store.ts`**（微信环境 offboard/scope 生命周期）：14 处 raw 读 automation 表（含 `interaction_auth_state`/`interaction_offboards`/`interaction_runtime_controls`/`risk_state` 的 `FOR UPDATE` 跨库锁 + `1359/2210/2225/2254` 的 **api+automation 同查询 JOIN**，须拆两查询）；**5 处 offboard 跨库联合提交**（见 §1）；已走端口 `:683`（只写 automation 表、无 api 共写→可干净切 HTTP）。**← 下一批读端口。**
- ~~**`panel/panel-store.ts`**（只读看板）：**7 处 raw 读**（`400 risk_state`、`422/439/469 risk_counters`、`592 alerts`、`633 interaction_feed`、`634 interaction_target_meta`）~~ **✅ 已解（`cf32544`，部署 dev）**
- 详细分解见新增 **§2.1**（client-user-store 14 处逐处归类 + 已解 6 / 待解 8）。：经 kernel 端口 `PanelAutomationReader`，属主实现 `PgPanelAutomationRead`（automation 池）；`accounts LEFT JOIN risk_state` 拆为「本地 accounts + 端口批量风控态 + 本地合入」；面板自读改 apiPool、与端口分池。见上「已完成」。

### 2.1 `client-auth/client-user-store.ts` 14 处 automation 读 · 逐处归类（2026-07-25 测绘 + 对抗性复核）

> 行号为解耦**前**（cf32544）的坐标，便于与历史文档对齐；已解那 6 处的现状见 `6796488`。
> 注意 **14 处引用 = 12 条语句**：`1918/1952/1964` 同属 `listAllEnvironments` 那一条巨型聚合。

| # | 行 | 表 | 方法 | 事务内 | 行锁 | 同语句含 api 表 | 归类 |
|---|---|---|---|---|---|---|---|
| 1 | 658 | `interaction_offboards` | `getOffboard` | 否 | 无 | 否 | ✅ 已解（纯读） |
| 2 | 1918 | `interaction_offboards` | `listAllEnvironments`（keys CTE 并集支） | 否 | 无 | 是 | ✅ 已解（拆并集） |
| 3 | 1952 | `risk_state` | `listAllEnvironments`（经 accounts 链） | 否 | 无 | 是 | ✅ 已解（批量合入） |
| 4 | 1964 | `interaction_offboards` | `listAllEnvironments`（清理回执 LEFT JOIN） | 否 | 无 | 是 | ✅ 已解（按 envKey 合入） |
| 5 | 2210 | `interaction_auth_state` | `reconcileRevocationHolds` 候选扫描 | 否 | 无 | 是 | ✅ 已解（拆两步） |
| 6 | 2254 | `interaction_auth_state` | `hasPendingRevocationHold` | 否 | 无 | 是 | ✅ 已解（拆两步） |
| 7 | 535 | `interaction_runtime_controls` | `enqueueCleanupHold`（helper，两个调用方都在 tx 内） | **是** | `FOR UPDATE` | 否 | ⛔ 须监督 |
| 8 | 614 | `interaction_auth_state` | `beginEnvironmentOffboard` | **是** | `FOR UPDATE` | 否 | ⛔ 须监督 |
| 9 | 719 | `interaction_offboards` | `consumeOffboardCleanupGrant` | **是** | `FOR UPDATE` | 否 | ✅ 已解（`7c2f6e3`：整笔事务收回属主域——它碰的表全是 automation 属主，是「假跨域」） |
| 10 | 1359 | `interaction_auth_state` | `withAuthorizedInteractionScope` | **是** | `FOR SHARE OF s,e,a,acc` | 是 | ⛔ 须监督 |
| 11 | 1511 | `interaction_auth_state` | `updateUser`（停用客户路径） | **是** | `FOR UPDATE` | 否 | ⛔ 须监督 |
| 12 | 2116 | `interaction_offboards` | `setScope`（离场进行中闸） | **是** | `FOR UPDATE` | 否 | ⛔ 须监督 |
| 13 | 2143 | `interaction_auth_state` | `setScope`（撤销归属取绑定） | **是** | `FOR UPDATE` | 否 | ⛔ 须监督 |
| 14 | 2225 | `interaction_auth_state` | `reconcileRevocationHolds` 事务内重取 | **是** | `FOR UPDATE OF h,a` | 是 | ⛔ 须监督 |

**为什么剩下这 7 处「不是更难，而是性质不同」——它们的失效是无声的。** 跨库行锁与本项目已经淘汰过一次的
库级 advisory lock 同形：两侧连不同库时，**两边各自加锁都会成功、互斥消失、且不产生任何错误**
（同一教训写在 `aidcp-cloud/src/db/environment-row-lock.ts` 的头注释里，那次是把 advisory lock 换成
`client_environments` 行锁）。所以「先 HTTP 化再说」对这 8 处是错的方向：必须显式改成最终一致
（把互斥落到单一属主域内、或用 outbox / 2-phase 表达），并接受语义变化 + 逐条测。

**已识别的具体破坏形态（改之前必须先答的题）**：
- **`setScope` 的两道闸分居两库**：`2107` 锁 `client_env_revocation_holds`（api）、`2116` 锁
  `interaction_offboards`（automation），今天同一事务 ⇒「有清理在飞的环境不可改派」是原子的。拆库后两闸各在
  一库，叠加 `reconcileRevocationHolds` 变成两次独立提交（`2233` 写 automation 离场记录、`2237` 删 api 的 hold），
  存在**hold 已删、离场记录尚不可见**的窗口 —— `setScope` 会在此窗口内**把一个正在清理的环境改派给新客户**。
- **离场写口收不住原子性**：`OffboardWritePort`（`client-auth/offboard-write-port.ts`）的每个方法都**接调用方的
  事务句柄**，实现方 `interactions/offboard-write-adapter.ts` 自己**不持任何连接**。故 `client-user-store` 那些
  `BEGIN` 出来的 client 是 **api 池**的连接 ⇒ 翻转后 `UPDATE interaction_runtime_controls` /
  `UPDATE interaction_auth_state` / `INSERT interaction_offboards` / `INSERT interaction_offboard_audit`
  **全部打到 api 库**。两种结局都坏：表不在 api 库 → 42P01，而 `beginEnvironmentOffboard` / `updateUser` /
  `setScope` / 两个 grant 方法**都没有缺表分支** ⇒ 客户解绑、停用客户、改派归属直接 500；表若两库都拷了 →
  写进 api 那份副本、automation 侧派发器永远看不到、边缘永远收不到清理命令 = **静默假成功**。
- **第 5 张 automation 表**：`interaction_offboard_audit` 也由本文件经上述写口写入（`683` / `733` / `743` 及
  `enqueueOffboard` / `enqueueProvisionedUnboundOffboard` 内部），此前清单未列。另 adapter 内部还有一处
  `SELECT 1 FROM interaction_runtime_controls … FOR UPDATE`（`offboard-write-adapter.ts:45`）——同样跑在
  api 连接上的 automation 读，且带行锁。
- **读后即取的语义**：`getOffboard` 是 `beginEnvironmentOffboard` 的读回半边，路由端点对「查不到」答 **404
  not_found**（`client-auth-server.ts:1946`）。离场写一旦变成 automation 侧独立提交，这个轮询会对**已受理**
  的离场合法地 404，端点目前**没有「已受理、尚未物化」这个词**。改最终一致时须同时给它一个诚实的中间态。

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
