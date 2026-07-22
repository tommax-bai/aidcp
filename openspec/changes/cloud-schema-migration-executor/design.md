## Context

### 现状事实（全部实测，给 file:line）

**F1 迁移工具无账本、无顺序、无校验。** `aidcp-cloud/scripts/run-migration.ts:20-26` 从 `process.argv[2]` 取单个文件路径；`:40-46` 建一次性 `Client`、`await client.query(sql)` 把整文件当一条批语句执行、打印 `{status:'ok'}` 后 `client.end()`。没有账本表、没有目录扫描、没有版本比较、没有校验和、没有执行目标标识、没有并发互斥。`aidcp-cloud/package.json` 的 `scripts` 只有 `build` / `typecheck` / `test` / `test:acceptance` / `start` / `trigger:like` / `test:feishu`，无 `migrate`。

**F2 编号四组碰撞、缺一号。** `aidcp-cloud/migrations/` 下 59 个 `.sql`，数字前缀覆盖 `0001`–`0056`。碰撞四组：`0002_bot_chats.sql` / `0002_risk_control.sql`、`0030_content_schedule_group_comments.sql` / `0030_panel_hardening_indexes.sql`、`0037_facebook_comment_mode_templates.sql` / `0037_session_join_group_budget.sql`、`0038_delegated_tasks.sql` / `0038_first_post_onboarding.sql`。`0012` 不存在。因为没有账本，两个库上同号文件的实际先后顺序既不可知也不可复现。

**F3 真实 schema 由两套互斥机制产出。**

- 自建派：34 个存储文件、`CREATE TABLE IF NOT EXISTS` 文本命中 76 处（去注释后生效约 58–60 条），由 `aidcp-cloud/src/server.ts` 的 39 处 `.init()` 触发。例：`src/config/model-config-store.ts:7`、`src/alerts/alert-store.ts:11`、`src/config/quota-config-store.ts:13` 的注释都写着「建表幂等，与 migrations/00xx 同源」——即承认存在两份同源 DDL。
- 迁移派：微信收件箱域三个存储只探测不自建。`src/interactions/interaction-store.ts:293` 注释 `Migrations own the schema`，`:296-331` 用 `to_regclass` + `information_schema.columns` + `pg_indexes` 判断形状；`src/interactions/reply-config-store.ts:72-73`、`src/interactions/reply-config-scope-store.ts:130-131` 同形。
- 对账结果：迁移目录建 59 张表、存储自建 58 张、并集 83 张（**MUST 与 change `cloud-service-boundary-gates` 任务 4.1 的表全集统一口径**——该处记 84 张 / 59 张由 `src/` 建；两个 change 中先动工的一个 MUST 跑一次统一口径脚本并把结果同时回写两处）。**24 张只由存储自建**（`accounts`、`client_users`、`client_environments`、`client_env_scope`、`client_environment_installations`、`client_environment_deletion_requests`、`client_env_revocation_holds`、`anchors`、`anchor_staging`、`concepts`、`curated_content`、`liked_notes`、`valuable_comments`、`group_route`、`hot_lead_config_global`、`facebook_group_target`、`facebook_group_target_scope`、`facebook_group_membership`、`facebook_group_join_audit`、`facebook_group_join_automation_config`、`account_facebook_publish_image`、`account_facebook_publish_image_set`、`persona_auto_fill_runs`、`persona_auto_fill_targets`），**25 张只由迁移建**，34 张两处都有。

**F4 自建表模式已经在牺牲数据完整性。** `src/client-auth/client-user-store.ts:123-127` 写明：`client_environments.account_id` **故意不写** `REFERENCES accounts(account_id)`，因为 `clientUserStore.init()` 跑在 `PgAccountStore` 构造之前，全新库上 `accounts` 尚不存在、加外键必抛；完整性改由读侧每次 JOIN 承担。这是启动顺序对 schema 的直接反向支配。

**F5 启动期 DDL 失败被吞。** `src/server.ts:639-660`：17 个配置类存储的 `init()` 全包在一个 `try` 里，`catch` 只 `console.warn('...初始化失败（回退代码默认模型...）')` 然后继续启动。`src/server.ts:827-833` 的锚点缓存同形。相对地，`src/server.ts:1160` 的 `accountState.init()` 无保护、失败即崩。同一个仓里对「schema 不可用」有三种互不一致的处置。

**F6 零 schema、零角色，唯一授权语句是事故补丁。** 全仓 `CREATE SCHEMA` 命中 0 次、`CREATE ROLE` / `CREATE USER` 命中 0 次。唯一的 `GRANT` 在 `aidcp-cloud/migrations/0050_wechat_group_reply_config_privileges.sql:1-28`，注释直言是 `0048` 被管理员角色执行后运行时角色失去 DML 权限的修复，做法是用 `pg_class.relowner` 反查运行时角色再 `format()` 出 `GRANT`。所有 SQL 未做 schema 限定，靠默认 `search_path=public`；另有 8 处硬编码 `'public.'`：`src/interactions/interaction-store.ts:300-302`、`src/interactions/reply-config-store.ts:72-73`、`src/interactions/reply-config-scope-store.ts:130-131`、`src/cache/curated-content-store.ts:357`。

**F7 库级作用域机制。** `pg_advisory_xact_lock` 共 7 处：`src/interactions/interaction-store.ts:339`、`:409`、`:989`，`src/client-auth/client-user-store.ts:619`、`:1468`、`:2001`、`:2128`。其中 `interaction-env:<envKey>` 这一个命名空间被 client-auth 与 interactions **两个域共用**（`interaction-store.ts:337-339` 的注释明写「Same lock as ClientUserStore.beginEnvironmentOffboard」）。指向 `accounts(account_id)` 的外键 26 处（迁移 19 处，含 `migrations/0039_interaction_inbox.sql` 的 14 处；源码 7 处，如 `src/config/persona-store.ts:41`、`src/delegated-task/store.ts:30`、`src/onboarding/first-post-onboarding-store.ts:27`）。跨 11 张表的单事务离场清理在 `src/interactions/interaction-store.ts:1634-1686`。

**F8 部署流程里没有迁移这一步。** `aidcp/docs/deployment-environments.md:199-210` 的 dev 七步与 ol 八步都不含迁移；破坏性 DDL 的护栏是第 66-69 行的「冻结破坏性/不兼容 dev schema 迁移」，验收方式是人眼看这批有没有新增 `migrations/*.sql`。`aidcp/scripts/deploy-target:41-45` 把目标建模为单 cloud 目录 + 单 service。

**F9 仓内已有可直接照抄的正确范式。** `src/interactions/schema-capability.ts:9-14`：`basePresent` 为假直接抛 `interaction_schema_missing_run_0042`，形状自相矛盾抛 `interaction_schema_inconsistent_run_0046`，绝不自建表；`:16-25` 的 `interactionWritesAllowed` 把「schema 只到旧版」翻译成写侧 fail-closed 而不是假装能写。`test/interactions/migration-contract.test.ts` 则是零数据库依赖的纯文本 SQL 合同测试范式（读 `.sql` 文件用正则断言约束存在）。

## Goals / Non-Goals

**Goals**

- 让「库里现在是哪个版本」成为可查询、可校验、可复现的事实。
- 让 DDL 只有一个所有者（迁移执行器），消灭 34 个存储里的运行时建表（计数按三元组：文本命中 76 处 / 去注释后生效约 58–60 条 / 34 个源文件；**收口范围以「去注释后生效」那一组为准**，MUST NOT 按 76 立范围）。
- 让代码与 schema 不匹配时**停机报错**，而不是自建表继续跑或静默重建空表。
- 让迁移期的每一次数据变更都可逆到「不需要恢复备份」的程度，收缩单独隔离。
- 让今天依赖「同一个数据库」才成立的机制被登记、被机械守住。

**Non-Goals**

- 不建 `CREATE SCHEMA`、不建独立数据库角色、不搬任何表到新 schema。那是拆分方案 §5.1 的后续 change，本变更只做它的前置。
- 不改 `search_path`、不改 dev/ol 共库结论、不动 `docs/deployment-environments.md` 已被用户推迟的拆库决策。
- 不改协议消息、角色注册、风控状态机、命令桥动作映射。
- 不在本变更内执行任何一次真实的表所有权迁移；只交付模板与执行器能力。

## Decisions

### D1 迁移账本：库级单表，一条序列，execution_target 只作审计

新增表 `schema_migrations`：`version TEXT PRIMARY KEY`、`name TEXT`、`checksum TEXT`（文件字节的 SHA-256）、`kind TEXT CHECK (kind IN ('expand','contract'))`、`applied_at TIMESTAMPTZ`、`applied_by TEXT`、`applied_from_target TEXT`、`duration_ms INTEGER`、`baseline BOOLEAN`。

**反直觉但必须写死的一条**：`applied_from_target` 只记「哪个目标的运维动作施加了这条迁移」，**不进唯一键、不参与任何查询过滤**。CLAUDE.md §2 要求持久任务按 `execution_target` 隔离 dev/ol，那条规则的对象是**行级业务数据**；schema 是库的属性，dev 与 ol 共用同一个数据库就只能有一条版本序列。如果照抄 target 隔离范式把账本按 target 分区，同一张表会被两套序列分别建，且两边都认为自己是对的——这是本变更要防的最严重实现误读。

执行器行为：

- 扫描 `migrations/*.sql`，按（数字前缀升序，文件名字典序升序）排序，得到规范序列。
- 用固定 key 的 `pg_advisory_lock` 做整批互斥；拿不到锁 MUST 立即退出并报告另一个执行器在跑，MUST NOT 等待超时后强行继续。
- 每条迁移在**自己的事务**里执行：`BEGIN` → 执行 SQL → 写账本 → `COMMIT`。绝不把整批放进一个事务（PostgreSQL 里部分 DDL 与 `CREATE INDEX CONCURRENTLY` 不能共事务，且一条失败不该让已成功的几条一起回滚而账本失联）。
- 已在账本且校验和一致 → 跳过，不重跑（幂等）。
- 已在账本但校验和不一致 → 整批拒绝，报 `migration_checksum_mismatch` 并列出 version，MUST NOT 重跑、MUST NOT 更新账本里的校验和。
- 存在「版本序小于账本最大已应用版本、却不在账本里」的文件 → 整批拒绝，报 `migration_out_of_order` 并列出 version，MUST NOT 补跑。顺序不可跳是硬约束：允许补跑等于承认存在两条不同历史的库。

不选「每条迁移在应用时才计算并写入自己的哈希、缺失就补写」：那样任何被手工改过的历史迁移都会被自动接受，校验和退化成装饰。

### D2 首次引入必须先实测对账，再基线登记

账本是新建的，而两个库上历史迁移早已由人手跑过（且哪些跑过并不确定——有的表被存储自建覆盖了）。因此执行器必须有 `verify` 与 `baseline` 两个子命令：

- `verify`：把每条迁移声明的表、列、索引、约束与 `information_schema.tables` / `.columns` / `pg_indexes` / `pg_constraint` 实测比对，输出「缺失对象」与「多余对象」两张清单。
- `baseline`：只有 `verify` 的缺失清单为空时才允许执行，把当前全部迁移以 `baseline=true` 写入账本，`applied_at` 记基线时刻。缺失清单非空 MUST 拒绝基线并逐条列出缺什么。

不选「无条件把 59 条全标为已应用」：那正是本项目第一红线禁止的形态——用一次「假设」冒充一次「验证」，一旦某个库其实少跑过一条，后续所有版本比较都建立在假账上。

`verify` 的对象声明来源：本变更为每个迁移文件补一段结构化头注释（`-- aidcp:objects=table:xxx,column:xxx.yyy,index:zzz`），由执行器解析。不选「解析 SQL 文本推断对象」：解析不完整就会产生假阴性，而假阴性在这里等于「验证通过」。

### D3 编号：冻结碰撞、复合序、缺号登记为空洞——不重排文件名

版本 id 定义为文件名去掉 `.sql` 后缀（如 `0002_bot_chats`），全局唯一。排序键为 `(数字前缀, 完整文件名)`。于是：

- 四组碰撞不再是歧义，`0002_bot_chats` 恒在 `0002_risk_control` 之前，顺序确定且可复现；
- 缺号 `0012` 不需要补，序列不要求稠密；
- 不改任何历史文件名。

同时加三条机械约束（文本级测试，零数据库依赖，照 `test/interactions/migration-contract.test.ts` 范式）：新增迁移 MUST NOT 复用已存在的数字前缀；MUST NOT 新建 `0012_*.sql`（`migrations/README.md` 登记 `0012` 为永不分配的历史空洞，防止后来者以为丢了一条）；四组碰撞文件的相对顺序写成断言，改名即测试失败。

不选「重命名碰撞文件以消除同号」：重命名即改版本 id，会让刚建立的账本与文件名对不上，且要在两个已上线的库上同步改账本主键——为一个纯表面问题引入一次真实的数据风险。也不选「用 manifest 文件声明顺序」：多一份需要人工同步的事实源，正是本变更要消灭的东西。

四组碰撞需在实施时逐组核对互不依赖（`0038_delegated_tasks` 与 `0038_first_post_onboarding` 都只依赖 `accounts`，互不引用；其余三组同样核对后再冻结顺序）。

### D4 取消存储自建表：先补迁移，再分批切换，四重保险

**第一步（零风险，必须先做）**：为 24 张只由存储自建的表补写迁移文件，DDL 从存储代码原样抽出、保留 `CREATE TABLE IF NOT EXISTS`。现有库上这些表已存在，补写迁移不改变任何运行时行为，但让迁移目录第一次成为完整事实源——没有这一步，`verify` 永远查不全，新库也永远只能靠存储自建拉起来。

**第二步（机械闸）**：建立 DDL 白名单快照测试。把当前 34 个文件里 `CREATE TABLE` / `ALTER TABLE` / `CREATE INDEX` 的位置固化成一份清单（计数按三元组记：文本命中 76 处 / 去注释后生效约 58–60 条 / 34 个文件；扫描 MUST 先剥注释），测试断言实际集合是清单的子集。清单**只减不增**：任何新增运行时 DDL 立即测试失败。这条闸当天生效，防止边切边被新代码打穿。

**第三步（分批，6 批）**：按域切分，每批把一组存储的建表调用替换为「探测 + 分类」，照抄 `src/interactions/schema-capability.ts` 的范式——探到就正常工作，探不到就该能力 fail-closed 降级并打明确日志，绝不建表。批次顺序按依赖度从低到高：

1. 配置类（`src/config/*`，13 个存储，`server.ts:640-656` 那一段）
2. 指标与告警类（`token-usage-store`、`alert-store`）
3. 缓存与语料类（`src/cache/*`，含 `anchors`、`concepts`、`curated_content`、`liked_notes`、`valuable_comments`、`group_route`、`interaction_feed`、`notification_contact`）
4. Facebook 群组与发布媒体类（`comment-agent/*`、`publish-agent/*`）
5. 委托任务与风控（`delegated-task/store.ts`、`risk/pg-risk-store.ts`、`onboarding/*`）
6. 身份与账号类（`account-store.ts`、`client-auth/client-user-store.ts`）——**放最后**，因为 `accounts` 是 26 处外键的目标，且 `client-user-store.ts:123-127` 那个被启动顺序逼出来的缺外键要在这一批里一并用迁移补回。

**第四重保险**：全局回滚旋钮 `AIDCP_SCHEMA_SELF_CREATE`（默认 `false`；设为 `true` 恢复本批切换前的自建行为），保留一个发布周期后随本 change 的收尾任务删除。旋钮为 `true` 时 MUST 在启动日志打出显式警告并标注这是过渡态。

同时把 `server.ts:639-660` 与 `:827-833` 的「DDL 失败只 warn 继续」改为：schema 契约门（D5）已在更早处把致命情况拦掉，此处的 catch 只允许覆盖连接类瞬时故障，且必须区分「连不上库」与「库里没有这张表」两种原因并分别报出，MUST NOT 再用一句通用 warn 把两者混为一谈。

### D5 启动期 schema 契约门：堵住回滚静默重建空表

构建内声明两个常量：`REQUIRED_SCHEMA_VERSION`（本构建正常工作所需的最低迁移版本 id）与 `KNOWN_MAX_SCHEMA_VERSION`（本构建认识的最高迁移版本 id，等于该构建 `migrations/` 里的最大版本）。启动时读账本的最大已应用版本，三分支：

- 账本最高 **等于或高于** `REQUIRED` 且 **不超过** `KNOWN_MAX` → 正常启动。
- 账本最高 **低于** `REQUIRED` → 拒绝启动，报 `schema_behind_code` 并逐条列出缺失版本。MUST NOT 自建表、MUST NOT 降级继续。
- 账本最高 **高于** `KNOWN_MAX`（库比代码新，即回滚场景）→ 默认拒绝启动，报 `schema_ahead_of_code` 并列出超前版本。

第三个分支就是本变更要堵的洞。今天回滚旧代码，旧存储在启动期发现表不在（被迁走/改名）就 `CREATE TABLE IF NOT EXISTS` 建一张空表并开始写入，且没有任何告警——一次静默假成功，事后只能靠数据对不上才发现。契约门把它变成一次显式的启动失败。

放行通道 `AIDCP_ALLOW_SCHEMA_AHEAD` **必须填具体的最高版本 id**，不得是布尔值。理由：布尔旁路一旦被打开就永久生效，下一次真正危险的超前也会被同一个开关放过；填版本号则每次超前都要重新做一次判断。放行时 MUST 在启动日志与告警通道各记一条，内容含被放行的版本区间与操作者。

该门 MUST 跑在任何存储 `init()` 之前，MUST NOT 被 `try/catch` 吞掉。契约门本身读账本失败（账本表不存在或连不上）时同样拒绝启动，理由是无法证明 schema 正确——这是 fail-closed，不是可用性折衷。

不选「按表逐个探测代替版本闸」：逐表探测只能回答「这张表在不在」，回答不了「库里的版本比我新」，而回滚场景里表往往是在的、只是语义变了。

### D6 只扩张不收缩

每个迁移文件头 MUST 声明 `-- aidcp:kind=expand` 或 `-- aidcp:kind=contract`；执行器解析并写入账本，缺声明 MUST 拒绝应用。

- `expand` = 新增表、新增列、新增索引、新增 `NOT VALID` 约束、数据回填、新增触发器。特征是旧版本代码在这条迁移之后仍能正常读写。
- `contract` = `DROP TABLE` / `DROP COLUMN` / `RENAME` / 类型收窄 / 加 `NOT NULL` / 删索引 / `VALIDATE` 之后的约束收紧。特征是旧版本代码在这条迁移之后会坏。

dev/ol 共库期间执行器 MUST 默认拒绝应用 `kind=contract`，只在显式 `--allow-contract` 时应用，并把该次授权连同操作者写入账本。这条是 `aidcp/docs/deployment-environments.md:66-69` 破坏性 DDL 冻结在迁移期的延伸，不是新护栏。

重命名 MUST NOT 用 `ALTER … RENAME`，MUST 改写为：新增目标列（expand）→ 双写 → 影子读比对 → 切读 → 停旧写 → 独立 contract 删旧列。收缩 MUST 是独立 change、独立部署、可单独回滚，MUST NOT 与任何 expand 迁移同批交付。

### D7 表所有权迁移六步模板

| 步 | 动作 | 验收信号（必须为可观测事实） | 回退动作 |
| --- | --- | --- | --- |
| 0 准备 | expand 迁移建新表/新列，旧路径完全不动 | 执行器 `verify` 报新对象齐备且无多余对象；旧路径全量测试通过 | 一条 contract 迁移删新对象；因无写入者，零数据损失 |
| 1 双写 | 旧所有者仍是权威写；新增对新表的同请求写。新表写失败 MUST 计错误数并告警，MUST NOT 静默吞，MUST NOT 因新表失败阻断权威写 | 双写错误计数在观察期内为 0；观察期 ≥ 3 个自然日且覆盖 dev 与 ol 各一个完整业务日 | 关双写开关；新表数据作废 |
| 2 影子读对账 | 读仍走旧表；对账器比对新旧两侧，输出差异条数、差异样例与**已比对行数** | 差异条数为 0，且已比对行数覆盖旧表全量或声明的抽样比例。MUST NOT 用「没发现差异」冒充「比对过」——覆盖率为 0 时结论是未验证，不是通过 | 修双写、清空新表、重新计观察期 |
| 3 切读 | 读切到新表，旧表继续双写 | 切读前后业务行数、错误率与既有日志关键字计数一致；开关可秒切回 | 开关切回读旧表；无数据动作 |
| 4 停旧写 | 新所有者成为唯一写入者，旧表停写 | 观察期内 `pg_stat_user_tables` 上旧表的 `n_tup_ins/upd/del` 不再增长 | 恢复旧写开关（恢复的是双写，不是把旧表重新当权威读） |
| 5 收缩 | 独立 change 的 contract 迁移删旧表/旧列 | contract 单独部署、单独验证；账本记 `kind=contract`、操作者与授权 | **不可逆**。回退只能从步 5 之前的备份恢复。因此步 5 MUST 在观察期结束、备份存在且校验过之后执行 |

跨服务执行同一模板时，步 1 的双写若落在两个进程里，MUST 走持久命令 / Outbox，MUST NOT 依赖 advisory lock 或共享事务——理由见 D8。

模板本身 MUST 落成 `aidcp-cloud/docs/table-ownership-migration.md`，每次表迁移的 change 引用它并逐步登记实际观察期与信号值。

### D8 库级作用域盘点：拆 schema 不失效，拆库才失效

必须先纠正一个容易被误读的点：`pg_advisory_lock` 与外键都是**数据库级**作用域，与 schema 无关。把表搬进新 schema，锁与外键**照常有效**；只有真正拆成两个数据库才失效，且失效方式是**静默的**——锁不再互斥、外键根本不存在，业务照跑，数据慢慢分叉。这正是本项目红线禁止的形态。

盘点产出 `aidcp/docs/database-scope-inventory.md`，每条记：机制、位置 file:line、当前作用域、拆 schema 后是否成立、拆库后是否成立、拆库时的替代方案。首批四类：

1. **advisory lock 7 处**：`src/interactions/interaction-store.ts:339`（`interaction-env:<envKey>`）、`:409`、`:989`（`interaction-send|<accountId>`），`src/client-auth/client-user-store.ts:619`、`:1468`、`:2001`、`:2128`（均为 `interaction-env:<envKey>`）。`interaction-env` 命名空间跨 client-auth 与 interactions 两域共用（`interaction-store.ts:337-339` 注释已确认这是有意的同一把锁）。拆库替代：改为对同一权威表行的 `SELECT … FOR UPDATE`，或按拆分方案 §6.2 的持久命令 + Inbox 去重。
2. **跨域外键**：指向 `accounts(account_id)` 26 处（迁移 19 处，其中 `migrations/0039_interaction_inbox.sql` 占 14 处；源码 7 处）；指向 `client_users(user_id)` 3 处（`src/client-auth/client-user-store.ts:189`、`src/config/persona-auto-fill-store.ts:51`、`migrations/0043_client_env_provisioning_intents.sql:8`）；指向 `publish_log(id)` 2 处（`src/publish-agent/facebook-publish-media-store.ts:109`、`:131`）。拆库替代：改为应用层校验 + 读侧 fail-closed，范式已存在于 `src/client-auth/client-user-store.ts:123-127`（该处因启动顺序被迫走这条路，正好是可复用的先例）。
3. **跨 11 表单事务清理**：`src/interactions/interaction-store.ts:1634-1686` 的 `purgeDueOffboards`。拆 schema 仍原子，拆库不原子。替代：改为可重入的分表 saga，每张表的清理独立幂等。
4. **硬编码 `'public.'` 形状探测 8 处**：`src/interactions/interaction-store.ts:300-302`、`src/interactions/reply-config-store.ts:72-73`、`src/interactions/reply-config-scope-store.ts:130-131`、`src/cache/curated-content-store.ts:357`。改 `search_path` 救不了这些。本变更内把它们收口到单一常量/配置读取点，为后续搬 schema 留缝（不改行为）。

清单 MUST 由源码扫描测试锁死：断言 `pg_advisory` 调用点集合、`REFERENCES` 跨域目标集合与清单一致，新增未登记即测试失败。只写文档不加测试等于没做——本仓已有先例证明纯文档约束会被静默打穿。

## Risks / Trade-offs

- **基线登记时发现两个库实际状态不同** → 这是本变更的主要发现风险，而不是失败。`verify` 的缺失清单就是修复清单：先补跑缺失迁移使两库一致，再 baseline。绝不允许为了让 baseline 通过而放宽比对。
- **补写 24 张表的迁移文件与存储 DDL 漂移** → 补写内容 MUST 从存储代码原样抽出并加文本级一致性测试（比对两侧的列名集合），漂移即测试失败；第三步切换完成后存储侧 DDL 被删除，漂移面自然归零。
- **契约门在共库期误拦 ol** → dev 跑主干、ol 跑发布分支，dev 应用一条新 expand 迁移后 ol 的账本立刻超前于 ol 代码的 `KNOWN_MAX`，会触发 `schema_ahead_of_code`。这是**真实的、必须显式处理**的后果，不是误报：处置是运维用 `AIDCP_ALLOW_SCHEMA_AHEAD=<版本id>` 逐次放行（只对 expand 有效，因为 contract 在共库期本来就被 D6 拒绝）。这条约束反过来给共库期加了一道机械提醒：每次 dev 加迁移，ol 必须表态。
- **分批切换期跨批的启动顺序依赖** → 第 6 批（身份与账号类）之前，`accounts` 仍由存储自建，而配置类存储的外键指向它。因此批次顺序 MUST 严格自低依赖向高依赖推进，且每批合并前跑一次全新空库拉起测试（迁移执行器 + 契约门 + 该批已切换的存储），证明新库不再需要该批存储自建。
- **`src/server.ts` 与 34 个存储文件是并行 fleet 的高冲突面** → 见下节串行说明。

## Migration Plan

1. 交付执行器 + 账本迁移 + `verify` / `baseline` 子命令，不改任何运行时代码；在 dev 库跑 `verify`，把缺失清单作为事实产出。
2. 补跑缺失迁移使 dev 与 ol 库对象齐备，再对该库做一次 `baseline`（共库，只做一次）。
3. 补写 24 张表的迁移文件 + DDL 白名单测试 + 编号约束测试。此批零运行时行为变化。
4. 上线启动期 schema 契约门（先以只告警模式跑满一个发布周期，确认无误拦后切为拒绝启动）。告警模式期间 MUST 输出与拒绝模式完全一致的判定结论，MUST NOT 只打一句「可能不匹配」。
5. 按 D4 的 6 批推进存储去 DDL，每批独立部署 dev、观察后再进下一批。
6. 收尾：删除 `AIDCP_SCHEMA_SELF_CREATE` 旋钮、删除 `scripts/run-migration.ts`（其能力已被执行器完全覆盖，保留即保留一条无账本旁路）、把迁移步骤写进 `docs/deployment-environments.md` 的 dev/ol 流程。

退出方式：步骤 1–3 任一阶段可直接 revert 分支，零数据成本（账本表留着无害，`baseline` 行可删）。步骤 4 起的退出是关掉契约门（改回告警模式），不是删账本。步骤 5 每批的退出是把该批旋钮设回 `true`。

## Open Questions

- 契约门告警模式的时长以「一个完整发布周期且覆盖一次 ol 部署」为准，具体日历天数在实施时由部署节奏确定，MUST 记进 tasks.md 而不是留在代码注释里。
- 执行器是否在 dev 部署序列里自动运行、还是保持人工显式调用，由步骤 6 定案；在定案前 MUST 保持人工显式调用，MUST NOT 因为「顺手」把未经审阅的迁移接进自动部署。
