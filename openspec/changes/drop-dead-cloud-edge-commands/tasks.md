# Tasks

> **⚡ 2026-08-06 事实源已翻转（`invert-split-fact-source` cutover，用户裁定不等在飞 change）**：
> `aidcp-cloud` 的 `src/` + `migrations/` 已冻结（task-preflight 会拦任何 cloud 侧源码改动），
> `sync-split-repos --apply` 已退役。**本 change 剩余的「cloud 侧」任务改为直接落对应派生仓**
> （aidcp-api / aidcp-automation / aidcp-content；逐文件属主查 `aidcp-cloud/boundaries/module-ownership.json`，
> 常见：`src/comm/**`、`src/orchestrator/**` → automation，`src/panel/**`、`src/client-auth/**` → api）。
> 已写但未推的 cloud src 改动请在派生仓重落，**勿再推 cloud**（推了会让全 fleet 任务准入变红）。
> 新迁移直接落属主仓 `migrations/`，编号取三仓并集的下一号。跨仓测试（整图/跨属主）落 cloud `test/`
> （它现在是纯集成测试仓，test/ 不冻结）。协议红线不变：edge ↔ aidcp-automation 两份 `src/comm/protocol.ts` 逐字一致。


> 词汇蓝图批 1。**迁移＝直接切换**：旧名从穷举表直接删，typecheck 即守卫。
> 与 `close-account-layer-operation-manual`（后台并行）在两份登记表 + 一个测试文件上重叠，集成串行、后到者 rebase。

## 0. 前置核实（已完成）

- [x] 0.1 三条命令云端发送点 grep 为零；`plan.response` 核出活发送点（v1 应答 + 点赞触发工具）→ 本批不删。 <!-- 2026-08-06 -->
- [x] 0.2 规格引用分诊：publish-pipeline 5 处全是禁令（不动）；两处真依赖出 delta。 <!-- 2026-08-06 -->

## 1. aidcp-edge（worktree `../aidcp-edge.wt/drop-dead-cloud-edge-commands`）

- [ ] 1.1 `src/comm/protocol.ts`：删 3 条 `MessageType` + 对应载荷类型 + 载荷映射条目。
- [ ] 1.2 `src/client/operation-registry.ts`：删 3 条登记（含 publish.request 的墓碑注释）。
- [ ] 1.3 `src/client/edge-client.ts`：删 `browse.next` / `browse.scroll` 路由分支与 `publish.request` 遗留信封识别分支。
- [ ] 1.4 `src/client/command-diagnostics.ts`、`src/main.ts`、`src/browse/browse-session.ts`（deprecated 处理分支）、`src/publish/approval-gate.ts`、`src/native-page-engine/command-mapper.ts`：逐个清引用。
- [ ] 1.5 测试清理：`command-manifest.test.ts`（排除清单里的 publish.request）、`publish-e2e` / `publish-approval-contract`（**AC-PUB 红线只许换对象不许消失**——对已死类型的断言删除前，确认 `publish.command` 路径上有等价断言）、`notification-handlers`、`operation-registry.test.ts` 手抄清单三条（若并行 change 已删整张清单则 rebase 自然消解）。
- [ ] 1.6 `npm run typecheck` + `npm test` + `npm run test:acceptance` 全过；AC-PUB 全绿。

## 2. aidcp-cloud（worktree `../aidcp-cloud.wt/drop-dead-cloud-edge-commands`）

- [ ] 2.1 `src/comm/protocol.ts`：与 edge 逐字一致地删同 3 条。
- [ ] 2.2 `src/comm/operation-registry.ts`：删 3 条登记。
- [ ] 2.3 相关测试清理（暂停闸用例若拿 `browse.next` 当例子，换 `page.scroll`）。
- [ ] 2.4 `npm run typecheck` + `npm test` + `npm run test:acceptance` 全过。

## 3. 控制仓

- [ ] 3.1 `docs/protocol.md`：头部计数与 §2 表随删同步（以两份 protocol.ts 的 `MessageType` 穷举为准数）。
- [ ] 3.2 `docs/edge-command-grammar.md` 蓝图批 1 行：写入 `plan.response` 核实结论（有活发送点，留待 v1 退役轮）。

## 4. 集成与派生仓

- [ ] 4.1 `scripts/land-change` 集成 edge / cloud（rebase → 全量测试 → 协议逐字对账闸 + 登记表对表闸 → ff 推 master）。与并行 change 的先后由实际完成顺序定，后到者解冲突。
- [ ] 4.2 `scripts/sync-split-repos --repo aidcp-automation` dry-run 确认唯一差异是登记表 → `--apply` → 派生仓 typecheck。
- [ ] 4.3 `scripts/operation-registry-parity` 三方一致（各 43 条）。

## 5. 部署与验证

- [ ] 5.1 部署 `dev`（§5 安全序列；部署 `aidcp-automation` 派生服务，MUST NOT 碰 `aidcp-cloud` 单体与 isales）。
- [ ] 5.2 healthcheck + 观察日志无 `operation_unclassified` 新增（删除的三条本就无人发，应零变化）。
- [ ] 5.3 **不出包**：三条全是 cloud→edge 方向且云端零发送，旧客户端多认识三个永远不会来的类型，无害。

## 6. 归档

- [ ] 6.1 `openspec validate drop-dead-cloud-edge-commands --strict` → archive。
