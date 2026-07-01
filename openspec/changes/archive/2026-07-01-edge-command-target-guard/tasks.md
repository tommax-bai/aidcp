# Tasks — edge-command-target-guard

> 全部代码改动落 **aidcp-cloud**；本仓（aidcp）只承载 openspec 契约与进度回写。
> 实装后按 CLAUDE.md §3 用 HTML 注释标 `[x]`，格式 `<!-- <repo> <commit-sha> 备注 -->`。

## 1. aidcp-cloud — 握手层：强校验节点号（R1）

- [x] 1.1 在 `src/orchestrator/connection-runtime.ts` 的 `onHandshake` 增补：`session.edgeId?.trim()` 缺失 / 空白时，复用 `this.deps.onConfigError(session, <说明>)` 拒绝握手，返回 `{ ok: false, code: 'missing_edge_id', message: ... }`；置于账号号校验之后、重连顶替之前，确保不建立任何连接运行时。 <!-- aidcp-cloud e0efbb9 归一化写回 trim 值 -->
- [x] 1.2 校验拒绝路径的日志与 `onConfigError` 说明文案与账号号缺失保持同风格（点明「无节点号 = 无可路由出站身份」）。 <!-- aidcp-cloud e0efbb9 -->

## 2. aidcp-cloud — 出口层：禁止隐式广播（R2 / R3）

- [x] 2.1 在 `src/comm/ws-server.ts` 的 `pushToEdges(env, edgeId)`：当 `edgeId` 为空（undefined / 空串 / 空白）时，不进入遍历发送，直接 `return 0` 并记一条 `console.warn`；带目标时行为不变（过滤条件简化为直接匹配，因 edgeId 现已保证非空）。 <!-- aidcp-cloud e0efbb9 -->
- [x] 2.2 同步 `EdgePusher`（ws-server.ts）与 `edge-steps.ts` 的同构接口注释，写明「空目标不广播、返回 0 视为诚实失败」的契约。 <!-- aidcp-cloud e0efbb9；command-sequencer.ts 的同构注释此前已在 HEAD -->
- [x] 2.3 （R3，仅注释）在 `pushToEdges` 处注明「如需全网广播须新增语义明确的独立方法，禁止靠省略 edgeId 触发」；本次不实现广播方法（YAGNI）。 <!-- aidcp-cloud e0efbb9 -->

## 3. aidcp-cloud — 回归断言（安全红线级）

- [x] 3.1 `test/integration/connection-runtime.test.ts`：新增两用例——缺 / 空白节点号握手 → `onHandshake` 返回 `ok:false`（`code:'missing_edge_id'`），`runtimeCount()` 未增、发配置告警、未建 dispatcher。 <!-- aidcp-cloud e0efbb9 -->
- [x] 3.2 新建 `test/comm/ws-server-target-guard.test.ts`（真机 ws 往返）：两个不同节点号在线时，`pushToEdges(env, undefined)` / `''` / 空白 均返回 0 且不下发。 <!-- aidcp-cloud e0efbb9 -->
- [x] 3.3 同文件：`pushToEdges(env, 'edge-a')` 只命中 edge-a（返回 1、edge-a 收到、edge-b 零收断言）；未知 edgeId 返回 0 不回退广播。另更新 `test/comm/ws-server-pause.test.ts` 改用定向下发（原用空目标广播，已随收紧改为显式带 edgeId）。 <!-- aidcp-cloud e0efbb9 -->
- [x] 3.4 acceptance 评估结论：本不变量属**交付安全红线**，与 `AC-PROTO`（协议漂移）/ `AC-RISK`（风控自残）均非同类，强并入会造成类别错配；已由 `ws-server-target-guard`（真机 ws 往返，等价端到端）+ `connection-runtime` 集成用例充分覆盖，故不再重复加 acceptance 断言（避免冗余）。 <!-- 评估：不新增 AC，理由如左 -->

## 4. aidcp-cloud — 回归纪律与验证

- [x] 4.1 `npm run test:acceptance`：26 pass（`AC-PROTO` / `AC-RISK` / `AC-SEARCH` 等红线全过）。 <!-- aidcp-cloud e0efbb9 -->
- [x] 4.2 `npm test` 全量：991 pass / 0 fail。 <!-- aidcp-cloud e0efbb9 -->
- [x] 4.3 `npm run typecheck`：clean（未改协议，两份 protocol.ts 零影响）。 <!-- aidcp-cloud e0efbb9 -->

## 5. 部署与归档

- [x] 5.1 按 CLAUDE.md §5 安全序列部署 cloud 到 ECS（备份 → rsync → restart → healthcheck）。 <!-- aidcp-cloud e0efbb9 2026-07-01 deployed；用户授权「整棵树一起部署」（含无关 publish-agent WIP，已确认可上线）；备份 cloud.bak.20260701-105017.tar.gz + .env.bak.20260701；healthcheck：active + 8787 LISTEN + 飞书长连接已建立；isales 未碰 -->
- [x] 5.2 `openspec validate edge-command-target-guard --strict` 通过后归档（`/opsx:archive`）。 <!-- 2026-07-01 validate 通过；delta 合并进 openspec/specs/edge-command-targeting/，change 移入 archive/ -->
