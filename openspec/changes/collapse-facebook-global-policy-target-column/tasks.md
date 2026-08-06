# Tasks — collapse-facebook-global-policy-target-column

> **前置（两条，性质不同，都不得引用本文件里的实测快照）**
>
> 1. **归档顺序**：本 change MODIFY 的地基能力 `facebook-global-policy-single-scope` 由
>    `unify-facebook-global-policy-across-targets` 引入。**那条归档之前，本条 MUST NOT 归档**，
>    否则 delta 合并会 `Aborted. No files were changed.`（本 change 的 delta 全部是 `## ADDED`，
>    但 ADDED 到一份尚不存在的能力上会写出一份悬空规格 —— 属「依赖序倒置」，validate 与 archive 都不报错。）
> 2. **上线顺序**：迁移只有在**全部**在跑的属主进程都已切读合并行之后才可执行。
>    2026-08-06 实测 dev 与 OL 的 `aidcp-api` 均已跑该版本（作用域常量存在、5 处引用），
>    但**执行时 MUST 重测**——期间任何一次从旧发布分支发版都会让这个前置失效。

<!-- 实装于 2026-08-06。落点：aidcp-cloud 2d34e06（事实源）→ 派生 aidcp-api cdeea7a + 90dfb6e、
     aidcp-automation ec3a8ad + ccc41b0、aidcp-content 7d312ba、aidcp-transport 2b54cc2（tag v0.1.1）。
     dev 与 OL 均已部署并验收（OL 见 §7.3 的说明：两个环境共用同一个接口库，必须同批）。 -->

## 1. 前置坐实（动手之前必须先有结论）

- [x] 1.1 逐环境实测「已切读单份」：在 dev 与 OL 上各确认 `aidcp-api` 进程跑的构建含作用域常量且被读写路径引用。判据是**进程实际在跑的那份代码**，不是分支名、不是台账。
  <!-- 2026-08-06 15:23 实测。两侧服务都是 `npx tsx src/api-service-entry.ts` 直跑源码（无 dist），
       故判据即 /opt/aidcp/api/src/ 下的字节：两侧作用域常量文件都在、值为 'all'，
       且被同样 5 个文件引用（client-user-store / api-sync-read-source / 两份策略存储 / 常量自身）。
       dev 进程起于 15:22:52、OL 起于 10:28:44，都早于本次改动，故跑的就是这份。 -->
- [x] 1.2 列出当前所有 `release/*` 分支，逐条判定是否已含本 change；未含者在本 change 上线后 MUST NOT 再发往任一环境。产出一份具名清单写进 7 组的部署任务。
  <!-- 2026-08-06 实测。本 change 落地前**没有任何 release 分支含它**（它当天才 land），
       故下列分支一律 MUST NOT 再发往任一环境，除非先 rebase 带上本 change：
       aidcp-api：release/20260805-fb-global-policy-unify、20260805-ol-cutover、20260805-ol-panel、20260806-ol-derived-services
       aidcp-automation：release/20260805-ol-capability-names、20260805-ol-cutover、20260805-ol-panel、20260805-ol-risk-scope、20260806-ol-derived-services
       aidcp-content：release/20260805-ol-cutover、20260805-ol-panel、20260806-ol-derived-services
       aidcp-cloud 的 14 条 release/* 与 aidcp-edge / aidcp-console 的不在此列：cloud 自 §8.0 起永不部署，
       edge/console 不读这三张表。**唯一可发 OL 的分支是本次新建的 release/20260806-fb-policy-collapse**（三仓同名）。 -->
- [x] 1.3 重跑三条数据前置并记录当次数值（不得引用 design 里的快照）：
  `all` 未覆盖的 `env_key` 数 / `all` 行内 `env_key` 重复数 / `all` 完成时刻晚于任一旧行的环境数，三者必须全为 0。
  <!-- 2026-08-06 15:26 实测：P1=0 / P2=0 / P3=0。
       另记当时行数：gp all/dev/ol = 1/1/1，gcp all/ol = 1/1（dev 侧本就无行），slow all/dev/ol = 49/46/27。
       同一组断言已写进迁移本体逐条执行，执行时又重跑了一次（见 2.2）。 -->
- [x] 1.4 确认审计表现状仍是「历史行跨目标有重复 revision」：若已不重复，D3 的论证需重新走一遍再决定是否收紧（**默认仍不收紧**，理由见 design D3 第二段）。
  <!-- 2026-08-06 实测：facebook_operation_global_policy_audit 14 行 / 11 个不同 new_revision /
       3 个 revision 出现两次。**与 design 写的「9 行 6 个不同」已不同**（那是 08-05 快照，之后又写了 5 行），
       但结论方向不变：仍有跨目标重复 ⇒ 收紧唯一约束会在现有数据上直接失败 ⇒ 按 D3 一个字节都不动。 -->

## 2. aidcp-cloud — 收缩迁移（**只做 contract 段**）

- [x] 2.1 新增 contract 迁移，头部按仓内约定声明 `aidcp:kind=contract` 与全部 `aidcp:objects`（三张主表 + 被删的 CHECK 约束 + 新增的单例约束）。**约束名 MUST ≤63 字节**——`0110` 曾因自动名 65 字节被 PG 截断、按全名 DROP 不命中且不报错而整体回滚。
  <!-- aidcp-cloud 2d34e06，migrations/0114_facebook_global_policy_collapse_target.sql。
       **偏离（有意）：被删的 CHECK 不写进 aidcp:objects，改用本次新增的 aidcp:retires 头。**
       原因：objects 的语义是「这条迁移之后**应当存在**的对象」，verify 拿它当期望集逐条核。
       把要删的约束写进 objects，等于声明它删完还在，verify 当场报缺失。
       写进新的 retires 头才是如实表达。新增的两条单例 CHECK 照常写进 objects（47 / 45 字节，均 ≤63）。
       约束名长度由用例 facebook-global-policy-collapse-migration.test.ts 机械守着。 -->
- [x] 2.2 迁移开头逐条断言 1.3 的三条数据前置，任一不成立即抛错使整条回滚；**MUST NOT 只删通过检查的那部分行**。
  <!-- 同上文件 §1，四条 RAISE EXCEPTION 全在一个 DO 块里、整体排在任何 DELETE 之前（用例断言了这个顺序）。
       **加了第四条（design 只写了三条）**：两张策略表「有旧行却没有合并行」时停手。
       理由与前置①同类：群评论策略 dev 侧本就无行、ol 侧是运营手写的 72 小时，
       若合并行缺席，删 ol 行会静默丢掉那个值，而代码只会退回默认档、不报错。 -->
- [x] 2.3 删除三张主表中作用域不是 `all` 的行。
- [x] 2.4 两张策略表：加 `singleton boolean NOT NULL DEFAULT true`，改 `PRIMARY KEY (singleton)` + `CHECK (singleton)`，再删 `execution_target` 列及其 CHECK。顺序不可颠倒（删列会先带走现有主键）。
  <!-- 列级 CHECK 随列一起消失，故迁移里不单独 DROP 那两条约束——它们在 aidcp:retires 里如实登记。 -->
- [x] 2.5 冷启动完成表：主键改 `(env_key)`，再删 `execution_target` 列及其 CHECK。**先删旧行（2.3）再改键**——同一 `env_key` 在 dev 与 ol 各有一行时 `(env_key)` 不成立。
  <!-- 顺带：索引 idx_facebook_environment_slow_start_completion_target 建在被删的列上、随列消失。
       迁移里显式 DROP INDEX 只为让这件事在文件里看得见；不补建替代索引（它唯一的用途就是按运行目标筛）。 -->
- [x] 2.6 **审计表零改动**：两张 `*_audit` 的 `execution_target`、CHECK、唯一约束一个字节都不动。迁移里 MUST NOT 出现针对它们的 DDL。
  <!-- 由用例「审计表零改动」机械守着（变异实验：往迁移里加一条 audit DDL → 该用例当场变红）。 -->
- [x] 2.7 `npm run migrate status` / `verify` 在 dev 上确认本迁移声明的对象与实际一致。
  <!-- 2026-08-06 16:40 dev：status 显示「已应用 72 / 待应用 1（0114, kind=contract）」，
       up --owner=api --allow-contract 应用成功（35ms）。
       应用后 verify --owner=api：**缺失对象 0**、声明 557 个对象（迁移前 554 = 554+7新-4退）。
       没有 aidcp:retires 的话这里会是 4 条假缺失，见下面的「新增机制」。 -->

### 2.x 新增机制（不在原任务清单里，实装中发现必须做）

- [x] 2.x.1 迁移头新增 `-- aidcp:retires=`，让收缩迁移显式说出自己移除了哪些**更早迁移声明过**的对象。
  <!-- aidcp-cloud 2d34e06：src/schema/migration-plan.ts 解析、src/schema/schema-inspect.ts 按复合序
       从期望集里减掉、scripts/generate-migration-headers.ts 跳过带该头的文件（避免 --rewrite 把它悄悄删掉）、
       migrations/README.md §4 写清用法。
       **为什么必须做**：对象声明是全目录取并集的，而旧文件校验和一经落账就改不得
       （改了即 migration_checksum_mismatch 整批拒绝）。于是本条删掉的 3 个 CHECK + 1 个索引
       （声明在 0103 / 0110）会永远留在期望集里，`migrate verify` 从此报 4 条缺失——
       而缺失清单是 `migrate baseline` 唯一的准入闸，**任何新建的属主库会被一条假缺失永久拒之门外，
       且按「缺失就补跑迁移」补多少次都不会变空**。这是本仓第一条删掉「已声明对象」的收缩迁移，
       此前没有任何机制处理它。判定按复合序取最晚一次表态：被更晚的迁移重新声明则重新计入期望集。 -->
- [x] 2.x.2 `REQUIRED_SCHEMA_VERSION` 与 `KNOWN_MAX_SCHEMA_VERSION` 一并抬到 `0114`。
  <!-- src/schema/schema-contract.ts。KNOWN_MAX 是仓内硬要求（新增迁移必抬，用例断言）。
       REQUIRED 也抬，因为这条是**真依赖**：切读后的存储探测直接要求 singleton 列，
       迁移没跑就起新构建 ⇒ 两个策略存储 degraded ⇒ 后台那两格返 503。
       与 0112/0113「只抬 KNOWN_MAX」的处理不同——那两条是幂等空转，这一条真的改了 schema。
       派生仓 migrations/ 只有本属主子集，目录最高版本低于 KNOWN_MAX 属预期，
       运行期由 narrowSchemaContract 按本属主版本集合收窄（实测 automation / content 都判 0113 通过）。 -->

## 3. aidcp-cloud — 存储与路由

- [x] 3.1 两张策略表的读写改为直取单行：去掉作用域参数与 `WHERE execution_target=$1`。
  <!-- src/config/facebook-operation-policy-store.ts（刷新读 / FOR UPDATE 读 / UPDATE，参数逐条重编号）
       与 src/config/facebook-group-comment-policy-store.ts（读 / FOR UPDATE / UPDATE / INSERT）。 -->
- [x] 3.2 冷启动完成事实的读写改为按 `env_key` 直取，去掉作用域参数。
  <!-- 5 处：策略存储的写/删/两处子查询/markGraduatedInTx；client-user-store.ts 6 处；
       api-sync-read-source.ts 1 处（automation 镜像的取数口）。 -->
- [x] 3.3 作用域常量文件在全部引用消除后删除；**MUST NOT 留一个恒为 `'all'` 的常量继续传参**——那等于把分行维度改名留在代码里。
  <!-- src/config/facebook-global-policy-scope.ts 已删；boundaries/ownership-rules.json 的 fileOverride
       手工删除（该文件是手工维护的紧凑清单，MUST NOT 整体重序列化），module-ownership.json 由
       npm run boundaries:refresh 重生成。
       **一处刻意保留的字面量，写在这里以免被当成漏改**：两张审计表的 execution_target 列仍在
       （2.6 明令不动它），且该列 NOT NULL、无默认值，故审计写必须给值。做法是**在两处审计 INSERT 的
       SQL 里直接写 'all' 字面量并就地注明它的身份**（追溯字段、不是选行键），不再共用一个常量。
       用例 4.5 把这两件事分开断言：主表 SQL 里一处 execution_target 都不许有；
       审计 SQL 里的那两处**必须**在——它消失了不是「更干净」，是把历史抹掉了。 -->
- [x] 3.4 视图里 `executionTarget` 那一格**保持不变**（它表示「通过哪个目标的接口读」，面板对它有 `['dev','ol']` 硬闸）。本 change MUST NOT 改它的语义或取值。
  <!-- 取值仍是 this.executionTarget ?? 'dev'，只更新了注释（原注释说「行键是作用域常量」，
       收缩后表上连分行键都没有了）。上线后两侧实测：dev 返 'dev'、OL 返 'ol'。
       **同时刻意未动**：global 读外面那层 `this.executionTarget ? … : 空` 的守卫。
       它问的是「本进程有没有声明部署目标」，与「读哪一行」无关；改它是行为变更、与本 change 目标无关。 -->

## 4. aidcp-cloud — 测试

- [x] 4.1 单测：插入第二行全局策略必然失败（单例约束真的在库层面拦住，而不是靠写入方只写一行）。
  <!-- **拆成两半做，两半都做了，MUST NOT 用其中一个冒充另一个**：
       ① 仓内 SQL 合同测试（test/schema/facebook-global-policy-collapse-migration.test.ts）守住
          迁移文件不退化——本仓所有 DB 相关单测都用假 pool，没有连真库的用例，这一层只能是文本断言；
       ② 真库行为证据在 8.2：dev 上真插第二行，被 facebook_operation_global_policy_pkey 拒绝。 -->
- [x] 4.2 单测：同一 `env_key` 的第二条完成事实必然失败或幂等合并。
  <!-- 同上两半：文件层断言 PRIMARY KEY (env_key)；真库层 8.2 实插被 pkey 拒绝。
       另：正常写路径走 ON CONFLICT (env_key) DO UPDATE，即幂等合并。 -->
- [x] 4.3 迁移用例：断言三条数据前置逐条被断言且任一不成立时整条失败；**把断言删掉后该用例必须变红**。
  <!-- 变异实验 2026-08-06，四次，每次只改一处、跑完即按字节还原（还原后与备份 diff 为空）：
       ① 删掉整个前置 DO 块 → 「三条数据前置逐条断言」变红 ✓
       ② 给迁移加一条审计表 DDL → 「审计表零改动」变红 ✓
       ③ CHECK (singleton) 改成 CHECK (true) → 「单例约束替代分行键」变红 ✓
       ④ 删掉一行 aidcp:retires → 「被删对象都写进了 retires」变红 ✓
       四次都是**该抓的那条用例**变红，不是别的用例连坐。 -->
- [x] 4.4 迁移用例：断言迁移**不含**任何针对两张审计表的 DDL（守住 D3）。
- [x] 4.5 反回归：断言代码里不再有以运行目标为键读写这三张表的路径，也不存在恒为 `'all'` 的替代常量。
  <!-- test/schema/facebook-global-policy-single-row-regression.test.ts。判据按**语句**给不按文件给：
       扫 src/ 全部模板字符串，凡提到三张主表（负向前瞻排除同名前缀的审计表）的语句里
       一处 execution_target 都不许有；作用域常量模块不存在且无人引用；
       第三条反过来断言两处审计写**必须**带着那个字段——按文件粗判会把它一起判成违规，
       于是这道闸只能被放宽或删掉。 -->
- [x] 4.6 两仓回归：`test:acceptance` → `npm test` → `typecheck` 全过。
  <!-- aidcp-cloud：acceptance 196/196、全量 4304 pass / 0 fail、typecheck 干净。
       派生三仓见 5.3 与 6.1。 -->

## 5. aidcp-api — 派生仓同步

- [x] 5.1 `scripts/sync-split-repos --apply --repo aidcp-api` 同步属主文件；组装根不派生，需手写的部分单独确认。
  <!-- aidcp-api cdeea7a。写入 4 个属主文件 + --prune 删掉作用域常量；组装根 src/index.ts / src/server.ts
       与三个 api 私有入口只报不改（本次它们无需改）。
       **同步器对 migrations/ 只报不改**（它当场报了「缺 0114」），故迁移逐字节手工拷贝并 diff 确认。
       **另外三仓也要同步**：src/schema/* 的属主是 automation、并镜像进共享包 aidcp-transport，
       故 aidcp-automation ec3a8ad 与 aidcp-transport 2b54cc2 各带同一份改动；aidcp-content 无属主文件变化。 -->
- [x] 5.2 派生仓 `test/` 不在同步器覆盖范围内：受影响的用例逐个手工对齐，对齐前先确认与云端同源（该仓的副本是手工适配过的，整份覆盖会静默还原它的适配）。
  <!-- 先 diff 出适配面：两份用例与云端的差异只有 kernel import 改包路径；
       facebook-operation-policy-store.test.ts 另外**少一个 api 私有用例**（api-mode wiring）。
       故：群评论那份重新派生后只改回 import 一行；操作策略那份**原地施加同一组语义修改**、
       绝不整份覆盖（覆盖会把那个私有用例删掉）。 -->
- [x] 5.3 派生仓 `typecheck` + 全量测试通过。
  <!-- aidcp-api：typecheck 干净、578 pass / 0 fail。
       中途一次红：`npm install <pkg>@<url>` 把 package.json 里的钉子改写成 `github:` 短形态，
       4b 组装根用例按全形态 `git+ssh://…#vX.Y.Z` 断言 ⇒ 当场变红。已改回全形态（aidcp-api 90dfb6e）。 -->

### 5.x 共享包发版（不在原任务清单里，实装中发现必须做）

- [x] 5.x.1 `aidcp-transport` 打 tag `v0.1.1` 并把三仓钉子从 `v0.1.0` bump 过去。
  <!-- aidcp-transport 2b54cc2 + tag v0.1.1；aidcp-api 90dfb6e / aidcp-automation ccc41b0 /
       aidcp-content 7d312ba 各 bump 钉子 + lockfile。
       **为什么必须**：src/schema/* 三个文件（retires 解析、期望集扣减、契约窗口抬到 0114）住在共享包里，
       而三个服务仓靠钉子取用。**钉子不跟着走不会报错**：npm 装到旧 tag、编译照过、测试照绿，
       只是 ECS 上 `migrate verify` 仍是旧判定、契约门仍认 0113。 -->

## 6. aidcp-automation — 零改动验证

- [x] 6.1 该域经同步读镜像消费策略，载荷本就是「一份」，预期零改动；**但 MUST 实测验证不因属主侧去掉分行列而漂移**：对比收缩前后镜像载荷逐格相同。
  <!-- 载荷投影函数 projectClientEnvironmentAutomationSnapshot 未改，改的只是它上游那条取数 SQL
       （去掉 AND c.execution_target=$1）。实测口径：把该 SQL 的取数结果按 env_key 排序拼成一张表取 md5。
       迁移前（带 all 过滤）= 01591ba4cf97afcf4948ea4641c5231c / 149 行；
       迁移后（不带过滤）= 01591ba4cf97afcf4948ea4641c5231c / 149 行。**逐格相同。**
       代码侧 aidcp-automation：typecheck 干净、acceptance 298/298、全量 2299 pass / 0 fail。
       aidcp-content：typecheck 干净、472 pass / 0 fail。
       **顺带证实了一件要写下来的事**：迁移**前**跑那条不带过滤的 SQL 会直接报
       「more than one row returned by a subquery」——同一 env_key 在 all 与 dev/ol 上各有一行。
       即：新代码在迁移前跑不通，旧代码在迁移后跑不通，两者没有共存窗口。这决定了 7.2 / 7.3 的次序。 -->
- [x] 6.2 若确有漂移，MUST 在本 change 内修完，MUST NOT 留给「反正镜像会自己刷新」。
  <!-- 无漂移，本条不触发。 -->

## 7. 部署与迁移执行

- [x] 7.1 迁移前备份：三张表各导出一份，记录导出时刻与文件位置。**这是本 change 唯一的回滚路径**（删列之后代码回滚救不了），MUST NOT 当作流程装饰。
  <!-- 2026-08-06 16:31:51，导在库所在机（dev，121.89.85.150）：
       数据 /opt/aidcp/backup/facebook-global-policy-precollapse.20260806-163151.sql（142 条 INSERT）
       结构 /opt/aidcp/backup/facebook-global-policy-precollapse-schema.20260806-163151.sql
       两份都覆盖五张表（三张主表 + 两张审计表）。**回滚 = 从这两份恢复**，不是换代码。
       服务目录 tar 与 .env 另备：dev /opt/aidcp/*.bak.20260806-163404.tar.gz、
       OL /opt/aidcp/*.bak.20260806-165729.tar.gz。 -->
- [x] 7.2 dev 部署 + 迁移；healthcheck 含「重启后真的起来了」，不只是部署前 active。
  <!-- 2026-08-06 16:31–16:43。次序（由 6.1 那条「无共存窗口」决定）：备份 → rsync 代码（不重启）→
       装共享包 → 跑迁移 → 立刻重启三服务。
       重启后：三服务 active；automation 8787、api 面板 8090 与属主口 8093 都在监听；
       api 的 schema 契约门（**enforce 模式**）打印「通过：账本最高版本 0114（所需 0114，本构建认识到 0114）」；
       automation / content 各自收窄后判 0113 通过；日志无 degraded / schema_incomplete / unavailable。 -->
- [x] 7.3 OL 部署：MUST 从含本 change 的发布分支执行，且执行前把 1.2 那份分支清单再核一遍。
  <!-- 2026-08-06 16:57–16:59，用户当场明确批准后执行，发布分支 release/20260806-fb-policy-collapse
       （aidcp-api / aidcp-automation / aidcp-content 三仓同名，均由各自 master 头创建；
       canonical checkout 全程停在 master，分支用 `git branch <name> HEAD` 创建、不 checkout）。
       **为什么不是「等下一次再说」——本条的实际执行序与计划不同，原因必须写下来**：
       **dev 与 OL 的接口库是同一个 PostgreSQL 实例**（OL 的 AIDCP_PG_API_URL 指向 121.89.85.150:5432/aidcp_api，
       就是 dev 本机那个库）。列一删，OL 上还跑着旧构建的 api 进程**立刻**开始报
       `column c.execution_target does not exist`：16:41–16:52 共 124 条，
       client_environment_slow_start 镜像停在 version=1768 不再前进（响亮失败、不是静默错值）。
       即：这条 contract 迁移对两个环境是**同一个动作**，MUST NOT 按「先 dev 观察几天再 OL」排期。
       部署后：三服务 active；8787 / 8090 / 8091–8094 全在监听；三道契约门都判通过；
       重启后 execution_target 报错数 = 0；镜像当场重载到 version=1789 并恢复推进。 -->
- [x] 7.4 迁移记录写清：执行时刻、三条数据前置的当次实测值、删除的行数（按表）、备份文件位置、**回滚方式＝从备份恢复**。
  <!-- 见同目录 migration-record.md。 -->
- [x] 7.5 上线后逐环境确认接口进程重启一次仍能起来，且策略读数与收缩前逐格相同（收缩不改任何数值，读数变了就是出事了）。
  <!-- 两侧都是「先重启、再从后台 HTTP 读」，不是只看进程活着：
       dev  GET /api/facebook/operation-global-policy → executionTarget=dev、revision=12、
            rule 5/2、consumption 5/2/2、reels 4/10 · 6/15 · 15 · 15、slowStart.totalDays=5
       OL   同一路径 → executionTarget=ol、其余逐格相同（同一行、两个接口）
       两侧 GET /api/facebook/groups/comment-policy → 72 小时、revision 2、source=db
       与 7.1 备份前抓的 BEFORE 快照逐格一致。 -->

## 8. 验收（缺一不可）

- [x] 8.1 三张表的 `execution_target` 列与 dev/ol 旧行确实不存在。
  <!-- 实测：information_schema 里带 execution_target 的 facebook* 表只剩两张审计表。
       行数 gp=1 / gcp=1 / slow=49（收缩前 1+1+1 / 1+1 / 49+46+27），删除行数
       gp 2 行、gcp 1 行、slow 73 行。 -->
- [x] 8.2 试插第二行全局策略在真库上被拒。
  <!-- dev 真库实测两条：
       ① 插第二行全局策略 → ERROR duplicate key value violates unique constraint
          "facebook_operation_global_policy_pkey"，Key (singleton)=(t) already exists
       ② 给已有 env_key 插第二条完成事实 → 被 facebook_environment_slow_start_completion_pkey 拒绝 -->
- [x] 8.3 两张审计表的列、CHECK、唯一约束与收缩前逐字节相同。
  <!-- 拿 7.1 的迁移前结构导出与迁移后重新导出对比：两侧各 14 条与审计表有关的语句，
       归一化空白后集合完全相同（IDENTICAL）。 -->
- [x] 8.4 两侧后台读到的策略与收缩前逐格相同（含 revision）。
  <!-- 见 7.5。revision 两侧都仍是 12，未被本次收缩推进（收缩不写策略行）。 -->
- [x] 8.5 自动化侧镜像载荷与收缩前逐格相同。
  <!-- 见 6.1：md5 与行数都相同；OL 侧镜像在部署后当场重载成功并继续推进。 -->
- [x] 8.6 真机 / 长周期观察项登记进 `docs/real-machine-acceptance-backlog.md`。
  <!-- 新建簇 147（登记于 2026-08-06）；同时把簇 144.3 那条「回滚窗口到期前必须有人决定」
       标记为**已到期并已执行**（旧行已删，退路自此只有备份）。 -->

### 8.x 写路径实弹演练（不在原任务清单里，实装中判断必须做）

- [x] 8.x.1 在真库上把收缩后**写路径**真正会发的语句跑一遍，事务末尾 ROLLBACK。
  <!-- 2026-08-06 16:48 dev。跑了 6 段：FOR UPDATE 读 / markGraduatedInTx 的 ON CONFLICT (env_key) /
       全局策略 UPDATE（参数重编号后的完整列清单）/ 审计写（'all' 字面量）/ 完成事实 upsert /
       群评论策略 UPDATE + 审计写。全部成功，ROLLBACK 后库回到原样（revision 仍 12、审计仍 14 行）。
       **为什么加这条**：本仓 DB 相关单测全用假 pool，而这次改动的实质是**逐条重编了 SQL 参数号**——
       假 pool 恰恰证明不了参数号与列清单跟真 schema 对得上。只读验收（8.1/8.4）也覆盖不到写路径。 -->

## 9. 归档前置

- [x] 9.1 `unify-facebook-global-policy-across-targets` 已归档（见文件头前置 1）。
  <!-- 归档目录 openspec/changes/archive/2026-08-06-unify-facebook-global-policy-across-targets/ -->
- [x] 9.2 `openspec validate collapse-facebook-global-policy-target-column --strict` 通过。
