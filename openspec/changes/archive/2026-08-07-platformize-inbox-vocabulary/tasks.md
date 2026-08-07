# Tasks

> 词汇批 6a：15 条 `interaction.*` → `wechat_channels.inbox.*`（design §1 名表为唯一权威）。
> 与批 6b（`platformize-publish-navigation-vocabulary`）并行开发、**集成串行、本批先落**。
> 静默失效点清单见 design §3（11 处），sed 红线见 design §4——实装时逐条对单。

## 0. 前置核实（已完成，2026-08-07 本 session 四路探查）

- [x] 15 条全量清单与方向（protocol.ts:146-161 穷举，修正蓝图「10 条」滞后计数）
- [x] kernel / transport 零协议消息名占用（本批不出 kernel 版本）
- [x] command-bridge / 动作关联键三表零占用（wechat_channels 空映射是设计）
- [x] `interaction.reply.send` 身份闸豁免已结构化（类别推导，无手抄清单可漏改）
- [x] `.result`/`.ack` 裁决事实齐备（三条 ack 方向、reply.result 一型两用、前缀匹配依赖）

## 1. aidcp-edge（worktree `../aidcp-edge.wt/platformize-inbox-vocabulary`）

<!-- aidcp-edge 7cbfbea 全部 1.1-1.9 一次落地（16 文件 172 行）；89911e4 集成期补 protocol-validation 名单逐名穷举断言（变异②首轮存活，批 5 同型教训重演）。typecheck 0 错，npm test 3240/0 败。 -->

- [x] 1.1 `src/comm/protocol.ts`：union（:146-161）+ PayloadMap（:2167-2181）15 条换名；`Interaction*` 类型标识符与能力串常量（:304-309）不动
- [x] 1.2 `src/wechat-channels/runtime.ts`：全部 send/request/断言点（:130/:135-136/:244/:258-261/:286-289/:593）与 envelope 分派（:318/:330/:337/:527/:531/:539/:572/:576/:596/:610/:624/:659）换名
- [x] 1.3 `src/wechat-channels/protocol-validation.ts`：扁平名单数组（:25-39）与 switch（:571-585）**成对**换名
- [x] 1.4 `src/wechat-channels/{sync-common,connector}.ts` 错误串内嵌消息名（design §3 #6）
- [x] 1.5 `src/client/edge-client.ts`：主动命令白名单 10 条（:761-772）+ `interactionExtensionCapability` 前缀匹配（:1016-1023，裸 string）
- [x] 1.6 `src/client/operation-registry.ts`：10 个 IM 键换名（platform_api_automation 4 条豁免成员随键名迁移、集合不扩）；`interaction.auth.request` / `interaction.workspace`（CLIENT 注册表，IPC 通道名）不动
- [x] 1.7 `src/client/command-diagnostics.ts`：`ACTIVE_COMMAND_TYPES`（:72-81）/ `FIXED_SUMMARIES` / `:279` 裸串三张结构
- [x] 1.8 `src/electron/renderer/renderer.js:2588` 中文标签键
- [x] 1.9 测试：protocol-contract 15 名穷举表、edge-client 白名单路由回归（22 处）、operation-registry、command-diagnostics、wechat-channels 桶（offboard-runtime 等）
- [x] 1.10 `npm test` + `npm run typecheck` 全绿

## 2. aidcp-automation（worktree `../aidcp-automation.wt/platformize-inbox-vocabulary`）

<!-- aidcp-automation a18488c（36 文件：14 编辑 + 22 fixture 迁移）。npm test 2413/0 败。偏离实录：①换名后 IM 族首次落入平台段出入闸辖区（旧名不过闸）——生产正确（sidecar hello 声明 wechat_channels、handler 持久化、解析器已要求该平台），但 ws-server-target-guard 两个 mock edge 未声明平台导致 pushToEdges=0 悬挂整套件，已补声明；②fixture 实为 20 份带类型 JSON + hello/welcome 共 22 份（任务写 21 系笔误）；③正则形引用（offboard-cleanup-core-contract.test.ts 转义点号）字面 grep 不可见，已改；④connector.ts:333 'interaction.command' 为错误上下文标签非线缆名，保留。 -->

- [x] 2.1 `src/comm/protocol.ts` 与 edge 逐字节一致（同 1.1）
- [x] 2.2 `src/comm/handler.ts`：5 入口 case（:624-632）+ 4 处 ack 构造（:1249/:1266/:1282/:1336）+ 6 处中文错误串（design §3 #7）
- [x] 2.3 `src/comm/ws-server.ts:394-395` 验证码暂停旁路集
- [x] 2.4 `src/comm/operation-registry.ts` 10 键与 edge 份逐条一致
- [x] 2.5 `src/interactions/{send-orchestrator,offboarding-service}.ts` 全部发送点（:269/:301/:338/:354/:382、:20）+ `src/automation-main.ts:1735`
- [x] 2.6 `src/automation-edge-access.ts:316` `interaction.offboard.` 前缀
- [x] 2.7 fixture：`test/fixtures/wechat-channels-interaction/` → `wechat-channels-inbox/`（21 份 JSON `type` 字段）+ `contract-fixtures.test.ts` 对照表与 `:94` 前缀断言
- [x] 2.8 其余测试：protocol-contract、ws-server-target-guard、offboarding-service、send-orchestrator 相关
- [x] 2.9 `npm test` + `npm run typecheck` 全绿

## 3. aidcp-cloud（集成测试仓，master 直改——无业务源码，仅 test/）

<!-- aidcp-cloud 84d6cdb：fixture 目录迁移 + contract-fixtures/send-orchestrator/pg-interaction-store 换名；interactions 桶 20/0 败。mirror-stale-stop-work 旧名向量按计划不动（经 api v0.1.1 旧 kernel 解析）。 -->

- [x] 3.1 fixture 21 份 + `contract-fixtures.test.ts` 与 automation 份逐字同步（目录同步改名）
- [x] 3.2 `test/interactions/` 桶（send-orchestrator.test 等 3 文件）换名；`mirror-stale-stop-work` / `handler.test` 的旧名字面属批 4/5 遗留断言、经 api v0.1.1 旧 kernel 解析，本批不动
- [x] 3.3 集成仓相关桶跑绿（硬前置：四兄弟仓已 clone + npm ci）

## 4. 集成（双仓锁步，本批先落）

<!-- 2026-08-07 集成：acceptance edge 40/40、automation 300/300；ff 落 edge 89911e4 / automation a18488c 并推送。四道复验全过（protocol-parity 逐字一致、登记表 56 条一致、关联键三表一致）。变异：①白名单删条→路由断言红 ✓；②validation 数组删条→首轮存活→补逐名穷举测试后红 ✓；③fixture 对照表改名→红 ✓；均复原回绿。 -->

- [x] 4.1 edge / automation worktree 各自 rebase 最新 master，跑 `test:acceptance` + typecheck
- [x] 4.2 ff 合入两仓 master + push；控制仓四道复验：protocol-parity + operation-registry-parity + action-key-parity（零改动跑通）+ typecheck
- [x] 4.3 变异纪律（先 commit 再变异）：白名单删条 / validation 数组删条 / fixture 对照表改名 三类各一，必红后复原回绿

## 5. 部署与切换窗口

<!-- 与 6b 同车部署 dev（2026-08-07 19:01，备份 automation.bak.20260807-185305.vocab-batch6.tar.gz，healthcheck 全过，60s 零 error）；IM 新名收发待视频号 sidecar 下次上线自然验证（登记真机簇 155）。出包窗口并入批 1–6 积压。 -->

- [x] 5.1 automation dev 部署（安全序列：backup → rsync → restart → healthcheck），确认 IM 族新名收发正常（send-orchestrator 日志）
- [x] 5.2 出包窗口照旧：并入批 1–5+7 未出包积压，真机验收登记 backlog（视频号 IM 链新名端到端）

## 6. spec delta 与文档

<!-- 控制仓（与 6b 集成同批提交）：docs/protocol.md 50 处换名（头部已明文不复制消息计数，无计数项）+ docs/contracts/wechat-channels-interaction/ 22 文件 58 处（schema const + ws fixtures + README——设计漏列的同步面，集成期发现）；edge-command-grammar.md 族约定表新增第三族 + 批 6a 行标 ✅ + 批 7 豁免注记销账。目录名与 capability 名（wechat-channels-interaction）为容器标签、另一命名空间，保留。 -->

- [x] 6.1 7 份机械 delta 已随 propose 生成（specs/ 下）；归档前对当时最新 spec 文本重生成一遍防漂移
- [x] 6.2 `docs/protocol.md`：§2 表 IM 15 行 + 载荷节标题与正文换名
- [x] 6.3 `docs/edge-command-grammar.md`：批 6 行标 ✅（IM 半边）+ **族约定表新增第三族「留痕写 durable-outbox 往返族」**（design §2 定案文本）+ §6.2 批 7 行豁免注记更新（到期已裁）

## 7. 归档

- [x] 7.1 `openspec validate platformize-inbox-vocabulary --strict` 通过
- [ ] 7.2 与批 6b 串行集成完成后 archive（specs delta 并入主 spec）
