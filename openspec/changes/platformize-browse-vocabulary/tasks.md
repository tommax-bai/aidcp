# Tasks

> 词汇蓝图批 4。**迁移＝直接切换**：旧名从两份穷举表直接删，typecheck 即守卫；名表唯一权威＝design §1（22 条）。
> **双仓锁步批**：改两份 protocol.ts + 两份登记表 + bridge，`land-change` 单仓串行模型中间态必红——照批 1 工序
> 「各 worktree rebase → 全量测试 + gate:native → 成对 ff push → 立即 protocol-parity + operation-registry-parity 复验全绿」。
> **并行冲突预案**：`restore-native-facebook-residual-parity` / `blocking-overlay-dom-capture` 在飞；引擎文件与
> `native-facebook-behavior-parity` spec 后到者 rebase。热点单写：两份 protocol.ts、登记表、bridge、白名单本批独占。
> **同形异义不改**：v1 `PlanStep.actionId` 的 `page.scroll`（`command.rs:973`、`xhs-command-router.js:910,912`）；
> EventBus 事件名（`feed.refresh.needed`、`notification.opening/browse_category/…`、`page.cards.arrived`）。

## 0. 前置核实（已完成，2026-08-06 本 session）

- [x] 0.1 面枚举坐实：feed/search/reels 三面；群滚动=引擎内部分解非协议命令；notification 结构性 xhs-only；FB search 成立；`note.close` 云端零发送点（留批 6 裁分工）。
- [x] 0.2 批 1 遗留修正：`browse_next` 真死可删；`browse_scroll` 是首帖探测内部载体、只改注记不删。
- [x] 0.3 规格引用分诊：4 个 capability 语义真变手写 delta；~29 个纯名字提及走机械批（6.1 名单）。

## 1. aidcp-edge（worktree `../aidcp-edge.wt/platformize-browse-vocabulary`）

- [x] 1.1 `src/comm/protocol.ts`：`MessageType` 删 14 增 22；`PayloadMap` 同步；载荷接口保留共享（`PageScrollPayload` 删 `targetSurface`、注释改面段说明；其余接口名不动，多名共用）；文内 prose 引用同步。
- [x] 1.2 `src/client/operation-registry.ts`：14 → 22 条，描述符逐条继承（`facebook.group.join` 保 `account_visible`），共 52 条。
- [x] 1.3 `src/client/edge-client.ts`：主动命令白名单 if-链 14 → 22 条（typecheck 不可见，逐条对名表核）。
- [x] 1.4 `src/client/command-diagnostics.ts`：`ACTIVE_COMMAND_TYPES` / `FIXED_SUMMARIES` / `summarizeCommand` 分支换 22 新名；`facebook.reels.scroll` 成独立类型后，Reels 标签判定从「type+中文摘要文案匹配」简化为按类型直判。
- [x] 1.5 `src/native-page-engine/command-mapper.ts`：信封→kind 表 22 条；新增 (platform, surface) 解析、scroll 三面 stamp 进引擎参数；`actionNames` 只改键值不动。
- [x] 1.6 `src/native-page-engine/browse-session.ts`：删 `FACEBOOK_UNSUPPORTED_COMMANDS` 拒集及其执行点；`search.execute` 回执特判改双平台新名。
- [x] 1.7 引擎：`command-manifest.json` schema `routeKey`/`edgeType` → `edgeTypes[]`（14 条目覆盖 22 信封名，kind 1:1 守恒）；Rust `PageScrollParams.target_surface` → 三值 `surface` 必填、`resume_target_missing` 臂删；FB 路由面分派按名声明+执行点核对（跨面到达诚实拒绝）；`browse_next` 全链删 + `browse_scroll` 注记改写（design §7 清单）；`node scripts/build-native-page-engine.mjs` 重建重钉 digest 五位点（**含生产常量 `native-page-engine-artifact.cjs:19`**）。
- [x] 1.8 `src/electron/renderer/renderer.js`：诊断标签表 22 新名 + 删 `browse.next`/`browse.scroll` 死键；Reels 标签改按类型直判。
- [x] 1.9 退役但仍编译代码同步改名（`src/browse/browse-session.ts`、`src/facebook/{facebook-session,comment-handler,join-handler}.ts` 及 `FB_COMMAND_ACTION_NAMES` 键）。
- [x] 1.10 测试：protocol-contract 穷举表 + 计数 95→103；operation-registry / manifest / 路由回归断言 / digest 两夹具；每平台至少一条新名命令过入口闸→mapper→引擎的端到端断言 + 平台段闸拒收断言（`xiaohongshu.*` 发 FB 会话）。
- [x] 1.11 `npm run typecheck` + `npm test` + `npm run test:acceptance` + `npm run gate:native` 全绿；变异验证按「先 commit 再变异→红→复原→复跑回绿」。

## 2. aidcp-automation（worktree `../aidcp-automation.wt/platformize-browse-vocabulary`）

- [x] 2.1 `src/comm/protocol.ts`：与 edge 逐字一致（同 1.1）。
- [x] 2.2 `src/comm/operation-registry.ts`：同 1.2 共 52 条；头注「46 条」笔误改实数。
- [x] 2.3 `src/comm/command-bridge.ts`：改 (action, platform[, surface]) 穷举组合表，`satisfies` 钉 `MessageType`，不存在组合响亮 throw；签名加 `platform` 参数。
- [x] 2.4 平台穿入：`automation-main.ts` `sendCommand` 三参 → 携平台；`automation-connection-dispatcher.ts:580` 闭包传 `ctx.platform`。
- [x] 2.5 `src/orchestrator/role-dispatcher.ts`：`EdgeCommand` 增可选 `surface`；显式面发送点标面（redrive/reels 续场/search/feed 各点）；无面发送点接单点解析器 `currentScrollSurface()`（sourcePageType + FB reels 在场态，默认 feed）；删 `targetSurface` 参数用法。
- [x] 2.6 `src/comm/handler.ts`：`LEGACY_ACTION_COMPLETION_ALIASES` 键 14→22 直接换（值不动）。
- [x] 2.7 直发点改名：`comment-agent/edge-steps.ts`（xhs 三处）、`facebook-edge-steps.ts`（三处）、`facebook-group-join-edge-steps.ts`（`facebook.group.join`）。
- [x] 2.8 `ws-server.ts` 出口闸零改动核验转正（新增断言：真实新名对错平台拒发、对正确平台放行）。
- [x] 2.9 测试全量更新（protocol-contract 计数 103、comment-agent 系列、ws-server-target-guard、platform-browse-protocol 等）；`npm run typecheck` + `npm test` + `npm run test:acceptance` 全绿；变异验证同 1.11 纪律。

## 3. 控制仓

- [x] 3.1 `docs/protocol.md`：§2 表 14 行 → 22 行、载荷节改名、bridge 映射段、`group.join` 直发注记、reels redrive 行文（`facebook.reels.scroll{reason:'resume_redrive'}`）。
- [x] 3.2 `docs/edge-command-grammar.md`：批 4 行标 ✅ + 前置核实结论（群滚动内部分解、notification xhs-only、`note.close` 零发送点→批 6、FB search 成立、reels 第三面）；`page.scroll` 拆分行按名表定稿。

## 4. 集成（双仓锁步）

- [x] 4.1 两 worktree 各自 rebase 最新 master → 全量测试 + gate:native 绿。
- [x] 4.2 成对 ff push（`git push origin <branch>:master` ×2，中间不跑闸）→ 立即 `python3 scripts/protocol-parity` + `python3 scripts/operation-registry-parity` 复验全绿（各 52 条）。
- [ ] 4.3 清 worktree。

## 5. 部署与切换窗口

- [x] 5.1 部署 `dev`（§5 安全序列：备份 `automation.bak.<ts>.<tag>.tar.gz` → rsync → restart → healthcheck active/NRestarts=0/8787/零 error）。**绝不碰 aidcp-cloud 单体与 isales。**
- [x] 5.2 部署后观察日志：新名命令 `platform_mismatch`/`operation_unclassified` 拒收计（旧客户端 fail-closed 属预期）；无其他新增 error。
- [ ] 5.3 **提请用户出包装机**（切换窗口连续完成的另一半；打包动作用户显式触发，不自动执行）；真机验收项登记 `docs/real-machine-acceptance-backlog.md`（并入现有边缘出包簇）。

## 6. spec delta 机械批

- [ ] 6.1 脚本化生成纯名字改名 delta，覆盖（以归档时 grep 实测为准）：command-pacing、native-facebook-behavior-parity、facebook-scheduled-comment、browse-loop-resilience、edge-companion-ui、concept-pool-search、author-profile-visit、note-extraction-fidelity、interaction-risk-gating、session-auto-resume、platform-search-activity、platform-runtime-abstraction、native-xiaohongshu-behavior-parity、native-facebook-view-activity、interaction-cooldown、facebook-reels-navigation、facebook-group-membership、edge-task-execution-coordination、comment-interaction、accounts-master-data、account-identity-resolution、native-page-engine、facebook-identity、facebook-group-join-resilience、curated-note-actions、console-panel-api、comment-search-command、captcha-incident-handling、facebook-scheduled-comment 等；逐条人审「机械改名 vs 语义变化」，语义变化升级为手写 delta。
- [ ] 6.2 归档前对当时最新 spec 文本重生成一遍（防并行 change 的 delta 撞车），`openspec validate platformize-browse-vocabulary --strict` 过。

## 7. 归档

- [ ] 7.1 全部 task 勾完 → validate --strict → archive（delta 并入主 spec）；蓝图 §6.3 批 4 行终态回写。

## 8. 实装偏离与实录（2026-08-07）

- **落点**：edge master `7daced2`（改名主提交 + 22 条路由断言补强，rebase 后含并行 blocking-overlay 两提交之上）、
  automation master `feeab71`、kernel `9f68ded` + **tag v0.1.2**、控制仓 `28627ce5`（立案）+ `90d568db`（protocol.md/蓝图同步）。
  parity 复验：protocol.ts 逐字一致、登记表各 52 条。部署 dev：`automation.bak.20260807-110723.vocab-batch4.tar.gz`
  备份 → rsync（kernel v0.1.2 随包送 node_modules）→ restart → healthcheck 全过（active/NRestarts=0/8787/零 error）。
- **计划外发现一（kernel 共享包点名旧命令）**：`aidcp-kernel` 的副本陈旧传输豁免名单（`transport-gate-exemptions.ts`）
  写死 `note.close`——不改则改名后详情页收尾在 mirror-unknown 窗被扣住。已改 kernel 源+测试（78/78）出 v0.1.2 tag，
  automation pin 升级（transport 同时随主干升 v0.1.4）。**api / content 仓的 kernel pin 未随本批升级**（§8.2 落后只报不拦）；
  api 进程出口闸在其升级前对新名 note.close 不豁免——api 不推浏览命令，风险登记不阻塞，pin 升级随各仓节奏。
- **计划外发现二（批 1 遗留不能全删）**：`browse_scroll` Rust 变体是首帖探测的引擎内部载体
  （`facebook/runtime.rs` 构造），只删 `browse_next`；`browse_scroll` 排除表理由与 postconditions 证据改写留任。
- **偏离一（scroll 拆名的引擎表示）**：Rust `PageScrollParams.surface` 为 `Option`（内部构造与测试兼容），
  非 design 所述必填——TS mapper 恒 stamp，协议层语义不变；`deny_unknown_fields` 拒绝 `targetSurface` 回流（有序列化测试钉住）。
- **偏离二（scheduler 测试断言口径）**：`comment-scheduler.test` 断言命令**序列**，改用剥平台前缀的
  `commandName()` 归一助手（精确名由 edge-steps / bridge / 契约 / 出入闸测试钉死），非逐处写死平台名。
- **变异验证实录**：白名单删 `facebook.reels.scroll` 首轮未被抓住 → 补 22 条逐条路由断言后红/绿循环闭合；
  manifest 删一条 edgeTypes 即红。全量最终口径：edge 3217/0 + acceptance 40/0 + gate:native；automation 2357/0 + acceptance 297/0。
- **AC-PROTO-02 计数 95→103**（交接文档「改名计数不变」预判有误：平台变体展开净 +8）。
- **切换窗口现状**：dev 云端已发新名，旧客户端 fail-closed 拒收（预期）；**dev 车队浏览停摆直至出包装机**（5.3 待用户触发）。
