## Why

单场浏览会话到时间上限即结束，且**云端无任何自动重启**——结束后只有边缘重新 `hello` 或运营在面板 `dispatch stop→start` 才能重开，飞书 `/resume` 也不重启超时会话。结果：到点即停、一直停着，无人值守时自动化不会自行继续。本 change 补这个缺口，让单场结束后按「歇一会儿再续刷」自动接续，并守住人化节奏与风控。

同时，连续运营暴露两类「不该被单场计时打断、也不该计入单场时长」的活动：**稿件生成 / 发布** 与 **通知巡视**。发布走独立全局编排器、人审窗口可达 ~15min（整管线 ~18min），期间边缘离开 feed、浏览侧静默；若放任并发，空闲看门狗会在静默期误杀并发浏览会话，且续场会把边缘从发布页拽回 feed 撞页。巡视虽是会话内 excursion，但其耗时当前直接计入单场、且可能在巡视途中触发时限把巡视掐断。两者都要在「不被打断、不计时」上做对。

## What Changes

- **单场结束后自动续场（新行为）**：单场**正常结束**（时长到上限 / 动作数到顶 / 互动预算耗尽）后，云端等待 `rest = 该账号单场时长 × rest_ratio`（默认 10%，叠 lognormal 抖动）再自动重开一场（计时归零、预算刷新）。休息计时器**每连接私有**，在「运营 stop / 账号被风控暂停 / 边缘掉线 / 休息期边缘先自连」时立即取消，**绝不全局广播**。
- **续场护栏**：① **活跃时段窗口**（按账号配，仅窗口内自动续）；② **每日上限**（每天最多 N 场 / 累计 M 分钟，到顶停续）；③ **撞风控不续**（风控状态 restricted/frozen 时不续）。运营 stop / 验证码-风控暂停 / 断连**不**走自动续场路径。
- **发布「让位」（修改发布与浏览的交互）**：`/publish` 触发即**干净结束该账号当前浏览会话**（标记非续场、**不触发休息**），发布独占边缘跑完；发布**结束**（经发布编排器 try/finally 的唯一保证终止点）后**再起一场全新浏览会话**（同受续场各闸）。由此发布时长不计入单场、发布不被并发浏览会话撞页，且**监测体零暂停逻辑**。
- **通知巡视「轻离」（修改单场计时口径）**：会话监测体在巡视开始时**暂停时限判定**、巡视结束时**把巡视那段从单场时长扣除**；巡视期**不冻空闲看门狗**（巡视上报本就刷新它，卡死巡视由看门狗兜底，故无需额外封顶）。
- **空闲看门狗重调 + 可配置（修改既有看门狗要求）**：看门狗两段——**恢复轻推**（保持 ~2min 频繁，真瞬时卡顿快速自愈）与**放弃结束**（默认改 **1 小时**，仅戳不活的真死局才回收）。两段阈值做成**按账号可配 + 热加载 + 缺值回落默认**。
- **不动协议、不动边缘**：本 change 纯 cloud 内部行为与配置，无新消息类型、无新 cloud→edge 主动命令。

## Capabilities

### New Capabilities
- `session-auto-resume`: 单场正常结束后的「歇 N% 再续场」自动接续——续场资格（哪些结束续、哪些不续）、休息时长与抖动、活跃时段窗口、每日上限、撞风控不续、每连接休息计时器的生命周期（取消条件、绝不广播），以及上述配置的「落库 + 热加载 + 缺值回落默认 + 绝不 brick」治理纪律。

### Modified Capabilities
- `browse-loop-resilience`: 既有「会话必须在有界 idle 内自愈或终止」要求改为**两段阈值可配置 + 热加载**（恢复轻推保持频繁；放弃结束默认 1h；缺值回落默认）；新增**单场计时须排除会话内 excursion（通知巡视）耗时**、且**时限 MUST NOT 在 excursion 进行中结束会话**（延期到 excursion 结束再判）。
- `publish-pipeline`: 新增**发布与浏览会话互斥（让位）**要求——发布触发即结束该账号并发浏览会话（不计时、不续场），发布**保证终止**后再起一场全新浏览会话；发布时长 MUST NOT 计入任何浏览会话，且 MUST NOT 与驱动同一边缘的浏览会话并发。

## Impact

- **cloud（aidcp-cloud）**：
  - `src/agents/session-monitor-role.ts`：可暂停时钟（多原因引用计数 early-return + 末次解除前移 `startedAt` 扣除 excursion 段）；看门狗两段阈值改读注入的可配提供者；pause 态在 subscribe/unsubscribe 清空、绝不跨场残留。
  - `src/orchestrator/role-dispatcher.ts`：每连接休息计时器 + 续场闸（活跃时段/每日上限/风控/人设）；订阅 `excursion.requested/ended` 驱动监测体暂停/恢复；发布结束起新场入口。
  - `src/orchestrator/connection-runtime.ts`：按 `accountId` 定向的「结束/启动会话」桥（仿 `startAll/endAll`），供发布让位调用。
  - `src/publish-agent/{types,publish-orchestrator}.ts`：`OrchestratorDeps` 加 `onPublishStart/onPublishEnd` 回调，`trigger()` 在真正开始处与 `finally` 各调一次。
  - `src/server.ts`：装配——把发布回调接到连接注册表；配置 store/facade 初始化（与其余 config store 同 try/catch 退化）。
  - 配置层：新增按账号配置（`rest_ratio` / 活跃时段 / 每日上限 / 看门狗两阈值）的 store + facade，复刻 `session-limits-to-quota-layer` 的 `session_config` 范式（**需 DB 迁移**，迁移号实装前 `ls ../aidcp-cloud/migrations/` 复核取未用号）。
  - 面板 API 层：JWT 守卫的 GET/PUT 回显与非乐观写。
- **console（aidcp-console）**：配置编辑区（按账号：续场护栏 + 看门狗阈值），非乐观写。
- **协议 / 边缘**：零改动（不触两份 `protocol.ts` / `command-bridge.ts` / `docs/protocol.md`、不改 edge）。
- **红线 / 保留**：不碰风控状态单写（`setQuotaLevel` / `applySignal` / `risk_state`）；不碰发布审批链（`AC-PUB-*`）；不静默假成功（自动化最坏是**诚实暂停**而非乱跑）；`AC-PROTO-*` 无协议漂移；缺值/缺行/非法值**绝不 brick**、逐位回落写死默认（空配置与现状逐位一致，严格零回归）。
