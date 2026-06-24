## Why

运营要在**一台机器上同时跑多个 edge 节点、各自驱动不同账号**。当前这条路是断的，且断在两层：

- **边缘层**：多节点默认都连同一调试端口、用同一浏览器用户数据目录，第二个节点起来时会**静默接管**第一个节点已登录的 Chrome（`aidcp-edge/src/cdp/chrome-launcher.ts:502-521`：探测到活实例即 attach、返回的 `kill` 是空操作、且不校验目录）。两个会话挤在一个浏览器/一个登录态上互相打架——并且「接管陌生浏览器还报成功」本身就踩了「绝不静默假成功」红线。
- **云端层**：编排器是**单租户**的——一套 `RoleDispatcher`/`SessionContext`/`EventBus` 写死 `currentAccountId='default'`（`aidcp-cloud/src/orchestrator/role-dispatcher.ts:157-164`），下行指令**广播给所有 edge**（`server.ts:568-572` 不带 edgeId → `comm/ws-server.ts:154-168` 无 edgeId 即广播），握手事件还把账号身份丢了（`comm/handler.ts:282` 只 emit `{edgeId,ts}`）。结果：不同账号会**串号**（按 A 的内容+人设算出的指令发到 B 的浏览器）、限频闸看的还是 `default`（`server.ts:375/530-538`）而记账按真实账号（`server.ts:383-387`）——真账号一进来**限频形同失效**。

随多账号方向，每个账号要有自己的人设；姊妹 change `account-persona-config`（接近完成）已把人设做成**按账号存储 + 按账号解析 + 后台可编辑**。但它为「短期单账号」保留了「缺人设→回落打包默认、绝不 brick」语义，且决策器的 `currentAccountId` 仍钉死 `default`。本 change 把云端真正改成**按连接多租户**，让那套已建好的按账号人设解析**真的按真实账号生效**，并补上一条产品规则要求的诚实闸：**新账号没设人设，节点不许启动**（绝不偷偷拿默认人设跑起来）。

> 本次覆盖**两种多节点**：① 不同账号各跑各的节点；② **同一账号被多个节点并行驱动**（N:1）——这要求同账号的多节点**共享该账号的单一风控/配额控制器**（额度按账号合并、不翻倍）、**防两节点对同一笔记/作者重复动作**、记账串行化。

## What Changes

- **edge — 每节点独立 Chrome**：外层启动器按节点分配独立调试端口 + 独立用户数据目录（目录名 `<accountId>-<节点号>`）+ 真实 `AIDCP_ACCOUNT_ID` / `AIDCP_EDGE_ID`（编排留在 edge 外、保持边缘薄）。唯一边缘核心改动：**堵掉静默接管**——探测到端口上已有别人的 Chrome 即**诚实报错**，除非显式 `AIDCP_CDP_ALLOW_REUSE`；崩溃残留的单例锁仅在确认无活进程持有时才清。**不引入指纹浏览器**（同机不同账号防关联不在本次范围）。
- **cloud — 按连接多租户编排**：① 把 `accountId` 穿透 `edge.hello` 事件并设入决策器当前账号；② 决策上下文（信息流状态 / 预算 / 待评论 / 当前账号）**按连接隔离**、**每连接一条私有事件通道**，连接间互不串味、互不重置会话；③ 下行指令**按 edgeId 精确路由**（不再广播）；④ 限频闸按连接的**真实账号**解析（复用已有 per-account 控制器注册表，停用 `default` 钉死）。
- **cloud — 同账号并行（N:1）安全**：同一账号的多节点**共享该账号的单一风控/配额控制器**（互动计数按账号合并、N 节点共用该账号每日额度、不翻倍）；**云端在下发互动前按账号去重**（含 in-flight 与已完成），防两节点对**同一笔记/作者**重复点赞/关注/评论（关注、评论无 per-note 去重，尤须此闸）；同账号控制器计数读改写**串行化**。同节点断线重连**顶替**旧连接，不算并行第二节点。
- **cloud — 诚实人设启动闸**：会话启动前用**独立的「绑没绑人设」判断**（不走会回落默认的解析器），未绑则**不开浏览循环、不发巡刷信号、在角色重订阅前短路**，账号置 `needs_persona_setup` 态 + **飞书通知**；**`default` 账号硬豁免**（保留其打包默认回落）；握手缺/空 `accountId` **按配置错误拒绝握手**，**不得偷偷映射成 `default`**。
- **cloud — 新账号自动登记**：握手时对新账号 upsert 一行「未配置」账号，使其在后台冒出来等设人设。
- **console — 状态可见 + 看板适配**：账号列表加「需设置人设 / 已绑人设」状态标 + 跳转人设页链接（人设页与设置 API 复用 `account-persona-config` 成果，**不新建**）；实时看板的事件扇出**改为跨「每连接私有通道」聚合**，对外仍是单一全局流（决策 ①的连带改动）。
- **被拒 / 需配置呈现**：经**飞书通知 + 后台状态**呈现，**不新增 cloud→edge 命令、不动边-云协议**（运营据飞书去设人设；被拒节点本次接受空转，由飞书把人叫去处理）。
- 兼容性：单 edge 场景下「按 edgeId 路由」与原「广播给唯一连接」行为等价，**非 BREAKING**。

## Capabilities

### New Capabilities
- `chrome-instance-isolation`：每个 edge 节点驱动**自己独立的 Chrome**（独立调试端口 + 独立用户数据目录），绝不静默接管/复用其它节点的浏览器，端口冲突诚实报错。
- `multi-tenant-orchestration`：云端编排器**按 edge 连接维护独立决策上下文 + 私有事件通道**、下行指令只发回**发起该决策的连接**（不广播）、限频闸按连接**真实账号**解析。
- `persona-gated-session-start`：会话仅对**已绑人设**的账号启动；未绑的非 `default` 账号被**诚实拒绝**并标记 `needs_persona_setup`，绝不静默以默认人设运行。
- `same-account-parallel-safety`：同一账号被多节点并行驱动时，**共享该账号单一风控/配额控制器**（额度合并不翻倍）、**按账号去重防同笔记/作者双动**、记账串行化；同节点重连顶替而非并列。

### Modified Capabilities
- `accounts-master-data`：新增**握手时自动登记**新账号（未配置态）+ 账号的**人设绑定状态**（派生字段）。
- `interaction-risk-gating`：限频闸由钉死 `default` 改为**按连接真实账号**解析控制器（与 `safety-quota-config` 在本 capability 上**需协调**，避免互相覆盖）。
- `console-panel-api`：`GET /api/accounts` 暴露**人设绑定状态**（沿用同一 JWT 鉴权）；实时看板事件扇出**改为跨每连接私有通道聚合**，对外仍单一全局流。

## Impact

- **aidcp-cloud（主体）**：改 `src/orchestrator/role-dispatcher.ts`（按连接决策上下文 + 私有事件通道 + `currentAccountId` setter + 启动闸 + 巡刷前短路 `:436-447/478-503/492-494`）、`src/comm/handler.ts:278/282`（accountId 入 `edge.hello`）、`src/comm/event-bus/types.ts:126`（事件载荷加 accountId）、`src/server.ts:568-572`（`sendCommand` 带 edgeId）+ `:375/530-538`（闸按真实账号）、`src/account-store.ts`（`ensureAccount` upsert + 绑定状态派生）、`src/panel/panel-server.ts`/`panel/types.ts`（`/api/accounts` 状态字段 + 看板扇出跨连接聚合）、`src/risk/*`（同账号控制器计数串行化 + 互动前按账号去重防双动）。**复用**：`account-persona-config` 的 `persona-store.ts`（`getForAccount` 作为「绑没绑」判据、解析器回落语义**不动**）、per-account 风控控制器注册表（同账号 N 连接天然共用一个，使额度按账号合并）。
- **aidcp-console（小）**：`src/pages/AccountsPage.tsx` 状态标 + 链接；`src/types/api.ts` DTO（与 cloud `panel/types.ts` **两处手工镜像、注明漂移风险**）。
- **aidcp-edge（小）**：`src/cdp/chrome-launcher.ts:502-521` 默认拒绝复用；新增 `scripts/` 启动器（每节点分配端口/目录/身份）；单例锁清理需判活进程。
- **协议**：本 change **完全不动边-云协议**——被拒/需配置经飞书通知 + 后台状态呈现，**不新增 cloud→edge 命令**（决策 ③）。
- **迁移 / 红线必做**：上线诚实闸前**给现存真实账号预种 `persona_config` 行**，否则它们突变「未绑定、拒启动」回归；**现默认账号的 edge 须显式声明 `AIDCP_ACCOUNT_ID=default`**（上线「拒绝缺账号握手」后不声明会被拒，决策 ④）；新增账号状态接口走同一 JWT；`accounts.persona_ref` 列是死的（`account-store.ts:25`）**留着别用**，绑定以 `persona_config` 行存在为准。
- **依赖 / 协调**：依赖 `account-persona-config`（人设存储/解析/后台页）；与 `safety-quota-config` 共改 `interaction-risk-gating`、与 `account-real-nickname` 共改 `account-store.ts` / panel DTO，需错峰协调。
- **非目标**：同机不同账号**防关联**（不同设备指纹 / 独立 IP / 指纹浏览器）——不在本次范围（edge 仍一机真实指纹）。
