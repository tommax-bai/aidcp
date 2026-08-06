# tasks

> **先读 design.md 的两条硬约束再动手**：① 已应用迁移的字节不可改（整文件 sha256 校验和，不一致即整批拒绝）；② 归属判定 MUST NOT 由 SQL 文本反推表名。违反任一条会让 dev / ol 的迁移命令当场全停。
>
> 实测基线（2026-08-06，`aidcp-cloud` master）：迁移目录 110 条；残留（无可定位属主的对象声明）**13 条**；派生仓分发 api 70 / automation 58 / content 20。这些数字随后续 change 增长，**实施当天 MUST 重测，MUST NOT 照抄**。

## 1. aidcp-cloud — 派生仓迁移命令修复（独立、先做、可单独验证）

> **⚠️ 本节立项时的范围判断是错的，实施当天被全量扫描推翻。原文保留在下面不删——它记录了「只看点名的那两处」会漏掉什么。**
>
> **真实故障面（2026-08-06 实测）**：不是「两处过期的 kernel 引用」，而是**整套迁移机器 api / content 根本够不着**。`src/schema/` 判归 automation 独占，只有 automation 有本地副本；api / content 靠共享包取用，而那个包只搬了 12 个文件里的 10 个——`migrate verify` 要用的对象探测器不在其中。**三仓 10 个脚本里 9 个的相对 import 指向本仓不存在的路径**（api / content 各 7 个文件断、automation 4 个）。
>
> **还有第二层，import 修完才露出来**：`migrationsDir()` / `tableOwnershipPath()` 的默认值是「模块文件往上两级」，装进共享包后指向包自己的目录。实测报错 `migrations_dir_unreadable dir=.../node_modules/aidcp-transport/migrations`。**这一层比 import 那层更该记**——漏传的后果不是报错而是**读到零条迁移**，契约门会据此说「通过」。

- [x] 1.1 把三个派生仓 `scripts/migrate.ts` 里指向共享内核的两处相对引用改为包引用：`../src/kernel/pg-owner-connection-resolver.js` → `aidcp-kernel/kernel/pg-owner-connection-resolver.js`，`../src/kernel/schema-name.js` → `aidcp-kernel/kernel/schema-name.js`。**MUST NOT 在 `aidcp-cloud` 里改**——事实源仓有 `src/kernel/`，相对引用在那里是对的；改法差异由第 4 节的同步改写器承担。
<!-- aidcp f79e58e3 + aidcp-transport 2c635e8 + aidcp-cloud 343c464 + api e91880d / automation 2bcca28 / content cc8a0ab。
     实际落地范围大于本条：除 kernel 两处外，另有 4 处 `../src/schema/**` 也要改（migration-files /
     migration-owners / migration-plan / schema-inspect），且 schema-inspect **原本不在共享包里**，
     须先把它纳入点名清单（准入逐条复核过：零属主表 SQL，只查 pg_indexes / pg_constraint；
     两个依赖 migration-plan / pg-catalog 本就在清单内）。
     「MUST NOT 在 aidcp-cloud 里改」这条守住了：事实源仓的相对引用一字未动，
     包说明符由控制仓同步脚本的 rewrite_shared_imports 产出。 -->
- [x] 1.2 全仓扫一遍**同类漏网**：三个派生仓的 `scripts/**` 里所有指向 `../src/kernel/` 的相对引用逐条列出并修掉。只修 1.1 点名的两处等于假设「就这两处」，而这个文件从没被任何工具看过。
<!-- 本条是本节唯一写对了的一项，而且它捞出的东西直接改写了 1.1 的范围。实测（逐文件解析相对说明符、
     检查目标是否真实存在）：**api 7 文件断 / content 7 文件断 / automation 4 文件断，cloud 全部可解析**。
     断的目标分两族：`../src/kernel/**`（已搬进包）与 `../src/schema/**`（判归 automation 独占）。
     处置分两类：`migrate.ts`（唯一被 package.json 引用的）纳入同步点名清单并改写；
     其余 7 个 .ts **删除**——它们零 package.json 引用、当前全断，且留着有害：
     `generate-migration-headers.ts` 会 `writeFile(migrationsDir()/…)` **写回迁移文件**，
     而派生仓 migrations/ 只有本属主子集（实测 api 70 / automation 58 / content 20，事实源 110），
     在那儿跑一次就会按不完整集合重算并改写已应用的迁移 → 校验和不符 → 该库迁移命令全停。
     `db-split/**` 与字体子集脚本判为「有意不纳管」，进 SCRIPT_UNMANAGED，与「多出」分开报、永不 prune。 -->
- [x] 1.3 逐仓自证 CLI 能起：在三个派生仓各跑一次迁移状态查询，确认**不是**因模块解析失败而退出。此步 MUST NOT 连 dev / ol 的库（无库连接时的预期失败形态是「连不上库」，不是「找不到模块」——两者 MUST 在输出里可区分）。
<!-- 三仓逐个实测 `npx tsx scripts/migrate.ts status`：均正常启动，读到**本仓属主范围**的迁移
     （api 70 / automation 58 / content 20，三个数各不相同即证明各读各的目录），
     如实打出「残留迁移 13 条」清单，最后停在 `connect ECONNREFUSED 127.0.0.1:5432`。
     可区分性达标：失败原因是连不上库，与修复前的 `ERR_MODULE_NOT_FOUND` /
     `migrations_dir_unreadable` 三者输出各不相同。未连 dev / ol。三仓 typecheck 均通过。 -->
- [x] 1.4 **（实施中新增）** 迁移目录与属主清单改取自**脚本自己的仓根**，不再吃 `migrationsDir()` / `tableOwnershipPath()` 的默认值。
<!-- aidcp-cloud 343c464。改在事实源仓一处，四仓逐字同解：`scripts/` 往上一级恒为本仓仓根。
     形态与 `src/*-schema-gate-startup.ts` 那道启动期契约门一致——**那边先撞过同一个坑**，
     `migration-files.ts` 的文件头注释也早写着「消费方 MUST 显式传入自己的 migrations 目录」，
     只是没人把这句话应用到 scripts/ 上。
     注意这一层与 import 那层的危险度不同：import 断了是响亮失败，路径默认值错了是**读到零条迁移**，
     而契约门会把「零条」判成通过。仓内那道空目录守卫正是为此而设，本次实测被它拦住（报
     migrations_dir_unreadable），是它第一次真正生效。 -->

## 2. aidcp — 控制仓：把 `scripts/` 纳入拆仓同步覆盖（根因，不做等于下次照漂）

- [x] 2.1 在 `scripts/sync-split-repos` 里新增 `scripts/` 的同步段，按**逐文件点名**（范式抄 `aidcp-transport` 那份点名清单），起手只点 `scripts/migrate.ts`。MUST NOT 整目录同步——`scripts/` 下多数脚本是控制仓 / 事实源仓自用的。
<!-- aidcp f79e58e3 `SCRIPT_MEMBERS` + `sync_scripts()`。另加 `SCRIPT_UNMANAGED`（前缀匹配，
     db-split/ 与字体子集脚本）——**这一条是实施中补的，不加就每次刷一屏「多出」把真该删的淹掉**：
     光 db-split/ 一族每仓就 8 条。三类分开报（点名 / 多出 / 有意不纳管），只有第二类会被 --prune 删。 -->
- [x] 2.2 该段 MUST 复用既有的 `rewrite_kernel_imports`（已验证它对 `scripts/migrate.ts` + `../src/kernel/x.js` 解析正确，产出 `aidcp-kernel/kernel/x.js`），MUST NOT 另写一份改写逻辑。
<!-- 偏离并说明理由：**不能直接复用，因为它只认 kernel**，而 `migrate.ts` 有 4 处要指向 transport 包。
     写成 `rewrite_shared_imports`（kernel + transport 一起判），与原函数同一套解析逻辑、同一条正则，
     只是包名按目标落在哪份清单里选——不是「另写一份改写逻辑」。
     `src/` 那边**保持只改 kernel 不变**：跨属主的相对 import 正是要留着让编译器报出来的断裂，
     而 `scripts/migrate.ts` 三仓同源、要用的东西全在两个共享包里，没有「留着报错」的余地。
     另一处判断：**automation 也走包说明符**，尽管它本地有 src/schema/。差异化改写等于给同一个脚本
     留两种形态，而两种形态的漂移没有任何工具会报。 -->
- [x] 2.3 自证覆盖生效：改一行事实源仓的 `scripts/migrate.ts`（可用无意义空白改动，验完还原），跑一次不带参数的对账，确认它**报出该文件有差异**；还原后再跑一次，确认报「无差异」。
<!-- 改从派生侧做（对账读的是事实源的 `git show <ref>:<path>`，事实源的**未提交**改动它看不见，
     从那侧注入只会得到假阴性）：往 `aidcp-api/scripts/migrate.ts` 追加一行 → 对账当场报
     「内容不同 1 · ~ scripts/migrate.ts」；`git checkout` 还原后复跑报「内容不同 0」。
     **这条差异在本 change 之前是完全不可见的**——scripts/ 根本不在对账范围里。 -->
- [x] 2.4 自证幂等：`--apply` 后立刻再跑一次对账，MUST 报零差异；三个派生仓 `git status --porcelain` 在第二次 apply 后 MUST 为空。
<!-- 实测：`--apply` 后复跑对账，三仓均报「新增 0 · 内容不同 0 · 多出 0 · 有意不纳管 9」；
     三仓 `git status --porcelain` 均为空。 -->
- [x] 2.5 在 `docs/cloud-cross-service-coupling-resolution.md`（或同批执行清单）里记一句：`scripts/` 自本 change 起是派生物，MUST NOT 手工改派生仓里的它。
<!-- 落点改为 `docs/cloud-composition-root-trisection.md` 新增 §0.0.4，与它已有的 §0.0.3
     「迁移文件不在同步脚本范围内」同族同形——同一份文档、同一类缺陷（某个目录没人管），
     放一起才能被同一个人一眼读到。一并写进该节的还有那条更危险的第二层：路径默认值指向包内、
     漏传的后果是读到零条迁移而非报错，而契约门会把「零条」判成通过。 -->

## 3. aidcp-cloud — 执行范围与账本范围拆开

- [x] 3.1 在 `src/schema/migration-owners.ts` 的归属结构里把「账本范围」与「执行范围」拆成两个字段，账本范围恒为全部属主（保持今日行为），执行范围按第 4 节的解析顺序给出。文件头那段说明 MUST 同批改写——**它现在写的「残留迁移不持有任何存活对象」是已被实测证伪的错误前提**，留着会继续骗下一个人。
<!-- aidcp-cloud e186154。`MigrationAttribution` 拆成 `ledgerOwners` / `executionOwners` + `executionBasis`。
     一处口径修正（原文没写、实施中判定）：**账本范围不是「恒为全部属主」**——今日行为是
     「对象声明能定位到表 ⇒ 那些表的属主；定位不到 ⇒ 全部属主」，两者不同。写成「恒为全部属主」
     会把 97 条正常迁移的分发面从 70/58/20 一口气放大到 110/110/110。按「保持今日行为」实装。
     文件头那段错误前提已整段重写并写明它是被 2026-08-05 空库实跑证伪的。 -->
- [x] 3.2 `scripts/migrate.ts` 的执行循环改为：执行范围内执行 SQL 并写账本行；执行范围外**只写账本行、一条语句都不发**。
<!-- aidcp-cloud e186154。施加动作析出到新文件 `src/schema/migration-apply.ts`（并入共享包）：
     那十几行装着本机制最危险的两种失败（范围外却发了 SQL / 执行了却没记账），而 CLI 脚本
     在模块层就 main()、**根本没法脱库单测**。账本行的 applied_by 上留 `(record-only)` 标记，
     让账本自己能回答「这一行是跑出来的还是记出来的」——账本表没有这一列，而加列要动 schema，
     本 change 刻意做到零 DDL，故沿用既有的 `(--allow-contract)` 那条写法。 -->
- [x] 3.3 每次运行 MUST 把「记账但未执行」的版本清单原样打出（沿用现有 `residue` 清单必须打出来的纪律），MUST NOT 静默。
<!-- aidcp-cloud e186154。三处都打：CLI 全局一行 + 每个属主组一份逐条清单 + 启动期契约门逐条打。
     实测 api 仓 `migrate status --owner=content`：账本范围 19 条、执行 5 条、记账不执行 14 条逐条列出。 -->
- [x] 3.4 脱库单测：单属主迁移在非属主库上「零 SQL + 一条账本行」；执行范围为空的条目在三个库上都零 SQL；执行范围与账本范围不等时清单被打出。
<!-- aidcp-cloud e186154，`test/schema/migration-apply.test.ts`（4 条）+ `migration-owners.test.ts`
     的 `recordOnlyVersionsForOwners` 用例。断言按**调用序列**判（BEGIN/INSERT/COMMIT 三句，
     且迁移正文一个字都没出现），不是只判返回值——判返回值的话，把 SQL 发出去再返回 executed:false
     照样绿。 -->


## 4. aidcp-cloud — 归属解析顺序与封闭名册

- [x] 4.1 新增文件内属主头 `-- aidcp:owner=<owner>[,<owner>]` 的解析（`parseMigrationHeader` 今天只认 `kind` 与 `objects`）。取值 MUST 限于既有属主枚举，非法值即失败。
<!-- aidcp-cloud e186154。解析在 migration-plan.ts（返回**原样字符串**，该文件 MUST 保持零依赖以便脱库单测），
     枚举校验在 migration-owners.ts。「没写这一行」与「写了但一个 token 都没有」是**两态**：
     后者是显式声明「哪个库都不执行」，压成一态就没法表达 0030 那种形态。 -->
- [x] 4.2 新增 `migrations/legacy-owner-overrides.json`：逐条 `{ version, owners[], basis, supersededBy? }`。`basis` MUST 写清判定依据（读了该迁移哪些语句、对应边界清单里哪一行的属主），MUST NOT 只写属主名。
<!-- aidcp-cloud e186154。13 条 + 冻结集合（110 条显式 version 清单）+ sealedEntryCount。
     Open Question 已解（见 6.3 那条）：冻结集合用**显式清单**，不用 mtime / git 首次出现时间。 -->
- [x] 4.3 实现解析顺序（唯一，MUST NOT 另立）：① 文件内属主头 → ② 名册条目 → ③ 对象声明能定位到表 → ④ **失败并指名**。**删除今天的残留分支**（「无可定位对象 ⇒ 计入全部属主」）。
<!-- aidcp-cloud e186154。残留分支只从**执行范围**里删掉；账本范围仍按今日口径保留它
     （见 3.1 的口径修正）。第 ④ 步进 `index.unresolvedExecution`，由 loadMigrationOwnerScopes 抛错，
     形态与既有的 unknownTables 一致（一次报全部，而不是撞到第一条就抛）。 -->
- [x] 4.4 名册的三条机械断言：(a) 条目数只减不增；(b) 每条 version MUST 属于一份冻结的「本 change 落地前已存在的迁移」清单——新迁移写进名册即失败；(c) 名册里不得有目录中已不存在的 version。
<!-- aidcp-cloud e186154。(a)(b) 在 loadLegacyOwnerOverrides（纯结构校验），(c) 在 attributeMigrations
     （要 files 才判得了）。另加一条原文没要求但同族的：**文件缺席 MUST 抛错，MUST NOT 退化成空名册**——
     退化的话报出来的会是「13 条判不出执行范围」，把一个部署问题伪装成数据问题。 -->
- [x] 4.5 `owners: []` MUST 同时带 `supersededBy`，且被点名的迁移合起来 MUST 覆盖它创建过的全部对象；缺任一条即失败。**这条不加，`0030` 的三个索引会在全新库上被悄悄丢掉。**
<!-- aidcp-cloud e186154。覆盖判据 = 接替迁移声明的对象键并集 ⊇ 本条声明的对象键集合。
     注入验证：把接替迁移的 objects 砍掉一个，闸当场报出被丢掉的那个索引名。 -->
- [x] 4.6 脱库单测覆盖解析顺序的四个分支 + 名册三条断言 + `owners: []` 的接替校验，每条都要有**注入验证**（改坏它、确认闸变红），不能只测 happy path。
<!-- aidcp-cloud e186154，`test/schema/migration-owners.test.ts` 12 条全绿。
     另加一条真语料判例：**声明收窄读的是执行范围而不是账本范围**——按账本范围判会把接替迁移的
     索引一路划进 unattributable，于是那些索引在**任何**库里都不被核验，验证装置变成摆设。 -->


## 5. aidcp-cloud — 13 条历史迁移逐条裁定

- [x] 5.1 逐条实读这 13 条迁移的 SQL，按它们**引用的表**在边界清单里的属主填名册。**MUST NOT 照抄下面这份粗扫结果**——它是正则扫出来的起点，`0030` 正是粗扫会看漏的那一类（去重后只报一个属主）。粗扫基线（2026-08-06）：`0021` / `0027` / `0030_content_schedule_group_comments` / `0040` / `0043` / `0044` / `0050` / `0051` / `0069` → api（9 条）；`0045` / `0046` / `0055` → automation（3 条）；`0030_panel_hardening_indexes` → automation + content（跨属主）。
<!-- aidcp-cloud e186154。13 条逐条实读 SQL（不是读文件头注释——那些注释里有好几条写着「本仓无迁移执行器、
     本文件仅人审留痕」，照信就会把它们当成不执行的文档）。结论与粗扫**一致**：9 api / 3 automation / 1 跨属主。
     一条实读才拿得到的补充事实：**全部 126 张登记表都由某条迁移创建过**，不存在「只靠运行时 store init
     自建、迁移里查不到创建者」的表——这一条是第 6 节那道闸能立判据的前提，靠粗扫看不出来。 -->
- [x] 5.2 `0050_wechat_group_reply_config_privileges` 单独复核：它是一个在表属主找不到时**主动抛异常**的 DO 块，与其它 12 条的失败形态不同（不是「关系不存在」而是显式 RAISE），归属填错的后果更响亮但同样是整批停。
<!-- aidcp-cloud e186154。实读确认：DO 块先查 interaction_reply_configs 的属主角色，查不到即
     `RAISE EXCEPTION 'interaction_reply_configs owner not found'`，再把三张 interaction_reply_scope*
     的权限授给它。四张表 owner 全是 api ⇒ 名册填 ['api']，失败形态差异已写进该条的 basis。 -->
- [x] 5.3 `0030_panel_hardening_indexes` 按 design D3 处置：名册里 `owners: []` + `supersededBy` 点名两条新迁移；新增两条迁移（新版本 id、排目录尾部）分别在 automation 与 content 的表上 `CREATE INDEX IF NOT EXISTS` 建回那三个索引。**MUST NOT 改 `0030` 的字节。**
<!-- aidcp-cloud e186154。`0112_panel_hardening_indexes_automation`（risk_counters / interaction_feed）
     + `0113_panel_hardening_indexes_content`（llm_token_usage），两条都带 `-- aidcp:owner=` 头。
     0030 字节零改动（git diff 为空）。`KNOWN_MAX_SCHEMA_VERSION` 抬到 0113、**REQUIRED 不抬**：
     两条都是幂等建索引，dev/ol 上索引早已存在，抬 REQUIRED 会让两个环境在跑 migrate up 之前一路判 behind。 -->
- [x] 5.4 **先解掉 design 的 Open Question**：实读 `migrate verify` 的对账代码，确认它是否接受「同一对象被两个版本声明」（`0030` 与两条接替迁移）。不接受时的退路是新迁移改用新索引名，并在名册 `basis` 里写明为什么换名。**MUST NOT 凭推测直接写**。
<!-- 实读 `src/schema/schema-inspect.ts`：`declaredObjects` 返回的是**可重复的扁平表**（每条声明一项、
     不去重、各自带来源版本），`diffSchema` 对每一项独立查「在不在库里」，多余项判定用的是集合。
     ⇒ **接受**同一对象被两个版本声明，无唯一性断言。故接替迁移**沿用原索引名**，不换名——
     换名反而会在 dev/ol 两个已有库上留下一对同定义不同名的索引。结论已写进名册该条的 basis。
     附带确认的第二件事：0030 执行范围为空 ⇒ 它的三条索引声明在每个库都进 unattributable
     并被如实打印「本次未核验」，而真正的核验由两条接替迁移的声明在各自库里承担。 -->
- [x] 5.5 给 `scripts/generate-migration-headers.ts` 加守卫：**已应用 / 冻结集合内的迁移不重写头声明**。不加这条，5.3 的新迁移一落地，下次重跑生成器就会去改 `0030` 的头 → 校验和冲突 → dev / ol 迁移命令全停。实测方式：落地后重跑一次生成器，`git status --porcelain migrations/` MUST 为空。
<!-- aidcp-cloud e186154。守卫挡两类：冻结集合内的 + 带 `-- aidcp:owner=` 头的（后者的对象声明是**人判结论**，
     生成器的模型表达不了「把一条跨属主迁移的产物拆给两条接替迁移各自声明」）。
     实测：`--write --rewrite` 后 `git status --porcelain migrations/` 只剩三个新增文件，零修改。
     **变异归因（守卫真的在挡什么，与立项时的假设不同）**：把守卫摘掉重跑，被改写的是 **35 条**已入账迁移，
     而**假设中的 0030 并不在其中**——`CREATE INDEX IF NOT EXISTS` 命中已存在对象时生成器按设计判 no-op、
     归属留在最早那条，所以 0112/0113 抢不走 0030 的声明。真正的风险面比立项时判断的大一个量级，
     但触发路径不是 5.3 那两条新迁移。 -->


## 6. aidcp-cloud — 可执行性静态闸

- [x] 6.1 新增可执行性闸：对执行范围含属主 O 的每条迁移，它引用的每张表 MUST 由某条执行范围也含 O 的迁移创建；不满足即失败并指名「迁移 / 属主 / 缺失的表」。
<!-- aidcp-cloud e186154，`test/acceptance/helpers/migration-executability.ts`。落在 test/ 而不是 src/：
     它只有验收用例一个消费方，放 src/schema/ 要多一次归属裁定、还够不着 boundary-scan 的扫描口径。
     **实测结论（本条最重要的产出，与立项时的预期不同）：0030 之外另有 8 条同类存量违规**，
     分布 api 3 / automation 2 / content 3，全部是「一个文件里装了两家的 DDL」或跨属主外键：
       [api] 0039 → risk_counters（DO 块里 'risk_counters'::regclass，表不存在即抛）
       [api] 0061 → risk_counters（无守卫的 ADD COLUMN + 建唯一索引）
       [api] 0070 → delegated_tasks ／ [automation] 0070 → account_content_schedule + contact_comment_attempts + publish_log
       [automation/content] 0067 → publish_log（REFERENCES publish_log(id)）
       [content] 0005 → publish_log（无守卫的 ADD COLUMN）
       [content] 0057 → publish_log（**跨属主外键**，与其余七条性质不同：物理拆库后两张表不在同一个库里，
                        这个外键无论迁移怎么排都建不出来，消除它要先裁定两张表的属主划分）
     它们**不能**用 0030 那套处置（0030 只建索引不建表，整条判记账不执行即可；这 8 条各自都在为自己的
     属主建真实对象，判成记账不执行等于让它们自己那批表/列也消失，接替迁移要逐字重抄整批 DDL）。
     故按仓内既有棘轮范式逐条登记进 `boundaries/migration-executability-debt.json`（只减不增、
     每条写清语句与后果），闸看住它们不再增长，逐条消除另立。**后果 MUST 如实说：全新空库拉起
     仍会停在这 8 条上——本 change 交付的是机制、闸与 0030，不是「空库已能拉起」。** -->
- [x] 6.2 表引用扫描 MUST 复用仓内既有口径（`src/schema/ddl-scan.ts` 与边界门禁那套 SQL 扫描），**不写第三份**；先剥注释；解析不了的语句 MUST 失败并指名，MUST NOT 静默跳过。
<!-- aidcp-cloud e186154。写操作（INSERT/UPDATE/DELETE/CREATE TABLE/ALTER TABLE）与读引用（FROM/JOIN）
     直接调 `test/acceptance/helpers/boundary-scan.ts` 的 `scanSqlSource`，逐字同源。
     只补了迁移文件独有、而 src/ 里几乎不出现的 8 种形态（每条在代码里写明理由）：
     `CREATE INDEX … ON <表>`（**0030 的全部内容就是三条这个，而 scanSqlSource 的写模式里没有 create_index**）、
     LOCK TABLE、REFERENCES、TRUNCATE、'x'::regclass、to_regclass、GRANT/REVOKE ON TABLE 列表、COMMENT ON。
     另有一类必须显式建模：`ALTER TABLE IF EXISTS` / `DROP TABLE IF EXISTS` 缺表即 no-op，**不构成**
     可执行性问题，MUST 从引用集合里剔掉——不剔的话闸会对一批本来就安全的语句报红、逼人关掉它。
     语句切分认 dollar-quote（`$$ … $$`），否则 DO 块会被切成一堆碎片、闸对着自己的解析残渣报「解析不了」。
     实测真语料 **0 条解析不了**。 -->
- [x] 6.3 在扫描器文件头写死：**它 MUST NOT 参与归属判定，只有否决权**。不写这句，它迟早被当成第二套归属口径，而现有判据明令禁止由 SQL 文本反推归属。
<!-- aidcp-cloud e186154。文件头单列一节，并加了一条可机械检查的形式约束：
     「本文件 MUST NOT 导出任何返回属主的函数」——只写一句劝诫，下一个人照样会把 tableRefs 喂给归属解析。 -->
- [x] 6.4 落成验收用例进 `npm run test:acceptance`，命名与既有 `AC-SCHEMA-*` 族对齐。
<!-- aidcp-cloud e186154，`AC-SCHEMA-EXEC-01..07`，7 条全绿；全量 acceptance 196 pass / 0 fail。
     EXEC-01 里额外加了一道「本仓是不是事实源仓」的显式断言：派生仓只持本属主子集，
     在那里跑整图判据必然报一堆假缺失——**判失败而不是静默跳过**，会自己关掉的闸比没有闸更坏。 -->
- [x] 6.5 注入验证（缺一不可）：(a) 造一条引用外域表的迁移 → 闸当场红并指名属主与表；(b) 把 `0030` 的名册条目改回 `owners: [automation, content]` → 闸当场红；(c) 造一条扫描解析不了的语句 → 闸失败而非放行。三条验完撤销。
<!-- aidcp-cloud e186154。三条都做成**常驻用例**而不是一次性手工注入（EXEC-03/04/05）：手工注入验完就撤销，
     半年后没人知道那道闸还灵不灵。(a) 还多验了反面——同一条迁移换到正确的库里就该放行，
     闸的意义在于分辨这两者，而不是一见跨属主就红。(b) 用真语料 + 内存里改执行范围，
     断言逐字指名 `automation:llm_token_usage` 与 `content:interaction_feed+risk_counters`，
     不改磁盘上的名册。 -->


## 7. 分发与验证

- [x] 7.1 跑 `npm run boundaries:refresh`（新增 `src/schema/**` 文件会要求逐个裁定归属）并把结果一并提交。注意 seed 窗口已于 2026-08-06 关闭，`--reseed` 一律被拒；新增豁免只走 `--raise` 三字段通道，**能不加就不加**。
<!-- aidcp-cloud e186154。新增 `src/schema/migration-apply.ts` 一条 fileOverride（layer=automation，
     手工 Edit 追加、未重序列化）。实测**零新增豁免**：跨层边 0 条、两份豁免清单条目均为 0、
     frozenTotal 0 不变（唯一 diff 是 recordedAt 日期）。它唯一写的表是每个库都有的账本表 ⇒ 不产生跨属主写。 -->
- [x] 7.2 `cd ../aidcp-cloud && npm run test:acceptance` → `npm test` → `npm run typecheck`，三件套全绿并记录数字。
<!-- aidcp-cloud e186154。test:acceptance **196 pass / 0 fail**（含新增 AC-SCHEMA-EXEC-01..07）；
     npm test **4273 pass / 0 fail / 11 skipped**（4284 tests / 253 suites）；typecheck **0**。
     过程中改红过两处、都是真闸而不是噪声：
       ① AC-SCHEMA-DDL-OWNER-02「文本命中」棘轮 271→272——我在 schema-contract.ts 的注释里写了连着的
          DDL 关键字。那道棘轮**故意**连注释一起数（防「注释里搬来搬去」），改写措辞即可，MUST NOT 抬基线。
       ② sync-read-checkpoint 那条 KNOWN_MAX 断言——加迁移必须同步抬，正是它存在的意义。
          同批把它改成按**执行范围**断言 0112/0113 的落点（原来的 versionsForOwner 是账本范围，
          对这两条恒为全部属主，断不出「只在哪个库跑」）。 -->
- [x] 7.3 跑控制仓 `scripts/sync-split-repos`（先不带参数对账、再 `--apply`）把改动分发到三个派生仓。**MUST NOT 因某条迁移执行范围收窄就从派生仓删除它的迁移文件**——账本范围不变，删了账本行会变成 `ledgerOnly` 噪声。逐仓核对 `migrations/` 数量变化并写进本文件。
<!-- aidcp aidcp-transport 505e804 / api 943882c / automation 39502c8 / content 643e488。
     迁移数量：api 70→**72**、automation 58→**60**、content 20→**22**（三仓各 +2）。
     **两条新迁移进全部三个仓是对的、不是漏筛**：它们只声明索引、声明里不带表名 ⇒ 账本范围恒为全部属主，
     而分发按账本范围。执行范围各自只有一家（0112→automation / 0113→content），由名册与文件头决定。
     一条迁移都没有从派生仓删除（12 条收窄执行范围的历史迁移原样留在原处）。
     **同步脚本另加两处**（都是本 change 的根因同族）：
       · `MIGRATION_AUX_MEMBERS` —— `migrations/` 下非 .sql 的判据文件逐字节镜像三仓一份。
         `.sql` 那道对账**只比 .sql 集合**，对目录里的 JSON 判据完全无感：缺了既不报缺也不报多，
         而三个服务的启动契约门读不到名册就拒绝启动。
       · `sync_transport` 的「点名了但源 ref 上还没有那个文件」改为**响亮跳过 + 退出码非 0**。
         此前它让整条同步当场崩掉——本次就被并行 change 的一个超前登记的成员名整批阻断，
         连带别人已就绪的文件一起同步不了。 -->
- [x] 7.4 三个派生仓各跑一次 `npm run typecheck` 与 `npm test`（若该仓有），确认同步没带进断裂。
<!-- 逐仓实测（2026-08-06）：
       · aidcp-content：typecheck **0**，npm test **472 pass / 0 fail**。
       · aidcp-automation：typecheck **0**，npm test **2288 pass / 4 fail**。
       · aidcp-api：typecheck **0**，npm test **576 pass / 2 fail**。
     **6 条失败逐条归因，全部不属于本 change**（判据是「改回本 change 落地前的状态它们照样红」）：
       · automation 2 条 + api 2 条 = 并行 change `report-host-standby-decisions` 的在途状态：
         它的 `src/comm/host-standby-decision-store.ts` / `src/transport/host-standby-decision-http.ts`
         未登记归属、路由未登记进 served-route 清单；而 `aidcp-transport@761b9bd` 把自己的 kernel pin
         写成了 `github:tommax-bai/...` 简写形态（该仓上一版是 `git+ssh://...`），
         api 两条「一份精确的 kernel pin」用例按**整串相等**判 ⇒ 同 sha 不同写法即红。
         **这条值得单独说**：那两条用例正是为这种漂移而设，它们抓对了。修复归属该 change。
       · automation 另 2 条（automation-model-exit / composition-root-4a-mode-wiring）单跑即绿，
         是全量跑与并发 npm install 抢资源的产物（首轮全量曾报 29 条失败，装包结束后复跑只剩 4 条）。
     本 change 自己在派生仓新增的东西全绿：automation 的 migration-owners / migration-apply 两个测试文件
     经 `--tests` 同步过去后通过；三仓 `migrate status` 均起得来并如实打出记账不执行清单。
     **另修一处本 change 造成的红**：automation 的 `boundaries/module-ownership.json` 缺 `migration-apply.ts`
     的归属登记（该仓 `boundaries:refresh` 对 17 个派生私有组装根 fail-closed、跑不动，属既有状态），
     按同族条目形态手工补一条。 -->
- [x] 7.5 在控制仓跑 `openspec validate restore-derived-migration-executability --strict`，回写本文件进度与 commit sha（格式 `<!-- <repo> <commit-sha> 备注 -->`）。
- [x] 7.6 部署 dev 前 MUST 先跑一次迁移状态查询自证零 pending 异常；**本 change 不产生任何需要在既有库上执行的 DDL**，若状态查询报出待应用迁移以外的任何异常，MUST 停手排查而非继续部署。
<!-- 2026-08-06 已部署 dev（api 7a4c6f3 / automation 7791de9 / content 838603a），三服务 active、
     NRestarts=0、8787/8090/8091/8092 全在监听、近 3 分钟零 error、isales 两服务未受影响。
     备份：/opt/aidcp/{content,api,automation}.bak.20260806-15*.tar.gz + 各自 .env.bak。

     **任务原文的两处前提就地更正（都是实测推翻的）：**
     ① 「本 change 不产生任何需要在既有库上执行的 DDL」**不成立**：0112 / 0113 是两条新迁移，
        必须入账。它们是幂等建索引、索引早已存在 ⇒ 执行时空转，但账本要补两行，否则账本最高版本
        停在 0110/0111 而代码 KNOWN_MAX 已是 0113。REQUIRED 未抬，故 up 之前契约门也不判 behind。
     ② 「部署前先跑状态查询」**在旧构建上物理做不到**：实测部署前在 dev 的 /opt/aidcp/api 上跑
        `migrate status`，报的是 `ERR_MODULE_NOT_FOUND: /opt/aidcp/api/src/kernel/pg-owner-connection-resolver.js`
        ——**这正是本 change 修的那个缺陷在真机上的原样复现**。故实际序列只能是
        送代码 → status → up → restart，本次即按此走。

     **两条部署机制，此前没有任何文档写过，下次照做：**
     · **ECS 拉不动共享包**：`git ls-remote git@github.com:tommax-bai/aidcp-transport.git` 在 dev 上
       是 `Permission denied (publickey)`，即那台机器没有 GitHub 私钥。⇒ kernel / transport 的 pin 一变，
       **MUST 把本机 node_modules 里那两个包的目录一起 rsync 上去**（`rsync -az --delete` 到同名目录），
       否则服务起来跑的是旧契约。本次三个服务各送了一份；automation 虽然 package.json 里没 pin
       aidcp-transport，node_modules 里却有一份且被 scripts/migrate.ts 用到，漏送即 ERR_MODULE_NOT_FOUND。
     · **dev 的库已经物理拆开，`migrate` MUST 带 `--owner=<本服务属主>`**：不带的话另外两个属主
       会回落到一个并不存在的库（实测报 `database "aidcp" does not exist`），看着像故障、其实是范围没收窄。

     **本机制在真库上的第一份证据（三个库各自表现不同，正是它该有的样子）：**
       · content 库：`record-only 0112`（未发出任何 SQL）+ `applied 0113 (2ms)`；
       · api 库：`record-only 0112` + `record-only 0113`（两条都不归它执行）；
       · automation 库：`applied 0112 (3ms)` + `record-only 0113`。
     三个库的账本最高版本随后都是 0113，三条 enforce 契约门全部通过，
     启动日志里新的「记账不执行 1 条：0030_panel_hardening_indexes」逐条打出。 -->
- [x] 7.7 把「空库 → migrate up → 启动服务」这条真验收挂回 change `cloud-schema-migration-executor` 的 5.9 与 backlog 簇 111.6，并注明本 change 是它的前置。**本 change MUST NOT 自称已验证空库拉起**——它只负责让那件事第一次可执行。
<!-- aidcp ca7413d2 之后一批。两处都写了，且都**没有勾选对方的项**（本 change 只解除前置，不代验）：
     · `cloud-schema-migration-executor` 5.9：记录前置已解除 + 为什么仍不勾 + 一条重要更正——
       该条 2026-08-05 的结论里写的修法「给 13 条补属主头」**是错的**，那会改字节 ⇒ 校验和不符 ⇒
       dev / ol 迁移命令当场全停。留着不改，下一个人会照着它去撞。
     · backlog 簇 111.6：补了三件事——本项此前根本不具备执行条件、口径从「启动 cloud」改成
       「三个派生服务各自对自己的属主库跑」、以及第一次跑必然停在 8 条已登记的存量违规上（预期结果，
       不是本项失败；只有清单之外的停顿才是新发现）。 -->
<!-- 挂回时一并写上了第 6 节实测出来的那 8 条存量违规
     （`aidcp-cloud/boundaries/migration-executability-debt.json`）：**空库拉起会停在它们上面**，
     所以 5.9 现在的形态是「机制已就位、可以开始跑，但第一次跑必然停在已登记的 8 条上」，
     而不是「跑通了」。这 8 条的消除需要先裁定「一个文件装了两家 DDL」怎么拆（其中 0057 更深一层：
     跨属主外键，拆库后无论怎么排都建不出来，要先裁定两张表的属主划分），属独立立项。 -->

