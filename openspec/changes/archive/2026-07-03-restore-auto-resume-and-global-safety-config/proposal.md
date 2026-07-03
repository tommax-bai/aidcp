## Why

一次真机测试（edge 真账号连生产云端 `ws://121.89.85.150:8787`）暴露两个**互相独立**的缺陷，需在同一 change 内分两条线（stream A / stream B）修，但**根因与修法不同、可分别落地**：

- **A — 自动续场彻底失效**：会话正常结束后云端**从不自动续场**，节点空转；新未读检测到也无人处理。根因是会话结束流程被**调了两次**，第二次把第一次刚为续场武装的休息计时器清掉、随即早退不再武装 → 续场永不触发（对所有结束方式必然发生）；即便修好，云端续场也**不重新驱动边端**、边端循环已停且无命令能唤醒它。这违反既有 `session-auto-resume` 能力「单场正常结束后自行接续而非停摆」的契约——是**回归修复**，非新功能。
- **B — 单场/续场安全配置错误地按账号维度**：后台对某账号设的「单场 30min / 续场策略 / 看门狗阈值」对真实账号无效（真实账号缺行回落写死默认 10min）。根因是这些**安全限额**被做成**按精确账号查表**。用户 2026-06-27 拍板：单场会话上限、续场策略、看门狗本质是**全局安全策略**，应**取消账号维度**——一份全局配置管所有账号。这是对前序两个 change（`session-limits-to-quota-layer`「按账号」决策 2026-06-24、及已归档的 `session-auto-resume-with-excursions`）的**明确决策翻转**，本 change 作为**取代前序「按账号」决策的新 change**推进。

两者都需修，不能只修一个：A 解决「续场没触发」，B 解决「30min 没生效（会话 10min 就结束）」。

## What Changes

### Stream A — 恢复自动续场（aidcp-cloud + aidcp-edge）

- **A① 消除会话结束双调（cloud）**：让「监测体正常结束」只有**单一**结束入口。删去 `session.should_end` 处理器里的二次结束调用（`role-dispatcher.ts:1083`），由会话监测体的结束回调（`role-dispatcher.ts:532` 注入、`session-monitor-role.ts:247-255` 触发）**唯一**负责结束。触发体已是「先发结束命令给边端、后走结束回调武装续场」的正确顺序。
- **A② 续场后主动重新驱动边端（cloud + edge）**：
  - cloud：续场重开会话发出的 `feed.entered{trigger:'session_start'}` 当前在翻译处理器（`role-dispatcher.ts:1028-1038`）里是 no-op（只对 `back_to_feed` 发命令）。为 `session_start` 增一条引导命令分支，下发一次滚动以重新驱动边端。
  - edge：边端浏览循环收到结束命令后停止（`browse-session.ts:295-301`），此后云端命令被静默堆进无人消费的队列（`browse-session.ts:374-382`），且**无任何命令路径能重启循环**。改为：循环已停时收到浏览类命令即重启循环（`start()` 已有幂等守卫），靠循环重新上报卡片再次驱动云端决策环。
- **复用既有滚动通道、不动协议**：经核实，引导用的滚动命令已端到端接线（动作 `scroll` → 消息 `page.scroll`，`command-bridge.ts:22-23`；边端主动命令白名单已放行 `page.scroll`，`edge-client.ts:353`）。**不新增协议消息类型**，不动两份 `protocol.ts` / `command-bridge.ts` / `docs/protocol.md`，不触 AC-PROTO 四点同步闸与白名单遗漏陷阱。（交接文档原担心的「协议映射 landmine」经核实**不成立**——真正卡点是边端循环已死、命令无人消费。）
- **回归断言（cloud）**：新增测试——一次监测体结束 MUST 只触发一次结束流程，且结束后续场休息计时器处于「已武装且未被取消」。

### Stream B — 单场/续场安全配置去账号维度、改全局通用（aidcp-cloud + aidcp-console）

- **BREAKING（配置面）取消账号维度**：单场会话上限（单场时长 + 单场互动预算）与续场/看门狗配置（rest_ratio、活跃时段窗口、每日上限、看门狗两段阈值）各收敛为**一份全局配置**——无 `default`、无按账号覆盖。
- **cloud 存储收敛为全局单例**：`session-config-store.ts` / `resume-config-store.ts` 的内存镜像从 `Map<accountId,Row>` 改为单个全局行；DB 改单行表（参照 `model-config-store.ts` 的 `id=1 CHECK` 单行模式）。新增**前向迁移**（`0022`）把现有 `account_id='default'` 行的值搬成全局行——**已设的 30min 立即作为全局生效、零数据丢失**。
- **cloud provider 接口去 accountId**：`SessionLimitProvider`（`risk/session-limits.ts:63`）与 `ResumeConfigProvider`（`risk/resume-limits.ts:60`）共 7 个方法去掉 `accountId` 参数，返回全局值；同步改 `role-dispatcher.ts` 的 7 个调用点（`:345,:536,:537,:621,:761,:799,:801`）。（会话监测体 `session-monitor-role.ts` 的 thunk 本就是无参 `()=>number`，**无需改**。）
- **cloud facade / 面板 API 去账号目录**：`session-config-facade.ts` / `resume-config-facade.ts` 从「`{'default'} ∪ getAll()` 账号目录」改为单个全局读/写；面板路由 `/api/session-limits`、`/api/resume-config`（`panel-server.ts:645,:705`）与 DTO（`panel/types.ts`）去 accountId、改全局形态。
- **console 改全局表单**：`QuotasPage.tsx` 的「单场会话上限」「自动续场与看门狗」两张**按账号表格 + 行内编辑弹窗**改为**两张全局配置表单卡片**（去账号列、去编辑弹窗里的账号、去任何账号选择）；`types/api.ts` / `api/queries.ts` 的 DTO 与取数/写回去账号维度。文案改为「对所有账号生效的全局安全限制；未配置时用系统内置默认」。
- **绝不 brick / 不触风控单写**（保留前序不变量）：全局配置缺失或字段非法时**逐项回落写死默认**（`risk/*.ts` 的写死常量保留作系统内置默认）；存储与编辑 MUST NOT 触碰风控状态单写路径（`RiskController` / `risk_state`）。
- **明确不动**：配额（按档位×动作，本就全局）；人设 `persona-store`、密钥 `credential-store`（按账号是对的，正交保留）。

## Capabilities

### New Capabilities
<!-- 无新增 capability：A 是既有续场能力的回归修复 + 边端唤醒补强；B 是把既有安全限额能力从按账号翻转为全局，delta 并入既有 capability -->

### Modified Capabilities

- `session-auto-resume`:
  - **A**：新增「会话正常结束流程对单次结束只触发一次、MUST NOT 取消同次为续场刚武装的休息计时器」；新增「续场重开会话后 MUST 主动重新驱动边端浏览闭环（复用既有滚动通道）」。
  - **B**：把「休息时长 = 该账号单场时长 × rest_ratio」「三道护栏阈值按账号可配」「续场/护栏配置按账号落库」从**按账号**改为**全局单例**（每日上限的**阈值**全局、计数仍按账号按日统计）。
- `browse-loop-resilience`:
  - **A**：新增「浏览循环因结束命令停止后 MUST 可被云端浏览类命令唤醒重启，MUST NOT 把命令静默堆积到无人消费的队列」。
  - **B**：把「看门狗两段阈值按账号可配、运行时现读」从**按账号**改为**全局**。
- `interaction-risk-gating`:
  - **B**：新增「单场会话上限（时长 + 六项互动预算）为**全局配置**、运行时现读、缺失/非法回落写死默认、不触风控单写」，**取代** `session-limits-to-quota-layer` 引入的「按账号」单场上限要求（见 design 的归档协调）。

## Impact

- **aidcp-cloud**：
  - `src/orchestrator/role-dispatcher.ts`（A①：`:1083` 删二次结束；A②：`:1028-1038` 加 `session_start` 引导分支；B：7 个 provider 调用点去 accountId `:345,:536,:537,:621,:761,:799,:801`）。
  - `src/agents/session-monitor-role.ts`（A：`:247-255` 触发体顺序复核；B：无需改，thunk 已无参）。
  - `src/config/session-config-store.ts`、`src/config/resume-config-store.ts`（B：`Map<accountId,Row>` → 全局单行；DB 单行表 `id=1 CHECK`；保「写库成功才刷镜像 / 逐字段非法回落 / 永不抛」三不变量）。
  - `src/config/session-config-facade.ts`、`src/config/resume-config-facade.ts`（B：去账号目录、改全局读写）。
  - `src/risk/session-limits.ts`、`src/risk/resume-limits.ts`（B：provider 接口去 accountId；写死默认常量保留作 builtin fallback）。
  - `src/panel/panel-server.ts`、`src/panel/types.ts`（B：`/api/session-limits` `:645/:653`、`/api/resume-config` `:705/:713` 去 accountId）。
  - `src/server.ts`（B：store 装配 / provider 注入随接口微调）。
  - `migrations/0022_*.sql`（B：**新增**——session_config + resume_config 收敛为单行全局表，迁入现有 `default` 行值。现有最高 `0021`，`0012/0017` 缺号；动前 `ls migrations/` 复核取号）。
  - 测试：`test/session-config-store.test.ts`（重写为全局）、`test/resume-config-store.test.ts`（**新建**）、`test/session-config-facade.test.ts`、`test/session-effective-limits.test.ts`、`test/integration/role-dispatcher-resume.test.ts`（mock provider 改无参）；A 回归断言（新增「单次结束=单次 endSession + restTimer 存活」用例）。
- **aidcp-edge**：
  - `src/browse/browse-session.ts`（A②：`:374-382` 循环已停时收到浏览类命令重启循环；注意 `start()` `:280` 会清空命令队列，靠循环重报卡片驱动而非保留排队命令）。
  - `src/main.ts`（A②：仅当选「专用 resume 信令」才需改；复用 `page.scroll` 则 `:368-376` 不动）。
- **aidcp-console**：
  - `src/pages/QuotasPage.tsx`（B：两张按账号表格 → 两张全局表单卡片）、`src/types/api.ts`（B：DTO 去 accountId、Catalog 数组 → 全局对象）、`src/api/queries.ts`（B：取数/写回改全局）。
- **协议 / docs**：**无改动**（A 复用既有 `page.scroll` 通道；B 是云端内部配置不经协议）。
- **前序 change 协调**：B 取代 `session-limits-to-quota-layer`（active 34/36、已部署生产 cloud `f1e0883`）的按账号单场上限 + 已归档 `session-auto-resume-with-excursions` 的按账号续场/看门狗（其要求已并入 `session-auto-resume` / `browse-loop-resilience` 正式 spec）；归档顺序见 design。`account-real-nickname`（已部署、28/30）经核实**不动** `QuotasPage`，仅与 B 共享 `console/src/types/api.ts` 且改的是不相交接口——无逻辑冲突。`role-dispatcher.ts` 为多 change 热点（尤其 `multi-account-node-support` 35/36 在同文件穿 accountId 多租路由），B 的 7 个调用点改动须与其 land 顺序协调。
- **红线保留**：MUST NOT 静默假成功；绝不 brick；不触风控状态单写；不漂移协议四点。
