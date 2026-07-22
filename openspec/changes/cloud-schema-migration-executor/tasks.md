## 1. aidcp-cloud — 迁移执行器与账本

- [x] 1.1 新增 `migrations/0057_schema_migrations_ledger.sql`（`kind=expand`）：建 `schema_migrations` 表，列为 `version TEXT PRIMARY KEY`、`name TEXT NOT NULL`、`checksum TEXT NOT NULL`、`kind TEXT NOT NULL CHECK (kind IN ('expand','contract'))`、`applied_at TIMESTAMPTZ NOT NULL DEFAULT now()`、`applied_by TEXT`、`applied_from_target TEXT`、`duration_ms INTEGER`、`baseline BOOLEAN NOT NULL DEFAULT false`。`applied_from_target` 无索引、无唯一约束、不参与任何查询谓词——它只是审计列。
<!-- aidcp-cloud aef34a0 偏离：文件名为 migrations/0064_schema_migrations_ledger.sql。0057 在写 tasks 时还没被占用，实施时 0057-0063 已被 publish-draft-refinement / risk-state-cross-process-integrity / config-mirror-cross-process-invalidation / publish-approval-signal-to-database 四个 change 占走，故顺延到 0064。列定义逐条按 tasks 落地。 -->
- [x] 1.2 新增 `src/schema/migration-plan.ts`：纯函数层，输入「文件名 + 内容」列表与账本行列表，输出 `{ pending, skipped, errors }`。排序键为 `(数字前缀数值升序, 完整文件名字典序升序)`。可判定的错误只有三类：`migration_checksum_mismatch`、`migration_out_of_order`、`migration_kind_missing`。此文件不 import `pg`，可脱库单测。
<!-- aidcp-cloud aef34a0 另返回 ledgerOnly（账本有、磁盘无），不作为可判定错误、交由启动期契约门处理 -->
- [x] 1.3 新增 `scripts/migrate.ts` CLI，四个子命令：`status`（列出已应用/待应用/异常，只读）、`up`（应用待应用项）、`verify`（实测对象比对）、`baseline`（写基线）。`package.json` 加 `"migrate": "tsx --env-file=.env scripts/migrate.ts"`。
<!-- aidcp-cloud aef34a0 -->
- [x] 1.4 `up` 实现：整批用固定 key `pg_advisory_lock` 互斥，拿不到锁立即退出并打印持锁提示，不等待、不强行继续；每条迁移单独 `BEGIN … COMMIT`，事务内先执行 SQL 再写账本；任一条失败即停止整批并以非 0 退出码报出失败的 version 与原始错误，已成功的几条保留在账本里。
<!-- aidcp-cloud aef34a0 -->
- [x] 1.5 `up` 拒绝语义：`migration_plan` 返回任一错误时整批拒绝、不执行任何 SQL；校验和不符时 MUST NOT 重跑、MUST NOT 更新账本 checksum；乱序时 MUST NOT 补跑低版本文件。
<!-- aidcp-cloud aef34a0 -->
- [x] 1.6 `up` 的 `kind` 闸：文件缺 `-- aidcp:kind=` 头声明即拒绝；`kind=contract` 默认拒绝并提示需 `--allow-contract`；带 `--allow-contract` 应用时把授权者写入账本 `applied_by`。
<!-- aidcp-cloud aef34a0 -->
- [x] 1.7 `applied_from_target` 取自 `AIDCP_DEPLOY_ENV`；未设置时写 `unknown` 并在输出里注明，MUST NOT 因为缺 target 就拒绝执行（schema 是库的属性，不是任务）。
<!-- aidcp-cloud aef34a0 -->
- [x] 1.8 为每个迁移文件补结构化对象声明头注释 `-- aidcp:objects=table:<t>,column:<t>.<c>,index:<i>,constraint:<c>`；`verify` 解析该声明并与 `information_schema.tables` / `information_schema.columns` / `pg_indexes` / `pg_constraint` 实测比对，输出「缺失对象」与「多余对象」两张清单。MUST NOT 由 SQL 文本推断对象。
<!-- aidcp-cloud aef34a0 头声明由一次性工具 scripts/generate-migration-headers.ts 生成后签入；只声明 table/column/index 三类，约束名不机械登记（PG 自动命名会制造噪声而非事实） -->
<!-- aidcp-cloud ecf5290 修 aef34a0 的一处硬缺陷：objectPresent 里 `key.endsWith(` ${name}`)` 的空格落成了 NUL 字节（git 把该文件判为 binary），后果是**每个声明的索引恒判缺失** → verify 刷假缺失、baseline 永远拒绝写入。已修并补脱库单测 test/schema/schema-inspect.test.ts -->
<!-- aidcp-cloud aef34a0 rebase 后 0061/0062/0063 三条新迁移缺头声明（编号治理用例当场红），已在 9c9e72b 用同一工具补齐 -->
<!-- aidcp-cloud a6c00c1 修两处解析缺陷：① 多子句 `ALTER TABLE t ADD COLUMN a, ADD COLUMN b` 只解析出第一列（生成端与运行时探测端共用同一个有缺陷的正则），实测 migrations/ 下 108 处加列只捕获 104 处——漏掉的列 verify 永远报不出缺失（而缺失清单是 baseline 唯一的准入闸），探测也会在真缺列的库上返回 ready。改成「先切 ALTER 语句、再在语句体内全局找 ADD COLUMN 子句」的两段解析，收口到 src/schema/ddl-objects.ts 的 findAddedColumns 一处，生成器改为复用它；实测补回 0041 的 1 列、0049 的 3 列。② 头声明的对象归属依赖复合序，文件一改名旧头就停在旧归属上，故 generate-migration-headers.ts 加 --rewrite（已有 kind 是人工结论，重生成时保留、不一致时报出）。重跑命令：npx tsx scripts/generate-migration-headers.ts --rewrite --write。注意它会改文件校验和，MUST 只在这批迁移进真库账本之前用 -->
<!-- aidcp-cloud a6c00c1 verify/baseline 的实测来源从 information_schema 改到 pg_catalog：原写法与同批交付的运行时探测（schema-capability.ts）刻意改用 pg_catalog 的理由直接冲突——information_schema 只显示当前角色有权限的对象，权限不全时会把「有表但没权限」刷成一串假缺失，baseline 被拒且补跑多少次迁移都不会变空（migrations/0050 就是那次权限事故的补丁）。表与列的查询收口到新的 src/schema/pg-catalog.ts 一处，消掉「同一件事两份口径」 -->
- [x] 1.9 `baseline` 实现：先内部跑一次 `verify`；缺失清单非空时拒绝写入并逐条打印缺什么、来自哪个 version；清单为空才把全部迁移以 `baseline=true` 写入账本。`baseline` 对已有账本行 MUST 幂等跳过、MUST NOT 覆盖。
<!-- aidcp-cloud aef34a0 + ecf5290（NUL 修复前 baseline 实际永远拒绝，属不可用而非静默通过） -->
- [x] 1.10 脱库单测（照 `test/interactions/migration-contract.test.ts` 的纯文本范式）：排序复合序、幂等跳过、校验和不符拒绝、乱序拒绝、缺 kind 拒绝、contract 默认拒绝、`baseline` 在缺失清单非空时拒绝。
<!-- aidcp-cloud aef34a0 test/schema/migration-plan.test.ts 覆盖前六条 -->
<!-- aidcp-cloud ecf5290 test/schema/schema-inspect.test.ts 补第七条（baseline 的拒绝依据 = diffSchema 的缺失清单非空，且缺失项须带来源 version） -->

## 2. aidcp-cloud — 编号治理

- [x] 2.1 新增 `migrations/README.md`：写明版本 id = 文件名去后缀、排序为 `(数字前缀, 文件名)` 复合序、四组历史碰撞（`0002` / `0030` / `0037` / `0038`）的既定相对顺序、`0012` 为永不分配的历史空洞、以及「新增迁移不得复用已有数字前缀」。
<!-- aidcp-cloud aef34a0 -->
- [x] 2.2 逐组核对四组碰撞文件互不依赖并把结论写进 `migrations/README.md`：`0002_bot_chats` vs `0002_risk_control`、`0030_content_schedule_group_comments` vs `0030_panel_hardening_indexes`、`0037_facebook_comment_mode_templates` vs `0037_session_join_group_budget`、`0038_delegated_tasks` vs `0038_first_post_onboarding`（后两者均只引用 `accounts`，互不引用）。若发现真实依赖，冻结的顺序必须与依赖一致。
<!-- aidcp-cloud aef34a0 四组均核对为表集合不相交 / 互不引用，结论逐行落 README §2 表格 -->
- [x] 2.3 新增 `test/schema/migration-numbering.test.ts`：断言（a）不存在 `0012_*.sql`；（b）除已登记的四组外不存在新的同号；（c）四组碰撞的文件名集合与相对顺序与 README 一致；（d）每个 `.sql` 都有 `-- aidcp:kind=` 与 `-- aidcp:objects=` 头。零数据库依赖。
<!-- aidcp-cloud aef34a0 -->
- [x] 2.4 MUST NOT 重命名任何历史迁移文件（重命名即改版本 id，会让账本主键与文件对不上）。本节只做冻结与断言。
<!-- aidcp-cloud aef34a0 零重命名。注：定稿 docs/cloud-service-decomposition-proposal.md §5.4.2 要求「消除 4 组编号碰撞与 0012 缺号，重编后的编号 MUST 与基线账本一致」，与本 change 的 D3 直接冲突。现状按 D3 冻结，冲突已写进 docpatch ⑤ 5.1 待裁决 -->
<!-- aidcp-cloud a6c00c1 仍是零历史重命名：a6c00c1 改的是本 change 自己新增、且尚未进任何真库账本的 0065/0066（合并为 0000）。D3 禁的是「改已上线库账本主键」，不是「改一条还没落过账的新文件的名字」——判据是账本里有没有它，backlog 110.2 落账之后这道口就永久关上 -->

## 3. aidcp-cloud — 补齐缺失迁移，使迁移目录成为完整事实源

- [x] 3.1 新增 `migrations/0058_baseline_self_created_tables.sql`（`kind=expand`）：把 24 张只由存储自建、迁移目录从未创建的表的 DDL 原样抽出，保留 `CREATE TABLE IF NOT EXISTS`。清单：`accounts`、`client_users`、`client_environments`、`client_env_scope`、`client_environment_installations`、`client_environment_deletion_requests`、`client_env_revocation_holds`、`anchors`、`anchor_staging`、`concepts`、`curated_content`、`liked_notes`、`valuable_comments`、`group_route`、`hot_lead_config_global`、`facebook_group_target`、`facebook_group_target_scope`、`facebook_group_membership`、`facebook_group_join_audit`、`facebook_group_join_automation_config`、`account_facebook_publish_image`、`account_facebook_publish_image_set`、`persona_auto_fill_runs`、`persona_auto_fill_targets`。文件可按域拆成多个，但每个都必须带 kind 与 objects 头。
<!-- aidcp-cloud aef34a0 按域拆成 0065 身份 / 0066 缓存语料 / 0067 Facebook / 0068 人设自动填充；0069 单独承接身份域两条 SET NOT NULL（kind=contract，留在 0065 会把一个纯基线文件整体标成 contract） -->
<!-- aidcp-cloud a6c00c1 **编号返工（审计坐实的 blocker）**：0065/0066 排在「后续 ALTER 这些表」的历史迁移之后，全新空库上按执行器自己的复合序跑 `migrate up`，第 5 条 0005_account_id_columns 就整批停住（relation "concepts" does not exist）——即「迁移目录是完整事实源」这句话只在旧库上成立（旧库表早被存储自建，走 baseline 记账不跑 up）。0065+0066 合并为 **0000_baseline_identity_and_corpus_tables.sql**、排在全部历史迁移之前；合并成一个文件是因为复合序要求数字前缀唯一，而 0001-0011 之间没有空号（0012 是登记在案的空洞）。0067（对 publish_log 有外键）/ 0068 保持原位——无任何历史迁移引用它们的表。改名成本为零的前提是这批迁移**尚未进任何真库账本**；一旦按 backlog 110.2 在 dev baseline 落账，改版本 id 就是改两个已上线库的账本主键（D3 明令禁止）。 -->
- [x] 3.2 抽取时必须包含存储侧的自愈 `ALTER TABLE … ADD COLUMN IF NOT EXISTS` 与 `CREATE INDEX IF NOT EXISTS`（例：`src/client-auth/client-user-store.ts:120-160` 的一串加列与两条索引），否则新库建出的表会缺列。
<!-- aidcp-cloud aef34a0 24 张表的自愈语句全部抽出 -->
<!-- aidcp-cloud 9c9e72b 新增 migrations/0070_baseline_self_heal_columns.sql 补第二类缺口：**表本身在迁移目录里、后续自愈加列却只活在存储常量里**的 16 列 3 索引（account_content_schedule 三档模式列、contact_comment_attempts 四个审计列、delegated_tasks.origin_chat_id + 两个局部表达式索引、publish_log 八列 + idx_publish_log_platform）。这类缺口在 dev/ol 上完全看不出来（列是存储早年自建的），只有全新空库才缺；由 test/schema/ddl-parity.test.ts 新增的「空库拉起静态前提」用例逐条找出 -->
- [x] 3.3 新增 `test/schema/ddl-parity.test.ts`：对这 24 张表，比对存储源码 DDL 与新迁移文件的列名集合、索引名集合，不一致即失败。此测试在第 5 节切换完成、存储侧 DDL 删除后随之删除。
<!-- aidcp-cloud 9c9e72b 四条断言：24 张表的列集合 / 索引集合 / 表存在性，外加一条更强的「只跑迁移建出的库能满足全部存储的探测要求」（不限于 24 张表）。解析口径收口在 src/schema/ddl-objects.ts，与探测层同源 -->
<!-- aidcp-cloud a6c00c1 修一处**诚实性问题**：第四条用例原名「只跑迁移建出的库能满足全部存储的探测要求（空库拉起的静态前提）」，但它只比对象**集合**、对执行顺序完全无感，所以上面那条编号缺陷它永远不会红。用例改名为「迁移目录没抄漏对象：存储探测要求的对象都在（只比集合，不含顺序）」，顺序那一半新增 test/schema/migration-order.test.ts（静态模拟复合序，断言没有任何迁移引用尚未建出的表；判定层在 src/schema/migration-order.ts）。该检查器在返工前的 HEAD 上报出 15 处顺序缺陷、返工后 0 处 -->
- [ ] 3.4 本节 MUST NOT 修改任何存储代码，MUST NOT 改变启动行为。交付后在 dev 跑 `migrate verify`，缺失清单应为空。
<!-- aidcp-cloud aef34a0 前半句成立：0065-0070 全部为 CREATE/ALTER … IF NOT EXISTS，现网库上是 no-op，且该批未动任何存储代码 -->
<!-- BLOCKED: 「在 dev 跑 migrate verify」需要真库，本 session 无 ECS 权限（集成与部署由主控串行做）。已登记 docs/real-machine-acceptance-backlog.md 新簇 110.1 -->

## 4. aidcp-cloud — DDL 单一所有者的机械闸

- [x] 4.1 新增 `test/schema/runtime-ddl-allowlist.test.ts`：扫描 `src/**/*.ts`，收集所有含 `CREATE TABLE` / `ALTER TABLE` / `CREATE INDEX` 的位置，断言集合是 `test/schema/runtime-ddl-allowlist.json` 的子集。基线快照 MUST 按三元组记，MUST NOT 只写 76：**文本命中 76 处 / 去注释后生效约 58–60 条 / 分布在 34 个源文件**（口径与定稿 §5.4.1 一致）。扫描器 MUST 先剥 `--` 行注释与 `/* */` 块注释再判定（与 change `cloud-service-boundary-gates` 任务 4.2 同规则），否则会把注释掉的 DDL 当成运行时建表点、给第 5 节的收口范围凭空加出十几条假目标。
<!-- aidcp-cloud 9c9e72b 扫描器 src/schema/ddl-scan.ts（先剥 SQL 行注释 / 块注释 / TS 行注释再判定），清单 test/schema/runtime-ddl-allowlist.json，用例落在 test/acceptance/schema-ddl-owner.test.ts（见 4.3 的偏离说明） -->
<!-- aidcp-cloud 9c9e72b **基线按当前 master 实测，未沿用 tasks 里的历史数字**：三个动词合计 271 文本命中 / 252 去注释后生效 / 37 个文件；其中仅建表动词 83 / 64 / 37（tasks 记 76 / 58–60 / 34），ALTER TABLE 115（定稿记 112）、CREATE INDEX 73（定稿记 63）。差额来源：config-mirror-cross-process-invalidation 新增 src/config/mirror-version-store.ts、publish-approval-signal-to-database 新增 src/publish-agent/publish-approval-store.ts（文件数 35→37），其余为这三个 change 在既有存储里追加的自愈 ALTER 与索引。重跑命令：npx tsx scripts/generate-ddl-allowlist.ts -->
- [x] 4.2 允许清单 MUST 只减不增：新增运行时 DDL 即测试失败并提示「DDL 只能加在 migrations/」。每完成一批切换，从清单里删掉对应条目。
<!-- aidcp-cloud 9c9e72b 子集断言 + 三元组只减不增断言（两条都要，只盯一个数会漏掉「注释里搬来搬去」与「同一文件里堆更多条」两种退化） -->
<!-- aidcp-cloud 9c9e72b 偏离说明：第 5 节切换后清单条目**暂未变少**。原因是 D4 第四重保险要求保留回滚旋钮 AIDCP_SCHEMA_SELF_CREATE，旋钮为 true 时仍要执行那些 DDL 常量，故常量必须留在 src/ 里。条目真正变少的时点是任务 5.11（删旋钮 + 删常量），已登记 backlog 110.9。今天的效果是「冻住不许变多」，不是「已经变少」 -->
- [x] 4.3 该测试进 `npm run test:acceptance`，与 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 同级作为红线用例，命名 `AC-SCHEMA-DDL-OWNER`。
<!-- aidcp-cloud 9c9e72b 偏离：npm run test:acceptance 只 glob test/acceptance/*.test.ts，故用例文件放在 test/acceptance/schema-ddl-owner.test.ts（而非 tasks 写的 test/schema/），清单 JSON 仍按 tasks 放 test/schema/runtime-ddl-allowlist.json。改 glob 会影响其他 change，不动 -->

## 5. aidcp-cloud — 分批取消存储自建表

- [x] 5.1 新增 `src/schema/schema-capability.ts`（通用版，范式照抄 `src/interactions/schema-capability.ts:9-25`）：给定探测结果返回 `ready` / `degraded` / `missing`；`missing` 时抛带 version id 的明确错误，MUST NOT 建表。
<!-- aidcp-cloud 9c9e72b degraded 同样抛（错误码 schema_incomplete_*，区别于 missing 的 schema_missing_*）：缺列时存储的 SELECT / ON CONFLICT 迟早会抛一条不带 version id 的原始 PG 错误，在 init 处一次把话说清楚严格更好 -->
<!-- aidcp-cloud 9c9e72b 「要求」不手写清单，而是由存储自己那段 DDL 常量解析得出（src/schema/ddl-objects.ts）——手写第二份列清单必然漂移。探测走 pg_catalog 而非 information_schema：后者只显示当前角色有权限的对象，会把「有表但没权限」误报成「表不存在」（migrations/0050 就是那次权限事故的补丁） -->
<!-- aidcp-cloud a6c00c1 补上 9c9e72b 的**零测试覆盖**（审计坐实的 serious）：本模块是 34 个存储 init() 共用的唯一入口、承担 5.1/5.2 声明的两条红线，此前 ensureCapabilitySchema / classifySchemaCapability / SchemaCapabilityError / AIDCP_SCHEMA_SELF_CREATE 在 test/ 下命中数为 0；同时 test/fixtures/schema-probe.ts 会用存储自己的 DDL 常量反推出「假库里恰好有它要的一切」，于是 13 个存储单测里探测永远成功，missing / degraded / 旋钮三条路径一次都没被走过。新增 test/schema/schema-capability.test.ts 六例：ready（只发 2 条探测语句、零 DDL）/ missing（schema_missing_* + 缺失表 + 处置动作）/ degraded（缺列、缺索引各一）/ 旋钮 true 确实回到自建 / 旋钮只认字面量 true / 纯判定层。「非 ready 路径一条 DDL 都没发出」用与 AC-SCHEMA-NO-SILENT-RECREATE 同一个扫描器判定 -->
- [x] 5.2 加全局回滚旋钮 `AIDCP_SCHEMA_SELF_CREATE`，默认 `false`；为 `true` 时恢复自建并在启动日志打显式过渡态警告。
<!-- aidcp-cloud 9c9e72b schemaSelfCreateEnabled() + warnSelfCreateOnce() -->
- [x] 5.3 批 1 — 配置类 13 个存储（`src/config/model-config-store.ts`、`credential-store.ts`、`role-config-store.ts`、`category-config-store.ts`、`quota-config-store.ts`、`pacing-config-store.ts`、`session-config-store.ts`、`hot-lead-config-store.ts`、`resume-config-store.ts`、`content-schedule-store.ts`、`persona-store.ts`、`approval-policy-store.ts`、`facebook-comment-config-store.ts`）：删除建表与自愈加列，改探测；`src/server.ts:639-660` 的统一 `catch` 拆成「连不上库」与「schema 缺对象」两类分别报出。
<!-- aidcp-cloud 9c9e72b 13 个存储全部切换；组合根传入的 configMirrorPool 与 mirrorVersionBumper 两条接线未动 -->
<!-- aidcp-cloud 9c9e72b 偏离：DDL 常量**保留但不再执行**（默认路径只探测），因为 5.2 的回滚旋钮要求 true 时能恢复自建。常量的删除在 5.11 -->
<!-- aidcp-cloud 9c9e72b server.ts 两处 catch 都做了拆分：配置层那处 + 锚点缓存那处（design.md D4 要求的 :827-833 同形处理） -->
- [x] 5.4 批 2 — 指标与告警（`src/metrics/token-usage-store.ts`、`src/alerts/alert-store.ts`）。
<!-- aidcp-cloud 9c9e72b -->
- [x] 5.5 批 3 — 缓存与语料（`src/cache/pg-anchor-cache.ts`、`concept-store.ts`、`curated-content-store.ts`、`liked-note-store.ts`、`valuable-comment-store.ts`、`group-route-store.ts`、`interaction-feed-store.ts`、`notification-contact-store.ts`）。同批把 `src/cache/curated-content-store.ts:357` 的硬编码 `'public.'` 收口到统一常量。
<!-- aidcp-cloud 9c9e72b 8 个存储全部切换；curated-content-store 的 to_regclass('public.curated_content') 已改用 src/schema/schema-name.ts 的 qualifiedObjectName()，行为不变（默认仍 public）。全仓硬编码 'public.' 从 8 处降到 7 处，剩余 7 处全在 src/interactions/**（定稿 §5.4.2 要求 8 处全收口，本 change 的 tasks 只授权了这一处；缺口见 docpatch ⑤ 5.2） -->
- [x] 5.6 批 4 — Facebook 群组与发布媒体（`src/comment-agent/facebook-group-store.ts`、`facebook-comment-audit-store.ts`、`src/publish-agent/publish-log-store.ts`、`facebook-publish-media-store.ts`、`src/config/facebook-group-join-automation-store.ts`、`src/config/persona-auto-fill-store.ts`）。
<!-- aidcp-cloud 9c9e72b 6 个文件 8 个 init（facebook-group-store 一个文件里三个 store 各一个 init） -->
- [ ] 5.7 批 5 — 委托任务、风控与引导（`src/delegated-task/store.ts`、`src/risk/pg-risk-store.ts`、`src/onboarding/first-post-onboarding-store.ts`）。
<!-- aidcp-cloud 9c9e72b 三者中已完成两个：src/delegated-task/store.ts、src/onboarding/first-post-onboarding-store.ts -->
<!-- BLOCKED: src/risk/pg-risk-store.ts 归 risk-state-cross-process-integrity 独占，待其稳定后另起一批 -->
- [ ] 5.8 批 6 — 身份与账号（`src/account-store.ts`、`src/client-auth/client-user-store.ts`）。同批用迁移补回 `client_environments.account_id → accounts(account_id)` 外键（`src/client-auth/client-user-store.ts:123-127` 记录的那处因启动顺序被迫放弃的完整性），并在补外键前先跑一次悬空绑定清理迁移。
<!-- aidcp-cloud 9c9e72b 两个存储的自建表已切换为探测 -->
<!-- BLOCKED: 外键与悬空绑定清理迁移**没有做**，且不建议按原样做。① 放弃外键的公开理由（启动顺序）确实随本 change 消失了；② 但还有一个没写进 design.md 的理由：src/server.ts:3869-3873 把 ensureAccount() 的失败显式吞掉并继续握手（注释直写「不阻塞握手」），而 src/client-auth/client-user-store.ts:1733 的 upsertEnvironment 会在同一次握手里写 account_id——加上外键会把「今天被容忍、且由读侧 binding_unknown 自愈」的软状态变成一次硬失败（环境登记直接报错）。③ 配套的清理迁移把 account_id 置空会擦掉绑定审计，与 client_environments 既有不变量「删除只改变环境生命周期，绝不擦账号绑定审计」冲突。建议独立 change 按六步模板做：先让 ensureAccount 在握手路径上从「失败即吞」改成「失败即拒绝环境登记并留具名错误」→ 观察一个周期 → 加 NOT VALID 外键 → 独立 contract change 做 VALIDATE。详见 docpatch ⑤ 5.5 -->
- [ ] 5.9 每批合并前跑一次「全新空库拉起」验证：空库 → `migrate up` → 启动 cloud → 断言该批存储不再需要自建即可就绪。此验证 MUST 在 dev 之外的一次性临时库上做，MUST NOT 对 dev/ol 共库执行。
<!-- aidcp-cloud 9c9e72b 已交付该验证的**静态前提**：test/schema/ddl-parity.test.ts 逐条比对 src 会建出的对象与迁移目录建出的对象，并因此发现并补上了 0070 的 16 列 3 索引。这只证明「静态上不缺对象」，不能替代真库拉起 -->
<!-- aidcp-cloud a6c00c1 静态前提补齐第二半：ddl-parity 只管「对象集合不缺」，migration-order 管「按复合序跑得完」。两条都绿仍不等于真库跑过一遍。本 session 另做过一次一次性证据（PGlite 0.5.4 真空库、复刻 commandUp 的「任一条失败即停整批」语义）：返工前停在第 5 条 0005，返工后 69/69 全部应用、建出 89 张表；再把全部 src DDL 常量解析成要求集合与该库比对，缺口 0。PGlite 不是 PG，且未起 cloud 进程，故 110.6 仍必须做 -->
<!-- BLOCKED: 需要一次性临时库 + 真跑 migrate up + 真启动 cloud，本 session 无 ECS / 真库权限。已登记 docs/real-machine-acceptance-backlog.md 簇 110.6 -->
- [ ] 5.10 每批部署 dev 并观察后再进下一批；每批在 tasks 里记录 commit sha 与观察结论。
<!-- BLOCKED: 部署由主控串行做，本 session 明确禁止 push / 部署 / 碰 ECS。六批的代码改动在同一个提交 9c9e72b 里交付（无法逐批部署观察），**部署前必须先按 10.3 的新步骤在 dev 上跑 migrate status/up**——存储不再自建表，带着未应用的迁移重启会让对应能力 fail-closed。已登记 backlog 簇 110.3 / 110.5 -->
- [ ] 5.11 全部批次完成后删除 `AIDCP_SCHEMA_SELF_CREATE` 旋钮与 `test/schema/ddl-parity.test.ts`，并删除 `scripts/run-migration.ts`（保留它等于保留一条无账本旁路）。
<!-- BLOCKED: 这是过渡期结束后的收尾动作，按 design.md D4「保留一个发布周期后随本 change 的收尾任务删除」。现在删掉旋钮等于取消第四重保险；scripts/run-migration.ts 也要等执行器在真库上跑通（110.1/110.2）之后才能删。已登记 backlog 簇 110.9 -->

## 6. aidcp-cloud — 启动期 schema 契约门

- [x] 6.1 新增 `src/schema/schema-contract.ts`：导出 `REQUIRED_SCHEMA_VERSION` 与 `KNOWN_MAX_SCHEMA_VERSION` 两个常量，后者由构建期从 `migrations/` 最大版本生成或由测试断言与目录一致。
<!-- aidcp-cloud aef34a0 常量写死 + test/schema/schema-contract.test.ts 断言与目录一致（构建产物里不一定带 migrations/，故不在运行时读目录） -->
<!-- aidcp-cloud 9c9e72b 第 5 节完成后 REQUIRED 从 0064_schema_migrations_ledger 抬到 0070_baseline_self_heal_columns（存储不再自建表，硬依赖从「账本存在」变成「补齐迁移全部到位」）；KNOWN_MAX 同步抬到 0070 -->
- [x] 6.2 新增启动闸函数：读账本 `MAX(version)`（按 D1 的复合序比较，不是字符串比较），三分支——低于 `REQUIRED` 报 `schema_behind_code` 并列出缺失 version；高于 `KNOWN_MAX` 报 `schema_ahead_of_code` 并列出超前 version；其余正常。
<!-- aidcp-cloud aef34a0 src/schema/schema-gate.ts + schema-contract.ts 的 evaluateSchemaGate；另有第四态 schema_ledger_unreadable（账本读不出来同样 fail-closed） -->
- [x] 6.3 在 `src/server.ts` 把该闸接在所有存储 `init()` 之前（当前最早的一处是 `:640`），MUST NOT 包进 `try/catch`；读账本本身失败（表不存在或连不上）同样拒绝启动并报明确原因。
<!-- aidcp-cloud aef34a0 接在 src/server.ts:501 附近（deploymentTarget 解析之后、配置镜像池构造之前），裸 await 无 try/catch -->
- [x] 6.4 放行通道 `AIDCP_ALLOW_SCHEMA_AHEAD`：值必须是具体版本 id，布尔值或空字符串一律视为未放行；生效时在启动日志与告警通道各记一条，含被放行区间与 `applied_by`。MUST NOT 提供「永久放行」形态。
<!-- aidcp-cloud aef34a0 parseAllowSchemaAhead 拒绝 true/false/1/0/yes/no/on/off/*/all/any 与不符 <数字>_<slug> 形状的值；告警走 takePendingSchemaGateAlert()，由 server.ts 在 alertStore 就绪后 flush（门跑在 alertStore 构造之前） -->
- [ ] 6.5 契约门先以只告警模式上线（env `AIDCP_SCHEMA_GATE=warn|enforce`，默认 `warn`），告警模式下 MUST 输出与 `enforce` 完全一致的判定结论与 version 清单，MUST NOT 只打模糊提示。跑满一个发布周期且覆盖一次 ol 部署后切 `enforce` 并把默认值改为 `enforce`。
<!-- aidcp-cloud aef34a0 实装部分已完成：默认 warn；判定层不接受 mode 参数，结论文本与版本清单在两种模式下逐字一致（由 AC-SCHEMA-NO-SILENT-RECREATE-02 断言） -->
<!-- BLOCKED: 「跑满一个发布周期且覆盖一次 ol 部署后切 enforce」是 rollout 动作，需真机 + ol 部署。实际跑满的日历天数按 design.md「Open Questions」要求 MUST 记进本 tasks（切换时补写）。已登记 backlog 簇 110.8 -->
- [x] 6.6 脱库单测：低于/等于/高于三分支、复合序比较（`0002_risk_control` > `0002_bot_chats`）、放行通道只接受具体版本 id、`warn` 与 `enforce` 判定结论一致。
<!-- aidcp-cloud 9c9e72b test/schema/schema-contract.test.ts（7 例） -->
- [x] 6.7 回滚场景回归用例：构造「账本含 `0058`、构建只认识到 `0057`」，断言启动被拒且错误为 `schema_ahead_of_code`，并断言此路径下没有任何 `CREATE TABLE` 被执行。这一条是本 change 的核心红线用例，命名 `AC-SCHEMA-NO-SILENT-RECREATE`，进 `npm run test:acceptance`。
<!-- aidcp-cloud 9c9e72b test/acceptance/schema-no-silent-recreate.test.ts（4 例）。「没有任何 CREATE TABLE 被执行」用与 AC-SCHEMA-DDL-OWNER 同一个扫描器判定（口径只有一份），并额外断言该路径只发了一条读账本语句 -->

## 7. aidcp-cloud — 只扩张不收缩纪律

- [x] 7.1 在 `migrations/README.md` 写死 expand / contract 的判定边界：expand = 新增表/列/索引/`NOT VALID` 约束/回填/触发器（旧代码之后仍能读写）；contract = `DROP` / `RENAME` / 类型收窄 / 加 `NOT NULL` / 删索引 / 约束 `VALIDATE` 收紧（旧代码之后会坏）。
<!-- aidcp-cloud aef34a0 migrations/README.md §5 -->
- [x] 7.2 写死：重命名 MUST NOT 用 `ALTER … RENAME`，MUST 改写为新增列 + 双写 + 影子读 + 切读 + 独立 contract 删旧列。
<!-- aidcp-cloud aef34a0 README §5 + 9c9e72b 指向 docs/table-ownership-migration.md 六步模板 -->
- [x] 7.3 写死：contract 迁移 MUST 是独立 change、独立部署、可单独回滚，MUST NOT 与 expand 同批交付；共库期需 `--allow-contract` 显式授权并入账本。
<!-- aidcp-cloud aef34a0 README §5 -->
- [x] 7.4 新增 `test/schema/expand-only.test.ts`：扫描所有 `kind=expand` 的迁移文件，断言不含 `DROP TABLE` / `DROP COLUMN` / `RENAME TO` / `ALTER COLUMN … TYPE` / `SET NOT NULL` / `DROP INDEX`；命中即失败并提示改标 contract。
<!-- aidcp-cloud 9c9e72b 两条断言：expand 里没有收缩语句 + contract 里确实有收缩语句（防止误标 contract、白白吃掉一次显式授权）。判定先剥注释——迁移注释里大量出现「本文件不做 DROP TABLE」这类说明文字，不剥会制造假阳性、最后逼着给用例加豁免 -->
- [x] 7.5 在 `aidcp/docs/deployment-environments.md` 的破坏性 DDL 冻结段落（第 66-69 行）加一句指针，说明本纪律是该冻结在迁移期的延伸，并指向 `migrations/README.md`。
<!-- 2026-07-23 主控套用 docpatch ② 2.1：docs/deployment-environments.md 破坏性 DDL 冻结段（item 1）末尾追加指向 migrations/README.md §5 与 table-ownership-migration.md 六步模板的指针。 -->

## 8. aidcp-cloud — 表所有权迁移模板

- [x] 8.1 新增 `docs/table-ownership-migration.md`，落 design.md D7 的六步表（准备 / 双写 / 影子读对账 / 切读 / 停旧写 / 收缩），每步写清动作、验收信号、回退动作。
<!-- aidcp-cloud 9c9e72b -->
- [x] 8.2 步 1 双写的硬要求写进文档：新表写失败 MUST 计错误数并告警、MUST NOT 静默吞、MUST NOT 阻断旧权威写。
<!-- aidcp-cloud 9c9e72b §2「步 1 双写：失败必须留下痕迹」 -->
- [x] 8.3 步 2 影子读对账的硬要求：对账器 MUST 同时上报差异条数与**已比对行数**；覆盖率为 0 时结论是「未验证」，MUST NOT 报「通过」。
<!-- aidcp-cloud 9c9e72b §2「步 2 影子读对账：覆盖率为 0 时结论是『未验证』」 -->
- [x] 8.4 步 5 收缩的诚实标注：该步不可逆，回退只能从备份恢复；文档 MUST 直写这一点，MUST NOT 写「可回滚」。
<!-- aidcp-cloud 9c9e72b 六步表末列直写「不可逆。回退只能从步 5 之前的备份恢复。」+ §2 单列一条 -->
- [x] 8.5 文档写明观察期最低口径：步 1 与步 2 各 ≥ 3 个自然日且覆盖 dev 与 ol 各一个完整业务日；每次实际表迁移的 change 引用本文件并登记实际观察期与信号值。
<!-- aidcp-cloud 9c9e72b §3「观察期口径」，另写明因修复而重置的必须重新计天 -->
- [x] 8.6 文档写明跨服务场景：步 1 的双写若落在两个进程，MUST 走持久命令 / Outbox，MUST NOT 依赖 advisory lock 或共享事务。
<!-- aidcp-cloud 9c9e72b §4「跨服务场景」，并给出仓内两个现成先例（publish-approval-outlet / risk-counter-outbox-store） -->

## 9. aidcp — 库级作用域盘点（控制仓）

- [x] 9.1 新增 `docs/database-scope-inventory.md`，表头固定为：机制 / 位置 file:line / 当前作用域 / 拆 schema 后是否成立 / 拆库后是否成立 / 拆库替代方案。开篇必须先纠正误读：advisory lock 与外键都是**数据库级**，搬 schema 不失效，拆库才失效，且失效是静默的。
<!-- 2026-07-23 主控套用 docpatch ①：新建 docs/database-scope-inventory.md（§0 误读纠正 + §1 advisory lock 6 处 + §2 外键 + §3 跨表单事务 + §4 硬编码 schema 名 7 处）。 -->
- [x] 9.2 登记 advisory lock 7 处：`aidcp-cloud/src/interactions/interaction-store.ts:339`、`:409`、`:989`，`aidcp-cloud/src/client-auth/client-user-store.ts:619`、`:1468`、`:2001`、`:2128`。标注 `interaction-env:<envKey>` 命名空间被 client-auth 与 interactions 两域共用（`interaction-store.ts:337-339` 注释确认）。替代方案：改为对权威表行 `SELECT … FOR UPDATE`，或持久命令 + Inbox 去重。
<!-- 2026-07-23 主控套用：docs/database-scope-inventory.md §1（advisory lock 6 处，含历史修正 7→6：client-user-store 的 3 处 interaction-env 锁已被 publish-approval 换成行锁）。 -->
<!-- 实测修正：现在是 **6 处**且构成不同。client-user-store 的 3 处 interaction-env: 锁已被 change publish-approval-signal-to-database 换成 client_environments 行锁（src/db/environment-row-lock.ts），并由 AC-LOCK-01 断言其消失。当前 6 处 = interaction-store.ts:430/:1011 + risk/writer-lock.ts:143/:205（风控单写者会话锁）+ scripts/migrate.ts:148/:209（迁移执行器整批锁）。docpatch 里记的是当前事实并显式写了这条修正 -->
- [x] 9.3 登记跨域外键：指向 `accounts(account_id)` 26 处（迁移 19 处，其中 `migrations/0039_interaction_inbox.sql` 14 处；源码 7 处含 `src/config/persona-store.ts:41`、`src/config/approval-policy-store.ts:22`、`src/delegated-task/store.ts:30`、`src/onboarding/first-post-onboarding-store.ts:27`、`src/comment-agent/facebook-group-store.ts:405`、`src/publish-agent/facebook-publish-media-store.ts:102`）；指向 `client_users(user_id)` 3 处；指向 `publish_log(id)` 2 处（`src/publish-agent/facebook-publish-media-store.ts:109`、`:131`）。替代方案：应用层校验 + 读侧 fail-closed，先例见 `src/client-auth/client-user-store.ts:123-127`。
<!-- 2026-07-23 主控套用：docs/database-scope-inventory.md §2（源码外键 21 处 + 迁移外键 + 指向 accounts 合计 27 处，扫描先剥注释）。 -->
<!-- 实测修正：指向 accounts(account_id) 合计 **27 处**（迁移 21 + 源码 6）。差额两处来源：① 第 3 节补齐的迁移把两条既有外键写进了迁移目录；② tasks 记的源码 7 处里有一处（client-user-store.ts:126）其实是注释里的反例说明「**故意不写** REFERENCES accounts」——不剥注释的扫描会把它当成真实外键。扫描器因此先剥注释。publish_log(id) 实测 3 处（多一处 src/publish-agent/draft-refinement.ts:50） -->
- [x] 9.4 登记跨 11 表单事务清理 `aidcp-cloud/src/interactions/interaction-store.ts:1634-1686`：拆 schema 仍原子、拆库不原子；替代方案为可重入分表 saga。
<!-- 2026-07-23 主控套用：docs/database-scope-inventory.md §3（purgeDueOffboards 跨 11 表单事务清理）。 -->
- [x] 9.5 登记硬编码 `'public.'` 8 处：`aidcp-cloud/src/interactions/interaction-store.ts:300-302`、`src/interactions/reply-config-store.ts:72-73`、`src/interactions/reply-config-scope-store.ts:130-131`、`src/cache/curated-content-store.ts:357`。标注改 `search_path` 救不了这些。
<!-- 2026-07-23 主控套用：docs/database-scope-inventory.md §4（硬编码 schema 名 7 处 + 收口进度：第 8 处已收口 qualifiedObjectName，剩 7 处在 src/interactions/** 未动）。 -->
<!-- 实测修正：现在是 **7 处**——第 8 处（curated-content-store）已在任务 5.5 收口到 qualifiedObjectName()。剩余 7 处全在 src/interactions/**，未在本 change 内改动（定稿 §5.4.2 要求 8 处全收口，缺口见 docpatch ⑤ 5.2） -->
- [x] 9.6 在 `docs/cloud-service-decomposition-proposal.md` §5.1 与 §12 阶段 2 各加一条指针：本 change 是「为 Schema、数据库账号和迁移建立唯一所有者」的前置，不依赖拆分、可立即执行；并回指 `docs/database-scope-inventory.md`。
<!-- 2026-07-23 主控套用 docpatch ③：docs/cloud-service-decomposition-proposal.md §5.1 表后加「前置说明（cloud-schema-migration-executor）」段；第二段指针按 docpatch 锚点落在 §5.4.7「子目标 A：迁移目录与所有权归属」之前（docpatch 标注为「§12 阶段 2」实为该锚点所在的 §5.4.7），均回指 database-scope-inventory.md。 -->

## 10. aidcp-cloud — 清单机械化与部署接线

- [x] 10.1 新增 `test/schema/database-scope-inventory.test.ts`：扫描 `src/**/*.ts`，断言 `pg_advisory` 调用点集合与 `REFERENCES` 跨域目标集合与控制仓清单的机器可读副本（`test/schema/database-scope-inventory.json`）一致；新增未登记即失败并提示先更新 `aidcp/docs/database-scope-inventory.md`。
<!-- aidcp-cloud 9c9e72b 扫描器 src/schema/db-scope-scan.ts（先剥注释——仓内大量注释在解释「这里**故意不写** REFERENCES accounts」，不剥会把一条明确的反例说明登记成真实外键）；机器副本 test/schema/database-scope-inventory.json；重跑命令 npx tsx scripts/generate-db-scope-inventory.ts --write -->
<!-- aidcp-cloud 9c9e72b 扩了两类：除 advisory lock 与 REFERENCES 外，还锁死硬编码 schema 名的形状探测点；扫描范围含 scripts/（迁移执行器的整批锁同样是库级机制，漏掉它就是漏掉一条） -->
- [x] 10.2 该测试进 `npm run test:acceptance`，命名 `AC-SCHEMA-DB-SCOPE`。
<!-- aidcp-cloud 9c9e72b test/acceptance/schema-db-scope.test.ts（4 例）。同 4.3 的偏离：用例文件放 test/acceptance/，JSON 仍在 test/schema/ -->
- [x] 10.3 在 `aidcp/docs/deployment-environments.md` 的 dev 与 ol 部署流程各插入迁移步骤：restart 之前跑 `npm run migrate status`（只读）确认无 pending 与无异常；有 pending 时人工审阅并跑 `migrate up`；`migrate` 失败即中止部署，MUST NOT 带着未应用迁移重启服务。
<!-- 2026-07-23 主控套用 docpatch ② 2.2：docs/deployment-environments.md dev 与 ol 部署流程各插入「Apply and verify database migrations before restarting」步（restart 之前跑 migrate status，pending 则人工 migrate up，失败即中止），后续步号顺延。 -->
- [x] 10.4 在同一文档写明：契约门为 `enforce` 后，账本落后于代码会直接表现为服务启动失败，这是预期行为，处置是补跑迁移而不是回滚代码或关闭契约门。
<!-- 2026-07-23 主控套用 docpatch ② 2.3：docs/deployment-environments.md 新增 ### Schema Contract Gate 段（enforce 后账本落后=启动失败、处置=补跑迁移、超前需具体版本 id 放行）。 -->
- [x] 10.5 部署验收信号补一条：restart 后除现有健康检查外，还须确认启动日志出现 schema 契约门的通过行（含账本最高版本 id），MUST NOT 只看进程 `active (running)`。
<!-- 2026-07-23 主控套用 docpatch ② 2.3：同 Schema Contract Gate 段写明部署验收信号新增「启动日志确认契约门通过行（含账本最高版本 id）」，仅 active (running) 不算通过。 -->

## 11. 验证与交付

- [x] 11.1 跑 `cd ../aidcp-cloud && npm run test:acceptance`，确认 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 全过，新增 `AC-SCHEMA-DDL-OWNER` / `AC-SCHEMA-NO-SILENT-RECREATE` / `AC-SCHEMA-DB-SCOPE` 全过。
<!-- aidcp-cloud ecf5290 npm run test:acceptance → tests 81 / pass 81 / fail 0（master 基线 70，新增 11 = DDL-OWNER 3 + NO-SILENT-RECREATE 4 + DB-SCOPE 4）。AC-PROTO-* / AC-PUB-* / AC-RISK-* / AC-LOCK-* 全过 -->
<!-- aidcp-cloud a6c00c1 审计返工后复跑：npm run test:acceptance → tests 81 / pass 81 / fail 0（不变）。中途 AC-SCHEMA-DDL-OWNER-02 曾红一次——新写的两段注释里出现了连着的 DDL 关键字字面量，被「文本命中数只减不增」抓住（273 > 271）。这是闸门按设计工作：注释里搬 DDL 同样算。改写注释而非抬基线 -->
- [x] 11.2 跑 `npm test` 全量与 `npm run typecheck`，记录命令与结果。
<!-- aidcp-cloud ecf5290 npm test → tests 3055 / pass 3047 / fail 0 / skipped 8（master 基线 3026 / 3017 / 1 fail）。注：接手时 master 基线**并非全绿**——test/schema/migration-numbering.test.ts 因 rebase 后 0061/0062/0063 缺 kind/objects 头而失败，已在 9c9e72b 修复。npm run typecheck → 0 error -->
<!-- aidcp-cloud a6c00c1 审计返工后复跑：npm test → tests 3068 / pass 3060 / fail 0 / skipped 8（新增 13 = schema-capability 6 + migration-order 4 + ddl-objects 3）。npm run typecheck → 0 error -->
- [x] 11.3 在 dev 跑 `migrate status` / `verify`，把缺失清单与多余清单原文记进本 tasks（不含任何凭据值）。
<!-- 2026-07-23 主控在 dev 实测，构建含 ecf5290 + a6c00c1（部署 sha 89c286d）。
     `migrate status`：账本表尚不存在，全部 70 个版本报 pending（预期——账本本批才引入）。
     `migrate verify`：实测对账（schema=public）声明 1111 个对象、覆盖 89 张表。
     **缺失对象 10 个，全部属 `0064_schema_migrations_ledger` 一条迁移**：table:schema_migrations 与它的
     9 个列（version / name / checksum / kind / applied_at / applied_by / applied_from_target / duration_ms / baseline）。
     除账本自身外**零缺失**——这就是「取消 34 个存储自建表在 dev 上安全」的直接证据。
     **多余对象 5 个（库里有、任何迁移都没声明）**：table:group_comment_attempts、table:hot_lead_queue、
     column:account_content_schedule.group_comment_daily_cap、column:account_content_schedule.group_comment_enabled、
     column:accounts.group_chat_info。这 5 个是历史自建表从未补迁移留下的真实缺口，
     MUST 在空库拉起验证前补齐迁移（否则新库起不来），已随 11.7 登记 backlog。 -->
- [ ] 11.4 在 dev 完成一次 `baseline` 并记录账本行数与最高版本 id。
<!-- BLOCKED: 同 11.3。已登记 backlog 簇 110.2 -->
- [ ] 11.5 每批存储切换按 §5.10 逐批部署 dev 并记录 commit sha 与观察结论；OL 部署只在用户明确要求时从发布分支执行。
<!-- 部分完成 / 2026-07-23 deployed：主控已把六批一次性部署 dev（sha 89c286d，含本 change 全部 4 个提交）。
     **「逐批观察」这一半未兑现**——六批代码在同一提交 9c9e72b，物理上无法分批上线，不改状态为 [x]。
     一次性上线的实测结论：34 个存储改探测后全部 init 成功、零 SchemaCapabilityError、零 error 日志、
     进程零重启；schema 契约门按 warn 模式如实报出「账本表 schema_migrations 不存在，所需最低版本
     0070_baseline_self_heal_columns」并放行启动（正是设计的诚实降级形态）。
     OL 未部署（需用户明确要求 + 发布分支）。逐批观察项留 backlog 簇 110.3 / 110.5 -->
- [x] 11.6 跑 `openspec validate cloud-schema-migration-executor --strict` 并记录输出。
<!-- 输出：Change 'cloud-schema-migration-executor' is valid -->
- [x] 11.7 真机验收项（共库 baseline、契约门 `warn→enforce` 切换、每批空库拉起验证）登记进 `docs/real-machine-acceptance-backlog.md`，按共享真机环境聚簇。
<!-- 2026-07-23 主控套用 docpatch ④：docs/real-machine-acceptance-backlog.md 新增簇 111（10 项，111.1–111.10）。原稿写簇 110，因 risk-state 按套用顺序先占 110，本 change 顺延为 111，内部 110.x 引用同步改 111.x；簇头「未部署」按 tasks 11.3/11.5 已部署 dev sha 89c286d 更正。 -->
