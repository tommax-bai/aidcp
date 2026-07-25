## Context

### 症状

客户在客户端选中一个**未启动**的视频号环境，「收取互动 / 评论收取 / 私信收取」三个开关是灰的，点不动。用户原话：「没开启浏览器时，无法调整开关」。

### 这次写入的真实链路（关键：不经过核心子进程）

```
renderer interaction-workspace.js:1177  api.interactionUpdateReadControls(...)
  → preload 具名 IPC 'interaction:read-controls:update'
  → main.cjs:3960  ipcMain.handle(...)                    ← 只做参数校验
  → main.cjs:550   interactionCustomerRequest(...)        ← 只查 clientAuthEnabled() + hasValidSession()
  → Cloud HTTP  PUT /environments/:envKey/interactions/read-controls
```

主进程侧**没有任何浏览器 / 环境 / 核心子进程闸**——`main.cjs:3960` 的 handler 只校验 `envKey`、`expectedVersion`、两个 boolean，然后直接发 HTTP。这条链路上唯一的闸在渲染层。

### Cloud 侧已经完全离线正确

| 事实 | 位置 |
| --- | --- |
| CAS 落库先于下发，stored 是权威 | `aidcp-cloud/src/interactions/interaction-customer-api.ts:300-308` |
| 无 Edge 在线时不抛错，返回 `{delivered:0}` | `aidcp-cloud/src/server.ts:1981-1995` |
| 如实回 `edgeDelivery:{status: delivered===1?'enqueued':'deferred', delivered}` | `interaction-customer-api.ts:326` |
| 下发失败被吞，注释明写「Stored CAS is authoritative; reconnect converges」 | `interaction-customer-api.ts:311-314` |
| 重连收敛**真的存在**：每次 hello 的欢迎信封带新鲜 `interactionRuntime` 快照 | `aidcp-cloud/src/comm/handler.ts:663-669` |
| `applicationStatus` 由 `edgeAppliedVersion === controls.version` 算出，离线保存后必然是 `pending`，不可能假报 `applied` | `interaction-customer-api.ts:70-72` |

**客户端拒绝了一次 Cloud 能完美履行的写入。**

### 闸问错了问题

```js
// aidcp-edge/src/electron/renderer/interaction-workspace.js:411-412
const editable = Boolean(stored && state.auth && state.auth.status === 'active' && !state.stale
  && env && env.connectivity === 'connected' && typeof api.interactionUpdateReadControls === 'function');
// :417-419
dom.readAll.disabled    = state.readControlsBusy || !editable;
dom.readComment.disabled = state.readControlsBusy || !editable;
dom.readDm.disabled      = state.readControlsBusy || !editable;
```

`connectivity` 的来源链：

- `renderer.js:231` — `connectivity: selected.status && selected.status.cloud`
- `main.cjs:1030` — `makeStatus()` 模板默认 `cloud: 'disconnected'`（**从未启动过的环境**）
- `main.cjs:2794` — 核心子进程退出 → `cloud: 'disconnected'`、`edge: 'stopped'`

即 `connectivity === 'connected'` 的语义是**「这个环境的核心子进程和云端的 WS 链路通着」**。用它授权一条根本不走核心子进程的 HTTP 写入，是拿 A 的在线状态去授权 B 的能力。

### 这是红线的镜像面

项目红线「MUST NOT 静默假成功」禁止把失败讲成成功。这里是同一枚硬币的反面：把一次**能成功**的操作在本地讲成「不可用」。两者共享同一个病根——**呈现层的断言与系统真实能力脱钩**。修的时候必须小心不要翻到另一面：**放开闸却不接 `edgeDelivery`，就是拿一个假阻断换一个假成功。**

### 已有的诚实素材（不是从零造）

- `interaction-workspace.js:1187-1189` **已经**读了 `edgeDelivery` 并分档写进 `state.actionNotice`（`enqueued` → 「收取开关已保存并下发本机。」/ 否则 →「收取开关已保存，等待本机重新连接后应用。」）。**实装者注意：这段不是缺失的，别重写。** 它的问题只在于落点。
- `interaction-workspace.js:422-427` 的 `dom.readApply` 已有「等待本机应用」词汇，由 `controls.applicationStatus` 驱动，且诚实。

## Goals / Non-Goals

**Goals:**

- 环境未启动（核心子进程离线）时，读取开关可编辑，写入真的发到 Cloud 并按 CAS 落库。
- 保存结果按 `edgeDelivery` 如实分档，且在读取设置区**持久**可见；离线保存 MUST NOT 被表述为已生效。
- 保持 `status` / `browserState` 正交，冷待机路径零回归。

**Non-Goals:**

- **不改 Cloud 任何文件。** 不碰 `client-user-store.ts`、`interaction-customer-api.ts`、`server.ts`、`handler.ts`。
- **不在 `main.cjs` 新增闸。** 主进程链路当前没有浏览器 / 环境闸，这是正确的，不要为「一致性」补一个。
- 不改协议、schema、IPC 形状、preload 暴露面。
- 不改 `connectivityWriteBlocked()`（`:277-279`）及其覆盖的回复草稿 / 发送写闸——那是另一组写入，本 change 不碰。
- 不改「收取开关」以外的任何开关；写字段继续没有入口。
- 不打 Edge 安装包（CLAUDE.md §6）。

## Decisions

### 1. 只摘 `connectivity` 一项，其余四项全留

改为：

```js
// connectivity 已移除：这次写入经主进程直发 Cloud HTTP，不经过该环境的核心子进程。
// Cloud 无 Edge 在线时按 CAS 正常落库并回 edgeDelivery.status='deferred'，
// Edge 下次 hello 由欢迎信封的 interactionRuntime 快照收敛（cloud handler.ts:663-669）。
const editable = Boolean(stored && state.auth && state.auth.status === 'active' && !state.stale
  && typeof api.interactionUpdateReadControls === 'function');
```

逐项理由：

| 项 | 去留 | 理由 |
| --- | --- | --- |
| `stored` | **留** | 没取到 stored 就没有 `expectedVersion` 可携，CAS 无法构造。 |
| `state.auth.status === 'active'` | **留（强制）** | 见决策 2。 |
| `!state.stale` | **留** | 见决策 3。 |
| `env.connectivity === 'connected'` | **删** | 见上；它授权的是一条它不参与的链路。 |
| `typeof api.… === 'function'` | **留** | preload 没暴露就真的调不到。 |

注意 `env` 本身仍在 `updateReadControls()`（`:1169`）的守卫里（`if (!active || !env || …) return`），`envKey` 从 `env.envKey` 取，所以摘掉 `editable` 里的 `env &&` 不会引入空引用。

### 2. `status === 'active'` 必须保留——它不是那个闸

这一项**看起来**像同类问题，实际不是。`aidcp-edge/src/electron/renderer/interaction-workspace.js:545-552` 明确把 `browserState === 'closed' && status === 'active'` 画成 **success chip**（「后台运行中（浏览器已关闭）」）；Edge 侧 `auth-session.ts:540-552` 把 `api_only_running` / `browser_open` / `browser_closing` **统统**映射为 `active`。

**浏览器关着 ≠ 不 active。** `status` 讲的是授权态，`browserState` 讲的是浏览器现场。把两者压成一个「是不是起着」的布尔量，正是这个 bug 的形状——本 change MUST NOT 制造它的第二个实例。

### 3. `state.stale` 是诱饵，但**留着**

证据链：

- `:1422` 选中一个 disconnected 环境时 `state.stale = true` ←（看起来像第二道 connectivity 闸）
- `:927` 一次成功的 `loadList` **无条件** `state.stale = false`

停止态环境的实际时序：选中 → `stale=true` → `loadList` 打 Cloud HTTP（不需要 Edge）→ 成功 → `stale=false` → 闸开。**所以 `state.stale` 不是这个 bug 的第二根因**，摘 `connectivity` 一项即足。

那为什么留着它？`stale` 的真实语义是「上次刷新失败，正在拿上次成功的数据顶着」，此时 `storedVersion` 可能已经落后，携着它发 CAS 是真实的版本冲突风险。而且它只在「先成功过、后续刷新失败且已有 items」时才为 true（`:938`、`:1239`），失败面是一个**临时禁用 + 界面已标「上次成功数据」**（`:576`、`:579`），诚实且可见。

**风险**：`:1422` 把 connectivity 折射进 `stale`，等于给 connectivity 留了一条回本闸的暗路。**缓解**：任务 1.4 要求一条钉死「停止态环境在一次成功 `loadList` 之后 `stale===false`、开关可编辑」的回归测试。若哪天 `:927` 改成有条件清除，这条测试会当场红，而不是让开关悄悄变回灰的。

### 4. `loadDetail` 的 stale 不对称：记录，不改

`:1011` — `if (env && env.connectivity === 'connected') state.stale = false;`

`loadList`（`:927`）无条件清 stale，`loadDetail` 只在 connected 时清。一次成功的 Cloud 详情拉取与一次成功的列表拉取，对「数据是否新鲜」是**同等**证据，这个不对称没有道理。

**但不在本 change 改**：`state.stale` 同时喂 `connectivityWriteBlocked()`（`:277-279`），后者经 `writeBlocked()`（`:287`）门控回复草稿的保存 / 生成 / 批准 / 发送（`:812-818`）。动它会把一批**本 change 没有分析过**的写入在离线环境上放开——那正是本 change 反对的那种「顺手推广」。

实际影响为零：`loadList` 先跑且无条件清 stale，`loadDetail` 到达时 `stale` 已是 `false`，`:1011` 的条件是死条件。登记在此，供后续 change 单独处置。

### 5. `edgeDelivery` 必须落在**持久**位，而不是一次性通知位

`:1187` 现在把分档结果写进 `state.actionNotice`。该字段渲染在 `:578`（头部状态行，与同步文案共用）与 `:809`（详情面板），且被**至少 10 处**无关动作清空（`:1060`、`:1077`、`:1113`、`:1130`、`:1174`、`:1222`、`:1329`、`:1365`、`:1446` …）。今天离线保存罕见（闸拦着），所以看不出问题；**闸一放开，离线保存就是常态**，一个下一次点击就被抹掉的通知不足以承载「这次没生效」这个事实。

改法（最小）：把 `edgeDelivery.status` 存进 state（如 `state.readDelivery`），在 `renderReadSettings()` 里驱动 `dom.readApply`：

| 条件 | 文案 |
| --- | --- |
| `applicationStatus === 'applied'` | `Cloud 已保存 v{n}，本机已应用同一版本`（现有，不动） |
| 未应用 且 本次 `edgeDelivery.status === 'deferred'` | `Cloud 已保存 v{n}，待该环境下次连接后生效（需要启动该环境）` |
| 未应用（其余，含 `enqueued`） | `Cloud 已保存 v{n}，等待本机应用（当前 v{m}）`（现有，不动） |

`state.actionNotice` 的既有分档保留——它是「刚刚点了一下」的即时反馈，与持久态互补，不冲突。

**为什么 `applicationStatus` 单独不够**：`pending` 把两种处境压成一句话——「Edge 在线、命令已下发、几秒后应用」与「Edge 离线、下次连接才应用、可能是几天后」。前者「等待本机应用」是准确的；后者对客户是**真话但没用**——他会以为卡住了。`deferred` 是 Cloud **已经在回包里给出**的区分依据，白拿不用才是浪费。

### 6. 放开闸后仍然假成功的失败模式（明确点名）

放开 `editable` **却不接决策 5**，就是把一个假阻断换成一个假成功——同一条红线，换一张面具。任务 1.2 与 1.3 必须同批落地，MUST NOT 只做 1.2。

## 被推翻的假设（不要重新发现）

### ❌ 红鲱鱼：`interaction-customer-api.ts:319` 的 503「平台登录状态尚不可用。」

`if (!auth) throw new InteractionError('INTERACTION_UPSTREAM_UNAVAILABLE', '平台登录状态尚不可用。', 503);`

**这条错误信息读起来跟症状一模一样，一定会被重新发现并「修」一遍——但它是不可达的死代码，改它行为零变化。** 两个独立理由：

1. **没有任何东西在浏览器关闭时清 `interaction_auth_state`。** 全仓只有 offboard / purge 会动它：`interaction-store.ts:1583`（DELETE）、`:1521`（status='disabled'）。关浏览器不在其中。
2. **`withAuthorizedInteractionScope`（`aidcp-cloud/src/client-auth/client-user-store.ts:783-795）已经 JOIN 了 `interaction_auth_state`** 并对整个操作持 `FOR SHARE OF s, e, a, acc`（`:793`）。scope 拿得到 `accountId`，就证明该行存在且被锁住；随后的 `getAuth` 结构上不可能返回 null。

它在测试里「会触发」纯粹是因为 `customer-api.test.ts:53` 把整个 scope 打了桩。

**判据**：Defect 3 的根因在 Edge 渲染层，**请求从未发出**。任何在 Cloud 侧的排查都是走错了仓。

### ❌ 「主进程 IPC 也该加个环境闸，保持一致」

`main.cjs:3960` 的 handler 与 `interactionCustomerRequest`（`main.cjs:550`）当前**没有**浏览器 / 环境闸，只有 `clientAuthEnabled()` + `hasValidSession()`。这是**正确的**——这条链路不碰核心子进程。补一个闸 = 在主进程里重建这个 bug。

### ❌ 「`status === 'active'` 也是同一个 connectivity 病，一起摘」

见决策 2。摘了它，浏览器关闭的正常后台运行态会被误判——而客户端自己在 `:551` 把这个组合画成 success chip。

### ❌ 「`state.stale` 是第二根因」

见决策 3。`:1422` 设、`:927` 无条件清；停止态环境在首次 `loadList` 成功后 `stale === false`。

## Risks / Trade-offs

| 风险 | 评估 |
| --- | --- |
| 客户在环境离线时改了开关，以为立刻生效 | 由决策 5 的持久 `deferred` 文案承接。这是本 change 的**主要**风险，也是 1.3 与 1.2 必须同批的原因。 |
| 离线期间开关被改多次 | 无害。CAS 每次 bump 版本，Cloud stored 是权威；Edge 下次 hello 收敛到**最新**版本（`handler.ts:663-669`），不重放中间版本。 |
| 放开闸让某个不可逆写入变得可达 | 不成立。read-controls 只写 `interaction_runtime_controls` 的两个 boolean：幂等、可逆、纯读取意图。不涉及发布 / 发送 / 加群等不可逆动作，也不改 `writeBlocked()` 覆盖的回复写入。 |
| 与 `wechat-channels-interaction-management` / `wechat-review-residuals` 并行改同一文件 | 真实冲突面。本 change 只碰 `interaction-workspace.js` 的 `renderReadSettings()` + `updateReadControls()` 两个函数，`git rebase` 前先 `fetch`；集成串行（CLAUDE.md §7）。 |
| 「凭什么认定停止态环境 `connectivity !== 'connected'`」 | **这是本 change 唯一未经真机观测的推断。** 由 `main.cjs:1030`（默认 `disconnected`）+ `main.cjs:2794`（核心退出置 `disconnected`）+ `renderer.js:231` 推出，代码上闭合，但未在真机上看过。列为验收项 A1。若真机上停止态环境居然报 `connected`，那么根因另有其人，本 change 的修法仍然正确（闸本就问错了问题），但**症状不会消失**——必须回头重新定位。 |

## 验收（真机）

### ⚠️ 复现必须用**已停止**的环境

**冷待机今天是好的。** `main.cjs:2212/2221` 在进入冷待机时显式置 `cloud: 'connected'`（核心还活着，只是浏览器关了）→ `connectivity === 'connected'` → 开关**可编辑**。

**因此：用应用内的「关闭浏览器 / 转入后台」按钮去复现，会看到开关好好的，从而得出「无法复现」的错误结论。** 必须用一个**从未启动**或**已停止**（核心子进程不在）的环境。

| # | 项 | 判据 |
| --- | --- | --- |
| A1 | **（唯一未验证推断）** 停止态环境的 `connectivity` 确实不是 `connected` | 修复前：选中一个已停止的视频号环境，三个开关灰。这一步同时**证明**推断成立。若开关是亮的 → 停手，根因另有其人。 |
| A2 | 修复后停止态可编辑且真的写进去了 | 同一环境，开关可点；点后 Cloud `interaction_runtime_controls` 版本 +1、boolean 变了。 |
| A3 | 离线保存不冒充已生效 | A2 之后读取设置区持久显示「待该环境下次连接后生效」，MUST NOT 出现「已应用」。 |
| A4 | 重连收敛 | 启动该环境 → Edge hello → 欢迎信封快照 → `applicationStatus` 转 `applied`，文案转「本机已应用同一版本」。**无需再点一次开关。** |
| A5 | 冷待机零回归 | 环境运行中点「转入后台 / 关闭浏览器」→ 开关仍可编辑，保存回 `enqueued`，文案为已下发本机。 |

A1–A5 需要一个装了本 change 的 Edge 安装包。本 change **不出包**（CLAUDE.md §6）；验收项登记进 `docs/real-machine-acceptance-backlog.md`，随下一次常规出包在共享真机环境上跑。
