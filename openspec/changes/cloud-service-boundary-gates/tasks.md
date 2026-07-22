## 1. aidcp-cloud — 模块归属表（全覆盖，无未分配态）

- [ ] 1.1 新建 `boundaries/module-ownership.json`：条目形如 `{ "path": "src/time/shanghai-day.ts", "layer": "kernel", "note": "" }`，`layer` 枚举固定为 `kernel` / `api` / `content` / `automation` / `composition`，**不设「未分配」取值**。放仓根 `boundaries/` 而不是 `src/`，避免动 `tsconfig` 的 `resolveJsonModule`。示例 MUST 取自定稿 §4.7 已裁定的 kernel 四文件之一；**MUST NOT 用 `src/comm/protocol.ts` 作示例**——§10.9 终局裁决它归 `aidcp-automation` 独占、MUST NOT 进 kernel，示例会被实施者照抄。
- [ ] 1.2 **归属判据不在本 change 内自立，一律引用控制仓定稿 `docs/cloud-service-decomposition-proposal.md` §4.7「归属总表」逐行填入**（该表已覆盖全部 `src/` 文件、未归属 = 0，并声明自己是 `AC-BOUND-*` 的输入）。本 change **MUST NOT 另立一套判据**；若实施者认为 §4.7 某一行错了，走控制仓 change 改 §4.7，不得在 `boundaries/module-ownership.json` 里单方面偏离。本条原稿写的「三边先填 255 文件（49/133/73）」判据**已作废**：其中 `config/`→`api`（49）把 §4.6.8 判归 automation 的 5 个限频配置文件一并塞给了 api。
- [ ] 1.3 逐条改正原稿与 §4.7 冲突的 7 处（本条替代原「63 个无归属文件默认落点」清单——该批文件已在 §4.7 内完成分配）：① `src/feishu/`（15）→**`api`**（§4.6.2 裁决，非 automation）；② `src/metrics/`（2）→**`content`**（§4.6.6，非 api）；③ `src/alerts/`（2）→**`automation`**（§5.1「告警表 owner = automation、api MUST NOT UPDATE」，非 api）；④ `src/config/`（30）→**25 归 api / 5 归 automation**（§4.6.8，非整目录归 api）；⑤ `src/onboarding/`（2）→**1 api / 1 content**（状态表归 api、创作桥接归 content，非整体 api）；⑥ `src/index.ts`→**`composition`**（非 api）；⑦ `src/cli/`（2）→**1 api（`test-feishu.ts`）/ 1 automation（`trigger-like.ts`）**，§4.7 已逐文件点名，非 `composition`。
- [ ] 1.4 `cache/`（11 文件 2949 行）逐文件归属**直接抄 §4.7 的 `src/cache/` 逐文件表**（api 2 / content 2 / automation 6 / kernel 1）。原稿四处与之相反、MUST 改正：`notification-contact-store.ts` 与 `bot-chat-store.ts` 归 **`api`**（原稿写 automation）、`valuable-comment-store.ts` 归 **`automation`**（原稿写 content）、`group-route-store.ts` 归 `automation`（与原稿一致）。`index.ts` 归 `automation`。
- [ ] 1.5 在归属表头部固定 `composition` 成员白名单（起手仅 `src/server.ts`、`src/cli/**`），并写明规则：`composition` MAY 导入任何层，任何层 MUST NOT 导入 `composition`，白名单外的文件不得声明为 `composition`。

## 2. aidcp-cloud — 共享内核层 kernel 的裁定与准入

- [ ] 2.1 **kernel 花名册以定稿 §4.7 kernel 段为唯一权威**：本基线上 kernel 恰好 4 个文件 251 行（`src/time/shanghai-day.ts`、`src/time/source-published-time.ts`、`src/deployment-target.ts`、`src/cache/pg-config.ts`）。原稿名单 MUST 按下列三条改：① **删除 `src/comm/protocol.ts`**——§10.9 已终局裁决「MUST 归 `aidcp-automation` 独占、MUST NOT 放进 kernel」，MUST NOT 再提案；② `src/soul/types.ts`、`src/panel/types.ts`、`src/feishu/types.ts` 的「纯类型段」与 `src/platform/registry.ts` 的「纯数据声明段」**不能按段落进 kernel**——§4.0 第 1 条是文件级单一归属、不承认「半个文件归 kernel」；要进必须先把该段**析出为独立新文件**再对新文件判 kernel，并在同一批改动里同步更新 §4.7 的目录行、kernel 计数与合计行；③ `src/event-bus/types.ts`（`RoleName` 所在）与 `src/platform/registry.ts` 纯数据段是否按②析出，是 §4.7 明列的**两处待裁决项**，MUST 在本步一次判定并回写 §4.7，MUST NOT 在本 change 与 §4.7 各判一次。
- [ ] 2.2 明确记录**不进 kernel**的三边共导文件及其原因（有 SQL / 有业务判定 / 有进程内活状态）：`src/cache/curated-content-store.ts`、`src/client-auth/client-user-store.ts`、`src/config/content-schedule-store.ts`、`src/risk/session-limits.ts`、`src/risk/resume-limits.ts`、`src/soul/writing-language.ts`、`src/event-bus/index.ts`。它们的三边共导进豁免清单等待削减，不得靠改归属绕过。
- [ ] 2.3 把 `DEFAULT_PG_CONFIG`（现在 `src/cache/pg-anchor-cache.ts:33`）移到 `src/cache/pg-config.ts`，反转现有依赖方向（该文件 `:2` 今天反向 import 回 `pg-anchor-cache.js`），并把 32 个引用方改为从 `pg-config.js` 取。行为不得改变：环境变量优先级与默认值逐字保持。**不得**在本次改动里把源码兜底口令写进新文件——它应在后续独立 change 改为纯配置读取。
- [ ] 2.4 收窄 `src/agents/base-role.ts` 的两处具体实现导入（`:8` 的 `../event-bus/index.js`、`:11` 的 `../llm/qwen.js`），改为 kernel 内的接口声明；照仓内既有弱接口范式（`src/agents/base-role.ts:14` 的 `RoleLlm`）。改完 `base-role.ts` 方可标为 `kernel`。
- [ ] 2.5 在门禁里实现 kernel 准入断言：kernel 成员 MUST NOT 含 `INSERT`/`UPDATE`/`DELETE`/`CREATE TABLE`/`SELECT` 字面量、MUST NOT 注册 HTTP 路由、MUST NOT 调用 LLM 或供应商 HTTP、MUST NOT 含模块级可变单例或定时器或连接池、MUST NOT 导入 `api`/`content`/`automation`/`composition` 任一层。任一条不满足即失败并指名文件。
- [ ] 2.6 建 `src/kernel/` 目录并把已裁定成员物理搬迁过去（分批，每批同批削减豁免清单）。本步在 1、3 两节门禁生效之后做。**搬迁范围 MUST 排除 `src/comm/protocol.ts`**（§10.9 终局裁决）；只删任务 5.1 的该项而不改本步与 2.1，`protocol.ts` 仍会经这两步进 kernel，§10.9 点名要消除的 6 处 type-only 依赖会就地合法化。

## 3. aidcp-cloud — 导入方向门禁（AC-BOUND-*）

- [ ] 3.1 新建扫描器 `test/acceptance/helpers/boundary-scan.ts`：递归列出 `src/**/*.ts`、解析静态 `import`/`export ... from` 与动态 `import()`（现有 3 处）、把相对说明符的 `.js` 后缀映射回 `.ts` 并解析到实文件（含 `index.ts` 目录解析）。零新依赖，只用 `node:fs` / `node:path`。范式照抄 `test/server-startup-order.test.ts:5-10` 与 `aidcp-edge/test/electron/interaction-ipc-security.test.ts:1-11`。
- [ ] 3.2 扫描器 MUST 在解析不到实文件时抛错并列出说明符，MUST NOT 静默跳过；MUST 在扫描文件数与归属表条目数不等时抛错。
- [ ] 3.3 新建 `test/acceptance/module-boundary.test.ts`，用例编号 `AC-BOUND-01..06`（**该编号即定稿 §12「两族门禁」的族内编号，两边逐条对齐，MUST NOT 出现同名不同义**）：01 归属表全覆盖且无孤儿条目；02 层枚举合法且 `composition` 成员在白名单内；03 kernel 准入断言（第 2.5 项）；04 无未豁免的跨边界 import；05 无失效（源码中已不存在）的豁免条目；06 `entries.length <= frozenTotal`，且上调 `frozenTotal` 必须带合规的 `raises[]`（字段要求见 3.4）。另加一条断言：`eliminatedBy` 为空的条目数 MUST 单调不增。
- [ ] 3.4 新建 `boundaries/import-exemptions.json`：头部含 `frozenTotal`、`recordedAt`、`raises[]`，条目为 `{ "from": "...", "to": "...", "reason": "", "eliminatedBy": null }`。**`eliminatedBy` 是第四个必填字段**（值为控制仓 openspec change 名），承载定稿 §12 棘轮规则的「计划消除它的 change 名」与 §10.9 的「每条各挂一个消除它的 change」；seed 期允许为 `null`，但 MUST 在本 change 的 tasks 里登记补齐时限，且为 `null` 的条目数只减不增。**`raises[]` 的每个元素 MUST 含 `{ amount, approvedByChange, eliminateBy }` 三个字段**：`approvedByChange` MUST 是控制仓一个已存在的 openspec change 名，`eliminateBy` MUST 是具体日期；三者任一缺失即门禁失败（与定稿 §12「例外通道（唯一）」逐字对齐）。以 record 模式（如 `AIDCP_BOUNDARY_RECORD=1 npx tsx test/acceptance/module-boundary.test.ts`）一次性生成，然后提交。生成后核对量级：三边之间应约 217 条；实测值与预期偏差超过 10% 时先查扫描器再提交。**原稿的 462 条上界与「63 个文件」口径已随 1.2–1.4 改判作废，MUST 以实施当天重跑结果为准。**
- [ ] 3.5 允许方向白名单写进测试源码（不进 JSON，改它必须改测试文件）：任何层 MAY→`kernel`；`composition` MAY→任何层；其余跨层方向一律需要豁免条目。
- [ ] 3.6 门禁 MUST 在输出里打印机器可读计数：按 `from→to` 方向分解的条数、总条数、`frozenTotal`、以及与 `frozenTotal` 的差值。

## 4. aidcp-cloud — 表写入归属门禁（AC-OWN-*）

- [ ] 4.1 新建 `boundaries/table-ownership.json`：表名→属主层的全量映射。**属主判定以定稿 §5.1「单一写入者」表为输入，MUST NOT 另立判据**。表全集取 `src/**/*.ts` 与 `migrations/*.sql` 里 `CREATE TABLE` 的并集。未登记的表出现在扫描结果里即失败。**计数口径 MUST 与同批 change `cloud-schema-migration-executor` 统一**：本稿原写「84 张 / 59 张由 `src/` 建」，该 change 的 `proposal.md` 写「并集 83 张 / 存储自建 58 张」，两者只要差一张，本门禁的「未登记的表出现即失败」当天就会红。MUST 由两个 change 中**先动工的一个**跑一次统一口径脚本（distinct 表名；`src/**/*.ts` 的 `CREATE TABLE IF NOT EXISTS` ∪ `migrations/*.sql` 的 `CREATE TABLE`；先剥 `--` 与 `/* */` 注释），把结果同时回写两处，并把脚本命令写进 tasks。
- [ ] 4.1b **两张运维表 `service_metrics` / `service_probe` 不进豁免清单**：它们是定稿 §5.1 具名的「设计内永久例外」（多写者计数表 / 探针独占表），到方案阶段 2 才建，其条目必然产生在本 change 一次性 seed 之后，且按设计无消除时限。MUST 单列为一份「例外表清单」文件，不占豁免清单条目、不参与棘轮计数（依据：定稿 §12「例外表清单」）；否则实施者会撞上「加条目违反棘轮、不加条目 `AC-OWN-02`/`03` 判违规」的死结。
- [ ] 4.2 扫描器新增 SQL 字面量扫描：`INSERT INTO <t>` / `UPDATE <t>` / `DELETE FROM <t>`（DML）与 `CREATE TABLE [IF NOT EXISTS] <t>` / `ALTER TABLE <t>`（DDL）。MUST 先剥掉 `--` 行注释与 `/* */` 块注释；MUST 对已知误命中形态给出显式排除规则（实测假阳性来源：`UPDATE ... SET` 后的列名、`skip`、`of`、`resolved_at`、`alerts` 等标识符碰撞）；MUST 在命中一个不在表全集里的标识符时失败并报出，MUST NOT 静默跳过。
- [ ] 4.3 新建 `test/acceptance/table-ownership.test.ts`，用例编号 `AC-OWN-01..05`（**该编号即定稿 §12「两族门禁」的族内编号，两边逐条对齐**）：01 表归属表覆盖全部已知表且无孤儿；02 无未豁免的跨层 DML 写入；03 无未豁免的跨层 DDL（建表 / 改表）；04 无失效豁免条目；05 `frozenTotal` 棘轮（同 3.3-06）。另加一条断言：`eliminatedBy` 为空的条目数 MUST 单调不增。
- [ ] 4.4 新建 `boundaries/table-write-exemptions.json` 并以 record 模式生成；条目 schema 与 `raises[]` 字段要求同 3.4（含必填的 `eliminatedBy`）。核对起手应至少含实测的 5 处跨边界多写：`interaction_runtime_controls`、`interaction_auth_state`、`interaction_offboards`、`interaction_offboard_audit`（`src/client-auth/client-user-store.ts` 属 `api` × `src/interactions/interaction-store.ts` 属 `automation`）与 `first_post_onboarding`（`src/config/persona-store.ts:196-215` × `src/onboarding/first-post-onboarding-store.ts:26`）。
- [ ] 4.5 DDL 归属条目必须覆盖今天 34 个文件里的 76 处 `CREATE TABLE IF NOT EXISTS`。这一步只冻结、不修——取消 store 自建表属阶段 2 的迁移执行器工作，不在本 change。
- [ ] 4.6 同层多写不判违规但仍须指定唯一属主层，逐条登记：`reply_templates` / `reply_rules` / `account_reply_profiles` / `interaction_reply_configs` / `interaction_reply_config_versions` / `interaction_audit_events` 六张表被 `src/interactions/interaction-store.ts` 与 `src/interactions/reply-config-store.ts` 各自写入，同属 `automation`。

## 5. aidcp-cloud — 削减路径（先冻结，后削减）

- [ ] 5.1 【反方向，收益最集中】原稿三个搬迁目标 MUST 按定稿裁决重排：**`src/comm/protocol.ts`（10 条）一项取消**——§10.9 终局裁决它归 `aidcp-automation` 独占、MUST NOT 进 kernel；`src/event-bus/types.ts`（46 条）与 `src/platform/index.ts`（13 条）两项的处置**随任务 2.1 对 §4.7「两处待裁决项」的定案而定**，定案前 MUST 视为未定。因此「一次性削掉 79 条里的 69 条」这个数字 MUST 按定案结果重算，MUST NOT 作为既定收益写进准入条件（连带影响见 6.3）。这一步不写业务代码，只改 import 路径与归属表，同批删除对应豁免条目。
- [ ] 5.2 `src/platform/registry.ts` 的纯数据声明段随 `platform/index.ts` 进 kernel，再削 4 条；剩余 6 条（`comm/edge-task-lease-client.ts` 2、`event-bus/index.ts` 1、`risk/session-limits.ts` 1、`risk/resume-limits.ts` 1、`comm/preemption.ts` 1）保留豁免并在条目 `reason` 里写明属真实跨边界依赖。
- [ ] 5.3 【正方向，单点最纠缠】起一个**专门的独立 change** 处理 `src/orchestrator/role-dispatcher.ts`（3088 行）文件头对 40 个角色类的 import（`automation→content` 53 条里的 43 条）：引入 `RoleName → 角色工厂` 注册表，dispatcher 只依赖 kernel 里的角色基类接口，具体角色类由组合根 `src/server.ts` 注入。按 CLAUDE.md §7 标记为热点文件、需串行独占，不与其它 change 并行。
- [ ] 5.4 每次削减 MUST 在同一提交里同步下调 `frozenTotal` 并删除失效条目（否则门禁的失效条目断言会直接失败）。**子仓 MUST NOT 在没有控制仓 change 批准的情况下上调 `frozenTotal`**：上调只走 3.4 定义的 `raises[]` 例外通道，且每个元素必须齐备 `amount` / `approvedByChange` / `eliminateBy` 三字段。
- [ ] 5.5 建立削减节奏约定并写进控制仓：每归档一批 change 至少削减 N 条豁免（N 由首批实测后确定），`role-dispatcher.ts` 那 43 条单列不计入常规配额。

## 6. aidcp — 控制仓文档与阶段准入

- [ ] 6.1 改写 `docs/cloud-service-decomposition-proposal.md` §6.4：禁令改为「禁止共享**包含业务逻辑**的公共包」，显式列出 `kernel` 例外、逐条写出准入条件（无 SQL / 无 HTTP 路由 / 无 LLM 与供应商调用 / 无进程内活状态 / 不反向依赖业务层），并写明 kernel 拆仓后由 `aidcp-automation` 单一拥有、以版本化包发布、其余两仓固定版本消费。
- [ ] 6.2 改写 §12 阶段 1 的条目顺序：把「模块导入和数据所有权检查」提到**首位**，并加一句「本项 MUST 先于任何边界重构落地」。
- [ ] 6.3 在 §12 阶段 3 加入可判定的准入条件，直接引用门禁输出的计数（形如「`import-exemptions.frozenTotal` 与 `table-write-exemptions.frozenTotal` 均降至约定阈值以下」），替换形容词式判断。
- [ ] 6.4 在 §14 验收红线里加一条：跨边界 import 与跨边界表写入的豁免条数 MUST 有机械门禁把守且只减不增；并在红线 6（不存在跨服务源码导入与表写入）旁注明「阶段 1 起由本门禁把守，阶段 2 之后由 Git 边界与数据库授权接管」。
- [ ] 6.5 **改为登记依赖，MUST NOT 在本 change 内直接改 `CLAUDE.md` §7**：该清单的改动属控制仓法条变更（定稿 §12 已写死「走独立 change，不在本方案文档内」），且定稿 §17 第 1 项已把它登记为一个**合并后共 8 项**的独立控制仓 change（定稿点名五处 `server.ts` / `role-dispatcher.ts` / `publish-agent/` / `panel/` / `agents/` + 本 change 需要的三项 `aidcp-cloud/src/kernel/**` / `boundaries/module-ownership.json` / `boundaries/table-ownership.json`）。本项的义务是：本 change 的门禁生效前，该控制仓 change MUST 已合入；两处各改一半 MUST NOT 发生。
- [ ] 6.6 在 `docs/cloud-service-decomposition-review.md` 的「如果只做三件事」第三件旁标注本 change 名，便于后续对账。

## 7. 验证与交付

- [ ] 7.1 在 `aidcp-cloud` 跑 `npm run test:acceptance`，确认两个新门禁用例通过且不拖慢整体（超过 2 秒则让两个用例共享一次扫描结果）。
- [ ] 7.2 跑全量 `npm test` 与 `npm run typecheck`，确认第 2.3、2.4 两处小手术零回归。
- [ ] 7.3 人工验证棘轮有效性：故意加一条跨边界 import，确认 `AC-BOUND-04` 失败并指名文件对；故意在非属主层加一条 `UPDATE`，确认 `AC-OWN-02` 失败并指名表与文件；随后撤销。
- [ ] 7.4 人工验证诚实性：故意把一个 import 说明符改成不存在的路径，确认扫描器**失败**而非静默跳过；故意在 SQL 里写一张未登记的表，确认 `AC-OWN-01` 失败。
- [ ] 7.5 人工验证全覆盖：新增一个空的 `src/` 文件而不登记归属，确认 `AC-BOUND-01` 失败。
- [ ] 7.6 在控制仓跑 `openspec validate cloud-service-boundary-gates --strict`，回写 tasks 进度与 commit sha（格式 `<!-- <repo> <commit-sha> 备注 -->`）。
