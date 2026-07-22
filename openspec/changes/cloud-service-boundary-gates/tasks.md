## 1. aidcp-cloud — 模块归属表（全覆盖，无未分配态）

- [ ] 1.1 新建 `boundaries/module-ownership.json`：条目形如 `{ "path": "src/comm/protocol.ts", "layer": "kernel", "note": "" }`，`layer` 枚举固定为 `kernel` / `api` / `content` / `automation` / `composition`，**不设「未分配」取值**。放仓根 `boundaries/` 而不是 `src/`，避免动 `tsconfig` 的 `resolveJsonModule`。
- [ ] 1.2 按方案 §4 的三条边界先填 255 个已可归类文件：`client-auth/`+`panel/`+`config/`→`api`（49）、`agents/`+`publish-agent/`+`render/`+`llm/`+`soul/`→`content`（133）、`comm/`+`orchestrator/`+`event-bus/`+`risk/`+`interactions/`+`platform/`+`delegated-task/`→`automation`（73）。
- [ ] 1.3 逐个补齐今日无归属的 63 个文件（19256 行），默认落点：`comment-agent/`（12/5346）→`automation`，其中 `facebook-comment-composer-prompt.ts` 与 `compose-approve.ts` 的 LLM 组稿段单列 `content`；`feishu/`（15/2701）→`automation`；`hot-lead/`（2）、`planner/`（3）→`automation`；`metrics/`（2/1309）、`alerts/`（2）、`onboarding/`（2）→`api`；`storage/`（4）→`content`；`time/`（2）与 `src/deployment-target.ts`→`kernel`；`src/account-store.ts`、`src/account-state.ts`、`src/account-display-name.ts`、`src/index.ts`→`api`；`src/server.ts` 与 `src/cli/`（2）→`composition`。偏离默认落点的条目必须在 `note` 里写一句理由。
- [ ] 1.4 `cache/`（11 文件 2960 行）逐文件按表属主拆分归属，不整目录归一层：`pg-anchor-cache.ts` 的锚点 store 段→`automation`、`curated-content-store.ts`→`content`、`interaction-feed-store.ts`→`automation`、`concept-store.ts`→`content`、`liked-note-store.ts`→`automation`、`valuable-comment-store.ts`→`content`、`bot-chat-store.ts`/`group-route-store.ts`/`notification-contact-store.ts`→`automation`、`pg-config.ts`→`kernel`、`index.ts` 按其 re-export 内容拆或删。
- [ ] 1.5 在归属表头部固定 `composition` 成员白名单（起手仅 `src/server.ts`、`src/cli/**`），并写明规则：`composition` MAY 导入任何层，任何层 MUST NOT 导入 `composition`，白名单外的文件不得声明为 `composition`。

## 2. aidcp-cloud — 共享内核层 kernel 的裁定与准入

- [ ] 2.1 在归属表里把下列文件标为 `kernel`（本步只登记归属，不移动文件）：`src/comm/protocol.ts`、`src/soul/types.ts`、`src/event-bus/types.ts`、`src/time/shanghai-day.ts`、`src/deployment-target.ts`、`src/platform/registry.ts` 的纯数据声明段、`src/panel/types.ts` 与 `src/feishu/types.ts` 的纯类型段。
- [ ] 2.2 明确记录**不进 kernel**的三边共导文件及其原因（有 SQL / 有业务判定 / 有进程内活状态）：`src/cache/curated-content-store.ts`、`src/client-auth/client-user-store.ts`、`src/config/content-schedule-store.ts`、`src/risk/session-limits.ts`、`src/risk/resume-limits.ts`、`src/soul/writing-language.ts`、`src/event-bus/index.ts`。它们的三边共导进豁免清单等待削减，不得靠改归属绕过。
- [ ] 2.3 把 `DEFAULT_PG_CONFIG`（现在 `src/cache/pg-anchor-cache.ts:33`）移到 `src/cache/pg-config.ts`，反转现有依赖方向（该文件 `:2` 今天反向 import 回 `pg-anchor-cache.js`），并把 32 个引用方改为从 `pg-config.js` 取。行为不得改变：环境变量优先级与默认值逐字保持。**不得**在本次改动里把源码兜底口令写进新文件——它应在后续独立 change 改为纯配置读取。
- [ ] 2.4 收窄 `src/agents/base-role.ts` 的两处具体实现导入（`:8` 的 `../event-bus/index.js`、`:11` 的 `../llm/qwen.js`），改为 kernel 内的接口声明；照仓内既有弱接口范式（`src/agents/base-role.ts:14` 的 `RoleLlm`）。改完 `base-role.ts` 方可标为 `kernel`。
- [ ] 2.5 在门禁里实现 kernel 准入断言：kernel 成员 MUST NOT 含 `INSERT`/`UPDATE`/`DELETE`/`CREATE TABLE`/`SELECT` 字面量、MUST NOT 注册 HTTP 路由、MUST NOT 调用 LLM 或供应商 HTTP、MUST NOT 含模块级可变单例或定时器或连接池、MUST NOT 导入 `api`/`content`/`automation`/`composition` 任一层。任一条不满足即失败并指名文件。
- [ ] 2.6 建 `src/kernel/` 目录并把已裁定成员物理搬迁过去（分批，每批同批削减豁免清单）。本步在 1、3 两节门禁生效之后做。

## 3. aidcp-cloud — 导入方向门禁（AC-BOUND-*）

- [ ] 3.1 新建扫描器 `test/acceptance/helpers/boundary-scan.ts`：递归列出 `src/**/*.ts`、解析静态 `import`/`export ... from` 与动态 `import()`（现有 3 处）、把相对说明符的 `.js` 后缀映射回 `.ts` 并解析到实文件（含 `index.ts` 目录解析）。零新依赖，只用 `node:fs` / `node:path`。范式照抄 `test/server-startup-order.test.ts:5-10` 与 `aidcp-edge/test/electron/interaction-ipc-security.test.ts:1-11`。
- [ ] 3.2 扫描器 MUST 在解析不到实文件时抛错并列出说明符，MUST NOT 静默跳过；MUST 在扫描文件数与归属表条目数不等时抛错。
- [ ] 3.3 新建 `test/acceptance/module-boundary.test.ts`，用例编号 `AC-BOUND-01..06`：01 归属表全覆盖且无孤儿条目；02 层枚举合法且 `composition` 成员在白名单内；03 kernel 准入断言（第 2.5 项）；04 无未豁免的跨边界 import；05 无失效（源码中已不存在）的豁免条目；06 `entries.length <= frozenTotal` 且上调 `frozenTotal` 必须带 `raises[]`。
- [ ] 3.4 新建 `boundaries/import-exemptions.json`：头部含 `frozenTotal`、`recordedAt`、`raises: []`，条目为 `{ "from": "...", "to": "...", "reason": "" }`。以 record 模式（如 `AIDCP_BOUNDARY_RECORD=1 npx tsx test/acceptance/module-boundary.test.ts`）一次性生成，然后提交。生成后核对量级：三边之间应约 217 条，含 kernel 与已补齐的 63 个文件后总量应 ≤462 条；实测值与此偏差超过 10% 时先查扫描器再提交。
- [ ] 3.5 允许方向白名单写进测试源码（不进 JSON，改它必须改测试文件）：任何层 MAY→`kernel`；`composition` MAY→任何层；其余跨层方向一律需要豁免条目。
- [ ] 3.6 门禁 MUST 在输出里打印机器可读计数：按 `from→to` 方向分解的条数、总条数、`frozenTotal`、以及与 `frozenTotal` 的差值。

## 4. aidcp-cloud — 表写入归属门禁（AC-OWN-*）

- [ ] 4.1 新建 `boundaries/table-ownership.json`：表名→属主层的全量映射。表全集取 `src/**/*.ts` 与 `migrations/*.sql` 里 `CREATE TABLE` 的并集（实测 84 张，其中 59 张由 `src/` 建）。未登记的表出现在扫描结果里即失败。
- [ ] 4.2 扫描器新增 SQL 字面量扫描：`INSERT INTO <t>` / `UPDATE <t>` / `DELETE FROM <t>`（DML）与 `CREATE TABLE [IF NOT EXISTS] <t>` / `ALTER TABLE <t>`（DDL）。MUST 先剥掉 `--` 行注释与 `/* */` 块注释；MUST 对已知误命中形态给出显式排除规则（实测假阳性来源：`UPDATE ... SET` 后的列名、`skip`、`of`、`resolved_at`、`alerts` 等标识符碰撞）；MUST 在命中一个不在表全集里的标识符时失败并报出，MUST NOT 静默跳过。
- [ ] 4.3 新建 `test/acceptance/table-ownership.test.ts`，用例编号 `AC-OWN-01..05`：01 表归属表覆盖全部已知表且无孤儿；02 无未豁免的跨层 DML 写入；03 无未豁免的跨层 DDL（建表 / 改表）；04 无失效豁免条目；05 `frozenTotal` 棘轮（同 3.3-06）。
- [ ] 4.4 新建 `boundaries/table-write-exemptions.json` 并以 record 模式生成。核对起手应至少含实测的 5 处跨边界多写：`interaction_runtime_controls`、`interaction_auth_state`、`interaction_offboards`、`interaction_offboard_audit`（`src/client-auth/client-user-store.ts` 属 `api` × `src/interactions/interaction-store.ts` 属 `automation`）与 `first_post_onboarding`（`src/config/persona-store.ts:196-215` × `src/onboarding/first-post-onboarding-store.ts:26`）。
- [ ] 4.5 DDL 归属条目必须覆盖今天 34 个文件里的 76 处 `CREATE TABLE IF NOT EXISTS`。这一步只冻结、不修——取消 store 自建表属阶段 2 的迁移执行器工作，不在本 change。
- [ ] 4.6 同层多写不判违规但仍须指定唯一属主层，逐条登记：`reply_templates` / `reply_rules` / `account_reply_profiles` / `interaction_reply_configs` / `interaction_reply_config_versions` / `interaction_audit_events` 六张表被 `src/interactions/interaction-store.ts` 与 `src/interactions/reply-config-store.ts` 各自写入，同属 `automation`。

## 5. aidcp-cloud — 削减路径（先冻结，后削减）

- [ ] 5.1 【反方向，收益最集中】把 `src/event-bus/types.ts`（46 条）、`src/platform/index.ts`（13 条）、`src/comm/protocol.ts`（10 条）三个目标随第 2.6 项搬进 `src/kernel/`，一次性削掉 `content→automation` 79 条里的 69 条。这一步不写业务代码，只改 import 路径与归属表，同批删除对应豁免条目。
- [ ] 5.2 `src/platform/registry.ts` 的纯数据声明段随 `platform/index.ts` 进 kernel，再削 4 条；剩余 6 条（`comm/edge-task-lease-client.ts` 2、`event-bus/index.ts` 1、`risk/session-limits.ts` 1、`risk/resume-limits.ts` 1、`comm/preemption.ts` 1）保留豁免并在条目 `reason` 里写明属真实跨边界依赖。
- [ ] 5.3 【正方向，单点最纠缠】起一个**专门的独立 change** 处理 `src/orchestrator/role-dispatcher.ts`（3088 行）文件头对 40 个角色类的 import（`automation→content` 53 条里的 43 条）：引入 `RoleName → 角色工厂` 注册表，dispatcher 只依赖 kernel 里的角色基类接口，具体角色类由组合根 `src/server.ts` 注入。按 CLAUDE.md §7 标记为热点文件、需串行独占，不与其它 change 并行。
- [ ] 5.4 每次削减 MUST 在同一提交里同步下调 `frozenTotal` 并删除失效条目（否则门禁的失效条目断言会直接失败）。
- [ ] 5.5 建立削减节奏约定并写进控制仓：每归档一批 change 至少削减 N 条豁免（N 由首批实测后确定），`role-dispatcher.ts` 那 43 条单列不计入常规配额。

## 6. aidcp — 控制仓文档与阶段准入

- [ ] 6.1 改写 `docs/cloud-service-decomposition-proposal.md` §6.4：禁令改为「禁止共享**包含业务逻辑**的公共包」，显式列出 `kernel` 例外、逐条写出准入条件（无 SQL / 无 HTTP 路由 / 无 LLM 与供应商调用 / 无进程内活状态 / 不反向依赖业务层），并写明 kernel 拆仓后由 `aidcp-automation` 单一拥有、以版本化包发布、其余两仓固定版本消费。
- [ ] 6.2 改写 §12 阶段 1 的条目顺序：把「模块导入和数据所有权检查」提到**首位**，并加一句「本项 MUST 先于任何边界重构落地」。
- [ ] 6.3 在 §12 阶段 3 加入可判定的准入条件，直接引用门禁输出的计数（形如「`import-exemptions.frozenTotal` 与 `table-write-exemptions.frozenTotal` 均降至约定阈值以下」），替换形容词式判断。
- [ ] 6.4 在 §14 验收红线里加一条：跨边界 import 与跨边界表写入的豁免条数 MUST 有机械门禁把守且只减不增；并在红线 6（不存在跨服务源码导入与表写入）旁注明「阶段 1 起由本门禁把守，阶段 2 之后由 Git 边界与数据库授权接管」。
- [ ] 6.5 更新 `CLAUDE.md` §7 的热点文件单写者清单：加入 `aidcp-cloud/src/kernel/**`、`boundaries/module-ownership.json`、`boundaries/table-ownership.json` 三项，注明改动需串行。
- [ ] 6.6 在 `docs/cloud-service-decomposition-review.md` 的「如果只做三件事」第三件旁标注本 change 名，便于后续对账。

## 7. 验证与交付

- [ ] 7.1 在 `aidcp-cloud` 跑 `npm run test:acceptance`，确认两个新门禁用例通过且不拖慢整体（超过 2 秒则让两个用例共享一次扫描结果）。
- [ ] 7.2 跑全量 `npm test` 与 `npm run typecheck`，确认第 2.3、2.4 两处小手术零回归。
- [ ] 7.3 人工验证棘轮有效性：故意加一条跨边界 import，确认 `AC-BOUND-04` 失败并指名文件对；故意在非属主层加一条 `UPDATE`，确认 `AC-OWN-02` 失败并指名表与文件；随后撤销。
- [ ] 7.4 人工验证诚实性：故意把一个 import 说明符改成不存在的路径，确认扫描器**失败**而非静默跳过；故意在 SQL 里写一张未登记的表，确认 `AC-OWN-01` 失败。
- [ ] 7.5 人工验证全覆盖：新增一个空的 `src/` 文件而不登记归属，确认 `AC-BOUND-01` 失败。
- [ ] 7.6 在控制仓跑 `openspec validate cloud-service-boundary-gates --strict`，回写 tasks 进度与 commit sha（格式 `<!-- <repo> <commit-sha> 备注 -->`）。
