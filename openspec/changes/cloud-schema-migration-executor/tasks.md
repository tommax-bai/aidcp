## 1. aidcp-cloud — 迁移执行器与账本

- [ ] 1.1 新增 `migrations/0057_schema_migrations_ledger.sql`（`kind=expand`）：建 `schema_migrations` 表，列为 `version TEXT PRIMARY KEY`、`name TEXT NOT NULL`、`checksum TEXT NOT NULL`、`kind TEXT NOT NULL CHECK (kind IN ('expand','contract'))`、`applied_at TIMESTAMPTZ NOT NULL DEFAULT now()`、`applied_by TEXT`、`applied_from_target TEXT`、`duration_ms INTEGER`、`baseline BOOLEAN NOT NULL DEFAULT false`。`applied_from_target` 无索引、无唯一约束、不参与任何查询谓词——它只是审计列。
- [ ] 1.2 新增 `src/schema/migration-plan.ts`：纯函数层，输入「文件名 + 内容」列表与账本行列表，输出 `{ pending, skipped, errors }`。排序键为 `(数字前缀数值升序, 完整文件名字典序升序)`。可判定的错误只有三类：`migration_checksum_mismatch`、`migration_out_of_order`、`migration_kind_missing`。此文件不 import `pg`，可脱库单测。
- [ ] 1.3 新增 `scripts/migrate.ts` CLI，四个子命令：`status`（列出已应用/待应用/异常，只读）、`up`（应用待应用项）、`verify`（实测对象比对）、`baseline`（写基线）。`package.json` 加 `"migrate": "tsx --env-file=.env scripts/migrate.ts"`。
- [ ] 1.4 `up` 实现：整批用固定 key `pg_advisory_lock` 互斥，拿不到锁立即退出并打印持锁提示，不等待、不强行继续；每条迁移单独 `BEGIN … COMMIT`，事务内先执行 SQL 再写账本；任一条失败即停止整批并以非 0 退出码报出失败的 version 与原始错误，已成功的几条保留在账本里。
- [ ] 1.5 `up` 拒绝语义：`migration_plan` 返回任一错误时整批拒绝、不执行任何 SQL；校验和不符时 MUST NOT 重跑、MUST NOT 更新账本 checksum；乱序时 MUST NOT 补跑低版本文件。
- [ ] 1.6 `up` 的 `kind` 闸：文件缺 `-- aidcp:kind=` 头声明即拒绝；`kind=contract` 默认拒绝并提示需 `--allow-contract`；带 `--allow-contract` 应用时把授权者写入账本 `applied_by`。
- [ ] 1.7 `applied_from_target` 取自 `AIDCP_DEPLOY_ENV`；未设置时写 `unknown` 并在输出里注明，MUST NOT 因为缺 target 就拒绝执行（schema 是库的属性，不是任务）。
- [ ] 1.8 为每个迁移文件补结构化对象声明头注释 `-- aidcp:objects=table:<t>,column:<t>.<c>,index:<i>,constraint:<c>`；`verify` 解析该声明并与 `information_schema.tables` / `information_schema.columns` / `pg_indexes` / `pg_constraint` 实测比对，输出「缺失对象」与「多余对象」两张清单。MUST NOT 由 SQL 文本推断对象。
- [ ] 1.9 `baseline` 实现：先内部跑一次 `verify`；缺失清单非空时拒绝写入并逐条打印缺什么、来自哪个 version；清单为空才把全部迁移以 `baseline=true` 写入账本。`baseline` 对已有账本行 MUST 幂等跳过、MUST NOT 覆盖。
- [ ] 1.10 脱库单测（照 `test/interactions/migration-contract.test.ts` 的纯文本范式）：排序复合序、幂等跳过、校验和不符拒绝、乱序拒绝、缺 kind 拒绝、contract 默认拒绝、`baseline` 在缺失清单非空时拒绝。

## 2. aidcp-cloud — 编号治理

- [ ] 2.1 新增 `migrations/README.md`：写明版本 id = 文件名去后缀、排序为 `(数字前缀, 文件名)` 复合序、四组历史碰撞（`0002` / `0030` / `0037` / `0038`）的既定相对顺序、`0012` 为永不分配的历史空洞、以及「新增迁移不得复用已有数字前缀」。
- [ ] 2.2 逐组核对四组碰撞文件互不依赖并把结论写进 `migrations/README.md`：`0002_bot_chats` vs `0002_risk_control`、`0030_content_schedule_group_comments` vs `0030_panel_hardening_indexes`、`0037_facebook_comment_mode_templates` vs `0037_session_join_group_budget`、`0038_delegated_tasks` vs `0038_first_post_onboarding`（后两者均只引用 `accounts`，互不引用）。若发现真实依赖，冻结的顺序必须与依赖一致。
- [ ] 2.3 新增 `test/schema/migration-numbering.test.ts`：断言（a）不存在 `0012_*.sql`；（b）除已登记的四组外不存在新的同号；（c）四组碰撞的文件名集合与相对顺序与 README 一致；（d）每个 `.sql` 都有 `-- aidcp:kind=` 与 `-- aidcp:objects=` 头。零数据库依赖。
- [ ] 2.4 MUST NOT 重命名任何历史迁移文件（重命名即改版本 id，会让账本主键与文件对不上）。本节只做冻结与断言。

## 3. aidcp-cloud — 补齐缺失迁移，使迁移目录成为完整事实源

- [ ] 3.1 新增 `migrations/0058_baseline_self_created_tables.sql`（`kind=expand`）：把 24 张只由存储自建、迁移目录从未创建的表的 DDL 原样抽出，保留 `CREATE TABLE IF NOT EXISTS`。清单：`accounts`、`client_users`、`client_environments`、`client_env_scope`、`client_environment_installations`、`client_environment_deletion_requests`、`client_env_revocation_holds`、`anchors`、`anchor_staging`、`concepts`、`curated_content`、`liked_notes`、`valuable_comments`、`group_route`、`hot_lead_config_global`、`facebook_group_target`、`facebook_group_target_scope`、`facebook_group_membership`、`facebook_group_join_audit`、`facebook_group_join_automation_config`、`account_facebook_publish_image`、`account_facebook_publish_image_set`、`persona_auto_fill_runs`、`persona_auto_fill_targets`。文件可按域拆成多个，但每个都必须带 kind 与 objects 头。
- [ ] 3.2 抽取时必须包含存储侧的自愈 `ALTER TABLE … ADD COLUMN IF NOT EXISTS` 与 `CREATE INDEX IF NOT EXISTS`（例：`src/client-auth/client-user-store.ts:120-160` 的一串加列与两条索引），否则新库建出的表会缺列。
- [ ] 3.3 新增 `test/schema/ddl-parity.test.ts`：对这 24 张表，比对存储源码 DDL 与新迁移文件的列名集合、索引名集合，不一致即失败。此测试在第 5 节切换完成、存储侧 DDL 删除后随之删除。
- [ ] 3.4 本节 MUST NOT 修改任何存储代码，MUST NOT 改变启动行为。交付后在 dev 跑 `migrate verify`，缺失清单应为空。

## 4. aidcp-cloud — DDL 单一所有者的机械闸

- [ ] 4.1 新增 `test/schema/runtime-ddl-allowlist.test.ts`：扫描 `src/**/*.ts`，收集所有含 `CREATE TABLE` / `ALTER TABLE` / `CREATE INDEX` 的位置，断言集合是 `test/schema/runtime-ddl-allowlist.json` 的子集。基线快照为当前 34 个文件、76 条语句。
- [ ] 4.2 允许清单 MUST 只减不增：新增运行时 DDL 即测试失败并提示「DDL 只能加在 migrations/」。每完成一批切换，从清单里删掉对应条目。
- [ ] 4.3 该测试进 `npm run test:acceptance`，与 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 同级作为红线用例，命名 `AC-SCHEMA-DDL-OWNER`。

## 5. aidcp-cloud — 分批取消存储自建表

- [ ] 5.1 新增 `src/schema/schema-capability.ts`（通用版，范式照抄 `src/interactions/schema-capability.ts:9-25`）：给定探测结果返回 `ready` / `degraded` / `missing`；`missing` 时抛带 version id 的明确错误，MUST NOT 建表。
- [ ] 5.2 加全局回滚旋钮 `AIDCP_SCHEMA_SELF_CREATE`，默认 `false`；为 `true` 时恢复自建并在启动日志打显式过渡态警告。
- [ ] 5.3 批 1 — 配置类 13 个存储（`src/config/model-config-store.ts`、`credential-store.ts`、`role-config-store.ts`、`category-config-store.ts`、`quota-config-store.ts`、`pacing-config-store.ts`、`session-config-store.ts`、`hot-lead-config-store.ts`、`resume-config-store.ts`、`content-schedule-store.ts`、`persona-store.ts`、`approval-policy-store.ts`、`facebook-comment-config-store.ts`）：删除建表与自愈加列，改探测；`src/server.ts:639-660` 的统一 `catch` 拆成「连不上库」与「schema 缺对象」两类分别报出。
- [ ] 5.4 批 2 — 指标与告警（`src/metrics/token-usage-store.ts`、`src/alerts/alert-store.ts`）。
- [ ] 5.5 批 3 — 缓存与语料（`src/cache/pg-anchor-cache.ts`、`concept-store.ts`、`curated-content-store.ts`、`liked-note-store.ts`、`valuable-comment-store.ts`、`group-route-store.ts`、`interaction-feed-store.ts`、`notification-contact-store.ts`）。同批把 `src/cache/curated-content-store.ts:357` 的硬编码 `'public.'` 收口到统一常量。
- [ ] 5.6 批 4 — Facebook 群组与发布媒体（`src/comment-agent/facebook-group-store.ts`、`facebook-comment-audit-store.ts`、`src/publish-agent/publish-log-store.ts`、`facebook-publish-media-store.ts`、`src/config/facebook-group-join-automation-store.ts`、`src/config/persona-auto-fill-store.ts`）。
- [ ] 5.7 批 5 — 委托任务、风控与引导（`src/delegated-task/store.ts`、`src/risk/pg-risk-store.ts`、`src/onboarding/first-post-onboarding-store.ts`）。
- [ ] 5.8 批 6 — 身份与账号（`src/account-store.ts`、`src/client-auth/client-user-store.ts`）。同批用迁移补回 `client_environments.account_id → accounts(account_id)` 外键（`src/client-auth/client-user-store.ts:123-127` 记录的那处因启动顺序被迫放弃的完整性），并在补外键前先跑一次悬空绑定清理迁移。
- [ ] 5.9 每批合并前跑一次「全新空库拉起」验证：空库 → `migrate up` → 启动 cloud → 断言该批存储不再需要自建即可就绪。此验证 MUST 在 dev 之外的一次性临时库上做，MUST NOT 对 dev/ol 共库执行。
- [ ] 5.10 每批部署 dev 并观察后再进下一批；每批在 tasks 里记录 commit sha 与观察结论。
- [ ] 5.11 全部批次完成后删除 `AIDCP_SCHEMA_SELF_CREATE` 旋钮与 `test/schema/ddl-parity.test.ts`，并删除 `scripts/run-migration.ts`（保留它等于保留一条无账本旁路）。

## 6. aidcp-cloud — 启动期 schema 契约门

- [ ] 6.1 新增 `src/schema/schema-contract.ts`：导出 `REQUIRED_SCHEMA_VERSION` 与 `KNOWN_MAX_SCHEMA_VERSION` 两个常量，后者由构建期从 `migrations/` 最大版本生成或由测试断言与目录一致。
- [ ] 6.2 新增启动闸函数：读账本 `MAX(version)`（按 D1 的复合序比较，不是字符串比较），三分支——低于 `REQUIRED` 报 `schema_behind_code` 并列出缺失 version；高于 `KNOWN_MAX` 报 `schema_ahead_of_code` 并列出超前 version；其余正常。
- [ ] 6.3 在 `src/server.ts` 把该闸接在所有存储 `init()` 之前（当前最早的一处是 `:640`），MUST NOT 包进 `try/catch`；读账本本身失败（表不存在或连不上）同样拒绝启动并报明确原因。
- [ ] 6.4 放行通道 `AIDCP_ALLOW_SCHEMA_AHEAD`：值必须是具体版本 id，布尔值或空字符串一律视为未放行；生效时在启动日志与告警通道各记一条，含被放行区间与 `applied_by`。MUST NOT 提供「永久放行」形态。
- [ ] 6.5 契约门先以只告警模式上线（env `AIDCP_SCHEMA_GATE=warn|enforce`，默认 `warn`），告警模式下 MUST 输出与 `enforce` 完全一致的判定结论与 version 清单，MUST NOT 只打模糊提示。跑满一个发布周期且覆盖一次 ol 部署后切 `enforce` 并把默认值改为 `enforce`。
- [ ] 6.6 脱库单测：低于/等于/高于三分支、复合序比较（`0002_risk_control` > `0002_bot_chats`）、放行通道只接受具体版本 id、`warn` 与 `enforce` 判定结论一致。
- [ ] 6.7 回滚场景回归用例：构造「账本含 `0058`、构建只认识到 `0057`」，断言启动被拒且错误为 `schema_ahead_of_code`，并断言此路径下没有任何 `CREATE TABLE` 被执行。这一条是本 change 的核心红线用例，命名 `AC-SCHEMA-NO-SILENT-RECREATE`，进 `npm run test:acceptance`。

## 7. aidcp-cloud — 只扩张不收缩纪律

- [ ] 7.1 在 `migrations/README.md` 写死 expand / contract 的判定边界：expand = 新增表/列/索引/`NOT VALID` 约束/回填/触发器（旧代码之后仍能读写）；contract = `DROP` / `RENAME` / 类型收窄 / 加 `NOT NULL` / 删索引 / 约束 `VALIDATE` 收紧（旧代码之后会坏）。
- [ ] 7.2 写死：重命名 MUST NOT 用 `ALTER … RENAME`，MUST 改写为新增列 + 双写 + 影子读 + 切读 + 独立 contract 删旧列。
- [ ] 7.3 写死：contract 迁移 MUST 是独立 change、独立部署、可单独回滚，MUST NOT 与 expand 同批交付；共库期需 `--allow-contract` 显式授权并入账本。
- [ ] 7.4 新增 `test/schema/expand-only.test.ts`：扫描所有 `kind=expand` 的迁移文件，断言不含 `DROP TABLE` / `DROP COLUMN` / `RENAME TO` / `ALTER COLUMN … TYPE` / `SET NOT NULL` / `DROP INDEX`；命中即失败并提示改标 contract。
- [ ] 7.5 在 `aidcp/docs/deployment-environments.md` 的破坏性 DDL 冻结段落（第 66-69 行）加一句指针，说明本纪律是该冻结在迁移期的延伸，并指向 `migrations/README.md`。

## 8. aidcp-cloud — 表所有权迁移模板

- [ ] 8.1 新增 `docs/table-ownership-migration.md`，落 design.md D7 的六步表（准备 / 双写 / 影子读对账 / 切读 / 停旧写 / 收缩），每步写清动作、验收信号、回退动作。
- [ ] 8.2 步 1 双写的硬要求写进文档：新表写失败 MUST 计错误数并告警、MUST NOT 静默吞、MUST NOT 阻断旧权威写。
- [ ] 8.3 步 2 影子读对账的硬要求：对账器 MUST 同时上报差异条数与**已比对行数**；覆盖率为 0 时结论是「未验证」，MUST NOT 报「通过」。
- [ ] 8.4 步 5 收缩的诚实标注：该步不可逆，回退只能从备份恢复；文档 MUST 直写这一点，MUST NOT 写「可回滚」。
- [ ] 8.5 文档写明观察期最低口径：步 1 与步 2 各 ≥ 3 个自然日且覆盖 dev 与 ol 各一个完整业务日；每次实际表迁移的 change 引用本文件并登记实际观察期与信号值。
- [ ] 8.6 文档写明跨服务场景：步 1 的双写若落在两个进程，MUST 走持久命令 / Outbox，MUST NOT 依赖 advisory lock 或共享事务。

## 9. aidcp — 库级作用域盘点（控制仓）

- [ ] 9.1 新增 `docs/database-scope-inventory.md`，表头固定为：机制 / 位置 file:line / 当前作用域 / 拆 schema 后是否成立 / 拆库后是否成立 / 拆库替代方案。开篇必须先纠正误读：advisory lock 与外键都是**数据库级**，搬 schema 不失效，拆库才失效，且失效是静默的。
- [ ] 9.2 登记 advisory lock 7 处：`aidcp-cloud/src/interactions/interaction-store.ts:339`、`:409`、`:989`，`aidcp-cloud/src/client-auth/client-user-store.ts:619`、`:1468`、`:2001`、`:2128`。标注 `interaction-env:<envKey>` 命名空间被 client-auth 与 interactions 两域共用（`interaction-store.ts:337-339` 注释确认）。替代方案：改为对权威表行 `SELECT … FOR UPDATE`，或持久命令 + Inbox 去重。
- [ ] 9.3 登记跨域外键：指向 `accounts(account_id)` 26 处（迁移 19 处，其中 `migrations/0039_interaction_inbox.sql` 14 处；源码 7 处含 `src/config/persona-store.ts:41`、`src/config/approval-policy-store.ts:22`、`src/delegated-task/store.ts:30`、`src/onboarding/first-post-onboarding-store.ts:27`、`src/comment-agent/facebook-group-store.ts:405`、`src/publish-agent/facebook-publish-media-store.ts:102`）；指向 `client_users(user_id)` 3 处；指向 `publish_log(id)` 2 处（`src/publish-agent/facebook-publish-media-store.ts:109`、`:131`）。替代方案：应用层校验 + 读侧 fail-closed，先例见 `src/client-auth/client-user-store.ts:123-127`。
- [ ] 9.4 登记跨 11 表单事务清理 `aidcp-cloud/src/interactions/interaction-store.ts:1634-1686`：拆 schema 仍原子、拆库不原子；替代方案为可重入分表 saga。
- [ ] 9.5 登记硬编码 `'public.'` 8 处：`aidcp-cloud/src/interactions/interaction-store.ts:300-302`、`src/interactions/reply-config-store.ts:72-73`、`src/interactions/reply-config-scope-store.ts:130-131`、`src/cache/curated-content-store.ts:357`。标注改 `search_path` 救不了这些。
- [ ] 9.6 在 `docs/cloud-service-decomposition-proposal.md` §5.1 与 §12 阶段 2 各加一条指针：本 change 是「为 Schema、数据库账号和迁移建立唯一所有者」的前置，不依赖拆分、可立即执行；并回指 `docs/database-scope-inventory.md`。

## 10. aidcp-cloud — 清单机械化与部署接线

- [ ] 10.1 新增 `test/schema/database-scope-inventory.test.ts`：扫描 `src/**/*.ts`，断言 `pg_advisory` 调用点集合与 `REFERENCES` 跨域目标集合与控制仓清单的机器可读副本（`test/schema/database-scope-inventory.json`）一致；新增未登记即失败并提示先更新 `aidcp/docs/database-scope-inventory.md`。
- [ ] 10.2 该测试进 `npm run test:acceptance`，命名 `AC-SCHEMA-DB-SCOPE`。
- [ ] 10.3 在 `aidcp/docs/deployment-environments.md` 的 dev 与 ol 部署流程各插入迁移步骤：restart 之前跑 `npm run migrate status`（只读）确认无 pending 与无异常；有 pending 时人工审阅并跑 `migrate up`；`migrate` 失败即中止部署，MUST NOT 带着未应用迁移重启服务。
- [ ] 10.4 在同一文档写明：契约门为 `enforce` 后，账本落后于代码会直接表现为服务启动失败，这是预期行为，处置是补跑迁移而不是回滚代码或关闭契约门。
- [ ] 10.5 部署验收信号补一条：restart 后除现有健康检查外，还须确认启动日志出现 schema 契约门的通过行（含账本最高版本 id），MUST NOT 只看进程 `active (running)`。

## 11. 验证与交付

- [ ] 11.1 跑 `cd ../aidcp-cloud && npm run test:acceptance`，确认 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 全过，新增 `AC-SCHEMA-DDL-OWNER` / `AC-SCHEMA-NO-SILENT-RECREATE` / `AC-SCHEMA-DB-SCOPE` 全过。
- [ ] 11.2 跑 `npm test` 全量与 `npm run typecheck`，记录命令与结果。
- [ ] 11.3 在 dev 跑 `migrate status` / `verify`，把缺失清单与多余清单原文记进本 tasks（不含任何凭据值）。
- [ ] 11.4 在 dev 完成一次 `baseline` 并记录账本行数与最高版本 id。
- [ ] 11.5 每批存储切换按 §5.10 逐批部署 dev 并记录 commit sha 与观察结论；OL 部署只在用户明确要求时从发布分支执行。
- [ ] 11.6 跑 `openspec validate cloud-schema-migration-executor --strict` 并记录输出。
- [ ] 11.7 真机验收项（共库 baseline、契约门 `warn→enforce` 切换、每批空库拉起验证）登记进 `docs/real-machine-acceptance-backlog.md`，按共享真机环境聚簇。
