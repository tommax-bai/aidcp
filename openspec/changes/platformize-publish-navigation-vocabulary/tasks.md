# Tasks

> 词汇批 6b：发布段化 + back/close 合并 + `task.*` + kernel v0.1.4（design §1 名表唯一权威）。
> 与批 6a（`platformize-inbox-vocabulary`）并行开发、**集成串行、6a 先落、本批 rebase 后重建 manifest 重钉 digest**。
> 静默失效点清单 design §6（10 处）、sed 红线 design §7——实装时逐条对单。

## 0. 前置核实（已完成，2026-08-07 本 session 四路探查）

- [x] 发布发送点唯一（automation command-sequencer:595）；content/api 零协议占用、不动
- [x] 平台事实：XHS 12 kind / FB 6 kind / 视频号 kernel 结构性拒绝；载荷 platform? 是手抄二元联合
- [x] 四层 `?? 'xiaohongshu'` 全单（api DB 层保留为事实缺省，automation 侧全清）
- [x] back/close 合并证据（FB 同路径、XHS close⊂back、云端零发送点、curator 判决落 back）
- [x] kernel 豁免表命中四改名面 → v0.1.4；transport 零占用不出版；api pin 不动（既有线头）

## 1. aidcp-kernel（worktree `../aidcp-kernel.wt/platformize-publish-navigation-vocabulary`，先行）

- [ ] 1.1 `transport-gate-exemptions.ts`：`edge.task.acquire/release`→`task.*`、删两条 note.close、`navigation.back`→`xiaohongshu./facebook.` 两形（7→6 条）
- [ ] 1.2 `test/transport-gate-exemptions.test.ts` 逐条按序断言同步；`:35` stale `interaction.like` 换现役真名
- [ ] 1.3 package.json version 0.1.4 + `npm test` + annotated tag `v0.1.4` 推远端

## 2. aidcp-edge（worktree `../aidcp-edge.wt/platformize-publish-navigation-vocabulary`）

- [ ] 2.1 `src/comm/protocol.ts`：publish 对拆双平台（FB kind 6 词子集类型、载荷删 `platform?`）、note.close 2 条删除、`navigation.back`→2 平台形（XHS 形 `targetPage` 必填）、`edge.task.*`→`task.*`；107→108
- [ ] 2.2 `src/client/edge-client.ts`：`:880` publish 分支双名、`:891` task 分支、白名单 back 双名/note.close 删条；审批族**不进白名单**（红线复查）
- [ ] 2.3 `src/client/{operation-registry,command-diagnostics,identity-command-gate}.ts`：登记表 ±、ACTIVE_COMMAND_TYPES、FIXED_SUMMARIES、ackGap 串；`PUBLISH_KINDS` 集合核对不动
- [ ] 2.4 `src/main.ts`：publish 路由删 `?? 'xiaohongshu'`（平台从消息名前缀解析）、task 收发 7 处、result 发送名按平台
- [ ] 2.5 发布执行链：`flows/publish-command-handlers.ts`、`facebook/publish-executor.ts`（FB 非法 kind fail-closed）、`native-page-engine/{command-mapper,publish,client}.ts`
- [ ] 2.6 back/close：`browse/browse-session.ts` 与 `facebook/facebook-session.ts` 分派（close 臂删除、close 内部函数保留供 back 子步骤）、`FB_COMMAND_ACTION_NAMES` close 行删除、mapper `actionNames` 同步、XHS back 校验 targetPage 必填 fail-closed
- [ ] 2.7 native 引擎：`command.rs`（note_close kind 删除、navigation_back/publish 名表、`NavigationBackParams` targetPage 必填化）、`facebook/{feed,shared,capability}.rs`、`xhs-command-router.js:635-663`、`facebook-router/90-dispatch.js:120-123`
- [ ] 2.8 `command-manifest.json` + `command-timing.json`：publish 12 条 edgeTypes/receipts 分平台、note_close 条目删除、task 4 处；`build-native-page-engine.mjs` 重建 → digest 五位点重钉
- [ ] 2.9 `renderer.js` 标签表（:2561,2562 删、:2583-2585 换）；`ui-event-lines.ts`
- [ ] 2.10 测试约 20 文件（含 `command-manifest.test.ts:64-84` kind 冻结表按平台重构 + `:139` 跳过谓词同批改、protocol-contract 计数 108、「缺 targetPage 拒收」回归断言）
- [ ] 2.11 `npm test` + `npm run typecheck` 全绿

## 3. aidcp-automation（worktree `../aidcp-automation.wt/platformize-publish-navigation-vocabulary`）

- [ ] 3.1 kernel pin `#v0.1.3`→`#v0.1.4`（npm 改写后手工恢复 `git+ssh://` 形、lock 内层镜像同查）
- [ ] 3.2 `src/comm/protocol.ts` 与 edge 逐字节一致（同 2.1）
- [ ] 3.3 发布链静默缺省清零：`platform-profile.ts:27` 入参必填、`command-sequencer.ts:281/:296/:556`（:556 直写 `xiaohongshu.publish.command`）、`publish-dispatcher.ts:895`、`publish-scheduler.ts:336`、`automation-main.ts:1454` —— 缺失 fail-closed 带 `draft_platform_missing` 类原因
- [ ] 3.4 `command-sequencer.ts:595` 按平台选消息名；FB 计划 kind 类型面收窄（非法组合不可表示）
- [ ] 3.5 back：`command-bridge.ts` `back` 进平台组合表双平台映射、close_note 映射行删除；`role-dispatcher.ts:4424` targetPage 显式补 `'feed'`、`close_note` EdgeCommand 动作清退（EventBus/curator 词汇不动）
- [ ] 3.6 task：`edge-task-lease-client.ts`、`handler.ts:723,726`、`ws-server.ts:392-393`、`preemption.ts:13`、`automation-edge-access.ts:325`
- [ ] 3.7 `handler.ts` `LEGACY_ACTION_COMPLETION_ALIASES`：close 键行删除、back 键双名（值 `back` 不动）；`operation-registry.ts` 键 ±
- [ ] 3.8 测试约 12 文件（protocol-contract 计数、operation-registry「与 note.close 同侧」锚点重锚、bridge back 双平台用例）
- [ ] 3.9 `npm test` + `npm run typecheck` 全绿

## 4. aidcp-cloud（集成测试仓，master 直改）

- [ ] 4.1 `test/publish-agent/publish-dispatcher.test.ts:982,1019` 消息名；`test/integration/role-dispatcher.test.ts` back/targetPage 断言
- [ ] 4.2 `mirror-stale-stop-work` / `handler.test` 经 api v0.1.1 旧 kernel 解析、**不动**（既有线头）
- [ ] 4.3 相关桶跑绿

## 5. 集成（6a 先落，本批 rebase）

- [ ] 5.1 rebase 后 manifest 重建、digest 五位点第二次重算重钉（若与其他在飞 native change 撞，按批 5+7 工序第三次重算）
- [ ] 5.2 双仓 `test:acceptance`（AC-PROTO-* / AC-PUB-* / AC-RISK-* 全过）+ typecheck；ff 合入 master + push
- [ ] 5.3 控制仓四道复验：protocol-parity + operation-registry-parity + action-key-parity（close 行删除后三表仍对账）+ typecheck
- [ ] 5.4 变异纪律（先 commit 再变异）：① manifest 删 publish edgeType→必红；② kernel 豁免表删 `task.release`→必红；③ bridge 删 back 单平台映射→必红；④ FB 载荷塞 `set_schedule`→拒收断言必红；复原回绿

## 6. 部署与切换窗口

- [ ] 6.1 kernel tag v0.1.4 已推；automation dev 部署（安全序列 + healthcheck），发布链冒烟（XHS draft 下发用新名、缺 platform draft fail-closed 原因可见）
- [ ] 6.2 出包窗口照旧：并入批 1–5+7 积压；真机验收（XHS/FB 发布端到端、back 新名、task 租约链）登记 backlog

## 7. spec delta 与文档

- [ ] 7.1 手写 delta 3 份（publish-pipeline 含 RENAMED+ADDED、browse-loop-resilience、command-pacing）+ 机械 delta 9 份已随 propose 生成；归档前对当时最新 spec 文本重生成机械份防漂移（interaction-risk-gating 与 6a 各改不同 requirement，无冲突已核）
- [ ] 7.2 `docs/protocol.md`：头部计数 107→108、§2 表（publish/back/task 行、note.close 行删）、载荷节、bridge 映射段（`close_note` 行删、`back` 平台化）
- [ ] 7.3 `docs/edge-command-grammar.md`：批 6 行标 ✅（全批完成）、back/close 分工裁决记录（§8 待决销项）、快照声明计数更新

## 8. 归档

- [ ] 8.1 `openspec validate platformize-publish-navigation-vocabulary --strict` 通过
- [ ] 8.2 与 6a 串行集成 + dev 部署完成后 archive
