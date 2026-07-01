# Tasks — edge-command-target-guard

> 全部代码改动落 **aidcp-cloud**；本仓（aidcp）只承载 openspec 契约与进度回写。
> 实装后按 CLAUDE.md §3 用 HTML 注释标 `[x]`，格式 `<!-- <repo> <commit-sha> 备注 -->`。

## 1. aidcp-cloud — 握手层：强校验节点号（R1）

- [ ] 1.1 在 `src/orchestrator/connection-runtime.ts` 的 `onHandshake` 增补：`session.edgeId?.trim()` 缺失 / 空白时，复用 `this.deps.onConfigError(session, <说明>)` 拒绝握手，返回 `{ ok: false, code: 'missing_edge_id', message: ... }`；置于账号号校验之后、重连顶替之前，确保不建立任何连接运行时。
- [ ] 1.2 校验拒绝路径的日志与 `onConfigError` 说明文案与账号号缺失保持同风格（点明「无节点号 = 无可路由出站身份」）。

## 2. aidcp-cloud — 出口层：禁止隐式广播（R2 / R3）

- [ ] 2.1 在 `src/comm/ws-server.ts` 的 `pushToEdges(env, edgeId)`：当 `edgeId` 为空（undefined / 空串）时，不进入遍历发送，直接 `return 0` 并记一条 `console.warn`（说明「缺目标节点号，拒绝广播，诚实失败」）；带目标时行为不变（仅命中匹配节点号）。
- [ ] 2.2 同步 `src/comm/ws-server.ts:53` 的 `EdgePusher` 接口注释与 `src/comment-agent/edge-steps.ts` / `src/publish-agent/command-sequencer.ts` 中同构 `pushToEdges` 接口注释，写明「空目标不广播、返回 0 视为诚实失败」的契约。
- [ ] 2.3 （R3，仅文档 / 注释）在 `pushToEdges` 处注明「如需全网广播须新增语义明确的独立方法，禁止靠省略 edgeId 触发」；本次不实现广播方法（YAGNI）。

## 3. aidcp-cloud — 回归断言（安全红线级）

- [ ] 3.1 `test/integration/connection-runtime.test.ts`：新增用例——握手携带合法账号号但缺 / 空节点号 → `onHandshake` 返回 `ok:false`（配置错误），且 `bySession` 未新增运行时。
- [ ] 3.2 `test/ws-server.test.ts`（或 `test/comm/ws-server-pause.test.ts`）：新增用例——多个不同节点号在线时，`pushToEdges(env, undefined)` 返回 0 且没有任何连接收到帧（stub socket 断言零 send）。
- [ ] 3.3 同文件：新增 / 复核用例——`pushToEdges(env, 'edge-A')` 只命中节点号为 `edge-A` 的连接，`edge-B` 不收到（正向定向不回归）。
- [ ] 3.4 acceptance 侧评估：将「无 edgeId 绝不广播」并入协议 / 风控红线系（`test/acceptance/protocol-contract.test.ts` 或 `risk-guard.test.ts`）作为端到端断言之一（如与既有红线重叠则仅补一条最小断言，避免冗余）。

## 4. aidcp-cloud — 回归纪律与验证

- [ ] 4.1 `npm run test:acceptance`（安全红线全过：`AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*`）。
- [ ] 4.2 `npm test` 全量通过。
- [ ] 4.3 `npm run typecheck` 通过（含两份 protocol.ts 不漂移——本次不改协议，应零影响）。

## 5. 部署与归档

- [ ] 5.1 按 CLAUDE.md §5 安全序列部署 cloud 到 ECS（备份 → rsync → restart → healthcheck → 失败回滚；绝不碰同机 isales）。
- [ ] 5.2 `openspec validate edge-command-target-guard --strict` 通过后归档（`/opsx:archive`）。
