## Context

### 现状实测（2026-07-22，`aidcp-cloud` HEAD）

| 项 | 实测值 | 取值方式 |
| --- | --- | --- |
| `src/**/*.ts` 源文件数 | 318 | `find src -name '*.ts' \| wc -l` |
| `src/` 总行数 | 85746 | 逐文件行数求和 |
| 按方案 §4 三条边界可归类的文件 | 255（api 49 / content 133 / automation 73） | 见下「归属判据」 |
| 无归属文件 | 63 个 / 19256 行 | 同上 |
| 三边之间跨边界 import | 217 条 | 解析全量相对 import 并解析到实文件后按层配对 |
| 含无归属层在内的跨层 import 上界 | 462 条 | 同上 |
| 被 api / content / automation 三边共同导入的文件 | 16 个 | 逐文件统计导入方所在层的集合 |
| 被两个不同边界各自写入的表 | 5 张 | 扫 SQL 字面量的 `INSERT`/`UPDATE`/`DELETE` |
| `src/` 内 `CREATE TABLE` 出现次数 / 所在文件数 | 76 / 34 | `grep -rc "CREATE TABLE" src` |
| 近 30 天 `src/` 提交 / 触碰 `src/server.ts` 的提交 | 447 / 237（53%） | `git log --since=30.days --oneline -- <path> \| wc -l` |
| `aidcp-cloud` 运行时依赖 | 6 个包 | `package.json:20-27` |
| CI | 0 | 无 `.github/workflows` |

无归属的 63 个文件按目录分布（文件数 / 行数）：`(根目录)` 6/5459、`comment-agent` 12/5346、`feishu` 15/2701、`cache` 11/2960、`metrics` 2/1309、`storage` 4/266、`onboarding` 2/258、`hot-lead` 2/261、`alerts` 2/178、`planner` 3/171、`cli` 2/131、`time` 2/216。

跨边界 import 的方向分解（三边之间）：

| 方向 | 条数 | 集中点 |
| --- | --- | --- |
| `content→automation` | 79 | `src/event-bus/types.ts` 46、`src/platform/index.ts` 13、`src/comm/protocol.ts` 10（合计 69；**这 69 条不等于可削减量**，处置见下文削减路径表） |
| `automation→content` | 53 | `src/orchestrator/role-dispatcher.ts` 单文件 43 条 |
| `api→automation` | 41 | `src/panel/types.ts`、`src/client-auth/client-auth-server.ts`、`src/panel/panel-server.ts` |
| `api→content` | 33 | 同上三处为主 |
| `content→api` | 7 | — |
| `automation→api` | 4 | — |

跨边界多写的 5 张表：

- `interaction_runtime_controls`、`interaction_auth_state`、`interaction_offboards`、`interaction_offboard_audit` —— 写方同时是 `src/client-auth/client-user-store.ts`（api）与 `src/interactions/interaction-store.ts`（automation）。
- `first_post_onboarding` —— 写方同时是 `src/config/persona-store.ts:196-215`（api）与 `src/onboarding/first-post-onboarding-store.ts:26`（今日无归属）。

另有同层多写（不构成跨边界违规，但归属表必须仍指定唯一属主）：`reply_templates` / `reply_rules` / `account_reply_profiles` / `interaction_reply_configs` / `interaction_reply_config_versions` / `interaction_audit_events` 六张表被 `src/interactions/interaction-store.ts` 与 `src/interactions/reply-config-store.ts` 各自写入。

### 仓内既有的「读源码做结构断言」范式（本 change 要照抄的）

- `aidcp-cloud/test/server-startup-order.test.ts:5-10` —— `readFile(new URL('../src/server.ts', import.meta.url))` 后按landmark下标先后做顺序断言。
- `aidcp-cloud/test/delegated-task/store-schema.test.ts:1-33` —— `readFileSync` 读 `migrations/*.sql` 与 store 里的 SQL 常量，用正则断言 DDL 结构。
- `aidcp-cloud/test/interactions/migration-contract.test.ts:1-27` —— 逐份读 migrations 断言表清单与不变量，含 `assert.doesNotMatch` 的否定断言。
- `aidcp-edge/test/electron/interaction-ipc-security.test.ts:1-11,20-26` —— 一次读三份源码、用正则做安全类结构断言（本 change 的门禁形态与它最接近）。
- 已有的验收闸命名与挂载点：`package.json:14` 的 `"test:acceptance": "tsx --test test/acceptance/*.test.ts"`；`aidcp/scripts/land-change:38-42` 在每次集成时先跑 `test:acceptance`、再跑 `npm test`、再跑 `npm run typecheck`，任一失败即拒绝合并。

结论：门禁只需要 `node:test` + `node:fs`，零新依赖；写进 `test/acceptance/` 当天就挂在既有集成闸上。

## Goals / Non-Goals

**Goals:**

- 让「某个文件属于哪一层」成为机器可判定、且**必须表态**的事实，而不是文档里的形容词。
- 让跨边界耦合的总量成为一个可读、只减不增的数字。
- 让门禁在阶段 1 的**第一天**生效，不以「先修完历史债」为前提。
- 裁决共享内核层的存废，并给它可执行的准入条件与单写者纪律。
- 给出两条按方向优先级排序、收益集中的削减路径。

**Non-Goals:**

- 不在本 change 里搬动任何业务代码到新目录、不切进程、不动数据库、不动协议。
- 不重新讨论是否拆仓（决策已定），也不把门禁当作拆仓的替代品。
- 不建 CI、不引入 lint 工具链、不引入依赖分析库。
- 不修复历史违规（只冻结与度量）；削减工作由本 change 列出的后续 tasks 分批执行。

## Decisions

### 1. 五层归属枚举，且没有「未分配」这个取值

层枚举固定为 `kernel` / `api` / `content` / `automation` / `composition`。归属表是一份路径→层的全量映射，条目数必须等于扫描到的源文件数。

**为什么必须全覆盖**：方案 §4 的三条边界今天只覆盖 255/318 文件（79%），19256 行无人认领。这 19256 行不是边角料——`comment-agent/`（5346 行）是 Facebook 群评论与加群整条产品线，`feishu/`（2701 行）同时是唯一人审入口与第二条运营控制入口。拆仓时它们必须去某一个仓；今天不表态，到那天就是三个仓互相推诿。全覆盖要求把「表态」这件事的成本从「拆仓当天一次性想清 63 个文件」摊薄成「新增文件时顺手写一行」。

**为什么要有 `composition`**：`src/server.ts` 有 89 条相对 import、39 处 `.init()` 调用，按定义要横跨全部层。若不单列，它一个文件就会产出上百条豁免、把清单的信噪比冲垮。规则是：`composition` MAY 导入任何层；任何层 MUST NOT 导入 `composition`；`composition` 的成员文件清单必须显式枚举（起手只有 `src/server.ts` 与 `src/cli/*`），不允许靠「新文件声明成 composition」来绕过门禁。

**归属判据已被控制仓定稿取代（本段保留只为记录本 change 的原始推导，MUST NOT 作为实施输入）。** 定稿 `docs/cloud-service-decomposition-proposal.md` §4.7「归属总表」已对全部 `src/` 文件完成分配、未归属 = 0，并声明自己是 `AC-BOUND-*` 的输入。实施时 MUST 逐行照抄 §4.7，MUST NOT 用下面这段默认落点判据；两者冲突的 7 处已在 tasks 1.3 逐条列出（`feishu/`→`api`、`metrics/`→`content`、`alerts/`→`automation`、`config/` 25 api + 5 automation、`onboarding/` 1 api + 1 content、`src/index.ts`→`composition`、`src/cli/` 1 api + 1 automation），`cache/` 的四处反向已在 tasks 1.4 列出。认为 §4.7 某行有误时走控制仓 change 改 §4.7，不得在 `boundaries/module-ownership.json` 里单方面偏离。

原始推导（**已作废**）：按「这段代码干活时需不需要碰只存在于本进程内存里的活对象（边缘连接注册表 / 进程内事件总线 / 会话上下文 / 风控控制器实例 / 在途租约）」判定——需要即 `automation`。据此：`comment-agent/`→`automation`（其 LLM 组稿段单列 `content`）、`feishu/`→`automation`、`hot-lead/`→`automation`、`planner/`→`automation`、`metrics/`→`api`、`alerts/`→`api`、`onboarding/`→`api`、`storage/`→`content`、`cache/` 按表属主逐文件拆、`time/` 与 `src/deployment-target.ts`→`kernel`、`src/account-store.ts` 与 `src/account-state.ts`→`api`、`src/server.ts` 与 `src/cli/`→`composition`。

### 2. 裁决 §6.4：承认并命名 `kernel`，不复制三份

**选定方案：承认共享内核层，给它准入测试与单写者纪律。**

实测被三边共同导入的 16 个文件是：`src/comm/protocol.ts`、`src/event-bus/types.ts`、`src/event-bus/index.ts`、`src/agents/base-role.ts`、`src/cache/pg-anchor-cache.ts`、`src/platform/index.ts`、`src/soul/types.ts`、`src/soul/writing-language.ts`、`src/panel/types.ts`、`src/feishu/types.ts`、`src/time/shanghai-day.ts`、`src/deployment-target.ts`、`src/risk/session-limits.ts`、`src/risk/resume-limits.ts`、`src/cache/curated-content-store.ts`、`src/client-auth/client-user-store.ts`、`src/config/content-schedule-store.ts`。

它们不是同一类东西，所以「全进 kernel」和「全复制三份」都错。用一条准入测试切开：

**`kernel` 准入条件（全部满足才可进）**：文件 MUST NOT 含 SQL 字面量（`INSERT`/`UPDATE`/`DELETE`/`CREATE TABLE`/`SELECT`）、MUST NOT 注册 HTTP 路由、MUST NOT 发起 LLM 或供应商 HTTP 调用、MUST NOT 持有进程内活状态（模块级可变单例、定时器、连接池）、MUST NOT 依赖 `api`/`content`/`automation`/`composition` 任一层。

按此裁定：

- **进 kernel**（本段为本 change 的原始提案，**已被控制仓定稿部分否决，MUST 按 tasks 2.1 执行**）：~~`comm/protocol.ts`~~ —— **该项被定稿 §10.9 终局否决**：`protocol.ts` MUST 归 `aidcp-automation` 独占、MUST NOT 进 kernel（进 kernel 等于让三边都可导入，会把 §10.9 点名的 6 处 api/content 侧 type-only 依赖就地合法化）；`time/shanghai-day.ts`、`deployment-target.ts` 已在定稿 §4.7 的 kernel 名单内；`soul/types.ts`、`panel/types.ts`、`feishu/types.ts` 的「纯类型部分」与 `platform/registry.ts` 的「纯数据部分」**不能按段落进 kernel**——定稿 §4.0 第 1 条是文件级单一归属，要进必须先析出为独立新文件；`event-bus/types.ts` 与 `platform/registry.ts` 纯数据段是否析出，是定稿 §4.7 明列的**两处待裁决项**，由 tasks 2.1 一次判定并回写 §4.7。
- **进 kernel 但需先做小手术**：`agents/base-role.ts` —— 它现在从 `../event-bus/index.js` 与 `../llm/qwen.js` 导入具体实现（`src/agents/base-role.ts:8,11`），必须先把这两处收窄成 kernel 内的接口声明（`RoleLlm` 已是仓内既有的弱接口范式，见 `src/agents/base-role.ts:14`）。
- **不进 kernel、必须留在原层**：`cache/curated-content-store.ts`、`client-auth/client-user-store.ts`、`config/content-schedule-store.ts`、`risk/session-limits.ts`、`risk/resume-limits.ts`、`soul/writing-language.ts`、`event-bus/index.ts` —— 它们有 SQL、有业务判定或有进程内活状态。它们被三边共导本身就是违规，进豁免清单等待削减。
- **需要拆文件**：`cache/pg-anchor-cache.ts` —— `DEFAULT_PG_CONFIG`（`src/cache/pg-anchor-cache.ts:33`）是纯配置、被 32 个文件引用，应移入 kernel（仓内已有半成品出口 `src/cache/pg-config.ts:1-2`，它现在反向 import 回 `pg-anchor-cache.ts`）；同文件里的锚点缓存 store 有 SQL、留 `automation`。

**为什么不照 §6.4 复制三份**：`src/event-bus/types.ts:558` 的 `RoleName` 是 43 个成员的联合类型，被 179 个文件消费。它今天的正确性完全靠单一源码树的类型穷举兜底。CLAUDE.md §2 记录了两处「类型检查抓不到」的漂移各自付出的代价（云端已发命令但边缘静默丢弃、角色永远等不到回执）。复制三份意味着在**建成 CI 合同测试之前**先手动制造第三次同类漂移的条件，而三个代码仓的 CI 今天是 0。这不是理论风险，是同一个坑第三次。

**kernel 的纪律（不靠自觉，靠三条硬规则）**：① `kernel` 目录进 CLAUDE.md §7 的热点文件单写者清单，改动标记为需串行；② 每新增一个 kernel 文件必须在同一 change 里逐条对照准入条件说明，门禁对 kernel 成员逐条跑准入断言；③ 拆仓时 kernel 以版本化包发布、由 `aidcp-automation` 单一拥有（协议、`RoleName`、命令桥动作映射、风控状态机四个热点按方案 §4.4 全部落在 automation），`aidcp-api` 与 `aidcp-content` 固定版本消费，不经 Git 路径引用源码。§6.4 的禁令相应改写为「禁止共享**包含业务逻辑**的公共包」并显式列出 kernel 例外与准入条件——禁令的原意（不许拿公共包偷渡业务逻辑绕开边界）由准入测试机械保证，比一句禁令强。

**为什么不选「复制三份 + CI 合同测试」**：那条路要求 CI 先存在。CI 从 0 建起不在本 change 范围，也不在方案 §12 任何一个阶段的交付物里。在 CI 存在之前复制，是净安全性下降。

### 3. 棘轮式豁免清单：三条断言构成棘轮

清单是一份具体条目的集合（导入侧：`{from, to}` 文件对；表写入侧：`{table, file}` 对），不是通配模式。门禁三条断言：

1. **不新增**：源码中每一条实际跨边界边 MUST 在清单里，否则失败。
2. **不留空位**：清单里每一条 MUST 在源码里仍然存在，否则失败。这条是棘轮的关键——削减后必须在同一提交里删条目，不能留着空位给未来的新违规回填。
3. **不静默上调**：清单头部记 `frozenTotal`；`entries.length > frozenTotal` MUST 失败。下调 `frozenTotal` 随削减自然发生；上调 MUST 在同一提交里写入 `raises[]` 条目（change 名 + 一句理由 + 日期），门禁对缺 `raises` 的上调 MUST 失败。

**诚实说明**：第 3 条挡不住「有人同时改代码和改 `frozenTotal` 并编一句理由」。逻辑门禁本质可绕过，这是它与 Git 物理边界的真实差距。它能保证的是：绕过必须是一次**显式、具名、可计数**的动作，而不是一次谁也没注意到的 import。这就是它相对「写在文档里的边界」的全部实质差别，不夸大。

**为什么不用「按方向对计数上限」而用具体条目**：只记数字的话，删一条旧违规就能白拿一个新违规的名额，棘轮变成配额交易。具体条目让每一次交换都在 diff 里可见。

### 4. 表写入归属门禁扫 DML 与 DDL 两类

表归属清单是一份表名→层的全量映射。门禁扫描 `src/**/*.ts` 里的 SQL 字面量：

- **DML**：`INSERT INTO <t>` / `UPDATE <t>` / `DELETE FROM <t>` 出现在非属主层的文件里即失败。
- **DDL**：`CREATE TABLE [IF NOT EXISTS] <t>` / `ALTER TABLE <t>` 出现在非属主层的文件里即失败。

**为什么必须一起扫 DDL**：今天真实 schema 由 34 个文件里的 76 处 `CREATE TABLE IF NOT EXISTS` 自愈建出。拆仓后「回滚到旧版本代码」会在表已迁走时静默重建空表并分叉写入——回滚动作本身变成一次静默假成功。把建表点绑到属主层，是让这个洞在阶段 2 建迁移执行器之前先被冻结住、不再扩大。

**归属粒度是层不是文件**：同层内多个 store 写同一张表（如 `interactions/` 那六张表）不判违规，但归属表仍必须给出唯一属主层。把粒度收到「唯一 store 类」是另一个议题，不在本 change。

**解析器必须诚实**：见决策 5。

### 5. 门禁自身不得静默假通过（把第一红线用在门禁上）

一个漏检的门禁比没有门禁更糟——它给出「已通过」的假信号。所以扫描器 MUST 对下列情况**失败**而不是跳过：

- 相对 import 说明符解析不到实文件（改名、路径错、扩展名映射失败）；
- SQL 扫描命中一个不在表归属清单、也不在 `migrations/` 已知表全集里的标识符（说明正则边界不对或有新表未登记）；
- 归属表里存在源码中已不存在的路径；
- 扫描到的源文件数与归属表条目数不相等。

同时 MUST 覆盖动态 `import()`（`src/` 现有 3 处），MUST 忽略 SQL 注释与 `--` 行注释后的内容，MUST 对 `UPDATE ... SET`、CTE 别名等已知误命中形态给出显式的排除规则而不是靠「不在白名单就跳过」。

### 6. 削减路径按方向优先级排序

**反方向 `content→automation`：79 条，主要靠 kernel 划分，几乎不写代码。原稿的「→ 10 条」结论 MUST 按下表重算——它假定三个目标全部进 kernel，而其中一个已被终局否决、另两个待裁决。**

| 目标文件 | 条数 | 处置 |
| --- | --- | --- |
| `src/event-bus/types.ts` | 46 | **待裁决**：定稿 §4.7 今天整体判 `automation`；是否析出 `RoleName` 等纯类型段进 kernel 由 tasks 2.1 一次判定并回写 §4.7 |
| `src/platform/index.ts` | 13 | **待裁决**：同上，随 `platform/registry.ts` 纯数据段的裁决一并定 |
| `src/comm/protocol.ts` | 10 | **不进 kernel（定稿 §10.9 终局裁决）**；这 10 条 MUST 留豁免并各挂消除 change，MUST NOT 计入削减收益 |
| `src/platform/registry.ts` | 4 | 纯数据部分随 `platform/index.ts` 的裁决一并定；进 kernel 前 MUST 先析出为独立文件（定稿 §4.7 kernel 新增通道） |
| `src/comm/edge-task-lease-client.ts` | 2 | 留豁免，属真实跨边界依赖 |
| `src/event-bus/index.ts` / `src/risk/session-limits.ts` / `src/risk/resume-limits.ts` / `src/comm/preemption.ts` | 各 1 | 留豁免 |

**正方向 `automation→content`：53 条中 43 条在一个文件。**

`src/orchestrator/role-dispatcher.ts`（3088 行）在文件头 import 并实例化 40 个角色类（`grep -c "^import .* from '../agents/"` = 40）。削减手段是角色工厂注册表：dispatcher 只依赖 kernel 里的角色基类接口 + 一张 `RoleName → 工厂` 注册表，具体角色类由组合根（`composition`）注入。这一处是全仓最纠缠的单点，也是收益最集中的一处，且与拆仓后 `aidcp-automation` 必须能在不 import content 角色的前提下启动这个硬要求完全同向。

这两条路径写成独立 tasks，且**明确排在门禁落地之后**——先冻结、再削减。

### 7. 豁免清单剩余条数是拆仓就绪度的度量

门禁 MUST 在每次运行时输出机器可读的当前计数（按方向分解 + 总数 + `frozenTotal`）。拆分方案 §12 阶段 3（提取 `aidcp-content`）的准入条件 MUST 引用这个数字，写成可判定的阈值，而不是「边界已经比较清晰」这类形容词。

理由：阶段 3 的成本是不可逆的（新 Git 远端、新部署单元、新 CI、fleet 脚本从 4 仓改 6 仓）。在跨边界 import 仍有数百条时提取，等于把这些耦合原样翻译成跨仓 HTTP 调用与手抄合同——方案 §6.4 禁止的「直接导入另一个业务仓库源码」会在提取当天变成几百个编译错误，而不是几百个已经收敛好的接口。用一个数字当准入，比用判断当准入更难自欺。

### 8. 门禁先于任何边界重构落地

方案 §12 阶段 1 的条目顺序 MUST 调整为：模块导入与数据所有权检查排第一位，其余边界重构（建模块边界、收口跨领域调用、迁 Outbox/Inbox）排其后。理由已在 proposal 的 Why 里给出：`src/server.ts` 每天约 8 次提交，门禁晚落地一周就是约 60 次未被检查的提交。

## Risks / Trade-offs

- **[豁免清单变成永久清单]** → 门禁输出的计数被写进阶段 3 准入条件（决策 7），使「不削减」直接等于「拆不了仓」；同时把 `role-dispatcher.ts` 那 43 条单列为一个专门 change，避免它永远排不上队。
- **[门禁可被改清单绕过]** → 诚实承认（决策 3）。缓解是让绕过必须显式具名可计数（`raises[]` + 条目级 diff），不假装它是物理边界。
- **[63 个文件的归属判定引发争议、拖住门禁落地]** → 归属表的**存在**与门禁的生效不依赖归属判得多准。判错只会让某条边从「不是违规」变成「一条豁免」，不影响棘轮工作。因此 tasks 要求先按默认判据一次性补齐、门禁先跑起来，归属争议走后续 change 调整（调整归属必须同批更新豁免清单，门禁的断言 2 会强制这一点）。
- **[kernel 变成新的垃圾桶]** → 准入测试逐条断言（决策 2），且 kernel 目录进热点文件单写者清单，新增文件必须在 change 里逐条对照准入条件说明。
- **[SQL 正则误判导致门禁 flaky]** → 决策 5 要求解析器对无法归类的命中**失败并报出**而不是跳过；首次落地时先跑一遍全量、把已知误命中形态（`skip`、`of`、`resolved_at`、`alerts` 等来自 `UPDATE ... SET` 与标识符碰撞的假阳性）写成显式排除规则。
- **[门禁拖慢 `test:acceptance`]** → 318 个文件的一次正则扫描在毫秒量级；两个用例合计读盘一次、缓存复用。若实测超过 2 秒，扫描结果 MUST 在两个用例间共享而不是各扫一遍。
- **[归属表与 CLAUDE.md 热点文件清单漂移]** → kernel 目录与两份归属清单一并写进 CLAUDE.md §7；本 change 的 tasks 含控制仓文档同步项。

## Migration Plan

1. 先落归属表与 kernel 准入裁定（不搬代码，只登记归属；kernel 成员此时仍在原路径，归属表用 `layer: "kernel"` 标注）。
2. 再落两道门禁与两份豁免清单，以 record 模式生成初始清单并提交。此时门禁当天生效、`npm run test:acceptance` 通过。
3. 然后做 kernel 的物理搬迁（建 `src/kernel/`、移动成员、`DEFAULT_PG_CONFIG` 与 `base-role.ts` 两处小手术），每移动一批同批削减豁免清单。
4. 最后做 `role-dispatcher.ts` 的角色工厂注册表改造——它是热点文件、必须串行独占。
5. 全程不改数据库、不改协议、不改运行时行为；任一步失败可单独回退（清单与门禁是纯新增文件）。

## Open Questions

- 无阻塞项。`kernel` 拆仓后的物理归属（由 `aidcp-automation` 拥有并发版）是决策 2 已给出的裁定；具体发版机制（npm 私有 registry / tarball / 版本号策略）属阶段 3 范围，本 change 不预先锁死。
