## Context

发帖今天有两条触发：手动飞书 `/publish`（`triggerManual(accountId)`，已按账号参数化）与自动扳机 `checkAndMaybeTrigger`（概念积累阈值 / 距上次≥`minHoursBetween` + 风控 normal）。自动扳机只支持**恰好一个账号**——唯一硬闸是开头的 `resolveSingleAccountId`（0 或多个即跳过，`publish-scheduler.ts:181-187`），而其下游 `buildTriggerInput(accountId)` / `doTrigger(reason,forced,accountId)` / `orchestrator.trigger` 全已按账号参数化。自动扳机由 `server.ts:1362-1371` 一个 `setInterval`（`AIDCP_PUBLISH_AUTO`，默认关）驱动。发送铁红线：草稿落 `pending_approval` → 飞书人审 → `PublishDispatcher` 仅 `approved===true` 才发（AC-PUB）。

「活跃时间设置」那张周历掩码（`weekly-active-window`，全局单行 `session_config_global.active_week_mask`）只被浏览闭环调度器消费、治「浏览会话开 / 续 / 结束」，**不治发帖**；其纯判定器 `isWeekActiveAt` / `isValidWeekActiveMask`（`risk/session-limits.ts:71-113`）以 mask 为入参、可复用，但它对**缺失 / 非法掩码回落「全天活跃」（fail-open）**——这是给浏览零回归用的。

账号存储 `accounts` 主表由各 store 的 `*_SCHEMA_SQL` 在 `init()` 自愈式建 / 补列（**本仓无迁移执行器**，`migrations/*.sql` 仅人审文档）。已有 1:1 侧表先例（`risk_state` / `persona_config`，`LEFT JOIN` 读）；已有「账号属性单写通道」`accountAttr`（`setGroupLabel` / `setGroupChatInfo`，面板 JWT 保护 PUT）——但它是**单值自由文本**通道。发帖成本记账依赖一个**全局可变槽** `publishAccountRef`（`server.ts:333-342`），其并发安全靠「`PublishOrchestrator` 全局单跑闸 + 发帖本就单账号 + 长间隔从不并发」这条**当前隐性前提**。

约束：无迁移器（DDL 必幂等）；退役保留账号 `default` 全写路径拒；协议 v2 两份 `protocol.ts` 逐字一致（本变更不动协议）；风控最终态由 `RiskController` 单写（本变更不写）；MUST NOT 静默假成功；发布前人审 AC-PUB 铁红线。

## Goals / Non-Goals

**Goals:**
- 多账号「按星期 × 小时时段」定时**自动发帖**：到点自动生成草稿 → 仍走飞书人审 → 通过才发。
- 只给现有发帖管线加一个**定时触发来源**，复用其生成 / 人审 / 发送，零新发送口、绝不自动发送。
- 每账号可配「是否自动发帖 + 日上限」；未配 = 完全不自动（零回归）。
- 多账号错峰、发帖日上限原子（防超发）、每次触发都回诚实结果卡。

**Non-Goals:**
- 不做评论排期、群评排期（后续独立变更；群评还有前置门槛）。
- 不做每账号自定义时段的编辑界面（侧表留 `content_active_mask` 列作扩展缝，v1 不接线 override 解析）。
- 不做作业调度框架 / 持久 outbox / 令牌桶 / 每动作各一张网格 / 每账号一个定时器 / 分布式锁（单进程内存心跳 + 持久发送计数 + 在途台账足够）。
- 不动浏览掩码、不动协议 v2、不写 `RiskController`、不加 dispatcher 角色、不做时区参数（服务器本地时间、单地域）。

## Decisions

### D1. 触发扇入，不是新发送通道

新增内容调度器只做「此刻对哪个账号试发帖」的判定，命中后调**现成**的发帖触发机器产草稿，发不发全过既有「生成 → 人审 → 派发」。绝不新增发送路径、绝不绕过人审。

- **为何**：全系统最重要的架构约束是「提议 → 人审 → 发送」这条链（AC-PUB）。排期只是给它加一个新的**触发来源**（定时器代替飞书消息 / 概念阈值），复用其审批 + 派发后端。
- **Alternatives**：建持久 outbox / durable job queue（否决——草稿廉价、重启中断可接受、飞书里那张审批卡本身就是队列）。

### D2. 数据：侧表 + 全局单例，全部 fail-closed（不复用 accounts 加列 / accountAttr）

- 全局单例表 `content_schedule_global`（`content_active_mask TEXT` 168 格 '0'/'1'，周一起头×24h、服务器本地时；**缺失 / 非法 = 全 0 = 不自动**）。
- 旁挂 1:1 侧表 `account_content_schedule`（PK `account_id`；`auto_enabled` 默认 false；`post_enabled` 默认 false；`post_daily_cap INTEGER` 默认 0；`content_active_mask TEXT` 每账号覆盖 null=继承全局，**v1 留列不接线**；审计列）。均 `CREATE TABLE IF NOT EXISTS` 于 store `init()` 自建。
- 写通道新建独立 dep（**不复用 `accountAttr`**）：UPSERT-only、UPSERT 前 `SELECT 1 FROM accounts` 校验账号存在（防造幽灵排期行）、退役 `default` 拒、非法整块拒不部分落库、`RETURNING` 回读真态、诚实结果联合 `{ok}|{ok:false,reason}`、绝不 raw SQL / 乐观假成功。
- **为何侧表不加列**：排期是 ~4 个结构化字段（总开关 + 发帖开关 + 日上限 + 时段覆盖），且 proposal 要求「另立独立结构、数据后端分开」；给 `accounts` 主表堆列会污染握手 / 暂停等热路径读的主行，而 1:1 侧表是本仓已有范式（`risk_state` / `persona_config`）。侧表无行 = 完全未配 = 不自动，零回归天然落地。
- **为何不复用 accountAttr**：`accountAttr` 是 `accounts` 表列的**单值自由文本**单写者；内容排期是另一张表、结构化多字段的另一个 owner，塞进去混淆所有权。
- **为何 fail-closed（与浏览掩码相反）**：浏览掩码缺失 = 全天活跃（浏览无害）；自动**发送**后果重，故内容侧缺失 / 非法一律「不自动」，账号总开关默认关做第二保险。

### D3. 调度器：单进程、每分钟心跳、账号扇出（不是每账号一个定时器）

新建 `ContentScheduler`（云端单进程、纯控制流、全 I/O 注入可脱边端单测；命令式触发器，**不进** `RoleDispatcher` 角色注册、**不走** `EventBus`），`server.ts` 一个 `setInterval(60_000)` 守卫在 `AIDCP_CONTENT_SCHEDULE_AUTO`。每 tick 遍历在线账号（`ConnectionRuntimeRegistry` 加 `onlineAccountIds()` 访问器），逐账号闸序：`enabled ∧ isValidWeekActiveMask(有效内容格) ∧ isWeekActiveAt(格,now) ∧ 分钟命中偏移 ∧ 未达日上限 ∧ 风控 normal`。

- **分钟错峰**：`offset = hash(accountId + localDayKey(now) + 'post') % 60`（复用 dispatcher 的 `localDayKey`，纯函数无状态可复现；每天变、账号间错开、同账号多动作彼此错开）。每分钟粗轮询，仅 `now.getMinutes()===offset` 且当前是该账号活跃内容格才尝试；时间只定「何时试」。
- **幂等 + 单飞 + 重入护栏**：`(account, action, 小时格)` 幂等键（同格不再触发）；每账号跨动作 single-flight 集合（本 Phase 只有发帖，但为 Phase 2/3 预留背板）；tick 重入标志（上轮未完即跳过本轮）。全内存、单进程、无分布式锁。
- **为何不上 Quartz / BullMQ / Temporal**：单云进程、账号数量级小，`setInterval` 单心跳遍历租户就是多租户 cron 的可扩展做法，重启丢内存态可用「持久发送计数 + 在途台账」补偿（见 D5），不值当引入作业调度框架。

### D4. 发帖多账号：泛化触发 + 全局串行 + fire-and-forget + 无条件关旧扳机

- **泛化**：发帖触发机器已按账号参数化，单账号限制唯一来源是 `checkAndMaybeTrigger` 的 `resolveSingleAccountId`。新增孪生入口 `triggerScheduled(accountId)`（`forced=false`，仍过 persona 绑定 + 风控 normal + `canDo('publish')` + 人审），**绕开**那道单账号闸；`resolveSingleAccountId` 只留给无参手动 `/publish`。`forced=false` 让 `ContentScout` 可诚实判「无新素材」而跳过。
- **发帖全局串行（load-bearing 不变量）**：`publishAccountRef` 是全局可变槽，多账号并发发帖会让 A 的生成段 LLM 记账被 B 的 `finally` 复位污染（成本错账 + finally-复位竞态）。故调度器下发任一发帖前经 `isPublishBusy()`（**真全局闸、无 accountId**）串行——同刻至多一个账号在发；代码注释锚定「发帖必须全局串行」，禁止未来「按账号并行发帖」优化，除非先消灭全局槽。
- **fire-and-forget**：发帖触发要 await 整条多角色生成管线（含 thinking 模型、单调用上限 180s、累计数分钟）；tick **绝不 await** 它，否则单分钟心跳阻塞数分钟、其间所有 tick 被重入护栏跳过、错峰被击穿、其它账号饿死。心跳「发起即返回 + busy 标志跟踪」。
- **无条件关旧扳机**：新调度器开启时**启动期确定性关闭**旧 `AIDCP_PUBLISH_AUTO` 单账号 `setInterval`。全局单跑闸只挡**并发**双跑，挡不住旧 30min 扳机与新 offset 分钟**错时**叠加造出同日两次独立草稿 → 超发。**不留 fallback**（两者不得并存）。

### D5. 发帖日上限做成原子（防 TOCTOU 超发）

日上限检查 = **已发历史**（`publish_log` 已账号感知，加 `countPublishedTodayForAccount(accountId)` 按服务器本地日历日）**+ 在途未审草稿**（复用 `hasPendingApprovalForAccount(accountId)`）。

- **为何**：只读「已发历史」有 TOCTOU——正挂在人审里的草稿不计数，重启丢内存幂等态或双扳机错时叠加可造出两张都没超限的草稿、都被批准 → 超发。发帖侧已有在途台账可堵此洞，一并计入。
- 内存态（`lastFired` 幂等键、busy 标志）重启清零可接受：日上限的正确性由「持久已发计数 + 在途台账」保证，不依赖内存计数器。

### D6. 掩码判定必须 fail-closed，不照搬 isWeekActiveAt 兜底

调度器判「当前是否活跃内容格」必须三连：`enabled && isValidWeekActiveMask(mask) && isWeekActiveAt(mask, now)`——**非法 / 缺失掩码一律当「不活跃、跳过」**。绝不能直接用 `isWeekActiveAt`（它对非法掩码回落 `true`=全天活跃，是浏览零回归语义），否则缺码账号会满世界自动发。这是个细微但致命的极性反转。

### D8.（2026-07-03 修订）三态合并网格 + 自动 ⊆ 活跃强制闸

初版落地为「排期页独立内容网格 + 安全页浏览网格」两页两张网格，偏离了用户更早的拍板（一张网格、标记画在活跃格内、休眠格绝不自动）。修正为：

- **UI 三态合并**：排期页一张周历，点格循环「休眠 → 活跃 → 活跃+可自动（白点）→ 休眠」，一次保存串行写两个端点（非原子可接受：任一失败诚实报错 + 整体重取，且中间态无安全风险——由下条云端闸兜底）；安全页「可活跃时间」卡只读化、指向排期页唯一编辑入口（防双写互踩）。底层两字段仍分离（兜底极性相反，绝不合并存储）。
- **云端强制「自动 ⊆ 活跃」**：调度器加浏览掩码活跃判定（沿其 fail-open：未配=全天活跃=不限制），不依赖 UI 正确性——数据不一致（外部写入）时休眠小时照样拦。
- **为何三态而非四态**：动作维度（发帖 / 未来的评论）不进网格——第三态语义是「该小时允许自动内容」，具体自动做什么由每账号表勾选；评论排期（Phase 2）接入时网格无需再改。

### D7. UI 合到一处：全局网格 + 每账号表；抽共用网格组件

先把控制台现有浏览掩码那张 168 格网格控件抽成共用组件；新页「内容排期」：Card1 = 全局「内容可自动时段」网格（复用该控件），Card2 = 每账号一行的「总开关（默认关）+ 发帖开关 + 日上限 + 时段=跟随全局」表。

- **为何这样反迷路**：168 格 painting 只在全局做一次；账号维度是一张扫一眼就懂的「开关 + 数字」表，账号变多只加行、绝不加要画的 168 格（负担 O(账号数) 而非 O(账号数×168)）。
- **文案红线**：网格文案显式区分「此格治**自动发帖**」vs 安全页那张「治浏览会话」，二者独立；并显式点破「格子 = 何时**允许**自动尝试、非保证发出」（无素材可诚实空槽、日上限 / 人审仍拦），避免「圈了就必发」的误导。
- 每账号自定义时段的「编辑时段」入口 v1 不做（Non-Goal），列先落。

## Risks / Trade-offs

- **[多账号共用全局内容格 → 小时级协同指纹残留]** 所有账号默认继承同一张全局内容格，活跃**小时段**逐位相同；分钟错峰只在小时内打散、不改「每天哪些小时活跃」。平台按小时聚合账号活跃度即见相同 hour-mask。→ **Mitigation**：本 Phase 记为**已知缺口**并写进文档；缓解（hour-mask 打散 / 强制少数账号开 override / 限最小账号集）留后续。发帖无「同码」内容指纹，残留弱于群评。
- **[发帖全局串行 → 到点很多账号没发]** `isPublishBusy()` 全局闸使一个账号发帖期间其它账号的发帖槽本小时顺延。→ **Mitigation**：安全优先接受全局串行；结果卡文案讲清「发帖全局排队、本槽顺延」；长期若要并行需先消灭 `publishAccountRef` 全局槽。
- **[排期发帖语义从「概念阈值」变「格子+错峰」]** `forced=false` 让 `ContentScout` 诚实判无新素材而跳过 → 许多排期槽诚实产出空、回卡。→ **Mitigation**：结果卡文案明写「本槽无新素材、本次不发」，避免运营困惑「到点怎么没发」；绝不静默、绝不为凑数硬发。
- **[心跳漂移 / 漏格 / 重启丢内存态]** `setInterval` 可能因 GC / 重启漏掉某分钟；`lastFired` 内存态重启清零。→ **Mitigation**：漏 = 本小时不发（诚实、无双触发），**绝不补跑漏格**（会 burst）；日上限用持久计数 + 在途台账保证重启不超发。
- **[DST / 时区]** 全按服务器本地时间、单地域；DST 切换令某小时格重复 / 跳过。→ **Mitigation**：单地域约定接受之，不做时区参数（否则过度工程），对齐既有掩码口径。
- **[与在途 WIP 交织]** 云端多文件被三个未提交 change 占用。→ **Mitigation**：新侧表 + 新写通道 + 新页最大化避开交织；落地前等那摊解结提交；迁移文档编号用 0028+。

## Migration Plan

- **DDL**：`content_schedule_global` 与 `account_content_schedule` 经 store `init()` 幂等 `CREATE TABLE IF NOT EXISTS` 自建；伴随人审文档 `migrations/0028_content_schedule.sql`。无数据回填（未配 = 不自动）。
- **回滚**：全为纯新增、所有开关默认关、`AIDCP_CONTENT_SCHEDULE_AUTO` 默认关 → 回滚 = 撤代码即回到今天行为；表可留空不删（幂等无副作用）。
- **部署序列**：等在途 WIP（group-label / group-chat / thinking）那摊解结、提交、测试通过后再落；cloud 面板层按安全序列（备份 → rsync → restart → healthcheck）；console 构建产物按既有 nginx root 发布（不 `--delete`）。**开启开关前**：先只建表 + 上界面配置、`AIDCP_CONTENT_SCHEDULE_AUTO` 保持关，确认配置读写诚实后再开自动。

## Open Questions

- 全局串行发帖在账号较多时「顺延」是否可接受，还是 Phase 1 就要消灭 `publishAccountRef` 全局槽做并行？（默认：先全局串行 + 顺延文案，并行留后续。）
- 结果卡刷屏：多账号同小时段可能涌进多张审批 / 结果卡；是否本 Phase 就加聚合层节流（全局每小时至多 M 张），还是留后续？（默认：本 Phase 靠「每活跃格至多一次 + 日上限」结构性上限，聚合节流留后续。）
- 每账号自定义时段的「编辑时段」界面何时上（存储列已留）。
