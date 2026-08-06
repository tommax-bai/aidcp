# tasks

> **先读 design.md 的两条硬约束再动手**：① 已应用迁移的字节不可改（整文件 sha256 校验和，不一致即整批拒绝）；② 归属判定 MUST NOT 由 SQL 文本反推表名。违反任一条会让 dev / ol 的迁移命令当场全停。
>
> 实测基线（2026-08-06，`aidcp-cloud` master）：迁移目录 110 条；残留（无可定位属主的对象声明）**13 条**；派生仓分发 api 70 / automation 58 / content 20。这些数字随后续 change 增长，**实施当天 MUST 重测，MUST NOT 照抄**。

## 1. aidcp-cloud — 派生仓迁移命令修复（独立、先做、可单独验证）

- [ ] 1.1 把三个派生仓 `scripts/migrate.ts` 里指向共享内核的两处相对引用改为包引用：`../src/kernel/pg-owner-connection-resolver.js` → `aidcp-kernel/kernel/pg-owner-connection-resolver.js`，`../src/kernel/schema-name.js` → `aidcp-kernel/kernel/schema-name.js`。**MUST NOT 在 `aidcp-cloud` 里改**——事实源仓有 `src/kernel/`，相对引用在那里是对的；改法差异由第 4 节的同步改写器承担。
- [ ] 1.2 全仓扫一遍**同类漏网**：三个派生仓的 `scripts/**` 里所有指向 `../src/kernel/` 的相对引用逐条列出并修掉。只修 1.1 点名的两处等于假设「就这两处」，而这个文件从没被任何工具看过。
- [ ] 1.3 逐仓自证 CLI 能起：在三个派生仓各跑一次迁移状态查询，确认**不是**因模块解析失败而退出。此步 MUST NOT 连 dev / ol 的库（无库连接时的预期失败形态是「连不上库」，不是「找不到模块」——两者 MUST 在输出里可区分）。

## 2. aidcp — 控制仓：把 `scripts/` 纳入拆仓同步覆盖（根因，不做等于下次照漂）

- [ ] 2.1 在 `scripts/sync-split-repos` 里新增 `scripts/` 的同步段，按**逐文件点名**（范式抄 `aidcp-transport` 那份点名清单），起手只点 `scripts/migrate.ts`。MUST NOT 整目录同步——`scripts/` 下多数脚本是控制仓 / 事实源仓自用的。
- [ ] 2.2 该段 MUST 复用既有的 `rewrite_kernel_imports`（已验证它对 `scripts/migrate.ts` + `../src/kernel/x.js` 解析正确，产出 `aidcp-kernel/kernel/x.js`），MUST NOT 另写一份改写逻辑。
- [ ] 2.3 自证覆盖生效：改一行事实源仓的 `scripts/migrate.ts`（可用无意义空白改动，验完还原），跑一次不带参数的对账，确认它**报出该文件有差异**；还原后再跑一次，确认报「无差异」。
- [ ] 2.4 自证幂等：`--apply` 后立刻再跑一次对账，MUST 报零差异；三个派生仓 `git status --porcelain` 在第二次 apply 后 MUST 为空。
- [ ] 2.5 在 `docs/cloud-cross-service-coupling-resolution.md`（或同批执行清单）里记一句：`scripts/` 自本 change 起是派生物，MUST NOT 手工改派生仓里的它。

## 3. aidcp-cloud — 执行范围与账本范围拆开

- [ ] 3.1 在 `src/schema/migration-owners.ts` 的归属结构里把「账本范围」与「执行范围」拆成两个字段，账本范围恒为全部属主（保持今日行为），执行范围按第 4 节的解析顺序给出。文件头那段说明 MUST 同批改写——**它现在写的「残留迁移不持有任何存活对象」是已被实测证伪的错误前提**，留着会继续骗下一个人。
- [ ] 3.2 `scripts/migrate.ts` 的执行循环改为：执行范围内执行 SQL 并写账本行；执行范围外**只写账本行、一条语句都不发**。
- [ ] 3.3 每次运行 MUST 把「记账但未执行」的版本清单原样打出（沿用现有 `residue` 清单必须打出来的纪律），MUST NOT 静默。
- [ ] 3.4 脱库单测：单属主迁移在非属主库上「零 SQL + 一条账本行」；执行范围为空的条目在三个库上都零 SQL；执行范围与账本范围不等时清单被打出。

## 4. aidcp-cloud — 归属解析顺序与封闭名册

- [ ] 4.1 新增文件内属主头 `-- aidcp:owner=<owner>[,<owner>]` 的解析（`parseMigrationHeader` 今天只认 `kind` 与 `objects`）。取值 MUST 限于既有属主枚举，非法值即失败。
- [ ] 4.2 新增 `migrations/legacy-owner-overrides.json`：逐条 `{ version, owners[], basis, supersededBy? }`。`basis` MUST 写清判定依据（读了该迁移哪些语句、对应边界清单里哪一行的属主），MUST NOT 只写属主名。
- [ ] 4.3 实现解析顺序（唯一，MUST NOT 另立）：① 文件内属主头 → ② 名册条目 → ③ 对象声明能定位到表 → ④ **失败并指名**。**删除今天的残留分支**（「无可定位对象 ⇒ 计入全部属主」）。
- [ ] 4.4 名册的三条机械断言：(a) 条目数只减不增；(b) 每条 version MUST 属于一份冻结的「本 change 落地前已存在的迁移」清单——新迁移写进名册即失败；(c) 名册里不得有目录中已不存在的 version。
- [ ] 4.5 `owners: []` MUST 同时带 `supersededBy`，且被点名的迁移合起来 MUST 覆盖它创建过的全部对象；缺任一条即失败。**这条不加，`0030` 的三个索引会在全新库上被悄悄丢掉。**
- [ ] 4.6 脱库单测覆盖解析顺序的四个分支 + 名册三条断言 + `owners: []` 的接替校验，每条都要有**注入验证**（改坏它、确认闸变红），不能只测 happy path。

## 5. aidcp-cloud — 13 条历史迁移逐条裁定

- [ ] 5.1 逐条实读这 13 条迁移的 SQL，按它们**引用的表**在边界清单里的属主填名册。**MUST NOT 照抄下面这份粗扫结果**——它是正则扫出来的起点，`0030` 正是粗扫会看漏的那一类（去重后只报一个属主）。粗扫基线（2026-08-06）：`0021` / `0027` / `0030_content_schedule_group_comments` / `0040` / `0043` / `0044` / `0050` / `0051` / `0069` → api（9 条）；`0045` / `0046` / `0055` → automation（3 条）；`0030_panel_hardening_indexes` → automation + content（跨属主）。
- [ ] 5.2 `0050_wechat_group_reply_config_privileges` 单独复核：它是一个在表属主找不到时**主动抛异常**的 DO 块，与其它 12 条的失败形态不同（不是「关系不存在」而是显式 RAISE），归属填错的后果更响亮但同样是整批停。
- [ ] 5.3 `0030_panel_hardening_indexes` 按 design D3 处置：名册里 `owners: []` + `supersededBy` 点名两条新迁移；新增两条迁移（新版本 id、排目录尾部）分别在 automation 与 content 的表上 `CREATE INDEX IF NOT EXISTS` 建回那三个索引。**MUST NOT 改 `0030` 的字节。**
- [ ] 5.4 **先解掉 design 的 Open Question**：实读 `migrate verify` 的对账代码，确认它是否接受「同一对象被两个版本声明」（`0030` 与两条接替迁移）。不接受时的退路是新迁移改用新索引名，并在名册 `basis` 里写明为什么换名。**MUST NOT 凭推测直接写**。
- [ ] 5.5 给 `scripts/generate-migration-headers.ts` 加守卫：**已应用 / 冻结集合内的迁移不重写头声明**。不加这条，5.3 的新迁移一落地，下次重跑生成器就会去改 `0030` 的头 → 校验和冲突 → dev / ol 迁移命令全停。实测方式：落地后重跑一次生成器，`git status --porcelain migrations/` MUST 为空。

## 6. aidcp-cloud — 可执行性静态闸

- [ ] 6.1 新增可执行性闸：对执行范围含属主 O 的每条迁移，它引用的每张表 MUST 由某条执行范围也含 O 的迁移创建；不满足即失败并指名「迁移 / 属主 / 缺失的表」。
- [ ] 6.2 表引用扫描 MUST 复用仓内既有口径（`src/schema/ddl-scan.ts` 与边界门禁那套 SQL 扫描），**不写第三份**；先剥注释；解析不了的语句 MUST 失败并指名，MUST NOT 静默跳过。
- [ ] 6.3 在扫描器文件头写死：**它 MUST NOT 参与归属判定，只有否决权**。不写这句，它迟早被当成第二套归属口径，而现有判据明令禁止由 SQL 文本反推归属。
- [ ] 6.4 落成验收用例进 `npm run test:acceptance`，命名与既有 `AC-SCHEMA-*` 族对齐。
- [ ] 6.5 注入验证（缺一不可）：(a) 造一条引用外域表的迁移 → 闸当场红并指名属主与表；(b) 把 `0030` 的名册条目改回 `owners: [automation, content]` → 闸当场红；(c) 造一条扫描解析不了的语句 → 闸失败而非放行。三条验完撤销。

## 7. 分发与验证

- [ ] 7.1 跑 `npm run boundaries:refresh`（新增 `src/schema/**` 文件会要求逐个裁定归属）并把结果一并提交。注意 seed 窗口已于 2026-08-06 关闭，`--reseed` 一律被拒；新增豁免只走 `--raise` 三字段通道，**能不加就不加**。
- [ ] 7.2 `cd ../aidcp-cloud && npm run test:acceptance` → `npm test` → `npm run typecheck`，三件套全绿并记录数字。
- [ ] 7.3 跑控制仓 `scripts/sync-split-repos`（先不带参数对账、再 `--apply`）把改动分发到三个派生仓。**MUST NOT 因某条迁移执行范围收窄就从派生仓删除它的迁移文件**——账本范围不变，删了账本行会变成 `ledgerOnly` 噪声。逐仓核对 `migrations/` 数量变化并写进本文件。
- [ ] 7.4 三个派生仓各跑一次 `npm run typecheck` 与 `npm test`（若该仓有），确认同步没带进断裂。
- [ ] 7.5 在控制仓跑 `openspec validate restore-derived-migration-executability --strict`，回写本文件进度与 commit sha（格式 `<!-- <repo> <commit-sha> 备注 -->`）。
- [ ] 7.6 部署 dev 前 MUST 先跑一次迁移状态查询自证零 pending 异常；**本 change 不产生任何需要在既有库上执行的 DDL**，若状态查询报出待应用迁移以外的任何异常，MUST 停手排查而非继续部署。
- [ ] 7.7 把「空库 → migrate up → 启动服务」这条真验收挂回 change `cloud-schema-migration-executor` 的 5.9 与 backlog 簇 111.6，并注明本 change 是它的前置。**本 change MUST NOT 自称已验证空库拉起**——它只负责让那件事第一次可执行。
