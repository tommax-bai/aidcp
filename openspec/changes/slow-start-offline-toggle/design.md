## Context

已核实的代码事实（实装 session **不必重新推导**）：

| 事实 | 位置 |
| --- | --- |
| 路由从活会话反查 accountId，解析不出即 `edge_offline` | `aidcp-cloud/src/server.ts:4192-4194` |
| 反查解析器（本 change 要删的那个） | `aidcp-cloud/src/comm/ws-server.ts:316-333` |
| 其接口声明（可选成员） | `aidcp-cloud/src/comm/ws-server.ts:85` |
| 其**唯一**生产调用点 | `aidcp-cloud/src/server.ts:4192` |
| 反方向解析器（**保留**，命令定向下发用） | `aidcp-cloud/src/comm/ws-server.ts:290-306` |
| 其测试（整文件都是被删函数的） | `aidcp-cloud/test/comm/ws-server-resolve-account.test.ts` |
| 「多账号即拒绝猜测」断言（要迁移的那条） | 同上 `:57-65` |
| 原作者「不是缺陷」注释 | `aidcp-cloud/src/client-auth/client-auth-server.ts:278-285` |
| 同源副本 2 | `aidcp-edge/src/electron/main.cjs:3828-3830` |
| 同源副本 3 | `aidcp-edge/src/electron/renderer/ui-logic.js:760-761` |
| 客户端内核在线闸 | `aidcp-edge/src/electron/renderer/ui-logic.js:762` |
| `connState` 真身 = 环境内核子进程的 WS 链路 | `aidcp-edge/src/electron/renderer/renderer.js:771-772` |
| 写入通路（**不碰内核**） | `renderer` → `main.cjs:3831` `'slow-start:set'` → `interactionCustomerRequest`（`main.cjs:550`）→ 云端 HTTP |
| 无快照即整行不渲染 | `aidcp-edge/src/electron/renderer/ui-logic.js:749` |
| `eligible === false` 分支（要镜像的） | `aidcp-edge/src/electron/renderer/ui-logic.js:754-759` |
| 不可用理由文案表（缺 `binding_unknown`） | `aidcp-edge/src/electron/renderer/ui-logic.js:734-738` |
| 停止的环境 `dailyUsage` 默认为 null | `aidcp-edge/src/electron/main.cjs:1038` |
| 慢启动投影产出（**纯云端**） | `aidcp-cloud/src/server.ts:2241`、`:4201`，均取自 `riskRegistry.getController(accountId).slowStartView()` |
| `slowStartView()` 定义 | `aidcp-cloud/src/risk/risk-controller.ts:304-322` |
| `SlowStartIneligibleReason` 联合类型（**不含且不应含 `binding_unknown`**） | `aidcp-cloud/src/risk/risk-controller.ts:82`、`src/comm/protocol.ts:331` |

**spec 现状**：`openspec/specs/client-customer-auth/spec.md` 的「客户只能为当前环境上正在运行的账号开关慢启动」明文 `MUST NOT 依赖持久化的环境↔账号绑定表`，并带「边缘未连接时诚实拒绝」「同环境解析出多个账号时诚实失败」两 scenario。本 change 必须 RENAMED + MODIFIED 改写它，否则代码与 spec 对撞。

## Goals / Non-Goals

**Goals**

- 边缘离线（含**从未启动过**）时也能开关慢启动。
- 删掉 `resolveAccountIdForEdge`，不给这个反模式留复用入口。
- 卡上如实区分「云端真态（新鲜）」与「本机用量（可能陈旧）」。
- `binding_unknown` 可见、可读、可行动。

**Non-Goals**

- 不改慢启动曲线、天数算法、配额计算、风控档位或风控终态。
- 不改 `protocol.ts`、不改 ws 协议、不新增消息类型。
- 不建绑定表、不写绑定行、不实现 D5 冲突闸——**全在依赖 change `curated-envkey-account-binding` 里**。
- **不把本 change 当成「可以摘掉在线判据」的通例**，见 D4。

## Decisions

### D1：accountId 改由持久绑定解析，活会话反查整条删掉

`server.ts:4192` 的 `server.resolveAccountIdForEdge(\`ads-${envKey}\`)` 换成读 `curated-envkey-account-binding` 在 `client_environments` 上建的绑定列（经 `clientUserStore`，读时 JOIN `accounts` ⇒ 悬空绑定 fail-closed，与 `client-user-store.ts:789-791` 既有写法同构）。

随后 `resolveAccountIdForEdge` 的生产调用点归零 → **删实现（`ws-server.ts:316-333`）+ 删接口声明（`ws-server.ts:85`）**。留着它 = 留一个「按活会话猜账号」的现成入口，下一个人会照着用。

**`resolveEdgeIdForAccount`（`ws-server.ts:290-306`）必须留**，且必须继续基于活会话：它回答的是「把这条命令发给哪台机器」，而**把命令发给一台没连上的边缘是结构上真的做不到**。这是 D4 判据的第一个应用。

**歧义消失是结构性的，不是被我们放弃了**：`client_environments.env_key` 是 PK ⇒ **一个环境至多一行 ⇒ 至多一个账号** ⇒ 「多候选里挑哪个」这个问题不再存在。旧测试 `:57-65` 的「多账号即拒绝猜测」不是被删，是被**迁移成 PK 单值测试**：绑定读的返回只能是「恰好一个账号」或「null」，没有第三种。

### D2：无绑定 = `409 binding_unknown`；查不动 = `503`。两者绝不合并

- 无绑定行（或绑定 JOIN 不到 account）→ `409 { error: 'binding_unknown' }`，不写入，**不猜账号**。
- 绑定查询本身抛错（PG 不可达 / 表缺失 / 42P01）→ `503 { error: 'binding_lookup_unavailable' }`。

**为什么必须分开**：把查询失败折成 `binding_unknown` = 用「这个环境没绑账号」这句**我们无法证实的事实断言**去盖住「我没查成」。这正是 `curated-content-store.ts:1038` 上那个把 42P01 降级成 `200 {items:[],total:0}` 的老毛病换个马甲——本项目 `MUST NOT 静默假成功` 红线的反面。

### D3：新增 `GET /environments/:envKey/slow-start`——不加它，云端改了也白改

**这是最容易被漏掉的一环**。停止的环境 `dailyUsage` 默认 null（`main.cjs:1038`）→ `slowStartLine` 在 `ui-logic.js:749` 直接 `return { visible: false }` → **整行不渲染** → 开关根本不存在于界面上。此时云端 PUT 改得再对也无人可点。

所以要一条**不依赖边缘**的读：`GET /environments/:envKey/slow-start`，同样经持久绑定解析、同样 ownership fail-closed、同样复用 `controller.slowStartView()` + `dayQuotas`（同一 producer ⇒ 与快照零计算漂移）。无绑定时返回 `{ eligible:false, ineligibleReason:'binding_unknown' }`。

**回包 MUST NOT 含 accountId**——既有 scenario「非所有者请求 fail-closed」已明令 `MUST NOT 泄露该环境的账号身份`，读路由不得从侧门把它漏出去。

**三个来源的优先级（必须是规则，不能靠巧合）**：

1. 该环境**有**活快照 → 快照治理这一行（它同时带用量计数）。
2. 该环境**无**活快照 → 用 HTTP 读填这一行（只有慢启动真态，无用量计数）。
3. PUT 回执 → 对**发起环境**在写入瞬间权威（既有 change `slow-start-optimistic-feedback` 的 D2 已定此口径）。

三者同源于 `controller.slowStartView()`，故不会算出不同结果。但客户端 **MUST NOT 把三者逐字段合并**——拼出一个哪个源都没说过的混合态，是自己造事实。

### D4：ESSENTIAL / INCIDENTAL 判据——本 change 不是摘在线闸的通行证

> 一道在线判据是**本质的**，当且仅当**没有活边缘这件事本身就让该操作无法被兑现**。否则它是**附带的**，只是实现凑巧路过了那里。

| 操作 | 边缘离线时能兑现吗 | 判据 | 结论 |
| --- | --- | --- | --- |
| 写 `slow_start_since` | 能。执行体是云端配额计算，开关运行时现读；且幂等、可逆 | INCIDENTAL | **本 change 摘掉** |
| 命令定向下发（`resolveEdgeIdForAccount`） | 不能。没有连接就没有收件人 | ESSENTIAL | **保留** |
| create-post / 建委托任务（发布） | 不能。发布真的需要一个活浏览器；且**不可逆** | ESSENTIAL | **保留，且本 change 不碰** |

对抗评审记下的那条必须写进来：**陈旧绑定会授权不可逆的写**。但这条打不到本 change——`slow_start_since` 幂等、可逆、且本路由**明令不得触碰**风控档位 / 风控终态 / 账号写总闸（既有 spec 硬约束，MODIFIED 后保留逐字保留）。真正不可逆的那两个（create-post、委托任务创建）本来就有 ESSENTIAL 在线前置，一分钱都不用本 change 付。

### D5：诚实的 UI 契约是「真态新鲜 vs 用量陈旧」，**不是**「已保存 vs 已应用」

**这里我刻意偏离了任务书的字面措辞，理由如下，请勿「修正」回去。**

互动读取开关那套 `stored / applied / effective` 二态是**必需的**，因为它的执行体在边缘：云端存下了 ≠ 本机应用了，所以有 `edgeDelivery: { status: 'enqueued' | 'deferred' }`。

慢启动**不是那样**。它的执行体在云端配额计算内，开关经运行时现读生效 ⇒ **云端写入成功即为已生效**，中间不存在「待下发边缘」这个状态。现有 spec 对此有明文：

> 回包 MUST NOT 引入「已保存 / 待下发边缘」二态——照抄一个不存在的状态同样是不诚实。

这条**没有被用户推翻，本 change 逐字保留**。照搬 saved-vs-applied 会亲手造出一个不存在的状态——用**相反的面具**再犯一次同一条红线（对抗评审对 DEFECT 3 的原话：把假阻断换成假成功）。

慢启动真正需要说清的新鲜度差异是**另一条轴**：

- **慢启动真态**（state / day / since / binding / dayQuotas）：云端算的，**新鲜**，PUT 回执当场刷新。
- **用量计数**（今日已浏览 N…）：边缘推的，离线时**陈旧**，必须打标签。

所以离线时这一行要说的是「开关已生效（云端）；下面的用量数字来自本机、当前未连接、可能已过期」——**不是**「已保存，等待本机应用」（那是假的）。

### D6：`binding_unknown` 不进 `protocol.ts`

`ui.snapshot` 的慢启动投影产于 `server.ts:2241` 的 `controller.slowStartView()`，而 controller 是**按 account 取的** ⇒ 能装配快照就必然已有 account ⇒ `binding_unknown` 在快照路径上**结构性不可达**。把它塞进 `protocol.ts:331` 与 `risk-controller.ts:82` 的联合类型 = 加一个死值，还平白把本 change 拖进 §2 的两份 protocol.ts 四处同步与热点串行。

它由**路由层**在「压根没有 account、因而也没有 controller」时合成，只活在客户鉴权 HTTP 面。

**合成时不许编造**：无绑定 ⇒ 不知道账号 ⇒ 不知道平台 ⇒ **`totalDays` / `state` / `since` 一律不给**，只给 `{ eligible:false, ineligibleReason:'binding_unknown' }`。`slowStartLine` 对此天然成立：`checked` 在 `:754-759` 分支里被覆写为 false，`totalDays` 在 `:751` 有兜底且该分支用不到。给一个 `state:'off'` 就是在替一个我们没读过的账号断言「它的慢启动是关的」。

### D7：客户端把闸从「内核在线」改成「够不够得着客户 API」

`ui-logic.js:762` 的 `out.disabled = stale` 拆掉。`:763` 的 `out.reason = '云端已断开，状态可能已过期'` **保留但改口径**——它描述的是**用量计数**陈旧，不再是禁用理由。

`ui-logic.js:734-738` 的文案表补 `binding_unknown`。注意 `:757` 现有兜底 `|| '当前无法启用慢启动'` 已能让文案不为空——**真正让它「什么都不显示」的是 `:749`（没有 payload ⇒ 整行不渲染），不是文案表缺键**。故 D3 的 GET 是 `binding_unknown` 可见性的**前置**，两者必须一起做，只补文案表等于没做。

「够不够得着客户 API」不需要新探针：`interactionCustomerRequest` 失败即失败，走 `slow-start-optimistic-feedback` 已建的 env-scoped 失败反馈原样展示。**不新增任何浏览器 / 环境闸**（对抗评审对 DEFECT 3 的原话：`main.cjs:550` 与 IPC handler 都没有环境闸，**不要为了「一致」去加一个**）。

## 安全

本 change **不新增**攻击面，但**继承并放大**一个既有的：边缘 WS 握手全文无鉴权，`session.accountId` 是 hello 里自报的字符串（`client-auth-server.ts:281-283` 原文），`edgeId` 由客户端自选（`aidcp-edge/src/client/edge-id.ts:41-42`），`ensureAccount`（`connection-runtime.ts:136`）接受任何自报 accountId。把这份自报身份**持久化**并用它授权写入，是从「瞬时、内存内」升级成「持久、新资产」。

- **D5 跨客户冲突闸在依赖 change 里**：绑定写入时若该 accountId 已绑到**另一个客户**的环境上，拒写 + 告警，fail-closed。本 change 只**消费**绑定，不实现该闸——但**没有它就不该上线**。
- **本路由的爆炸半径本来就有界**，且 MODIFIED 后逐字保留：`slow_start_since` 是本路由**唯一**可写字段；风控档位、风控终态、账号写总闸、其它账号配置一律不可触碰。且该字段**幂等、可逆**，下一次诚实 hello 会把绑定纠正回来。
- ownership 仍由**管理员授予的 `env_key`** 判定、fail-closed。客户端**永不提交 accountId**（既有 scenario「请求体夹带账号选择器被拒绝」原样保留，GET 同样只吃 `envKey`）。

## Risks / Trade-offs

- **[陈旧绑定 → 改到已撤走的号头上]** → 这正是原 spec 拒绝持久绑定的理由（「账号早已从该环境撤走而绑定行仍在」），**该顾虑是真的、不是稻草人**。缓解：写入侧用 `COALESCE(EXCLUDED.x, current)` 语义（新值来了就覆盖）⇒ 下一次 hello 自愈；本路由唯一可写字段幂等可逆；不可逆操作另有 ESSENTIAL 在线前置（D4）。**残余风险明确接受**：一个从此再不上线的环境，其绑定会永久停在最后一个登录过的账号上。
- **[快照与 HTTP 读打架致闪烁]** → D3 的优先级是规则不是巧合：有活快照即快照治理，无快照才用 HTTP 读，**永不逐字段合并**。
- **[「开关能点了」被误读成「卡是活的」]** → D5 的双轴标注就是为这个：真态新鲜、用量陈旧，分别说。
- **[本 change 被引用成「摘在线闸」的先例]** → D4 的 ESSENTIAL / INCIDENTAL 判据写进 design 并在 spec 里落成 `resolveEdgeIdForAccount` 必须保留的需求。

## Migration Plan

1. **等 `curated-envkey-account-binding` 落地并部署 dev**（硬序：本 change 读它建的列；两者同改 `client-user-store.ts`，§7 热点串行）。
2. 云端：路由改读绑定 → 加 GET → 删 `resolveAccountIdForEdge` + 接口声明 → 迁移测试 → `test:acceptance` → `test` → `typecheck`。
3. 客户端：拆内核在线闸 → 接 GET → `binding_unknown` 可见态 → 三份注释同步 → 测试。
4. 部署 dev（客户端改动不出安装包，除非用户明确要求）。
5. **回滚**：本 change 不建表、不写数据，回滚 = 回退两仓提交即可；绑定列由依赖 change 拥有，不随本 change 回滚。

## Open Questions

- **`GET /environments/:envKey/slow-start` 是独立路由，还是并进 `/my-environments`（`client-auth-server.ts:273-276`，客户端唯一调用点 `main.cjs:594`）？** 本设计选独立路由：按需懒取、与既有 PUT 同形、不给环境列表加一次 N 账号的扇出读。若实装时发现客户端为渲染左栏本来就要逐环境取，可并入——**但绝不能因此把 accountId 漏进列表回包**。
- **`ui-logic.js:763` 那句「云端已断开，状态可能已过期」的最终文案**未定。约束（`ui-logic.js:726-733` 有测试守着）：`#daily-summary` 全域不得出现「已达 / 上限 / 额度 / 释放 / 已满」，不得出现「新账号」，不得暗示「动作更慢 / 更像真人」。
