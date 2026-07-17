## Why

慢启动开关在边缘不在线时改不了。运营的原话诉求是：**要在启动浏览器之前就把慢启动摁下去**——养号曲线约束的是接下来那一程的配额，而当前实现要求「先把你想保护的号跑起来，才允许保护它」，把工作顺序倒了过来。

两道闸各锁一半，且**两道都锁在与这次写入无关的东西上**：

- **云端**：`aidcp-cloud/src/server.ts:4192` 用 `server.resolveAccountIdForEdge(\`ads-${envKey}\`)` 从**活会话**反查 accountId，解析不出即 `{ ok:false, reason:'edge_offline' }`（`src/server.ts:4193-4194`）。解析器本体在 `src/comm/ws-server.ts:316-333`。
- **客户端**：`aidcp-edge/src/electron/renderer/ui-logic.js:762` 的 `out.disabled = stale`，其中 `stale = connState !== 'online'`，而 `connState` 来自 `renderer.js:771` 的 `status.cloud === 'connected'` ——**该环境内核子进程自己那条 WS 链路**。

而这次写入**根本不经过那条链路**：`renderer → main.cjs:3831 的 'slow-start:set' IPC → interactionCustomerRequest → 云端客户鉴权 HTTP API`，全程不碰环境内核子进程。这与 DEFECT 3（视频号读取开关被 `interaction-workspace.js:410-411` 的 `env.connectivity === 'connected'` 闸住）是**同一个形状的错**：拿「这个环境的内核在线吗」去授权一次根本不碰内核的写。

### 原作者把这条明确写成了「不是缺陷」——用户已决定推翻

`aidcp-cloud/src/client-auth/client-auth-server.ts:278-285` 逐字如下：

> ```
> // 账号级慢启动开关（change account-level-slow-start）：env-scoped 写。
> //
> // **绝不走 WS 写**：ws-server 全文无鉴权，session.accountId 是边缘 hello 里自报的字符串
> // ——改一个字符串就能替别人关慢启动。这里 ownership 由管理员授予的 env_key 判定（fail-closed），
> // accountId 由云端经活会话映射解析、客户端永不提交。
> //
> // **「边缘不在线就改不了」不是缺陷**：慢启动状态本身就搭在 ui.snapshot.dailyUsage 上，
> // 边缘离线时这张卡本来就不更新、开关本来就该禁用——两者是同一件事，不额外损失。
> ```

用户已明确要求推翻（「推翻它，按我说的改」）。本 change SHALL 更新该注释，并同步更新另外两份同源副本：`aidcp-edge/src/electron/main.cjs:3828-3830` 与 `aidcp-edge/src/electron/renderer/ui-logic.js:760-761`。

**这条论证不止活在注释里，它已经被写进 spec**：`openspec/specs/client-customer-auth/spec.md` 的需求「客户只能为当前环境上正在运行的账号开关慢启动」明文写着 `MUST NOT 依赖持久化的环境↔账号绑定表`，并带有「边缘未连接时诚实拒绝」与「同环境解析出多个账号时诚实失败」两个 scenario。**不改 spec 就实装 = 代码与 spec 直接对撞**，因此本 change 必须走 RENAMED + MODIFIED 正式改写它。

### 诚实对待原作者真正的那半个论点

原作者的论据里**有一半是真的，必须承认**：「今日节奏」卡上的**用量计数**（今日已浏览 / 已点赞…）确实来自边缘推的 `ui.snapshot.dailyUsage`（`server.ts` 快照装配路径），边缘离线时它确实不刷新。

但**「两者是同一件事」是错的**——它把共用一张卡的两条数据通路当成了一条：

| 卡上的东西 | 数据源 | 边缘离线时 |
| --- | --- | --- |
| 用量计数（今日已做了多少） | 边缘上报 `ui.snapshot.dailyUsage` | **确实陈旧**，原作者说得对 |
| 慢启动投影（state / day / since / binding / eligible）与 `dayQuotas` | **纯云端**：`server.ts:4201` 的 `controller.slowStartView()` + `pickDailyUsageCounts(controller.effectiveQuotas().day)`，取自 `riskRegistry.getController(accountId)`，**零边缘输入** | **永远新鲜**，且 PUT 回执当场带回写后真态 |

卡上有一半是陈旧的，是**给那一半打上标签**的理由，不是**禁用一个数据通路全在云端的控件**的理由。离线时这张卡照样能诚实地显示：慢启动真态（云端算的、写入瞬间由回执刷新）+ 一份**明确标注为陈旧**的历史用量。

**所以开关仍然值得开**：运营要决定的是「接下来这一程按不按曲线放量」，这个决定与「今天已经做了多少」无关，而做这个决定最自然的时刻恰恰是**浏览器还没起来的时候**。

## What Changes

- 慢启动路由改用**持久绑定**解析 accountId（依赖 change `curated-envkey-account-binding`），不再要求边缘在线。
- 无绑定时 SHALL 返回 `409 binding_unknown`；绑定查询本身失败（PG 不可达 / 表缺失）SHALL 返回 `503`，**绝不把「查不到」说成「没绑定」**。
- **删除 `resolveAccountIdForEdge`**（`ws-server.ts:316-333` 实现 + `ws-server.ts:85` 接口声明），其最后一个生产调用点在本 change 后归零；把 `test/comm/ws-server-resolve-account.test.ts:57-65` 的「多账号即拒绝猜测」断言迁移成 **PK 单值**测试。**保留 `resolveEdgeIdForAccount`**（`ws-server.ts:290-306`）——把命令发给一台没连上的边缘是**结构上真的做不到**，那道在线判据是本质的。
- 新增 `GET /environments/:envKey/slow-start`：**不依赖边缘**的 env-scoped 读，让从未连过的环境也能把这一行渲染出来。
- 客户端：拆掉 `ui-logic.js:762` 的内核在线闸；卡上**分别**标注「慢启动真态（云端）」与「用量计数（本机，可能陈旧）」的新鲜度。
- **`binding_unknown` 成为一等可见状态**（镜像 `ui-logic.js:754-759` 的 `eligible === false` 分支），而不是当前的**整行不渲染**。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `client-customer-auth`：改写慢启动写路由的 accountId 解析口径（活会话 → 持久绑定），移除「边缘未连接即拒绝」与「多账号歧义」两条判据，新增 env-scoped 慢启动读路由与 `binding_unknown` / 查询失败的诚实语义。
- `edge-companion-ui`：慢启动开关不再被环境内核在线状态闸住；卡上区分云端真态与本机用量的新鲜度；未绑定环境必须可见地说明原因。

## Impact

- **依赖（硬）**：`curated-envkey-account-binding` **必须先落地**——本 change 消费它写入的 `client_environments` 账号绑定列与 D5 跨客户冲突闸。两者都改 `aidcp-cloud/src/client-auth/client-user-store.ts`，属 CLAUDE.md §7 热点文件，**必须串行、绝不并行**。
- 代码：`aidcp-cloud` 的 `src/server.ts`、`src/client-auth/client-auth-server.ts`、`src/comm/ws-server.ts`（删函数）；`aidcp-edge` 的 `renderer/ui-logic.js`、`renderer/renderer.js`、`main.cjs`。
- **协议：不变**。`binding_unknown` 只经客户鉴权 HTTP 面产生（无绑定 ⇒ 无 account ⇒ 无 controller ⇒ 该状态在 `ui.snapshot` 路径上结构性不可达），**不进 `protocol.ts`**，因此不触发 §2 的两份 protocol.ts 四处同步与串行约束。
- 数据：不新增表；只读 `curated-envkey-account-binding` 建的绑定列。
- 安全：本路由从此基于**持久化的自报身份**授权写入。风险有界且已声明，见 design.md「安全」。
