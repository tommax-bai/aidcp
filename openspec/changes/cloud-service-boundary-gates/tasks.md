<!--
实装记录（2026-07-22 / 2026-07-23，worktree ../aidcp-cloud.wt/cloud-service-boundary-gates 分支同名）
五个提交尚未 push，sha 待主控 session 集成后复核（前四个已随 rebase 换 sha）：
  071252c cloud-service-boundary-gates: seed module ownership and two boundary gate families（原 071252c）
  af05b3c cloud-service-boundary-gates: emit content-involvement count for phase-3 admission（原 af05b3c）
  8224c82 cloud-service-boundary-gates: strip stray NUL bytes from scanner dedup keys（原 8224c82）
  31dfab2 cloud-service-boundary-gates: close scanner blind spots found by audit（原 31dfab2；2026-07-23 审计后修复，见 2.5 / 3.2 / 4.1 / 4.2 / 7.3 / 7.4 各条注释）
  e8c0e04 cloud-service-boundary-gates: rebaseline the two gate families on the merged trunk（2026-07-23 rebase 后重新基线，见下方「基线迁移」）
  620c0db cloud-service-boundary-gates: close four ratchet blind spots found by audit（2026-07-23 第二轮审计后修复，见 3.4 / 4.3 / 4.4 / 5.4 / 7.3 各条注释）
  89c286d cloud-service-boundary-gates: adjudicate src/schema/ and schema_migrations ownership（2026-07-23 第三次基线迁移，见下方「基线迁移二」）

第二轮审计（2026-07-23）坐实的四条缺陷已全部修复，四条都是「棘轮自己把违规写进清单还退出 0」这一类静默假成功：
  ① 表侧棘轮按条目数计而非按「表×文件×操作」计 → 已豁免的 (表,文件) 对上新增 ALTER TABLE 会被 refresh
     自行拓宽写回、AC-OWN-03 恒绿。修法是把「操作」加回键里：一条豁免条目 = 一个三元组，
     table-write-exemptions.json 由 10 条 ops[] 形态改为 12 条三元组形态（豁免的实际面一条未变，
     seedTotal / seedUnplanned / frozenTotal 同步 10 → 12，理由写进该文件的 seedBasis）。
  ② 默认路径的 refresh 会静默删掉两份清单头部的 seedBasis（seed 基线由来的唯一在仓记录）。
  ③ 生成物 module-ownership.json 被回喂当「已裁决集」，手工塞一条即可洗白 → 准入依据挪进新的人工文件
     boundaries/adjudicated-files.json（147 个 grandfathered 文件，只减不增）。
  ④ --reseed 零机械守卫 → 补四道门（seedWindow.open / --seed-note / --i-am-reseeding-the-ratchet / raises[] 非空即拒）。
  归档时的强制动作：把 boundaries/ownership-rules.json 的 seedWindow.open 改成 false（关掉 seed 窗口）。

基线迁移（2026-07-23）：本分支 rebase 到最新 origin/master 后，主干已含 risk-state-cross-process-integrity /
config-mirror-cross-process-invalidation / publish-approval-signal-to-database 三个 change，新增 15 个源文件、5 张表。
两族冻结基线原在 aidcp-cloud@313eba2 上算，rebase 后 AC-BOUND-01 / AC-BOUND-04 / AC-OWN-01 三条当场红
（实测 15 个源文件未归属、17 条未豁免跨边界 import、5 张表无属主）。已在合并基线上按定稿判据重新裁定与 seed。

  口径迁移：源文件 323 → 338（api 91→101 / content 80→80 / automation 146→151 / kernel 4 / composition 2）；
  跨边界 import 257 → 274（frozenTotal 同步，delta 0）；involvingContent 112 → 112（未变，17 条新增全在 api↔automation）；
  表全集 84 → 89（src 自建 59→64 ∪ migrations 60→65）；SQL 写入点 231 → 245；
  跨层写入 12 / DDL 违规 0 / 表写入豁免 10 条 / frozenTotal 10 —— 表侧四个数一个未变（5 张新表的属主与写入方同层）。

  可重跑命令（新，取代原来的 seed 一次性脚本）：`cd ../aidcp-cloud && npm run boundaries:refresh`
  （只读对账：`npm run boundaries:census`）。change cloud-schema-migration-executor 落地后 MUST 再跑一次收敛
  —— **已于 89c286d 跑完，见下方「基线迁移二」**。
  该命令在干净树上**幂等**（2026-07-23 于 620c0db 复核：重跑后 `git status --porcelain` 为空）。

基线迁移二（2026-07-23，89c286d）：change cloud-schema-migration-executor land 到 master 后，主干新增
`src/schema/` 12 个源文件与 `schema_migrations` 账本表。两族门禁按设计拒绝自动填默认层，AC-BOUND-01 与
AC-OWN-01 当场红（12 个源文件无归属层、1 张表无属主），要求人工裁决。本次只做归属登记与棘轮移动，
src/ 与 migrations/ 零改动（`git status --porcelain src/ migrations/` 为空）。

  裁决一 —— `src/schema/` 整目录判 `automation`，标【待定稿裁决】。三条理由：
    ① MUST NOT 判 kernel：§4.7 的 kernel 花名册是封闭的 4 文件名单，新增成员 MUST 走「析出 + 回写 §4.7」
       通道；且 `schema-capability.ts`（pg_indexes 查询）与 `pg-catalog.ts`（pg_class 查询）含 SQL 字面量，
       AC-BOUND-03 的「无 SQL」准入当场不过——与 kernel-non-members.json 里 curated-content-store.ts /
       client-user-store.ts / content-schedule-store.ts 三条被拒条目同一条判据。
    ② MUST NOT 判 composition：AC-BOUND-02 限定 composition 只能是 compositionWhitelist 里的组合根，
       且让 34 个存储反向导入组合根是依赖倒置。
    ③ 落 automation 是最小失真选择：design.md 已写明拆仓后 kernel 由 aidcp-automation 以版本化包发布、
       api 与 content 固定版本消费，故「尚未获得 kernel 准入的共享基础设施」暂随 automation。
    目录规则的 `newFile` 取 **adjudicate**（不是 inherit）：本条是尚未回写 §4.7 的临时归属，§4.7 并没有判定
    「本目录任意新文件属于哪一层」，后续新增文件（尤其是从 schema-capability.ts 析出的纯判定段，按消除
    路径 (a) 恰恰应判 kernel）MUST 重新逐个裁。**连带后果：现有 12 个文件必须逐个写进 fileOverrides**
    ——adjudicate 目录的既有文件只能靠人工名册 adjudicated-files.json 放行，而该名册按 620c0db 的纪律
    MUST NOT 增长，故本次名册一条未增、12 条全部进 fileOverrides。

  裁决二 —— `schema_migrations` 属主判 `automation`，标【待定稿裁决】。§5.1 未具名；迁移账本由部署期
    执行器 `scripts/migrate.ts` 单写（migrate.ts:185 / :252 的 INSERT），三服务运行时只读
    （schema-gate.ts:73 的 SELECT）。拆库后账本归属随 §5.4.7 子目标 B 的数据库角色划分定，待回写 §5.1。
    **MUST NOT 写进 boundaries/exception-tables.json**：那份清单明写「条目数只减不增，新增 MUST 由
    控制仓 change 批准」，且其两条现有条目的例外理由（多写者是设计前提 / owner 是三服务之外的外部探针）
    本表都不符合。

  口径迁移（前 → 后）：源文件 338 → **350**（api 101 → 101 / content 80 → 80 / automation 151 → **163** /
  kernel 4 / composition 2）；跨边界 import 274 → **295**，frozenTotal 274 → **295**（delta 0）；
  involvingContent 112 → **117**（新增 21 条里有 5 条一端是 content）；
  方向分解 api→automation 85 → **101**、content→automation 27 → **32**，其余四向不变；
  表全集 89 → **90**（src 自建 64 不变 ∪ migrations 65 → **90**；migrations 侧的跃升是该 change 新增的
  合并基线迁移文件把既有表一并 CREATE TABLE 了，不是新表——表全集只 +1，即 schema_migrations）；
  SQL 写入点 245 → 245（未变）；跨层写入 12 / DDL 违规 0 / 表写入豁免 12 条 / frozenTotal 12
  —— **表侧四个数一个未变**（账本表的唯一写入方在 `scripts/`，不在 `src/` 扫描面内）。

  棘轮走的是 **seed 窗口内的 `--reseed`，不是 §12 的具名上调通道 `--raise`**。理由（已实测，不是推断）：
  `--raise` 要求三字段齐备（批准它的控制仓 change 名 + 数量 + 消除日期），且 AC-BOUND-06 另有一条
  「未挂消除 change 的条目数单调不增」——新条目必须带 `eliminatedBy`。本轮既没有承接消除的控制仓 change，
  也没有定稿给出的消除时限，填任何一个都是编造事实。实测 `refresh --raise=cloud-service-boundary-gates:21:<日期>`
  确实退出 0 并把 frozenTotal 抬到 295，但 AC-BOUND-06 当场红：「未挂消除 change 的条目数 295 高于 seed 值 274」。
  故按 `seedWindow.open` 仍为 true 的设计目的移动 seed 基线，理由全文写进两份清单的 `seedBasis`。

  新增 21 条豁免的来源**高度集中**：20 条指向 `src/schema/schema-capability.ts`（34 个存储的 init() 导入它的
  ensureCapabilitySchema，其中 api 16 / content 4 产生跨边界边），另 1 条指向同目录的 `schema-name.ts`
  （src/cache/curated-content-store.ts 引 qualifiedObjectName）。这 21 条共享**同一条 §4.7 消除路径**，
  二选一：(a) 把纯判定段（classifySchemaCapability / 错误形状 / 自建旋钮）析出为独立**无 SQL** 的新文件后
  判 kernel、探测执行段留 automation；(b) 确认 automation 归属 + 按拆仓设计以版本化包供 api / content 消费。
  **MUST NOT 把它们当成 21 处各自独立、需要各自消除的架构违规**——逐条各挂一个消除 change 会把一次裁决
  摊成 21 次无意义返工。该口径已逐条写进这 21 条的 `note` 字段。

控制仓文档改动（第 6 节）未直接改 docs/，改为写进 docpatch 供主控串行套用；rebase 后的重新裁定与被取代的数字
在同一份 docpatch 的 R 组（R0–R3），第二轮审计后的口径修正在 S 组（S1–S3，含表侧阈值 10 → 12 与 seed 窗口关闭动作）：
  /private/tmp/claude-501/-Users-baitianxing-codes-aidcp/f0ef76c1-69d8-483a-8df8-115c38a2f9d0/scratchpad/docpatch-cloud-service-boundary-gates.md
-->

## 1. aidcp-cloud — 模块归属表（全覆盖，无未分配态）

- [x] 1.1 新建 `boundaries/module-ownership.json`：条目形如 `{ "path": "src/time/shanghai-day.ts", "layer": "kernel", "note": "" }`，`layer` 枚举固定为 `kernel` / `api` / `content` / `automation` / `composition`，**不设「未分配」取值**。放仓根 `boundaries/` 而不是 `src/`，避免动 `tsconfig` 的 `resolveJsonModule`。示例 MUST 取自定稿 §4.7 已裁定的 kernel 四文件之一；**MUST NOT 用 `src/comm/protocol.ts` 作示例**——§10.9 终局裁决它归 `aidcp-automation` 独占、MUST NOT 进 kernel，示例会被实施者照抄。
<!-- aidcp-cloud 071252c 323 条条目 / 未归属 0。清单是生成物，事实源为 boundaries/ownership-rules.json（§4.7 的机械转写），重跑 `npx tsx test/acceptance/helpers/boundary-record.ts ownership` 即可接住后续 change 新增的源文件 -->
<!-- 修正 aidcp-cloud e8c0e04（2026-07-23 rebase 后）：上一条注释里「重跑即可接住后续 change 新增的源文件」这句**当时是错的、已改掉**。目录规则接住新文件这件事本身，在 §4.7 把该目录逐文件切开的场合就是「脚本替人裁决」——实测反例：src/publish-agent/ 在 §4.7 是 7 api / 54 content / 6 automation 三分的，旧规则会把新增的 publish-approval-store.ts 静默判成 content，而它建的 publish_approval_decision 是 §5.1 具名归 api 的表，静默落 content 会让 AC-OWN-03 变红、且红的原因是「脚本判错层」而非「代码违规」。现给目录规则加 newFile 字段（inherit = §4.7 该行单层、新文件已被判过；adjudicate = §4.7 逐文件切开、新文件 MUST 进 fileOverrides 逐个裁定），缺省按 adjudicate 处理。生成器遇 adjudicate 目录的新文件即 exit 1 并列出待裁决清单。实测 338 条条目 / 未归属 0 -->
<!-- 归属裁定（本轮 15 个新文件）：src/risk/ 5 个走 inherit（§4.7 该行 19/19 automation）；src/publish-agent/ 的 publish-approval-store / -outlet / -api 按 §4.6.3 import 指纹判据第三条（写授权记录即台账与审批段）+ §4.6.3 正文对 publish_approval_decision 的直接点名，落 api；src/config/ 的 mirror-registry / mirror-version-store / mirror-refresher 按 §4.6.8（例外名单封闭为 5 个限频配置文件）落目录默认 api。四处判据两可的按最保守填并在 basis 里标「待定稿裁决」+ 写进 docpatch R1：src/config-mirror-freshness.ts（新根文件；MUST NOT 判 kernel——花名册封闭且它 :59 有模块级可变单例，AC-BOUND-03 准入不过）、src/db/environment-row-lock.ts（§4.7 无 src/db/ 行，用 fileOverride 而非目录规则，故该目录后续新增仍会逐个报待裁决）、src/config/mirror-stop-work.ts（两种判法豁免净额均为 3，即净额 0）、src/publish-agent/pending-dispatch-watchdog.ts（落 api 新增 0 条、落 automation 新增 1 条） -->
<!-- 归属裁定二（89c286d，cloud-schema-migration-executor land 后的 12 个新文件）：`src/schema/` 是 §4.7 里不存在的新目录，整目录判 automation（三条理由见头部「基线迁移二」，逐条写在 ownership-rules.json 该目录规则的 basis 里）。目录规则的 newFile 取 **adjudicate**，因此 12 个既有文件全部逐个进 fileOverrides、adjudicated-files.json 名册一条未增（该名册按 620c0db 的纪律 MUST NOT 增长）。其中两条 basis 写得更细：schema-capability.ts 是 34 个存储 init() 的共享入口、单点产出 20 条跨边界豁免，schema-name.ts 另产出 1 条；其余 10 个文件只被同目录 / 组合根 / scripts / 测试导入，0 条。实测 350 条条目 / 未归属 0。请求回写 §4.7 见 docpatch R4 -->
- [x] 1.2 **归属判据不在本 change 内自立，一律引用控制仓定稿 `docs/cloud-service-decomposition-proposal.md` §4.7「归属总表」逐行填入**（该表已覆盖全部 `src/` 文件、未归属 = 0，并声明自己是 `AC-BOUND-*` 的输入）。本 change **MUST NOT 另立一套判据**；若实施者认为 §4.7 某一行错了，走控制仓 change 改 §4.7，不得在 `boundaries/module-ownership.json` 里单方面偏离。本条原稿写的「三边先填 255 文件（49/133/73）」判据**已作废**：其中 `config/`→`api`（49）把 §4.6.8 判归 automation 的 5 个限频配置文件一并塞给了 api。
<!-- aidcp-cloud 071252c ownership-rules.json 每条规则的 basis 字段逐条标章节号（§4.6.1–§4.6.8 / §4.7 / §7.2 判据三）；AC-BOUND-01 断言文件级清单必须是该规则表的机械展开，绕过规则表直接改清单即失败 -->
- [x] 1.3 逐条改正原稿与 §4.7 冲突的 7 处（本条替代原「63 个无归属文件默认落点」清单——该批文件已在 §4.7 内完成分配）：① `src/feishu/`（15）→**`api`**（§4.6.2 裁决，非 automation）；② `src/metrics/`（2）→**`content`**（§4.6.6，非 api）；③ `src/alerts/`（2）→**`automation`**（§5.1「告警表 owner = automation、api MUST NOT UPDATE」，非 api）；④ `src/config/`（30）→**25 归 api / 5 归 automation**（§4.6.8，非整目录归 api）；⑤ `src/onboarding/`（2）→**1 api / 1 content**（状态表归 api、创作桥接归 content，非整体 api）；⑥ `src/index.ts`→**`composition`**（非 api）；⑦ `src/cli/`（2）→**1 api（`test-feishu.ts`）/ 1 automation（`trigger-like.ts`）**，§4.7 已逐文件点名，非 `composition`。
<!-- aidcp-cloud 071252c 七处逐条落地。实测层分布 api 91 / content 80 / automation 146 / kernel 4 / composition 2，与 §4.7 基线（api 91 / content 78 / automation 146 / kernel 4 / composition 2）之差恰为基线 sha 之后新增的 2 个 publish-agent 文件 -->
- [x] 1.4 `cache/`（11 文件 2949 行）逐文件归属**直接抄 §4.7 的 `src/cache/` 逐文件表**（api 2 / content 2 / automation 6 / kernel 1）。原稿四处与之相反、MUST 改正：`notification-contact-store.ts` 与 `bot-chat-store.ts` 归 **`api`**（原稿写 automation）、`valuable-comment-store.ts` 归 **`automation`**（原稿写 content）、`group-route-store.ts` 归 `automation`（与原稿一致）。`index.ts` 归 `automation`。
<!-- aidcp-cloud 071252c 逐文件抄 §4.7，四处反向已改正，实测 api 2 / content 2 / automation 6 / kernel 1 -->
- [x] 1.5 在归属表头部固定 `composition` 成员白名单（起手仅 `src/server.ts`、`src/cli/**`），并写明规则：`composition` MAY 导入任何层，任何层 MUST NOT 导入 `composition`，白名单外的文件不得声明为 `composition`。
<!-- aidcp-cloud 071252c 白名单在 ownership-rules.json 的 compositionWhitelist；**按 §4.7 改为 src/server.ts + src/index.ts**（§4.7 把 src/cli/ 两个文件逐个点名为 api / automation，不属 composition）。规则由 AC-BOUND-02 与 classifyEdge 机械执行：指向 composition 的边判 forbidden、无豁免通道 -->

## 2. aidcp-cloud — 共享内核层 kernel 的裁定与准入

- [x] 2.1 **kernel 花名册以定稿 §4.7 kernel 段为唯一权威**：本基线上 kernel 恰好 4 个文件 251 行（`src/time/shanghai-day.ts`、`src/time/source-published-time.ts`、`src/deployment-target.ts`、`src/cache/pg-config.ts`）。原稿名单 MUST 按下列三条改：① **删除 `src/comm/protocol.ts`**——§10.9 已终局裁决「MUST 归 `aidcp-automation` 独占、MUST NOT 放进 kernel」，MUST NOT 再提案；② `src/soul/types.ts`、`src/panel/types.ts`、`src/feishu/types.ts` 的「纯类型段」与 `src/platform/registry.ts` 的「纯数据声明段」**不能按段落进 kernel**——§4.0 第 1 条是文件级单一归属、不承认「半个文件归 kernel」；要进必须先把该段**析出为独立新文件**再对新文件判 kernel，并在同一批改动里同步更新 §4.7 的目录行、kernel 计数与合计行；③ `src/event-bus/types.ts`（`RoleName` 所在）与 `src/platform/registry.ts` 纯数据段是否按②析出，是 §4.7 明列的**两处待裁决项**，MUST 在本步一次判定并回写 §4.7，MUST NOT 在本 change 与 §4.7 各判一次。
<!-- aidcp-cloud 071252c 花名册 = §4.7 的 4 文件，protocol.ts 已删除并进 boundaries/kernel-non-members.json 拒入清单（AC-BOUND-03 断言拒入清单内文件不得标 kernel）。两处待裁决项一次判定：event-bus/types.ts 与 platform/registry.ts **均不析出、整体维持 automation**，理由三条写在 kernel-non-members.json。§4.7 回写属控制仓文档改动，已写成 docpatch P1 交主控套用。2026-07-23 主控套用 docpatch P1/P2/P3 + R1/R4：§4.7 kernel 段「两处待裁决项」bullet 改为「均不析出」裁决结论；目录级聚合行点名 src/agents/ 两文件（persona-auto-fill.ts 136 + persona-format.ts 16 = 152）；合计表下新增「基线 sha 之后的增量」note（350 文件 / api 101 content 80 automation 163；新目录 src/schema 12、src/db 1 及四个两可文件标「待定稿裁决」）。 -->
- [x] 2.2 明确记录**不进 kernel**的三边共导文件及其原因（有 SQL / 有业务判定 / 有进程内活状态）：`src/cache/curated-content-store.ts`、`src/client-auth/client-user-store.ts`、`src/config/content-schedule-store.ts`、`src/risk/session-limits.ts`、`src/risk/resume-limits.ts`、`src/soul/writing-language.ts`、`src/event-bus/index.ts`。它们的三边共导进豁免清单等待削减，不得靠改归属绕过。
<!-- aidcp-cloud 071252c 七个文件逐条写进 boundaries/kernel-non-members.json 的 rejected 段（另加 protocol.ts / event-bus/types.ts / platform/registry.ts / platform/index.ts / agents/base-role.ts）；AC-BOUND-03 断言这些路径仍存在且归属层不是 kernel -->
- [x] 2.3 把 `DEFAULT_PG_CONFIG`（现在 `src/cache/pg-anchor-cache.ts:33`）移到 `src/cache/pg-config.ts`，反转现有依赖方向（该文件 `:2` 今天反向 import 回 `pg-anchor-cache.js`），并把 32 个引用方改为从 `pg-config.js` 取。行为不得改变：环境变量优先级与默认值逐字保持。**不得**在本次改动里把源码兜底口令写进新文件——它应在后续独立 change 改为纯配置读取。
<!-- PARTIAL(aidcp-cloud 071252c)：已完成「搬迁 + 反转依赖方向」这一半——DEFAULT_PG_CONFIG 整体移入 pg-config.ts，pg-anchor-cache.ts 改为再导出，31 个引用方零改动、取值逐字不变、typecheck 与全量测试全绿。这一半是 kernel 准入的硬前置（搬迁前 pg-config.ts 反向 import 业务层，AC-BOUND-03 当天即红）。 -->
<!-- BLOCKED（未完成的两半）：① 「把 32 个引用方改为从 pg-config.js 取」未做——那是削减动作而非门禁前置，且引用方含 src/risk/pg-risk-store.ts，属本轮明令不得触碰的范围；这些边已按「先冻结后削减」进 import 豁免清单。② 「不得把源码兜底口令写进新文件」这条与「移到 pg-config.ts」+「默认值逐字保持」三者互斥：口令是 DEFAULT_PG_CONFIG 的一个字段，移过去必然带上，不带就改变行为。取舍是**整体搬迁、不复制**（全仓出现点仍恰好 1 处，只是换了文件），并按定稿 §6.5.6 把「删除明文兜底、改为纯配置读取」留给它已登记的拆分前置 change——搬到 kernel 之后它反而收敛到唯一一处，那个 change 更好做。该偏离已在最终报告与 docpatch 里登记。 -->
<!-- 2026-08-05 复核后勾选：当时挂 BLOCKED 的那一半**已由后续 change 完成**（登记比代码旧的又一例）。
     实读现状：`DEFAULT_PG_CONFIG` 定义在 `src/kernel/pg-config.ts`、无任何反向 import；
     **48 个文件直接从 `kernel/pg-config.js` 取**；`src/cache/pg-anchor-cache.ts` 已**不再再导出**它
     （grep `export.*DEFAULT_PG_CONFIG` 在该文件里零命中，只剩三处说明归属的注释）。
     第二半「不得把源码兜底口令写进新文件」维持原偏离结论（整体搬迁、全仓仍恰好 1 处），
     已按定稿 §6.5.6 留给那个独立 change，不因本次勾选而消失。 -->
- [ ] 2.4 收窄 `src/agents/base-role.ts` 的两处具体实现导入（`:8` 的 `../event-bus/index.js`、`:11` 的 `../llm/qwen.js`），改为 kernel 内的接口声明；照仓内既有弱接口范式（`src/agents/base-role.ts:14` 的 `RoleLlm`）。改完 `base-role.ts` 方可标为 `kernel`。
<!-- BLOCKED：与定稿冲突，按「定稿优先」不做。§4.7 kernel 段写死「本基线 sha 上恰好 4 文件 251 行，这是 kernel 的全量名单」，base-role.ts 不在其中；且 §4.7 规定新增 kernel 成员 MUST 先走「准入 + 析出为独立新文件 + 同批回写 §4.7 目录行与计数」三条通道。本 change 无权单方面把第 5 个文件塞进花名册。base-role.ts 已登记在 boundaries/kernel-non-members.json，注明「是否进 kernel 由后续控制仓 change 改 §4.7 后再定」。 -->
<!-- 2026-08-05 复核：**两处只收窄了一处，本项维持不勾**（同批的 2.3 / 2.6 已因现实推进而勾上，
     本项没有，别顺手一起划）。实读 `src/agents/base-role.ts` 现在的全部 import：
     · `../llm/qwen.js` 那处**已收窄**——改成 kernel 的 `TextCompletionPort`（`kernel/llm-contract.js`）✓
     · `../event-bus/index.js` 那处**仍在**（`import type { EventBus }`），kernel 里也没有对应接口
       （只有 `event-fanout-port.ts` / `panel-event-delivery-port.ts`，都不是 EventBus 本身）✗
     `base-role.ts` 至今仍具名留在 kernel 拒入名册里，与「改完方可标为 kernel」的验收口径一致。
     ⚠️ 只按「import 行数变少了」判这项已做，会得出相反结论——本次差点就那么判了。 -->
- [x] 2.5 在门禁里实现 kernel 准入断言：kernel 成员 MUST NOT 含 `INSERT`/`UPDATE`/`DELETE`/`CREATE TABLE`/`SELECT` 字面量、MUST NOT 注册 HTTP 路由、MUST NOT 调用 LLM 或供应商 HTTP、MUST NOT 含模块级可变单例或定时器或连接池、MUST NOT 导入 `api`/`content`/`automation`/`composition` 任一层。任一条不满足即失败并指名文件。
<!-- aidcp-cloud 071252c AC-BOUND-03：四类正则逐条断言 + 花名册比对 + 拒入清单比对；反向依赖由 classifyEdge 判 forbidden（无豁免通道），实测搬迁前 kernel->automation 1 条、搬迁后 0 条 -->
<!-- 缺陷修复 aidcp-cloud 31dfab2（2026-07-23 审计坐实）：「模块级可变单例」那一条原只锚行首裸 let/var，`export let …` 以 export 开头故整类漏过（已注入 `export let` 到 kernel 成员验证过：当时 AC-BOUND-03 仍绿）——而导出型可变单例正是最容易被其它层写坏的一种。现改为 `^(?:export\s+)?(?:let|var)\s`，并补一条模块级 `const x = new Map()/new Set()` 的可变容器检查；「SQL 字面量」一条改为复用扫描器的 UPDATE 语法源串（原来同样对带别名的 UPDATE 失明）。三条机械回归写在 module-boundary.test.ts 的「kernel 准入判据保真自检（非 AC 编号）」里（export/裸形态必命中、不可变导出与函数内局部量必不误判、带别名 UPDATE 必命中） -->
- [x] 2.6 建 `src/kernel/` 目录并把已裁定成员物理搬迁过去（分批，每批同批削减豁免清单）。本步在 1、3 两节门禁生效之后做。**搬迁范围 MUST 排除 `src/comm/protocol.ts`**（§10.9 终局裁决）；只删任务 5.1 的该项而不改本步与 2.1，`protocol.ts` 仍会经这两步进 kernel，§10.9 点名要消除的 6 处 type-only 依赖会就地合法化。
<!-- BLOCKED：与定稿冲突，按「定稿优先」不做。§4.7 的 kernel 花名册用的就是四个文件的**现有路径**（src/time/shanghai-day.ts、src/time/source-published-time.ts、src/deployment-target.ts、src/cache/pg-config.ts），物理搬到 src/kernel/ 会让 §4.7 那四行路径逐条失效，属「两处各判一次」。另两条理由：搬迁不改变任何门禁判定（归属层已是 kernel，方向规则按层不按路径），且本 change 是 5 条并行流里最后集成的一条，动路径会与另 4 条的 rebase 全面冲突。搬迁范围已排除 protocol.ts 的要求由 boundaries/kernel-non-members.json + AC-BOUND-03 机械保证。 -->
<!-- 2026-08-05 复核后勾选：当时挡住本步的前提（§4.7 花名册只有 4 个文件、搬路径会让那四行失效）
     **已被后续 change 整体取代**——现在 `src/kernel/` 里有 **109 个文件**、名册 `kernelRoster.members` **112 条**，
     物理搬迁事实上早已完成，只是没人回来勾。
     本步那条硬约束逐条复验仍成立：`src/kernel/protocol.ts` **不存在**，且 `comm/protocol.ts`
     仍具名留在 `boundaries/kernel-non-members.json` 的拒入段里（AC-BOUND-03 会查）。 -->

## 3. aidcp-cloud — 导入方向门禁（AC-BOUND-*）

- [x] 3.1 新建扫描器 `test/acceptance/helpers/boundary-scan.ts`：递归列出 `src/**/*.ts`、解析静态 `import`/`export ... from` 与动态 `import()`（现有 3 处）、把相对说明符的 `.js` 后缀映射回 `.ts` 并解析到实文件（含 `index.ts` 目录解析）。零新依赖，只用 `node:fs` / `node:path`。范式照抄 `test/server-startup-order.test.ts:5-10` 与 `aidcp-edge/test/electron/interaction-ipc-security.test.ts:1-11`。
<!-- aidcp-cloud 071252c 零新依赖（package.json 未动）；覆盖静态 import / export…from / 动态 import() / 内联 import('...').Type / 副作用 import / require 兜底 -->
- [x] 3.2 扫描器 MUST 在解析不到实文件时抛错并列出说明符，MUST NOT 静默跳过；MUST 在扫描文件数与归属表条目数不等时抛错。
<!-- aidcp-cloud 071252c 前者由 AC-BOUND-04 首条断言，后者由 AC-BOUND-01。两条都已人工验证会红（见 7.4 / 7.5） -->
<!-- 缺陷修复 aidcp-cloud 31dfab2（2026-07-23 审计坐实）：还有第三类静默跳过没堵上——两族门禁都会把「端点查不到归属」的边 / 写入点直接丢弃（module-boundary.test.ts 的 `if (!from || !to) return []`、table-ownership.test.ts 的 `if (!owner || !writerLayer) continue`），与扫描器文件头自述的诚实契约相反。可达形态实测存在：`../../scripts/x.js` 会被解析到 src/ 之外确实存在的 .ts（如 scripts/run-migration.ts），而那正是最该报警的越界。现两处都改为收集后断言（AC-BOUND-01 / AC-OWN-01 各一条，消息指名 file/edge）；AC-OWN 侧同时自持这条断言，去掉对另一测试文件里 AC-BOUND-01 的隐式依赖。已注入验证：向 src/panel/retention-sweeper.ts 加 `import "../../scripts/run-migration.js"` → AC-BOUND-01 当场红，报「src/panel/retention-sweeper.ts -> scripts/run-migration.ts（无归属）」 -->
- [x] 3.3 新建 `test/acceptance/module-boundary.test.ts`，用例编号 `AC-BOUND-01..06`（**该编号即定稿 §12「两族门禁」的族内编号，两边逐条对齐，MUST NOT 出现同名不同义**）：01 归属表全覆盖且无孤儿条目；02 层枚举合法且 `composition` 成员在白名单内；03 kernel 准入断言（第 2.5 项）；04 无未豁免的跨边界 import；05 无失效（源码中已不存在）的豁免条目；06 `entries.length <= frozenTotal`，且上调 `frozenTotal` 必须带合规的 `raises[]`（字段要求见 3.4）。另加一条断言：`eliminatedBy` 为空的条目数 MUST 单调不增。
<!-- aidcp-cloud 071252c 六条逐条存在、未压成 2 个 ID；棘轮上界基准用不可变的 seedTotal / seedUnplanned，AC-BOUND-06 同时断言这两条 -->
- [x] 3.4 新建 `boundaries/import-exemptions.json`：头部含 `frozenTotal`、`recordedAt`、`raises[]`，条目为 `{ "from": "...", "to": "...", "reason": "", "eliminatedBy": null }`。**`eliminatedBy` 是第四个必填字段**（值为控制仓 openspec change 名），承载定稿 §12 棘轮规则的「计划消除它的 change 名」与 §10.9 的「每条各挂一个消除它的 change」；seed 期允许为 `null`，但 MUST 在本 change 的 tasks 里登记补齐时限，且为 `null` 的条目数只减不增。**`raises[]` 的每个元素 MUST 含 `{ amount, approvedByChange, eliminateBy }` 三个字段**：`approvedByChange` MUST 是控制仓一个已存在的 openspec change 名，`eliminateBy` MUST 是具体日期；三者任一缺失即门禁失败（与定稿 §12「例外通道（唯一）」逐字对齐）。以 record 模式（如 `AIDCP_BOUNDARY_RECORD=1 npx tsx test/acceptance/module-boundary.test.ts`）一次性生成，然后提交。生成后核对量级：三边之间应约 217 条；实测值与预期偏差超过 10% 时先查扫描器再提交。**原稿的 462 条上界与「63 个文件」口径已随 1.2–1.4 改判作废，MUST 以实施当天重跑结果为准。**
<!-- aidcp-cloud 071252c record 模式落在 `npx tsx test/acceptance/helpers/boundary-record.ts seed`（不用环境变量开关，避免测试文件带写盘副作用）。实测 257 条，非预期的 217。**偏差已查证不是扫描器问题**：217 是 design.md 旧判据下的数字，§4.7 把 feishu/ panel/ config/ 等大块判给 api，跨边界配对随之改变。三条独立佐证：① §10.9 说「按 §4.7 / §4.6.8 归属重算后属 api/content 侧的边云协议 type-only 依赖共 6 处」，实测恰好 6 条且逐个文件对上；② §10.9 点名「不构成违规」的 3 处（pacing-config-store.ts / pacing-config-facade.ts / pg-anchor-cache.ts）确实未出现在清单里；③ 层分布与 §4.7 合计行逐栏吻合 -->
<!-- eliminatedBy 补齐时限：seed 时 257 条全为 null（seedUnplanned=257，门禁断言只减不增）。§10.9 点名的 6 条已在 note 字段标出「MUST 在 §12 阶段 1 内补齐」，其余随各自的削减 change 逐批补齐 -->
<!-- 重新 seed aidcp-cloud e8c0e04（2026-07-23 rebase 后）：257 → 274 条，seedTotal / seedUnplanned / frozenTotal 同步重置为 274，raises[] 仍为空。**这不是「seed 之后追加豁免」**——定稿 §12 写死「清单 MUST 在阶段 1 的第一个 change 里用扫描器一次性 seed 全量既存违规」，本 change 就是那个 change、尚未归档，棘轮尚未开始计数，故 seed 基线随合并基线移动是 seed 本身而非松动。棘轮自本 change 归档起生效，此后 --reseed MUST NOT 再用。新增 17 条按来源三簇，**逐条**手写了 reason（点名 change 与 commit）与 note（消除动作）：risk-state-cross-process-integrity 1 条（account-store 引风控层归属占位结果类型）、config-mirror-cross-process-invalidation 13 条（新鲜度查询口 3 + 统一停手判据 3 + 人设三态取值口 3 + 四类限频配置 store 递增镜像版本表 4）、publish-approval-signal-to-database 3 条（环境行锁 1 + 授权存储取 DEFAULT_PG_CONFIG 兜底 1 + 下发器直读授权存储 1） -->
<!-- 第二次重新 seed aidcp-cloud 89c286d（2026-07-23，cloud-schema-migration-executor land 后）：274 → 295 条，seedTotal / seedUnplanned / frozenTotal 同步重置为 295，raises[] 仍为空；表侧 12 条一条未动。**先试过不 reseed 的常规棘轮路径，实测走不通**：`refresh --raise=cloud-service-boundary-gates:21:<日期>` 确实退出 0 并把 frozenTotal 抬到 295，但 AC-BOUND-06 的第二条断言当场红——「未挂消除 change 的条目数 295 高于 seed 值 274」，要绿就得给 21 条新条目各填一个 eliminatedBy，而本轮既无承接消除的控制仓 change、也无定稿给出的消除时限，`--raise` 的三字段里那个日期同样无处可取，填任何一个都是编造事实。故按 seedWindow.open 仍为 true 的设计目的移动 seed 基线，理由全文（含这段 --raise 实测）写进两份清单的 seedBasis。新增 21 条来源高度集中：20 条指向 src/schema/schema-capability.ts（api 16 + content 4）、1 条指向 src/schema/schema-name.ts（content），共享同一条 §4.7 消除路径，已逐条写进 note 并明写「MUST NOT 当成 21 处各自独立、需要各自消除的架构违规」 -->
<!-- 缺陷修复 aidcp-cloud 620c0db（2026-07-23 第二轮审计坐实）：清单头部还有第五个字段 `seedBasis`（seed 基线为何是 274 / 12 的唯一在仓记录），而**默认棘轮路径的 refresh 会把它静默删掉**——那条返回路径从零重建 list 对象、只搬 seedTotal / seedUnplanned / frozenTotal / recordedAt / raises / entries 六个字段，seedBasis 只在 --reseed 分支被保留。实测：在完全干净的工作区跑一次 `npm run boundaries:refresh`（报「新增 0 / 删除 0」、退出 0），两份清单唯一的改动就是整段删除 seedBasis。根因是它靠 `as` 强转写入、ExemptionList<T> 里根本没声明，typecheck 与全部用例都无感。现已在类型里正式声明 `seedBasis?: string`，两条返回路径都改为 `{ ...list, … }` 展开保留未知字段，并给 AC-BOUND-06 / AC-OWN-05 各加一条「MUST 携带非空 seedBasis」的断言。复跑 refresh 后 `git status --porcelain` 为空（四份生成物逐字节不变）——「重跑幂等」这条现在才真正成立 -->
<!-- 未做的一半（如实登记）：新增 17 条的 eliminatedBy 仍为 null。原因是控制仓今天**没有**一个真实存在的 change 承接这些消除动作，填任何名字都是假承诺；曾在验证过程中误填过 cloud-service-boundary-gates（本 change 并不消除它们），已当场清回 null。消除动作写在每条的 note 字段里（§5.1 / §12 阶段 1 退出判据各自点名的收口路径）。补齐 eliminatedBy 属 §12 阶段 1 排期时的动作 -->
- [x] 3.5 允许方向白名单写进测试源码（不进 JSON，改它必须改测试文件）：任何层 MAY→`kernel`；`composition` MAY→任何层；其余跨层方向一律需要豁免条目。
<!-- aidcp-cloud 071252c classifyEdge() 在 test/acceptance/helpers/boundary-scan.ts，不进任何 JSON。另明确两条无豁免通道的方向：任何层→composition、kernel→业务层 -->
- [x] 3.6 门禁 MUST 在输出里打印机器可读计数：按 `from→to` 方向分解的条数、总条数、`frozenTotal`、以及与 `frozenTotal` 的差值。
<!-- aidcp-cloud 071252c af05b3c 每次运行打印单行 `AC-BOUND metrics {...}`，含 sourceFiles / ownershipEntries / crossBoundaryEdges / byDirection / involvingContent / exemptionEntries / frozenTotal / delta / unplanned。involvingContent（实测 112）是 6.3 阶段 3 准入阈值的唯一取值来源 -->
<!-- rebase 后实测 aidcp-cloud e8c0e04：{"sourceFiles":338,"ownershipEntries":338,"crossBoundaryEdges":274,"byDirection":{"api->automation":85,"automation->content":28,"automation->api":77,"content->automation":27,"content->api":23,"api->content":34},"involvingContent":112,"exemptionEntries":274,"frozenTotal":274,"delta":0,"unplanned":274}。**involvingContent 仍是 112**（17 条新增全在 api↔automation 之间），故 6.3 的阶段 3 准入里只有 import frozenTotal 阈值随 seed 值变（145 → 162 = 274-112），另两条不变 -->

## 4. aidcp-cloud — 表写入归属门禁（AC-OWN-*）

- [x] 4.1 新建 `boundaries/table-ownership.json`：表名→属主层的全量映射。**属主判定以定稿 §5.1「单一写入者」表为输入，MUST NOT 另立判据**。表全集取 `src/**/*.ts` 与 `migrations/*.sql` 里 `CREATE TABLE` 的并集。未登记的表出现在扫描结果里即失败。**计数口径 MUST 与同批 change `cloud-schema-migration-executor` 统一**：本稿原写「84 张 / 59 张由 `src/` 建」，该 change 的 `proposal.md` 写「并集 83 张 / 存储自建 58 张」，两者只要差一张，本门禁的「未登记的表出现即失败」当天就会红。MUST 由两个 change 中**先动工的一个**跑一次统一口径脚本（distinct 表名；`src/**/*.ts` 的 `CREATE TABLE IF NOT EXISTS` ∪ `migrations/*.sql` 的 `CREATE TABLE`；先剥 `--` 与 `/* */` 注释），把结果同时回写两处，并把脚本命令写进 tasks。
<!-- aidcp-cloud 071252c 84 张表全量登记，每条 basis 写明所依据的 §5.1 行；§5.1 未具名的以「§5.1 未具名」标出并已写进 docpatch P5 请求回写 -->
<!-- 属主裁定二（aidcp-cloud 89c286d）：cloud-schema-migration-executor land 后表全集 89 → 90，新增的唯一一张是迁移账本 `schema_migrations`，判 owner=automation 并标【待定稿裁决】（§5.1 未具名；唯一写入方是部署期执行器 scripts/migrate.ts，三服务运行时只读；拆库后归属随 §5.4.7 子目标 B 的数据库角色划分定）。**MUST NOT 写进 exception-tables.json**——那份清单条目数只减不增、新增须控制仓 change 批准，且其两条现有条目的例外理由（多写者是设计前提 / owner 是外部探针）本表都不符合。请求回写 §5.1 见 docpatch R5。注：census 的 migrations 侧计数 65 → 90 是该 change 新增的合并基线迁移文件把既有表一并 CREATE TABLE 了，**不是新表**，表全集只 +1 -->
<!-- 数字修正（原写「34 张」是错值，与产出清单对不上；已按 table-ownership.json 实数改正，docpatch P5 同步改并写明口径）：口径一＝basis 标「§5.1 未具名」的条目 **22 张**；口径二＝basis 完全不引 §5.1 的另 **2 张**（first_post_onboarding 依 §4.7、group_comment_attempts 为 migrations/0036 已 RENAME 的历史表名），故「无具名 §5.1 依据」合计 **24 张**。第三种口径（表名字面出现在定稿 §5.1 正文里）实测 22 出现 / 62 未出现，与前两种都不等——请求回写 §5.1 时 MUST 连口径一起写，否则无法核对。核对命令：`node -e "const j=require('./boundaries/table-ownership.json');console.log(j.tables.filter(t=>/未具名/.test(t.basis)).length, j.tables.filter(t=>!/§5\.1/.test(t.basis)).length)"` -->
<!-- 统一口径脚本命令：`cd ../aidcp-cloud && npx tsx test/acceptance/helpers/boundary-record.ts census`。于 aidcp-cloud@313eba2 实测：并集 **84 张**（src 自建 59 ∪ migrations 建 60）；src 内 CREATE TABLE 文本命中 **77 处** / 去注释后生效 **59 处** / 分布在 **35 个源文件**。与 cloud-schema-migration-executor 的「83 / 58」差的一张是基线 sha 之后新增的 publish_draft_refinement_jobs，非口径分歧。回写两处的请求已写进 docpatch P6（§17 第 8 项） -->
<!-- 口径迁移 aidcp-cloud e8c0e04（2026-07-23 rebase 后，命令改为 `cd ../aidcp-cloud && npm run boundaries:census`）：并集 **89 张**（src 自建 **64** ∪ migrations 建 **65**）；src 内 CREATE TABLE 文本命中 **83 处** / 去注释后生效 **64 处** / 分布在 **37 个源文件**。新增 5 张表逐张按 §5.1 登记属主：publish_approval_decision（§5.1 **具名** api 单写）/ publish_approval_outbox / config_mirror_version / config_mirror_stale_refusal → api；risk_counter_outbox → automation。四张标「§5.1 未具名」并请求回写（docpatch R1(c)）。**注意 cloud-schema-migration-executor 落地后本口径会再变一次**：它会新增 src/schema/** 若干文件（src/schema/ 无目录规则 → 生成器会报「待人工裁决」，MUST 先按 §4.7 裁定）并把运行时 DDL 从各 store 删干净（srcCreatedTables 与建表点三元组会大幅下降），届时 MUST 重跑 `npm run boundaries:refresh` 并把新口径回写本条与 docpatch R0 -->
- [x] 4.1b **两张运维表 `service_metrics` / `service_probe` 不进豁免清单**：它们是定稿 §5.1 具名的「设计内永久例外」（多写者计数表 / 探针独占表），到方案阶段 2 才建，其条目必然产生在本 change 一次性 seed 之后，且按设计无消除时限。MUST 单列为一份「例外表清单」文件，不占豁免清单条目、不参与棘轮计数（依据：定稿 §12「例外表清单」）；否则实施者会撞上「加条目违反棘轮、不加条目 `AC-OWN-02`/`03` 判违规」的死结。
<!-- aidcp-cloud 071252c boundaries/exception-tables.json；这两张表今天还不存在，门禁把它们当已登记标识符（不判孤儿、不判未登记），写入判定直接跳过、不产生豁免条目。两条静态判不了的不变量（每行 svc 等于写入方自身、探针无业务表写权限）已在文件里写明须人工与 GRANT 补位 -->
- [x] 4.2 扫描器新增 SQL 字面量扫描：`INSERT INTO <t>` / `UPDATE <t>` / `DELETE FROM <t>`（DML）与 `CREATE TABLE [IF NOT EXISTS] <t>` / `ALTER TABLE <t>`（DDL）。MUST 先剥掉 `--` 行注释与 `/* */` 块注释；MUST 对已知误命中形态给出显式排除规则（实测假阳性来源：`UPDATE ... SET` 后的列名、`skip`、`of`、`resolved_at`、`alerts` 等标识符碰撞）；MUST 在命中一个不在表全集里的标识符时失败并报出，MUST NOT 静默跳过。
<!-- aidcp-cloud 071252c 剥注释两步：TS 的 // 与 /* */（// 前紧邻 : 的不剥，护住 URL），再剥 SQL 的 -- （**显式规则**：只有「行首或空白 + -- + 空白或行尾」才算，故 i-- / --i 不受影响）。假阳性用**语法锚定**消除而非跳过名单：UPDATE 分支必须带 SET，`DO UPDATE SET` / `FOR UPDATE SKIP LOCKED` / `FOR UPDATE OF` 三类实测假阳性天然不命中，跳过名单为空。未登记标识符必失败（已人工验证，见 7.4） -->
<!-- 缺陷修复 aidcp-cloud 31dfab2（2026-07-23 审计坐实的 blocker）：**上一条对 UPDATE 分支的描述当时不成立**——语法锚定写成了「表名后紧跟 SET」，对本仓主流的 `UPDATE <表> <别名> SET` 形态整类失明（实测 14 处 / 6 文件不可见），门禁从第一天起就对这类 DML 报「无违规」而实为「没看见」，违反红线「MUST NOT 静默假成功」。现别名段改为可选（`UPDATE_TABLE_PATTERN_SOURCE`，另加 `(?<!\bDO\s)` / `(?<!\bFOR\s)` 双保险），三类假阳性仍不命中。实测 writeSites 229→231（新增两处均为同层写入，crossLayerWrites 仍 12、豁免清单与 frozenTotal 不变）。**7.3 的人工负向验证当时只覆盖了会命中的无别名写法**，现补机械回归：table-ownership.test.ts 新增「SQL 扫描器保真自检（非 AC 编号）」三条（别名 / AS 别名 / ONLY+public. / 换行形态必命中；三类假阳性必不命中；假阳性与真写入同段时只取真写入），并已重跑带别名的注入负向验证（api 层注入 `UPDATE risk_state r SET …` → AC-OWN-02 当场红） -->
<!-- 额外落地（定稿 §12 要求「无法静态判定的动态拼接 SQL MUST 判为失败，MUST NOT 跳过」）：新增 boundaries/dynamic-sql-resolutions.json 作为该失败的唯一解除通道。全仓实测 1 处（src/interactions/reply-config-store.ts 的 `INSERT INTO ${table}`，插值取自同文件的三元素字面量数组），已逐处具名登记；未登记的动态拼接与失效登记条目都判失败（AC-OWN-01） -->
- [x] 4.3 新建 `test/acceptance/table-ownership.test.ts`，用例编号 `AC-OWN-01..05`（**该编号即定稿 §12「两族门禁」的族内编号，两边逐条对齐**）：01 表归属表覆盖全部已知表且无孤儿；02 无未豁免的跨层 DML 写入；03 无未豁免的跨层 DDL（建表 / 改表）；04 无失效豁免条目；05 `frozenTotal` 棘轮（同 3.3-06）。另加一条断言：`eliminatedBy` 为空的条目数 MUST 单调不增。
<!-- aidcp-cloud 071252c 五条逐条存在；AC-OWN-05 同时断言 seedTotal 上界与 seedUnplanned 单调不增。豁免按 {表, 文件, 操作} 三元组匹配——已豁免 delete 的条目挡不住新加的 insert -->
<!-- 缺陷修复 aidcp-cloud 620c0db（2026-07-23 第二轮审计坐实）：**上一条只对门禁一侧成立、对生成器一侧不成立**。门禁确实按三元组匹配，但清单的**条目粒度**是 (表, 文件) 对 + ops[] 数组，棘轮的键因此少了「操作」这一维：已豁免的对上新增一个操作时条目数不变（needed 恒为 0），`npm run boundaries:refresh` 在默认棘轮模式下会自己把 ops 数组拓宽写回文件并**退出 0**，只在 census 输出里混一行提示；带着这份被拓宽的清单跑门禁，AC-OWN-03「无未豁免的跨层 DDL」全绿。现把条目粒度改成逐个三元组（ops[] 字段取消，10 条 → 12 条），门禁匹配用的键与棘轮用的键成为同一个键。注入验证：向已豁免的 (interaction_runtime_controls, src/client-auth/client-user-store.ts) 对追加 `ALTER TABLE … ADD COLUMN` → refresh 退出 1 并列出该三元组；绕过 refresh 直接跑门禁 → AC-OWN-03 当场红（ddlViolations 0→1）。机械回归见 table-ownership.test.ts 的「棘轮键保真自检（非 AC 编号）」四条 -->
- [x] 4.4 新建 `boundaries/table-write-exemptions.json` 并以 record 模式生成；条目 schema 与 `raises[]` 字段要求同 3.4（含必填的 `eliminatedBy`）。核对起手应至少含实测的 5 处跨边界多写：`interaction_runtime_controls`、`interaction_auth_state`、`interaction_offboards`、`interaction_offboard_audit`（`src/client-auth/client-user-store.ts` 属 `api` × `src/interactions/interaction-store.ts` 属 `automation`）与 `first_post_onboarding`（`src/config/persona-store.ts:196-215` × `src/onboarding/first-post-onboarding-store.ts:26`）。
<!-- aidcp-cloud 071252c 实测 10 条（12 个 {表,文件,操作} 三元组）。点名的 5 处里前 4 处逐条命中；**first_post_onboarding 按 §4.7 不构成违规**——§4.7 把 src/config/persona-store.ts 与 src/onboarding/first-post-onboarding-store.ts 都判归 api，是同层双写。这与本 change design.md 的旧判据结论相反，按「定稿优先」采信 §4.7，并已在 table-ownership.json 的该表 basis 里写明 -->
<!-- 另 6 条为 §4.6.1 点名的跨 owner 单事务清理（interaction-store.ts 的 purgeDueOffboards 删 api 属主的 6 张配置面表），reason / note 逐条写明消除方式与 §12 阶段 1 退出判据的要求 -->
<!-- 粒度修正 aidcp-cloud 620c0db（2026-07-23）：清单条目由「(表, 文件) 对 + ops[] 数组」改为逐个 {表, 文件, 操作} 三元组，**10 条 → 12 条**，seedTotal / seedUnplanned / frozenTotal 同步 10 → 12。豁免的实际面一条未变（原来就是这 12 个三元组，见 071252c 那条注释里「10 条（12 个三元组）」的记法），改的只是棘轮的键；理由与前后对照写进该文件的 seedBasis。**同批把 4.1b 里两张运维表的口径也复核过一遍**：exception-tables.json 不受粒度影响，仍不占条目、不参与计数 -->
<!-- 缺陷修复 aidcp-cloud 31dfab2（2026-07-23 审计坐实）：定稿 §12「阶段 1 退出判据」点名 MUST 有明确结论的**五处**里，boundaries/README.md 的「门禁看不见什么」清单原来只登记了 client_environments 一处，漏了同形态的**跨域保留清理**——src/panel/retention-sweeper.ts（api）调用 riskStore.purgeCountersOlderThan（src/risk/pg-risk-store.ts，automation，表 risk_counters）、interactionFeedStore.purgeOlderThan（src/cache/interaction-feed-store.ts，automation，表 interaction_feed）、tokenUsageStore.purgeOlderThan（src/metrics/token-usage-store.ts，content，表 llm_token_usage），DELETE 语句全在属主一侧、由 api 侧驱动，正是 §12 门禁定义第 3 条第 ① 类天然失明形态，AC-OWN-02 永远不会红。现已补登记在 README 的失明清单与那三张表的 basis 里；五处的逐条结论（哪两处门禁看得见、哪两处看不见、first_post_onboarding 为何不构成违规）已写成 docpatch P16 请求回写定稿 §12，避免「门禁全绿即无违规」的误读 -->
- [x] 4.5 DDL 归属条目必须覆盖今天 34 个文件里的 76 处 `CREATE TABLE IF NOT EXISTS`。这一步只冻结、不修——取消 store 自建表属阶段 2 的迁移执行器工作，不在本 change。
<!-- aidcp-cloud 071252c 实测口径已更新为 77 文本命中 / 59 生效 / 35 文件（基线 sha 之后新增 draft-refinement.ts）。全部建表点都在属主层内，故 **DDL 侧豁免条目 = 0**；冻结靠 table-ownership.json 覆盖全部 84 张表 + AC-OWN-03 —— 此后任何非属主层的 CREATE TABLE / ALTER TABLE 当场失败。已人工验证 AC-OWN-01/02 会红（见 7.3 / 7.4） -->
- [x] 4.6 同层多写不判违规但仍须指定唯一属主层，逐条登记：`reply_templates` / `reply_rules` / `account_reply_profiles` / `interaction_reply_configs` / `interaction_reply_config_versions` / `interaction_audit_events` 六张表被 `src/interactions/interaction-store.ts` 与 `src/interactions/reply-config-store.ts` 各自写入，同属 `automation`。
<!-- aidcp-cloud 071252c 六张表已逐条指定唯一属主层（均为 api）。**但「同属 automation」这个前提按 §4.7 不成立**：§4.6.1 把 reply-config-store.ts 判归 api（配置存储与查询面 8 文件之一）、interaction-store.ts 判归 automation，故这六张是**跨层双写**，六条全部进豁免清单并挂上 §4.6.1 的消除方式。同层多写不判违规的规则本身已实现（属主层相同即跳过），实测 first_post_onboarding 正是这一类 -->

## 5. aidcp-cloud — 削减路径（先冻结，后削减）

- [x] 5.1 【反方向，收益最集中】原稿三个搬迁目标 MUST 按定稿裁决重排：**`src/comm/protocol.ts`（10 条）一项取消**——§10.9 终局裁决它归 `aidcp-automation` 独占、MUST NOT 进 kernel；`src/event-bus/types.ts`（46 条）与 `src/platform/index.ts`（13 条）两项的处置**随任务 2.1 对 §4.7「两处待裁决项」的定案而定**，定案前 MUST 视为未定。因此「一次性削掉 79 条里的 69 条」这个数字 MUST 按定案结果重算，MUST NOT 作为既定收益写进准入条件（连带影响见 6.3）。这一步不写业务代码，只改 import 路径与归属表，同批删除对应豁免条目。
<!-- aidcp-cloud 071252c 三项处置已定：protocol.ts 取消（§10.9）；event-bus/types.ts 与 platform/index.ts 按 2.1 判为不析出。**重算结果 = 削减 0 条**，故本步不产生 import 路径改动、不产生豁免条目删除。实测方向分解也已把原稿的「79 条」纠正为 content→automation **27 条**（其中 event-bus/types.ts 6 条、platform/index.ts 2 条、platform/registry.ts 1 条、protocol.ts 0 条——protocol.ts 的 6 条来自 api 侧）。「不作为既定收益写进准入条件」已落实：6.3 的阈值用的是实测 involvingContent=112，不含任何假定收益 -->
- [ ] 5.2 `src/platform/registry.ts` 的纯数据声明段随 `platform/index.ts` 进 kernel，再削 4 条；剩余 6 条（`comm/edge-task-lease-client.ts` 2、`event-bus/index.ts` 1、`risk/session-limits.ts` 1、`risk/resume-limits.ts` 1、`comm/preemption.ts` 1）保留豁免并在条目 `reason` 里写明属真实跨边界依赖。
<!-- BLOCKED：前半段已被 2.1 的裁决作废（registry.ts 纯数据段判为不析出），「再削 4 条」不成立。后半段的六个具名目标按 §4.7 归属实测也已失真：edge-task-lease-client.ts 与 comm/preemption.ts 的被导入条数为 0（没有 content 层文件导入它们），event-bus/index.ts 2 条、session-limits.ts 4 条、resume-limits.ts 1 条。这些边已全部在豁免清单里、reason 写明是实测既存跨边界依赖，但没有按原稿那份（已失真的）名单逐条加特写理由。正确的后续动作是：按实测的 content→automation 27 条重新分组、逐条挂消除 change，属独立削减 change 的范围。 -->
- [x] 5.3 【正方向，单点最纠缠】起一个**专门的独立 change** 处理 `src/orchestrator/role-dispatcher.ts`（3088 行）文件头对 40 个角色类的 import（`automation→content` 53 条里的 43 条）：引入 `RoleName → 角色工厂` 注册表，dispatcher 只依赖 kernel 里的角色基类接口，具体角色类由组合根 `src/server.ts` 注入。按 CLAUDE.md §7 标记为热点文件、需串行独占，不与其它 change 并行。
<!-- BLOCKED：本条要求「起一个专门的独立 change」，属控制仓建 change 的动作，本 session 只有本 change 目录的写权限，无权新建。**收益量级 MUST 重算**：按 §4.7 归属实测，role-dispatcher.ts 的 40 条 ../agents/ import 里只有 **4 条**跨边界（其余 36 条被导入的角色同属 automation），不是 43 条；automation→content 总数也是 28 条而非 53 条。该独立 change 本身仍成立（拆仓时 automation MUST 能在不 import content 角色的前提下启动），但排期依据要按 4 条写。重算请求已写进 docpatch P7。这 4 条已在豁免清单里逐条挂了说明性 note。2026-07-23 主控套用 docpatch P7：§12 两族门禁第 1 条已回写（role-dispatcher 跨边界 4 条、panel 8、customer→risk 1、首批 seed 295+12），评审报告 P12 的 43→4 同步。本任务「起一个专门的独立 change」的部分仍 BLOCKED（本 session 无权建控制仓 change）。 -->
<!-- 2026-08-05 结案，**改判为「不再需要那个独立 change」**，与 5.1「重算结果 = 削减 0 条」同形。
     用户本轮本来是要我把它摘出去单独立项的；先去代码里核，核出来的结论是立项等于造无用功。

     **判据一：那 36 条一条都不跨边界。** 逐个文件核过——`aidcp-automation/src/orchestrator/role-dispatcher.ts`
     文件头 36 条 `../agents/*` import，**对应的 36 个文件全部存在于 `aidcp-automation` 仓自己里**
     （逐条 `test -f src/agents/<name>.ts`，不在本仓的 = **0** 条）。同属主 import 不是边界问题。
     台账正文写的「53 条里的 43 条」是立项当日的估计，本条自己的上一段批注早在 2026-07-23 就把它
     **改判成 4 条**并同步进了 §12 门禁与评审报告 P12——正文没跟着改，于是这个已作废的数字又骗了一轮。

     **判据二：真正跨边界的那 4 条已经解决，且解法正是本条要的那个。**
     automation 侧现有 `ContentRoleFactoryOptionMap` / `ContentRoleName` / `makeContentRole<K>()`
     （`src/orchestrator/role-dispatcher.ts:237/244/2716`）——**就是本条要求的「RoleName → 角色工厂注册表 +
     具体角色类由组装根注入」**，content 域的四个角色已按此走，dispatcher 不再直接 import 它们。

     **判据三：豁免棘轮已归零。** `boundaries/import-exemptions.json` 现在 `frozenTotal=0`、条目 0 条
     ⇒ 门禁口径下**一条跨属主 import 违规都不剩**，包括本条原本要消除的那些。

     ⇒ 本条的立项理由（「拆仓时 automation MUST 能在不 import content 角色的前提下启动」）**已达成**。
     剩下的「3000 行文件头有 36 个同属主 import」属代码整洁度，不是拆仓阻塞，按 YAGNI 不为它立 change。
     若日后确要做，判据要重写成「文件体量 / 可测性」，MUST NOT 再引用已作废的「43 条跨边界」。 -->
- [x] 5.4 每次削减 MUST 在同一提交里同步下调 `frozenTotal` 并删除失效条目（否则门禁的失效条目断言会直接失败）。**子仓 MUST NOT 在没有控制仓 change 批准的情况下上调 `frozenTotal`**：上调只走 3.4 定义的 `raises[]` 例外通道，且每个元素必须齐备 `amount` / `approvedByChange` / `eliminateBy` 三字段。
<!-- aidcp-cloud 071252c 纪律已机械化而非只写在文档里：AC-BOUND-05 / AC-OWN-04 判失效条目，AC-BOUND-06 / AC-OWN-05 判 frozenTotal 上界（基准是不可变的 seedTotal）与 raises[] 三字段齐备。已人工验证：只加条目不加 raises 时两条同时红（见 7.3 记录）。操作说明写在 boundaries/README.md -->
<!-- 缺陷修复 aidcp-cloud 620c0db（2026-07-23 第二轮审计坐实）：`--reseed`（拆掉整个棘轮的开关）此前**零机械守卫**——同一个 npm 入口、无必填参数、不校验 seed 窗口是否还开着，且会连带清空 raises[]（已批准上调及其消除时限的唯一记录）。实测：注入一条 content→automation import 后，默认 refresh 正确拒绝，但紧接着 `refresh --reseed`（连 README 写的 --seed-note 都不给）退出 0、seedTotal / frozenTotal 一起从 274 抬到 275、raises[] 被重置为 []，随后 AC-BOUND-06 全绿。现补四道机械门，任一不满足即 exit 1：① `boundaries/ownership-rules.json` 新增 `seedWindow.open` 必须为 true（缺省按已关闭处理，fail-safe）；② 必须给 `--seed-note=`；③ 清单已 seed 过时必须再加 `--i-am-reseeding-the-ratchet`；④ raises[] 非空时直接拒绝、要求先人工处置。四种拒绝形态逐条实测通过，「全标志齐备 + 窗口开着」时仍能正常 reseed。**归档本 change 时的强制动作：把 seedWindow.open 改成 false** —— 那一刻起 --reseed 一律拒绝，与 §12「棘轮自本 change 归档起开始计数」逐字对齐 -->
- [ ] 5.5 建立削减节奏约定并写进控制仓：每归档一批 change 至少削减 N 条豁免（N 由首批实测后确定），`role-dispatcher.ts` 那 43 条单列不计入常规配额。
<!-- BLOCKED：本条要求「写进控制仓」，属控制仓法条改动，本 session 不直接改控制仓 docs。已按首批实测（257 条 import + 10 条表写入）拟出具体节奏并写成 docpatch P15 交主控套用：每批清账 frozenTotal 至少降 12 条（≈seed 的 5%），role-dispatcher 那一簇（重算后 4 条）与表写入侧 10 条各自单列不计入常规配额。2026-07-23 主控套用 docpatch P15 + S1：§12 棘轮规则已加削减节奏（每批降 ≥12 条、seed 实测终值 295 import + 12 表写入）与「条目粒度 = 违规粒度」通则；表写入侧按 S1 记 12 条（三元组口径，非松动）。本任务「写进控制仓法条」的部分即由此落地。 -->

## 6. aidcp — 控制仓文档与阶段准入

> 本节全部是控制仓 `docs/` 的改动。5 条并行 change 都要动同一份定稿，本 session 按编排要求**不直接改文件**，改为把逐处精确编辑写进 docpatch 交主控串行套用：
> `/private/tmp/claude-501/-Users-baitianxing-codes-aidcp/f0ef76c1-69d8-483a-8df8-115c38a2f9d0/scratchpad/docpatch-cloud-service-boundary-gates.md`
> 因此以下各条在**套用前**一律保持未勾选。

- [x] 6.1 改写 `docs/cloud-service-decomposition-proposal.md` §6.4：禁令改为「禁止共享**包含业务逻辑**的公共包」，显式列出 `kernel` 例外、逐条写出准入条件（无 SQL / 无 HTTP 路由 / 无 LLM 与供应商调用 / 无进程内活状态 / 不反向依赖业务层），并写明 kernel 拆仓后由 `aidcp-automation` 单一拥有、以版本化包发布、其余两仓固定版本消费。
<!-- 2026-07-23 主控套用 docpatch P8：docs/cloud-service-decomposition-proposal.md §6.4 第 7 条改为「共享**包含业务逻辑**的公共包」，并在 §6.4 末尾新增 kernel 例外段（准入 5 条 + AC-BOUND-03/04 机械保证 + 版本化包发布 + protocol.ts 不援引）。 -->
- [x] 6.2 改写 §12 阶段 1 的条目顺序：把「模块导入和数据所有权检查」提到**首位**，并加一句「本项 MUST 先于任何边界重构落地」。
<!-- 2026-07-23 主控确认 docpatch P9：定稿 §12 阶段 1 开头已写「本阶段任务 MUST 按以下顺序执行，门禁先行…MUST NOT 排在本阶段末尾」，本条已满足、无编辑，标记完成。 -->
- [x] 6.3 在 §12 阶段 3 加入可判定的准入条件，直接引用门禁输出的计数（形如「`import-exemptions.frozenTotal` 与 `table-write-exemptions.frozenTotal` 均降至约定阈值以下」），替换形容词式判断。
<!-- 2026-07-23 主控套用 docpatch P10（按 R4/S1 终值）：docs/cloud-service-decomposition-proposal.md §12 阶段 3 新增准入条件段，阈值 involvingContent==0、import frozenTotal<=178（=295-117）、table-write frozenTotal<=12。取代原稿 145 与 rebase 中间值 162（见下两条阈值修正）。 -->
<!-- 阈值修正 aidcp-cloud e8c0e04（2026-07-23 rebase 后）：import frozenTotal 阈值 **145 → 162**（=274-112）。另两条不变——involvingContent==0 与 table frozenTotal<=10 不受影响，因为新增 17 条全在 api↔automation 之间、表侧一条未增。套用 docpatch P10 时 MUST 先按 R0 对齐这个数 -->
<!-- 阈值再修正 aidcp-cloud 89c286d（2026-07-23，cloud-schema-migration-executor land 后）：import frozenTotal 阈值 **162 → 178**（=295-117）。**这次 involvingContent 变了**（112 → 117）：新增 21 条里有 5 条一端是 content（src/cache/concept-store.ts / curated-content-store.ts ×2 / src/metrics/token-usage-store.ts / src/publish-agent/facebook-publish-media-store.ts → src/schema/），故与上一轮「新增全在 api↔automation、involvingContent 不变」的情形不同。另两条判据形态不变：involvingContent==0 仍是阶段 3 的硬门，表侧阈值仍按 S1 的 12 计。套用 docpatch P10 时 MUST 按本条对齐，R0 的 162 已被取代 -->
- [x] 6.4 在 §14 验收红线里加一条：跨边界 import 与跨边界表写入的豁免条数 MUST 有机械门禁把守且只减不增；并在红线 6（不存在跨服务源码导入与表写入）旁注明「阶段 1 起由本门禁把守，阶段 2 之后由 Git 边界与数据库授权接管」。
<!-- 2026-07-23 主控套用 docpatch P11：docs/cloud-service-decomposition-proposal.md §14.1 尾部追加红线 AC-DECOMP-33（边界执行·豁免只减不增）+ 红线 6（AC-DECOMP-06）验收方式加旁注。原稿拟 31，因三条并行新增红线按套用顺序排号，本 change 末位取 33（config-mirror=31、publish-approval=32）。 -->
- [ ] 6.5 **改为登记依赖，MUST NOT 在本 change 内直接改 `CLAUDE.md` §7**：该清单的改动属控制仓法条变更（定稿 §12 已写死「走独立 change，不在本方案文档内」），且定稿 §17 第 1 项已把它登记为一个**合并后共 8 项**的独立控制仓 change（定稿点名五处 `server.ts` / `role-dispatcher.ts` / `publish-agent/` / `panel/` / `agents/` + 本 change 需要的三项 `aidcp-cloud/src/kernel/**` / `boundaries/module-ownership.json` / `boundaries/table-ownership.json`）。本项的义务是：本 change 的门禁生效前，该控制仓 change MUST 已合入。两处各改一半 MUST NOT 发生。
<!-- BLOCKED: 依赖未满足——§17 第 1 项那个控制仓 change 尚未立项、更未合入，而本 change 的门禁代码已就绪。CLAUDE.md §7 未被本 session 触碰（符合 MUST NOT）。另有一处口径需改：该 change 列的 `aidcp-cloud/src/kernel/**` 路径**不存在**，本 change 按 §4.7 判定不建 src/kernel/ 目录（见 2.6）；应改为列 kernel 花名册的四个现有路径。已写成 docpatch P14。2026-07-23 主控复核（严守 rule 6）：CLAUDE.md §7 未改；§17 第 1 项本身未改（P14 明写「无需改动 §17 第 1 项本身」）；P14 的「src/kernel/** 路径不存在→应改列 kernel 花名册四个现有路径」作为 caveat 记入主控报告，交那个独立控制仓 change 落地。依赖（该独立 change 合入）仍未满足，本项保持未勾选。 -->
- [x] 6.6 在 `docs/cloud-service-decomposition-review.md` 的「如果只做三件事」第三件旁标注本 change 名，便于后续对账。
<!-- 2026-07-23 主控套用 docpatch P12：docs/cloud-service-decomposition-review.md §四 第三件标注承接 change 名，三个作废数字改为实测终值（295 条跨边界 import + 12 条跨层表写入，role-dispatcher 簇 4 条）。 -->

## 7. 验证与交付

- [x] 7.1 在 `aidcp-cloud` 跑 `npm run test:acceptance`，确认两个新门禁用例通过且不拖慢整体（超过 2 秒则让两个用例共享一次扫描结果）。
<!-- aidcp-cloud 071252c af05b3c 实测 79 tests / 79 pass / 0 fail / duration 1595ms。两个门禁套件合计 ~7ms（AC-BOUND 4.6ms + AC-OWN 2.4ms），远低于 2 秒；两者本就共享 boundarySnapshot() 的一次扫描缓存 -->
<!-- aidcp-cloud 31dfab2 修复后复跑：85 tests / 85 pass / 0 fail / duration 1627ms（+6 条为两个保真自检套件）。门禁套件耗时无变化 -->
<!-- aidcp-cloud e8c0e04 rebase 重新基线后复跑：89 tests / 89 pass / 0 fail / duration 1693ms（+2 条为新增的「归属生成器保真自检」套件：逐文件切分目录的新文件必报待裁决、单层目录的新文件必继承）。门禁套件耗时无变化 -->
- [x] 7.2 跑全量 `npm test` 与 `npm run typecheck`，确认第 2.3、2.4 两处小手术零回归。
<!-- aidcp-cloud af05b3c npm test：2920 tests / 2912 pass / 0 fail / 8 skipped（8 个 skipped 为既有的真机 gated e2e，与本次改动无关）；npm run typecheck 零错误。2.3 的搬迁零回归；2.4 未做（见该条 BLOCKED） -->
<!-- aidcp-cloud 31dfab2 修复后复跑：npm test 2926 tests / 2918 pass / 0 fail / 8 skipped（skipped 仍是那 8 个既有真机 gated e2e）；npm run typecheck 零输出退出 0 -->
<!-- aidcp-cloud e8c0e04 rebase 重新基线后复跑：npm test 3034 tests / 3026 pass / 0 fail / 8 skipped（skipped 仍是那 8 个既有真机 gated e2e，与本次改动无关）；npm run typecheck 零输出退出 0。**「本次 src/ 与 migrations/ 零改动」这句只对 e8c0e04 这一个提交成立**——整条分支对 origin/master 仍有 2 个 src 文件改动（src/cache/pg-anchor-cache.ts、src/cache/pg-config.ts，来自更早的 071252c，即任务 2.3 的 DEFAULT_PG_CONFIG 搬迁），该偏离在 2.3 的 PARTIAL / BLOCKED 注释里已如实登记 -->
<!-- aidcp-cloud 620c0db 第二轮审计修复后复跑：npm run test:acceptance 94 tests / 94 pass / 0 fail / 0 skipped（+5 条为新增的「棘轮键保真自检」四条与「归属生成器保真自检」新增的一条）；npm test 3039 tests / 3031 pass / 0 fail / 8 skipped（skipped 仍是那 8 个既有真机 gated e2e）；npm run typecheck 零输出退出 0。两族 metrics：import 274 / frozenTotal 274 / delta 0 / involvingContent 112（均未变）；表侧 writeSites 245 / crossLayerWrites 12 / ddlViolations 0 / 条目 12 / frozenTotal 12 / delta 0（条目与 frozenTotal 由 10 变 12 是粒度修正，见 4.4）。**幂等复核**：干净树上重跑 `npm run boundaries:refresh` 后 `git status --porcelain` 为空，四份生成物逐字节不变 -->
<!-- 本次 src/ 与 migrations/ 零改动（`git status --porcelain src/ migrations/` 为空），只动 boundaries/ 清单与 test/acceptance/ 下的门禁与扫描器 -->
<!-- aidcp-cloud 89c286d 第二次基线迁移后复跑（三件套全绿）：npm run test:acceptance 105 tests / 105 pass / 0 fail / 0 skipped；npm test 3092 tests / 3084 pass / 0 fail / 8 skipped（skipped 仍是那 8 个既有真机 gated e2e）；npm run typecheck 零输出退出 0。与本仓 master 基线一致（acceptance 全绿 / test 0 failing / typecheck 0 error）。两族 metrics：AC-BOUND {"sourceFiles":350,"ownershipEntries":350,"crossBoundaryEdges":295,"byDirection":{"api->automation":101,"automation->content":28,"automation->api":77,"content->automation":32,"content->api":23,"api->content":34},"involvingContent":117,"exemptionEntries":295,"frozenTotal":295,"delta":0,"unplanned":295}；AC-OWN {"knownTables":90,"srcCreatedTables":64,"migrationTables":90,"exceptionTables":["service_metrics","service_probe"],"writeSites":245,"crossLayerWrites":12,"dmlViolations":12,"ddlViolations":0,"exemptionEntries":12,"frozenTotal":12,"delta":0,"unplanned":12}。**幂等复核**：reseed 后再跑一次默认 `npm run boundaries:refresh` 报「新增 0 / 删除 0」，人工补写的 21 条 reason / note 原样保留。**involvingContent 112 → 117 会影响 6.3 的阶段 3 准入取值**：import frozenTotal 阈值由 162（=274-112）变为 **178（=295-117）**，套用 docpatch P10 时 MUST 按此对齐 -->
<!-- 本次 src/ 与 migrations/ 同样零改动（`git status --porcelain src/ migrations/` 为空），只动 boundaries/ 下的四份清单与规则表 -->
- [x] 7.3 人工验证棘轮有效性：故意加一条跨边界 import，确认 `AC-BOUND-04` 失败并指名文件对；故意在非属主层加一条 `UPDATE`，确认 `AC-OWN-02` 失败并指名表与文件；随后撤销。
<!-- 实测已做、已撤销。① 在 src/llm/qwen.ts（content）加 import '../risk/risk-controller.js'（automation）→ AC-BOUND-04 红，报「src/llm/qwen.ts -> src/risk/risk-controller.ts (content->automation)」。② 在 src/panel/panel-store.ts（api）加字符串 'UPDATE risk_state SET status=1' → AC-OWN-02 红，报「risk_state <- src/panel/panel-store.ts [update]（表属主 automation / 写入方 api）」。③ 另验棘轮本体：往豁免清单塞一条源码中不存在的条目并把 frozenTotal 从 257 改到 258 → AC-BOUND-05 与 AC-BOUND-06 同时红，后者报「frozenTotal 258 高于 seed 值 257 且未由 raises[] 覆盖」 -->
<!-- 缺陷修复 aidcp-cloud 31dfab2（2026-07-23 审计坐实）：**上面第 ② 条只覆盖了会命中的无别名写法**，换成本仓主流的带别名形态就假绿——修复前在同一文件注入 `UPDATE risk_state r SET status='frozen' WHERE r.id=1`，AC-OWN-01..05 全绿、metrics 行的 writeSites/crossLayerWrites 纹丝不动（229/12），即这条写入根本没被记录。修复后重跑同一注入 → AC-OWN-02 当场红，报「risk_state <- src/panel/panel-store.ts [update]（表属主 automation / 写入方 api）」，writeSites 232 / crossLayerWrites 13。同批补的两条注入验证：向 kernel 成员 src/cache/pg-config.ts 加 `export let __probe…` → AC-BOUND-03 红（修复前绿）；向 src/panel/retention-sweeper.ts 加 `import "../../scripts/run-migration.js"` → AC-BOUND-01 红（修复前静默丢弃）。三条注入均已撤销（`git checkout` / 备份还原，工作区仅剩五个改动文件）。**教训**：人工负向验证 MUST 覆盖仓内实际主流写法，不能只用最规范的教科书形态；已把三处形态各做成机械回归（见 2.5 / 3.2 / 4.2） -->
- [x] 7.4 人工验证诚实性：故意把一个 import 说明符改成不存在的路径，确认扫描器**失败**而非静默跳过；故意在 SQL 里写一张未登记的表，确认 `AC-OWN-01` 失败。
<!-- 实测已做、已撤销。① 在 src/llm/qwen.ts 加 import '../does-not-exist/gone.js' → AC-BOUND-04 首条断言红，报「相对 import 说明符解析不到实际源文件：src/llm/qwen.ts -> ../does-not-exist/gone.js」。② 在 src/panel/panel-store.ts 加 'INSERT INTO totally_unregistered_probe_table (a) VALUES (1)' → AC-OWN-01 红，报「SQL 扫描命中未登记的表标识符：totally_unregistered_probe_table」 -->
- [x] 7.5 人工验证全覆盖：新增一个空的 `src/` 文件而不登记归属，确认 `AC-BOUND-01` 失败。
<!-- 实测已做、已撤销。新建 src/zz-boundary-probe.ts（两行）→ AC-BOUND-01 红，报「新增源文件未登记归属，先跑 boundary-record ownership 再提交：src/zz-boundary-probe.ts」 -->
<!-- 缺陷修复 aidcp-cloud 620c0db（2026-07-23 第二轮审计坐实）：「归属表 MUST 是规则表的机械展开」这条断言此前**把生成物 module-ownership.json 自己回喂当「已裁决集」**，于是「是否被裁决过」退化成「是否已经在生成物里」。实测洗白路径：新建 src/publish-agent/zz-handedited-probe.ts（§4.7 里三分、标 adjudicate 的目录），手工往 module-ownership.json 加一条 {path, layer:'content'}（目录默认层）、**不**加任何 fileOverrides 裁定 → module-boundary.test.ts 11/11 全绿，随后 `boundaries:refresh` 退出 0 并把它重新写回生成物，洗白后不可逆。现把「已裁决文件集」挪进新的**人工文件** boundaries/adjudicated-files.json（登记 seed 当天已存在于逐文件切分目录里的 147 个文件，**只减不增**：此后这类目录的新文件一律进 ownership-rules.json 的 fileOverrides 并写明 §4.7 判据，源文件删除时由 refresh 同步剔除）；生成物只作输出、不再充当准入依据。同批加两条名册自检（名册里不得有已不存在的路径、不得与 fileOverrides 重叠）与一条机械回归「手工往生成物里塞一条新文件 MUST NOT 让它被当成已裁决」。注入验证：同样的手工塞入现在让 AC-BOUND-01 当场红 -->
<!-- 补充实测 aidcp-cloud e8c0e04（2026-07-23，四条注入均已撤销）：① 同时在 src/publish-agent/（§4.7 逐文件切分）与 src/risk/（§4.7 单层）各建一个空文件 → `npm run boundaries:refresh` 退出码 1，只报 publish-agent 那个「待人工裁决」，risk 那个正常继承 automation——证明「逐文件切分目录不替人判、单层目录才继承」这条判据两侧都成立；未裁决时 AC-BOUND-01 同步变红。② 在 src/llm/qwen.ts（content）注入 import '../risk/risk-controller.js'（automation）→ refresh 拒绝并列出该条、给出三条处置（先查归属是否填错 / 修掉 / 走 raises 通道）。③ 带 `--raise=<change>:1:2026-09-30` 才放行，frozenTotal 274→275 且 raises[] 落三字段；`--raise=<change>:1`（缺日期）当场拒绝。④ 只 --raise 不给消除 change 时 AC-BOUND-06 仍红（「未挂消除 change 的条目数 275 高于 seed 值 274」）——即上调通道也堵不住「加豁免却不挂消除动作」 -->
- [ ] 7.6 在控制仓跑 `openspec validate cloud-service-boundary-gates --strict`，回写 tasks 进度与 commit sha（格式 `<!-- <repo> <commit-sha> 备注 -->`）。
<!-- PARTIAL：`openspec validate cloud-service-boundary-gates --strict` 已跑，输出「Change 'cloud-service-boundary-gates' is valid」，退出码 0。tasks 进度与 sha 已回写（本文件）。 -->
<!-- BLOCKED（未完成的一半）：071252c / af05b3c / 8224c82 / 31dfab2 四个 sha 均尚未 push（本 session 按编排约定不推送、不集成），主控 rebase 到最新 master 后 sha 会变，**MUST 在集成后按实际 sha 复核回写本文件**。原注只列了前两个，8224c82 与 31dfab2 已在本文件头部与各条注释里补齐。 -->
<!-- 2026-07-23 更新：rebase 已由主控做完，四个 sha 实际变为 071252c / af05b3c / 8224c82 / 31dfab2，另加重新基线提交 e8c0e04，共五个（见本文件头部）。五个仍**未 push**，集成后 sha 可能再变，**MUST 再复核一次**。`openspec validate cloud-service-boundary-gates --strict` 于本次改动后重跑仍输出「Change 'cloud-service-boundary-gates' is valid」、退出码 0。 -->
<!-- 2026-07-23 第二轮审计修复后更新：新增第六个提交 620c0db（同样**未 push**）。本条仍保持未勾选——`openspec validate` 这一半已做（见上），但六个 sha 集成后仍可能再变、MUST 复核，且第 6 节的 docpatch 尚未套用。 -->
<!-- 归档前的强制动作（本轮新增）：把 aidcp-cloud 的 boundaries/ownership-rules.json 里 seedWindow.open 改成 false —— 关掉 seed 窗口后 `--reseed` 一律拒绝，与 §12「棘轮自本 change 归档起开始计数」对齐。 -->
<!-- 主控接手须知（可重跑收敛）：change `cloud-schema-migration-executor` 落地后 MUST 在 aidcp-cloud 跑一次 `npm run boundaries:refresh` 并把结果一起提交。预期它会先**报错**——src/schema/ 是 §4.7 里不存在的目录、生成器不替人判层，需先在 boundaries/ownership-rules.json 加规则或 fileOverride（判据引 §4.7，拿不准同样标「待定稿裁决」）；同时它把运行时 DDL 从各 store 删干净后，表全集与建表点口径会大幅下降，refresh 会自动删掉失效条目并同步下调 frozenTotal（棘轮下调恒允许、不需要任何标志）。 -->
