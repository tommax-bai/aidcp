## Context

真机测试（edge 真账号连生产云端）暴露两个独立缺陷，已逐行对照现役代码核实（行号为 2026-06-27 复核值）：

- **A 自动续场失效**：会话结束流程被调两次。触发体「先发结束命令、后走结束回调」顺序正确（`session-monitor-role.ts:247-255`），但结束命令的事件处理器**自己也调了一次结束**（`role-dispatcher.ts:1083`），叠加注入的结束回调（`:532`）共两次。结束流程顶部「无条件取消续场计时器」（`:731`）在「会话活跃守卫早退」（`:732`）之前，故：第①次结束武装续场计时器（`:743/armRestTimer`），第②次顶部取消之、随即因 `sessionActive=false` 早退、不再武装 → 续场计时器**武装即被自毁**，续场永不触发。对所有结束方式必然发生（事件总线同步派发，`event-bus/index.ts:59-79`）。即便修好①，续场重开会话只发 `feed.entered{trigger:'session_start'}`，而其翻译处理器（`:1028-1038`）只对 `back_to_feed` 发命令、对 `session_start` 是 no-op → 边端不被重驱。边端侧：循环收结束命令后停（`browse-session.ts:295-301`），此后命令被静默堆进无人消费的队列（`:374-382`），且无任何路径重启循环。
- **B 安全配置按账号**：单场上限存储 `session-config-store.ts`（`Map<accountId,Row>`，DB `0015` PK `account_id`）与续场/看门狗存储 `resume-config-store.ts`（DB `0020` PK `account_id`）均按精确账号查表；provider 7 方法带 `accountId`（`risk/session-limits.ts:63`、`risk/resume-limits.ts:60`）。后台只对 `default` 账号设过 30min，真实账号缺行回落写死 10min。

**前序 change 现状**（已核实）：
- `session-limits-to-quota-layer`：**active 34/36**，已部署生产（cloud `f1e0883` 2026-06-26），只剩真机校准 + 归档。它**创建**了按账号 `session_config`；其 `interaction-risk-gating` 的「按账号单场上限」delta **尚未并入正式 spec**（仍在 change 目录内）。
- `session-auto-resume-with-excursions`：**已归档**（`archive/2026-06-27-...`），创建了按账号 `resume_config`；其「按账号续场/看门狗」要求**已并入正式 spec**（`session-auto-resume` + `browse-loop-resilience` 现都写「按账号可配」）。
- `model-config-store.ts`（DB `0007`，`id=1 CHECK` 单行）是全局单例的**参照模式**。

## Goals / Non-Goals

**Goals:**
- A：续场对所有正常结束方式可靠触发；续场后边端浏览闭环被重新驱动；加回归断言锁死「单次结束=单次结束流程 + 续场计时器存活」。
- B：单场上限 + 续场/看门狗配置收敛为**全局单例**，取消账号维度；已设的 30min 经迁移保留生效；保「绝不 brick / 写库成功才刷镜像 / 不触风控单写」三不变量。
- 全程不动协议（A 复用既有滚动通道；B 是云端内部配置）。

**Non-Goals:**
- 不动配额（按档位×动作，本就全局）、人设、密钥（按账号是对的，正交保留）。
- 不接「状态迁移接真实平台封号/限流信号」（既有缺口，与本次正交）。
- 不引入新协议消息类型、不改两份 `protocol.ts` / 命令桥 / 协议文档。
- 不在本次重构 `role-dispatcher.ts` 的多租路由（与 `multi-account-node-support` 协调，不抢其面）。

## Decisions

### D1：一个 change、两条线（stream A / B）、可分离提交
用户拍板合一个 change。A 是紧急小回归（核心是删一行 + 边端唤醒 + 云端轻推），B 是跨三仓大改 + 迁移。两线**分别成 commit**，使 A 能先行部署、不被 B 拖住。tasks.md 按 stream + 子仓分节。

### D2：A① 用「删二次结束调用」而非「改触发体」
**选**：删 `role-dispatcher.ts:1083` 的二次结束调用，保留事件处理器只发结束命令；由注入的结束回调（`:532`）作**唯一**结束入口。
**理由**：触发体顺序（先 emit 发结束命令给边端、后走回调武装续场）本就正确；此改 diff 最小、语义清晰。
**备选（未选）**：改触发体为「只 emit、不走回调」、把结束职责留给处理器——同样能去重，但改动面更大且与既有回调约定相左。
**护栏**：新增回归断言——一次监测体结束 → 结束流程恰好一次、且续场休息计时器结束后「已武装未被取消」。

### D3：A② 复用既有滚动通道重驱边端，不新增协议
**关键澄清**：交接文档担心的「协议映射 landmine」**不成立**。经核实 `scroll` 动作已映射为消息 `page.scroll`（`command-bridge.ts:22-23`），且 `page.scroll` 已在边端主动命令白名单（`edge-client.ts:353`）并有处理分支（`browse-session.ts:533`）。真正卡点是**边端循环已死、命令无消费者**。
**选**：
- cloud：在 `feed.entered` 翻译处理器（`:1028-1038`）为 `trigger:'session_start'` 增一条分支，下发一次 `scroll`（统一在命令翻译出口发，最一致）。
- edge：`browse-session.ts` 的云端命令入口（`:374-382`）在「循环未运行且收到浏览类命令」时调 `start()` 重启循环（`start():276` 已有 `if(running)return` 幂等守卫）。
**坑（必须处理）**：`start():280` 会清空命令队列——故**靠循环重启后重报卡片**重新驱动云端，而非依赖那条排队命令存活；不要「先 push 再 start」。重启 MUST 被「主动关闭/下线」流程抢占（关闭中迟到命令不复活循环），呼应 `browse-loop-resilience` 的诚实下线要求。
**收益**：不触 AC-PROTO 四点同步闸与白名单遗漏陷阱；顺带让 idle 看门狗的 nudge 也真正生效。

### D4：B provider 接口彻底去 accountId（而非保留签名忽略）
**选**：7 个方法去掉 `accountId` 参数（`sessionDurationMs()` / `sessionBudget()` / `restRatio()` / `activeWindow()` / `dailyCaps()` / `idleNudgeMs()` / `idleEnd()`），改 `role-dispatcher.ts` 7 个调用点（`:345,:536,:537,:621,:761,:799,:801`）。
**理由**：干净、类型即文档；churn 集中在一个文件 7 处。会话监测体 `session-monitor-role.ts` 的 thunk 本就是无参 `()=>number`（交接 B.7 列它是**误**），**无需改**。
**备选（未选）**：保留签名忽略参数——churn 最小但留account维度残形，违背「去维度」本意。

### D5：B 存储收敛为单行全局表，参照 `id=1 CHECK` 模式；新迁移迁入 default 值
- 内存镜像 `Map<accountId,Row>` → 单个全局 `Row|null`；`get()/set(patch,updatedBy)` 去 accountId。
- DB：单行表（`id INTEGER PRIMARY KEY DEFAULT 1 CHECK(id=1)`，`ON CONFLICT(id)`），仿 `model-config-store`。
- 新迁移 `0022`（现有最高 `0021`，`0012/0017` 缺号——动前 `ls migrations/` 复核取号）：把现有 `account_id='default'` 行的值搬成全局行（**保 30min**）。
- 保留三不变量：写库成功才刷镜像、逐字段非法回落写死默认、永不抛。
- facade 去「`{'default'} ∪ getAll()` 账号目录」→ 单个全局读/写（GET 返回全局生效值 + 来源 override/builtin 两态；PUT 写全局、非乐观、整块校验）。

### D6：B 的「单场上限」spec 取代前序——归档顺序协调（关键）
B 的 `interaction-risk-gating` delta 现写为 `## ADDED`（全局单场上限要求），propose 阶段 `validate --strict` 可过（baseline 尚无此要求）。但 `session-limits-to-quota-layer` 持有未并入的「按账号单场上限」delta，二者指同一概念，**归档时须保证 baseline 只剩一条（全局）**。
**推荐路径**：实现工作（代码/测试/console）**现在并行做**（这是用户「现在就做」的含义）；**spec 归档**按序——
1. 让 `session-limits-to-quota-layer` 先跑完其 gated 真机校准并**先归档**（其按账号单场上限要求并入 baseline）；
2. 把 B 的 `interaction-risk-gating` delta 由 `## ADDED` 改为 `## REMOVED`（移除按账号那条，注明 Reason/Migration）+ `## ADDED`（全局那条）或等价 `## MODIFIED`；
3. `openspec validate restore-... --strict` 通过后归档 B。
**备选**：若 `session-limits-to-quota-layer` 被废弃/不归档，则改其 delta 为全局或删其按账号 delta，避免与 B 双写。
续场/看门狗部分无此问题：其按账号要求**已在 baseline**，B 直接用 `## MODIFIED`（已写）。

### D7：每日上限 = 阈值全局、计数仍按账号按日
「每日续场场数/累计时长上限」的**阈值**全局共用，但**计数**仍按账号按日统计（账号 A 用满不影响账号 B）。spec 已据此措辞，避免把全局阈值误读成「所有账号共享一个计数」。

### D8：console 两表 → 两全局表单卡片
`QuotasPage.tsx` 的两张按账号表格（行内编辑走弹窗，非 antd inline）改为两张**全局表单卡片**：去账号列、去编辑弹窗里的账号、去任何账号选择；`来源` 由每行 Tag 改为每卡单个 override/builtin 徽标；文案改「对所有账号生效；未配置时用系统内置默认」。`types/api.ts` 的 `Catalog{limits[]/configs[]}` 数组壳收敛为单个全局对象；`api/queries.ts` 取数/写回改全局（端点名与 queryKey 可不变）。与 `account-real-nickname` 仅共享 `types/api.ts` 且改不相交接口——合并无冲突。

## Risks / Trade-offs

- **`role-dispatcher.ts` 多 change 热点**（A①/A②/B 都改它；`multi-account-node-support` 35/36 正在同文件穿 `currentAccountId` 多租路由）→ B 的改动严格限定 7 个 provider 调用点；与 `multi-account-node-support` 协调 land 顺序；逐 hunk 暂存提交（参照「并发会话精准 git add」纪律）。
- **`start()` 清空命令队列** → 靠重启后重报卡片驱动，绝不「先 push 再 start」；写测试覆盖「循环已停→收 page.scroll→重启→重报 cards」。
- **边端自动重启误复活** → 重启须被主动关闭/下线流程抢占（关闭中迟到命令不复活）；加 shutdown 守卫与回归用例。
- **B 反转生产 schema** → 前向迁移；部署前 ECS 备份；旧表数据迁入全局行后再废弃旧维度；never-brick 回落兜底。迁移须确认 ECS 上是否真有 `default` 行（store 不预置行；运营经面板设过 30min 则应有该行）——若无行则表空、回落写死默认（零回归）；若存在多个非 default 账号行，安全配置本不该按账号，迁移取 `default` 行值、其余按账号行废弃并 `log` 记录。
- **B spec 归档时序**（D6）→ 现用 ADDED 让 propose 阶段 validate 可过；归档前按 D6 改写 + 重新 validate。若团队选择先并行而 `session-limits-to-quota-layer` 迟迟不归档，B 归档前必须主动处理其未并入 delta，避免 baseline 双写。
- **A② 协议复用的隐性前提** → 依赖 `page.scroll` 持续在白名单；若未来有人收紧白名单需回归保护（既有 AC-PROTO 白名单回归断言覆盖）。

## Migration Plan

1. **edge（A②）** 本地改 `browse-session.ts`，`npm run typecheck` + `npm test` + `npm run test:acceptance`（含 AC-PROTO 白名单回归）。
2. **cloud（A①/A②/B）** 本地改 + 新迁移 `0022`；`npm run test:acceptance` 先过（AC-PROTO/AC-PUB/AC-RISK 红线），再全量 `npm test`，再 `npm run typecheck`。新增 A 回归用例与 B 全局存储用例。
3. **console（B）** `npm run build` 通过；本地连面板冒烟。
4. **部署（显式动作，按 CLAUDE.md §5 安全序列）**：cloud 先 ECS 备份（`cloud.bak.<ts>.tar.gz` + `.env.bak`）→ 迁移 `0022` 在 PG 执行（迁入 default 值）→ rsync（排除 `.env/node_modules/.git`）→ `systemctl restart aidcp-cloud.service` → healthcheck（active + 8787 + 飞书长连 + `select 1`）→ 失败即回滚。console 静态 + nginx。**红线：绝不碰同机 isales**。
5. **回滚**：恢复备份 tar + `.env`；迁移设计保留旧表/旧列直至全局行验证生效后再清理，使回滚不丢数据。
6. **真机验证**：edge 真账号连生产，证 A（结束→~1min 续场→边端重报卡片→闭环恢复）与 B（设全局 30min → 任意账号单场按 30min；改全局续场/看门狗即时生效）。

## Open Questions

1. **迁移形态**：新建单行表 vs 原表收敛（drop `account_id` PK、留单行）？倾向**原表收敛 + 迁入 default 值**（表名/queryKey 不变、改动小）。
2. **console 编辑 UX**：每卡常驻 inline `<Form>` + 各自 Save（推荐，单记录更顺）vs 保留单个编辑弹窗去掉账号？
3. **面板路由命名**：保留现 `/api/session-limits`（与 `/api/resume-config` 不对称）还是改名 `/api/session-config` 求对称？倾向**保留**（console 已接线、churn 小）。
4. **A② 云端落点**：`feed.entered` 翻译分支（推荐，单一发命令出口）vs 直接在 `startSession/restartSession` 发？
5. **边端自动重启触发面**：任意非 `session.end` 浏览类命令即重启（简单、覆盖 idle nudge 与 session_start nudge）vs 仅显式唤醒命令？倾向前者 + shutdown 守卫。
6. **default 行确认**：部署前在 ECS 实证 `session_config`/`resume_config` 是否有 `default` 行及其值（确认 30min 会被迁移带走）。
