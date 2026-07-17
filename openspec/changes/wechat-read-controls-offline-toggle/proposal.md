## Why

视频号环境**没启动**时，客户端的「收取互动 / 评论收取 / 私信收取」三个开关是灰的，客户改不了（用户原话：「没开启浏览器时，无法调整开关」）。

这次写入**根本不经过该环境的核心子进程**：渲染层 → 主进程 IPC（`aidcp-edge/src/electron/main.cjs:3960`）→ `interactionCustomerRequest`（`main.cjs:550`）→ Cloud HTTP。Cloud 侧**已经完全离线正确**：`deliverInteractionRuntimeControls`（`aidcp-cloud/src/server.ts:1981-1995`）在无 Edge 在线时返回 `{delivered:0}` 且不抛错，API 如实回 `edgeDelivery: { status: 'deferred', delivered: 0 }`（`aidcp-cloud/src/interactions/interaction-customer-api.ts:326`），Edge 下次 hello 时经欢迎信封里的 `interactionRuntime` 快照收敛（`aidcp-cloud/src/comm/handler.ts:663-669`）。**Cloud 能受理、能持久化、能收敛——是客户端自己把这次写入拦下来的，请求从未发出。**

拦它的那道闸问错了问题：`aidcp-edge/src/electron/renderer/interaction-workspace.js:411-412` 的 `editable` 要求 `env.connectivity === 'connected'`，即「这个环境的核心子进程连上云端了吗」，用它去授权一次**碰不到核心子进程**的写入。`connectivity` 来自 `renderer.js:231`（`selected.status.cloud`，即每环境核心子进程自己的 WS 链路；默认值 `disconnected` 见 `main.cjs:1030`，核心退出后置 `disconnected` 见 `main.cjs:2794`）。

这是「MUST NOT 静默假成功」红线的**镜像面**：不是把失败讲成成功，而是把一次**能成功**的操作在本地讲成「不可用」。

## What Changes

- 从 `interaction-workspace.js:411-412` 的 `editable` 判定里去掉 `env.connectivity === 'connected'` 这一项；`state.auth.status === 'active'`、`stored` 已取到、`!state.stale` 与 IPC 通道存在四项全部保留。
- 把 Cloud 已经回来的 `edgeDelivery`（`{status:'enqueued'|'deferred', delivered}`）落进读取设置区的**持久**呈现：`deferred` 读作「已保存，待该环境下次连接后生效」并指明需要启动该环境，`enqueued` 读作已保存并已下发本机。二者 MUST NOT 读作已生效。
- 保持 `status` 与 `browserState` 正交：`browserState=closed && status=active`（后台 API-only 运行）继续可编辑——把两者压成单一「是不是起着」布尔量正是这个 bug 的形状。
- 补齐渲染层回归测试：停止态环境可编辑、冷待机不回归、离线保存不冒充已生效、`enqueued`/`deferred` 可区分、stale 仍拦截。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-companion-ui`: 视频号读取开关的可编辑性 SHALL 只由「这次写入能不能被受理」决定，MUST NOT 由该环境核心子进程的在线状态决定；保存结果 SHALL 按 `edgeDelivery` 如实分档且持久可见。

## Impact

- `aidcp-edge`: 仅 `src/electron/renderer/interaction-workspace.js` 与 `test/electron/interaction-workspace.test.ts`。
- `aidcp-cloud`: **无改动**。Cloud 侧已经正确；本 change MUST NOT 触碰 `client-user-store.ts`、`interaction-customer-api.ts` 或任何 Cloud 文件。
- `aidcp-console`: 无改动。
- 协议 / schema / IPC：无改动。**MUST NOT** 在 `main.cjs` 里为「保持一致」新增任何浏览器 / 环境闸。
- 部署：本 change 不含 Cloud 部署项。Edge 停在 commit / push，**不打安装包**；真机验收随下一次常规出包进行（见 `design.md` 验收节）。
