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

- [ ] 1.1 `src/comm/protocol.ts`：union（:146-161）+ PayloadMap（:2167-2181）15 条换名；`Interaction*` 类型标识符与能力串常量（:304-309）不动
- [ ] 1.2 `src/wechat-channels/runtime.ts`：全部 send/request/断言点（:130/:135-136/:244/:258-261/:286-289/:593）与 envelope 分派（:318/:330/:337/:527/:531/:539/:572/:576/:596/:610/:624/:659）换名
- [ ] 1.3 `src/wechat-channels/protocol-validation.ts`：扁平名单数组（:25-39）与 switch（:571-585）**成对**换名
- [ ] 1.4 `src/wechat-channels/{sync-common,connector}.ts` 错误串内嵌消息名（design §3 #6）
- [ ] 1.5 `src/client/edge-client.ts`：主动命令白名单 10 条（:761-772）+ `interactionExtensionCapability` 前缀匹配（:1016-1023，裸 string）
- [ ] 1.6 `src/client/operation-registry.ts`：10 个 IM 键换名（platform_api_automation 4 条豁免成员随键名迁移、集合不扩）；`interaction.auth.request` / `interaction.workspace`（CLIENT 注册表，IPC 通道名）不动
- [ ] 1.7 `src/client/command-diagnostics.ts`：`ACTIVE_COMMAND_TYPES`（:72-81）/ `FIXED_SUMMARIES` / `:279` 裸串三张结构
- [ ] 1.8 `src/electron/renderer/renderer.js:2588` 中文标签键
- [ ] 1.9 测试：protocol-contract 15 名穷举表、edge-client 白名单路由回归（22 处）、operation-registry、command-diagnostics、wechat-channels 桶（offboard-runtime 等）
- [ ] 1.10 `npm test` + `npm run typecheck` 全绿

## 2. aidcp-automation（worktree `../aidcp-automation.wt/platformize-inbox-vocabulary`）

- [ ] 2.1 `src/comm/protocol.ts` 与 edge 逐字节一致（同 1.1）
- [ ] 2.2 `src/comm/handler.ts`：5 入口 case（:624-632）+ 4 处 ack 构造（:1249/:1266/:1282/:1336）+ 6 处中文错误串（design §3 #7）
- [ ] 2.3 `src/comm/ws-server.ts:394-395` 验证码暂停旁路集
- [ ] 2.4 `src/comm/operation-registry.ts` 10 键与 edge 份逐条一致
- [ ] 2.5 `src/interactions/{send-orchestrator,offboarding-service}.ts` 全部发送点（:269/:301/:338/:354/:382、:20）+ `src/automation-main.ts:1735`
- [ ] 2.6 `src/automation-edge-access.ts:316` `interaction.offboard.` 前缀
- [ ] 2.7 fixture：`test/fixtures/wechat-channels-interaction/` → `wechat-channels-inbox/`（21 份 JSON `type` 字段）+ `contract-fixtures.test.ts` 对照表与 `:94` 前缀断言
- [ ] 2.8 其余测试：protocol-contract、ws-server-target-guard、offboarding-service、send-orchestrator 相关
- [ ] 2.9 `npm test` + `npm run typecheck` 全绿

## 3. aidcp-cloud（集成测试仓，master 直改——无业务源码，仅 test/）

- [ ] 3.1 fixture 21 份 + `contract-fixtures.test.ts` 与 automation 份逐字同步（目录同步改名）
- [ ] 3.2 `test/interactions/` 桶（send-orchestrator.test 等 3 文件）换名；`mirror-stale-stop-work` / `handler.test` 的旧名字面属批 4/5 遗留断言、经 api v0.1.1 旧 kernel 解析，本批不动
- [ ] 3.3 集成仓相关桶跑绿（硬前置：四兄弟仓已 clone + npm ci）

## 4. 集成（双仓锁步，本批先落）

- [ ] 4.1 edge / automation worktree 各自 rebase 最新 master，跑 `test:acceptance` + typecheck
- [ ] 4.2 ff 合入两仓 master + push；控制仓四道复验：protocol-parity + operation-registry-parity + action-key-parity（零改动跑通）+ typecheck
- [ ] 4.3 变异纪律（先 commit 再变异）：白名单删条 / validation 数组删条 / fixture 对照表改名 三类各一，必红后复原回绿

## 5. 部署与切换窗口

- [ ] 5.1 automation dev 部署（安全序列：backup → rsync → restart → healthcheck），确认 IM 族新名收发正常（send-orchestrator 日志）
- [ ] 5.2 出包窗口照旧：并入批 1–5+7 未出包积压，真机验收登记 backlog（视频号 IM 链新名端到端）

## 6. spec delta 与文档

- [ ] 6.1 7 份机械 delta 已随 propose 生成（specs/ 下）；归档前对当时最新 spec 文本重生成一遍防漂移
- [ ] 6.2 `docs/protocol.md`：§2 表 IM 15 行 + 载荷节标题与正文换名
- [ ] 6.3 `docs/edge-command-grammar.md`：批 6 行标 ✅（IM 半边）+ **族约定表新增第三族「留痕写 durable-outbox 往返族」**（design §2 定案文本）+ §6.2 批 7 行豁免注记更新（到期已裁）

## 7. 归档

- [ ] 7.1 `openspec validate platformize-inbox-vocabulary --strict` 通过
- [ ] 7.2 与批 6b 串行集成完成后 archive（specs delta 并入主 spec）
