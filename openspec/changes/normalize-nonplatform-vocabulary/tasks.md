# Tasks

> 词汇蓝图批 7。**迁移＝直接切换**：旧名从两份穷举表直接删，typecheck 即守卫；名表唯一权威＝design §1（5 条改名，总数 103 不变）。
> **同形异义不改**：design §4 清单（能力串、nativeKind、`edge.task.*` 全家、`captcha.assist.*`、邻近遥测消息）。
> **双仓锁步批**：照批 4/5 工序「各 worktree rebase → 全量测试 + gate:native → 成对 ff push → 立即 protocol-parity + operation-registry-parity 复验」。
> **集成串行**：批 5（`objectify-interaction-vocabulary`）先落主干，本批 rebase 后再集成。

## 0. 前置核实（已完成，2026-08-07 本 session）

- [x] 0.1 两仓 + kernel 全量触点探查：kernel 豁免名单零命中（不出 kernel 版本）；无 `risk.` 前缀整族判断；`ui.snapshot` 无应答无配对；host-assembly-guard 正则闸静默失效点定位。
- [x] 0.2 应答约定定案：过去分词/过去式事实形；唯一实际改名 `state.report`→`state.observed`；豁免名单（ping/pong、`.result`/`.ack` 族、assist 子族）成文。
- [x] 0.3 规格引用分诊：全部机械改名（12 个 capability），无手写语义 delta。

## 1. aidcp-edge（worktree `../aidcp-edge.wt/normalize-nonplatform-vocabulary`）

- [ ] 1.1 `src/comm/protocol.ts`：`MessageType` 5 条改名；`PayloadMap` 同步（payload 接口名可随改：`CaptchaDetectedPayload` 等按新名，或保留并注记——实装取一致做法）；prose 同步；能力串脱钩注释（design §3 末条）。
- [ ] 1.2 发送点改名：`native-page-engine/browse-session.ts:1855/1748`（captcha 两条）、`browse/captcha-assist.ts:844`（cleared 第二发送点）+ 5 处纪律注释、`native-page-engine/browse-session.ts:931` + `main.ts:1551`（state.observed 两发送点）+ 失败日志文本。
- [ ] 1.3 `src/client/edge-client.ts`：`ui.push_snapshot` 路由分支（:909）、`identity.read_current_page` 白名单条目（:849）+ 注释。
- [ ] 1.4 `src/client/operation-registry.ts`：2 键改名，52 条计数不变；`command-diagnostics.ts` 若含 identity 条目随改（探查：identity 在 `page_observation` 路由，`ACTIVE_COMMAND_TYPES` 不含 ui.snapshot——以 grep 为准）。
- [ ] 1.5 `src/native-page-engine/command-mapper.ts`：两张表左键 `identity.read_current`→`identity.read_current_page`（右值 nativeKind 不动）。
- [ ] 1.6 引擎 manifest：grep 全部 5 旧名；`identity.read_current` 条目 `edgeTypes[]` 换新名（`receipts[]` 的 `identity.observed`、`sessionControls` 的 `edge.task.acquired` 不动）；重建重钉 digest 五位点（**含生产常量 `native-page-engine-artifact.cjs:19`**）。
- [ ] 1.7 测试：protocol-contract 穷举表逐键换（计数断言值 103 不变）；**host-assembly-guard 4 条正则换新名并确认 `doesNotMatch` 闸仍真实断言**；core-log-severity 日志串断言随改；captcha-assist 系列 13 处、xhs-session-guard-blocking、browse-session、state-observation、identity-revalidation、operation-registry、edge-client 路由回归（ui.push_snapshot 不得静默丢弃）、digest 夹具。
- [ ] 1.8 `npm run typecheck` + `npm test` + `npm run test:acceptance` + `npm run gate:native` 全绿；变异验证「先 commit 再变异→红→复原→复跑回绿」（变异项：删白名单 identity 条目 / 改 manifest edgeTypes 一条 / 把一处发送点改回旧名）。

## 2. aidcp-automation（worktree `../aidcp-automation.wt/normalize-nonplatform-vocabulary`）

- [ ] 2.1 `src/comm/protocol.ts`：与 edge 逐字一致（同 1.1）。
- [ ] 2.2 `src/comm/handler.ts`：5 个 case 分支改名（:707/:710/:719 不动 acquired——只改 captcha 两条与 :905 identity.observed 不动、:917 state 条）；`emit('state.observed.arrived')`。
- [ ] 2.3 `src/event-bus/types.ts`：`state.report.arrived`→`state.observed.arrived`；`role-dispatcher.ts:3062` 接线、`:2111` prose、`:3032/:3040` identity 分派三元、`nickname-enricher.ts:30/:173` 类型与分支随改。
- [ ] 2.4 `src/comm/ui-snapshot.ts:293` 发送点 + 文件头 prose；`ws-server.ts:374/:391` 两张名单成员改名。
- [ ] 2.5 `src/comm/command-bridge.ts` identity case（:123-126）左值信封名改；`src/comm/operation-registry.ts` 2 键改名（52 不变）；`src/platform/registry.ts:224/:280` `identityCapture.command` 改名（capability 串不动）。
- [ ] 2.6 测试：protocol-contract、state-observation、identity-command-routing、platform-registry、nickname-enricher、ws-server-target-guard / ws-server-pause / browser-standby / ui-snapshot、operation-registry、automation-edge-access；`npm run typecheck` + `npm test` + `npm run test:acceptance` 全绿；变异验证同 1.8 纪律。

## 3. 控制仓（集成期由主 session 执行）

- [ ] 3.1 `docs/protocol.md`：5 条改名（§2 表 + 载荷节 + captcha/身份/状态观察各节 prose）。
- [ ] 3.2 `docs/edge-command-grammar.md`：§6.2 批 7 小节按落地名定稿（含应答族约定全文与豁免名单）、§6.3 批 7 行标 ✅。

## 4. 集成（双仓锁步，批 5 落地后执行）

- [ ] 4.1 两 worktree rebase 最新 master（含批 5）→ 全量测试 + gate:native 绿。
- [ ] 4.2 成对 ff push → 立即 `python3 scripts/protocol-parity` + `python3 scripts/operation-registry-parity` 复验全绿。
- [ ] 4.3 清 worktree。

## 5. 部署与收尾

- [ ] 5.1 部署 `dev`（可与批 5 合并为一次部署；§5 安全序列）。
- [ ] 5.2 真机验收项并入 backlog 出包簇（登记前 grep 最大簇号）；并入出包提请。

## 6. spec delta

- [ ] 6.1 机械改名 delta 覆盖 grep 实测 12 个 capability（proposal 名单），逐条人审，同形异义按 design §4 红线；归档前对最新 spec 文本重生成，`openspec validate normalize-nonplatform-vocabulary --strict` 过。

## 7. 归档

- [ ] 7.1 全部 task 勾完 → validate --strict → archive；蓝图批 7 行终态回写。

## 8. 实装偏离与实录

（实装时回写）
