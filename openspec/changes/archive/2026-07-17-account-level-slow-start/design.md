## Context

风控的每日 / 分钟 / 小时配额由 `RiskController.effectiveQuotas()`（`aidcp-cloud/src/risk/risk-controller.ts:174`）算出：先取档位基准（经注入的 `quotaProvider` 热读 `quota_config`，缺值回落 `quotas.ts` 写死三档），按风控态缩放（`warned` ×0.7 / `restricted` 互动清零 / `frozen` 归零），最后叠 `applyColdStartClamp`（`:195`）——`effectiveQuotas = min(冷启动天花板, 风控缩放)`，逐窗口逐动作取小（`minWindowQuotas`，`quotas.ts:83`）。

冷启动曲线写死在 `cold-start-planner.ts`（XHS `:10-18` / FB `:31-39`，各 7 天，区间上界即当日天花板），按 `platform === 'facebook'` 二选一（`:44`）。第 8 天起 `coldStartDailyCap` 返回 null、clamp 放行（`:42-48` → `risk-controller.ts:199`）。

当前生产态：`coldStartRampEnabled = process.env.AIDCP_COLDSTART_RAMP === 'true'`（`server.ts:1259`），默认关，`risk-controller.ts:196` 直接 return。**`created_at` 在生产上是死数据，本 change 会是它的第一个（也是唯一被拒绝的）候选消费者。**

关键约束：
- `effectiveQuotas()` 是**同步热路径**——被 `canDo` / `explain` / `dailyRemaining` / `quotaReleaseAfterMs` 全同步调用（`risk-controller.ts:90/111/121/174`），`canDo` 在浏览闭环每个动作都调。任何 provider 契约必须同步、零 IO、永不抛。
- `RiskControllerRegistry` 的 controller Map **永不驱逐**（`risk-controller-registry.ts:30/48-56`，全文无 delete / invalidate / TTL），controller 活到进程结束；面板仪表盘还会为每个有计数的账号 materialize controller（`panel-server.ts:643-652`）。
- 本仓 **无迁移执行器**（`account-store.ts:44` 注释自陈），schema 靠启动自建 + 自愈 `ALTER`。
- dev 与 OL **共读写同一个 PG**（`docs/deployment-environments.md:62`），仅靠 account_id 隔离。

## Goals / Non-Goals

**Goals:**
- 让运营能只给某一个真·新号开 7 天逐日爬坡，不牵连同云端其它账号。
- 「显示的 = 生效的」：客户端徽章的天数与 clamp 实际用的天数同源同格；勾了但没压时如实说明。
- 起点零说谎面：由云端在勾选那一刻写下，不推测账号年龄。
- 逐位零回归：账号级默认全 NULL、env 路径一行不动。

**Non-Goals:**
- 不删 `AIDCP_COLDSTART_RAMP` / `createdAt`（spec 明文保留的 MAY + 因生产事故加的回滚拉杆；往热点单写者文件塞不相关删除只放大 rebase 冲突面）。
- 不引入 `platform_registered_at` 与运营录入口（要新造入口 + 改 4 段导入格式 + 依赖运营真知道注册日期——号从卡商买来时运营自己常常也不知道。「永远填不上」是稳态不是过渡态；而新起点根本不需要它）。
- 不重新设计曲线（曲线跟档位走 = 另一个 change）。
- 不做 i 图标 / tooltip 基建、不建持久绑定表、不动 console、不做左栏 rail 徽章、不支持视频号、不动 pacing。

## Decisions

### D1：起点用 `slow_start_since`，绝不用 `created_at`

**选择**：`accounts` 表加一列 `slow_start_since TIMESTAMPTZ`（允许 NULL）。NULL = 关；非 NULL = 开且为起点。

**理由**：`created_at` 语义是「第一次连上本云端库」，FB 号主要靠 cookie 导入 → 三年老号会被算「第 1 天」；号复活时 `ON CONFLICT DO NOTHING`（`account-store.ts:237`）保留原值 → 「第 180 天」而它只跑过 3 天。这与 `persona-bound-tristate`、`honest-first-connect-label` 是同族错误的第三例：把「我们认识它 N 天」读成「它存在了 N 天」。

**附带效果（决定性）**：曲线只有 day 1..7。若沿用 `created_at` 当起点，**给任何入库超 7 天的号勾上慢启动 = 彻底零效果**，界面显示「已开启」、运行时什么都不做——比不做还糟。

**一列而非两列（`enabled` + `since`）**：一列同时表达开关 / 起点 / 三态，结构上不可能出现 `enabled=true && since=NULL` 这种非法组合，绕开枚举列才需要的幂等 CHECK 约束与旧行回填。「重新养一轮」= 覆写 `since`，与「打开」是同一个写，不需要第二个按钮。

**Alternatives**：(a) 沿用 `created_at` — 见上，上膛的 no-op + 谎言。(b) 新建 `account_nurture` 表 — accounts 表的拥有者本就是 `AccountStore`，新开 store 写同一张表破「单一拥有者」。

### D2：起点写入时对齐上海日起点

**选择**：`since = shanghaiDayStartMs(now)`（`server.ts:414` 已有），勾选当天整天算第 1 天。

**理由**：dayIndex 若按墙钟算（`floor((now-since)/86400000)+1`，照抄 `risk-controller.ts:197`），与「今日进展」的计数窗口（上海自然日）**不同相**。失败场景：23:50 勾选 → 次日 23:49 显示「浏览 18/20 · 第 1/7 天」，23:51 变成「18/25 · 第 2/7 天」——计数没清零、上限凭空长 5，一个打满的号在午夜前十分钟又能动。第 7→8 天毕业同理发生在自然日正中间，上限从 70 一下放开到档位值——那一刻的补量恰是最像机器的行为、恰发生在最敏感的新号上。且车队里 20 个号在 20 个不同墙钟时刻换档，运营对不上账。

**这是只能在写入时刻做对的决定**，事后补要迁数据。

### D3：摘掉 controller 的构造期快照，改 provider 现读

**选择**：把 `createdAt` / `platform` / `nurtureMetaResolver` 一起从 `RiskController` 构造期摘掉。`AccountStore` 已有两个同款同步内存镜像（`:164` nicknameCache / `:166` platformCache），加第三个 `slowStartCache`，由 `AccountStore` 自己实现 provider：`{ platformFor(id), slowStartSinceFor(id) }`。契约与已有 `quotaProvider` 逐字同款（`risk-controller.ts:47` 注入 + `:178-179` 在 `effectiveQuotas` 内每次现算）：**同步、零 IO、永不抛**。registry 删掉 `nurtureMetaResolver`（含 `:60` 那颗 `.catch(() => null)` 哑弹），只透传 provider。

**理由**：不这么做，勾选会「写库成功、HTTP 回 200、行为纹丝不动到重启，且零日志」——controller Map 永不驱逐，而 `coldStartRampEnabled` 是 `:50/67` 构造期冻结的 readonly。面板仪表盘会主动 materialize 每个有计数账号的 controller，所以**「重启才生效」不是边缘 case，是常态**。

**这是本设计唯一真正消灭问题而非绕过问题的地方**：做对之后，「Map 永不驱逐」从一个需要被绕开的坑变成一个不再相关的事实——registry 不需要任何失效机制。

**Alternatives**：(a) 给 registry 加 invalidate — 要求每个写入点都记得调；漏一处就是静默不生效。(b) TTL 驱逐 — 引入「几秒后才生效」的模糊态，且驱逐 controller 会丢滑动窗计数。

### D4：两条启用路径严格「谁开用谁的起点」，绝不合成

**选择**：anchor 解析优先级严格是：
1. `slow_start_since` 非 NULL → 用它
2. 否则 `AIDCP_COLDSTART_RAMP=true` 且 `createdAt` 存在 → 回落现状（env 路径原样保留，一行不动）
3. 否则 null → 逐位零回归

**MUST NOT** OR / AND / min 合成。

**理由**：合成一次就会把 FB 全车队夹回 `view=70`——正是 07-15 判为 bug 根因的那个上限。

### D5：平台未知 → 不 clamp，绝不静默回落 XHS 曲线

**选择**：platform 与 since 由同一个 live provider 现读；platform 解析不到 → `eligible=false`、不 clamp、UI 如实说明。

**理由**：`coldStartDailyCap(ageDays, platform)`（`risk-controller.ts:198`）→ `platform === 'facebook' ? FB曲线 : XHS曲线`（`cold-start-planner.ts:44`），**非 facebook 一律走 XHS 曲线**。而 `this.platform` 来自 `registry:59-60` 的 `nurtureMetaResolver(...).catch(() => null)` → meta 为 null 时传 `undefined`。失败场景：某 FB 账号首次 `getController` 时 PG 抖一下 → platform=undefined → D1 上限取 XHS 的 `view=50` 而非 FB 的 `20`（差 2.5 倍），且该 controller 整个进程生命周期不再重解析、无日志无告警。更慢性的一条：`accounts.platform` 的自愈 ALTER 是 `NOT NULL DEFAULT 'xiaohongshu'`（`account-store.ts:47`），任何被错标的 FB 行永久按 XHS 曲线跑。

**FB 那条更保守的曲线正是本功能唯一的存在理由**，不能记成「已知缺口」。

### D6：慢启动语义 = 取更严的（min），并如实标注「没压」

**选择**（用户 2026-07-17 拍板）：保持 `min(曲线, 档位)` 语义。云端在同一次组装里已有 clamp 前后两份数字，多算一个布尔 `binding`（clamp 是否至少收紧一项）随字段下发。

**理由与代价**：曲线写死、档位数字面板可热编辑，**两者之间没有任何不变量保证曲线更紧**。实测小红书 conservative 档（view 80 / like 20 / comment 3 / publish 1）vs XHS 曲线 D5-7 上界（view 120 / like 20 / comment 3 / publish 1）取 min 后：

| 动作 | D5-7 慢启动后 | 相对不开 |
|---|---|---|
| view | 80 | **不变** |
| like | 20 | **不变** |
| comment | 3 | **不变** |
| publish | 1 | **不变** |
| collect / follow / comment_like | 5 / 3 / 2 | 收紧 |

D3-4 的 view 上界也是 80 → **view 从第 3 天起就不再被慢启动约束**。更糟：`risk-controller.ts:181` 规定 `warned` 强制走 conservative 基准——**给一个 warned 的小红书号勾慢启动求稳，第 5 天起浏览/点赞/评论/发布一个数字都不变**。

这不否决功能（FB 曲线明显更紧、normal/aggressive 档增量也大），但它否决三件事：① UI 文案 MUST NOT 说「正在压低你的配额」，只能说「取更严的一个」；② 验收判据 MUST NOT 是「勾选后面板数字当场变」——用 XHS conservative 号验收数字纹丝不动，会去改一个没坏的东西；③ 「勾上 ⟺ 配额被压低」MUST NOT 写成机械断言——它在生产配置下为假，而单测用写死默认三档会稳过，即这条守卫守不住它声称守的东西。

**解法**：`binding=false` 时 UI 显示「慢启动 · 第 5/7 天 · 当前档位已更严，不额外限制」——让「没变」成为一个被明说的态，而不是一个看起来像 bug 的沉默。

### D7：协议加可选字段挂 `dailyUsage`，不新增消息类型

**选择**：挂 `ui.snapshot` 的 `UiDailyUsagePayload`（cloud `src/comm/protocol.ts:260` / edge `:555-579`，两份逐字一致）：

```
slowStart?: {
  state: 'off' | 'active' | 'graduated'
  day?: number          // active 时 1..7
  totalDays: number     // 7
  since?: number
  binding?: boolean     // active 时：clamp 是否至少收紧一项（见 D6）
  eligible: boolean
  ineligibleReason?: 'platform_unsupported' | 'platform_unknown' | 'edge_offline'
                   | 'client_auth_unavailable' | 'globally_disabled'
}
```

**放 `dailyUsage` 内而非 `UiSnapshotPayload` 顶层**：白拿 hello 回填 + 约 60s 自续跳（`ui-snapshot.ts:142-144`「hello 是这条周期链的唯一起点」；`server.ts:2072` refreshAt = asOf + 60s）。放顶层则只在 hello 下发（`pushDailyUsageSnapshot:229` 只发 dailyUsage + browserStandby），要另接即时推送点。附带收益：绕开 `main.cjs:3469-3473` 那处把 account payload 硬重建成三字段的白名单。

**这是必须付的一笔**：砍掉协议改成「selectEnv 时 GET 一次」，在常开数天的陪伴客户端上徽章会冻结在第 1 天，用户要的「7 天后消失」永远不发生。

**不触发协议四处同步的任何硬闸**：MessageType 数不变（`AC-PROTO-02` 不动）、command-bridge 不涉及（它只映射角色命令）、edge onMessage 白名单已含 `ui.snapshot`（`edge-client.ts:680`）、`docs/protocol.md` 只补表行与示例。

**但必须手写往返断言**：两份 protocol.ts 的机械保障只覆盖 MessageType 穷举（`protocol-contract.test.ts:4-6/37`），**payload 字段漂移 typecheck 完全抓不到——而且已经漏过**：`inspirationSummary` 只活在 edge（`protocol.ts:566` + `ui-event-lines.ts:77/108` + `main.cjs:1683/1703`），cloud 全仓含 test 零命中，客户端在渲染一个云端从未发过的字段。两仓各一条，照抄 `AC-PROTO-14`（`protocol-contract.test.ts:173/198/222`）。

### D8：UI 落点 = 「今日节奏」卡内常驻脚注行，不是标题区

**排除标题区**（用户原提案）三条理由：
- **算术上挤爆**：titlebar 无任何窄窗媒体查询（`styles.css:41-54`），`.tb-winctl-pad.win` 固定吃 140px（`:64`），`main.cjs:740` minWidth=640 → Windows 最坏格下 `.acct` 仅剩约 150px、昵称只剩约 60px（4 字）；而 `.acct-p` 是 `flex-shrink:0`（`:74`），新徽章的截断代价 100% 由昵称的 ellipsis 承担。**这是算术不是概率**——jsdom 不做布局、单测会全绿，mac 上（winctl-pad=0）永远复现不了。
- **作用域错**：标题区跟随选中环境（`renderer.js:992`），慢启动是账号级——位置本身在暗示错误的作用域。
- **与它改变的数字不同屏**。

**选 `#daily-summary` section（`index.html:259-303`）内、`#quota-windows`（:302）之后、section 闭合前**四条理由：
- 该 section 永不 hidden（`renderer.js` 全文只在 `:583` toggle `expanded`，无 hidden 路径）→ 离线也在。对比 `#quota-windows`：`windows.length===0` 时整块 hidden + 清空（`:590-594`），而慢启动正是「启动新号之前」要设的——放那儿等于在唯一需要它的时刻它不存在。
- 不在折叠区内（`quotaDetailsOpen` 是模块级裸变量、默认收起、不持久化 `:366`；`ui-state.cjs` 只存 lastPublish → 埋进去发现率归零）。
- 不在任何 innerHTML 重建范围内（`:596` 只重建 `#quota-windows` 内部）→ 静态节点，JS 只切 checked / disabled / hidden / textContent。
- 与它改变的数字同屏。

**其它排除**：设置抽屉（本机运行时配置，改完要重启核心 `renderer.js:2827`，账号级放那儿会多机各写各的）、左栏 rail（`.rail-name` 空间更紧 = 第二轮挤压；登记为已知缺口：多号并行时看不出哪个号在养）。

**视觉**：用 `.switch.inline-switch`（`styles.css:1529-1543`），照 `browser-cold-standby`（`index.html:775-779`）——它已被两个「行为策略」类开关占用、语义一致；裸 checkbox 在本客户端偏向临时/辅助选项，不匹配长期生效的账号策略。徽章新建 `.acct-age` 类照 `.acct-p` 尺寸口径（10px / 2px 6px），**别复用 `.badge`**（12px/4px 11px、为浮层行设计、会撑高行）。

**必须 `stopPropagation`**：`renderer.js:1744-1747` 的 `fields.dailySummary` 整卡点击委托只认 `closest('button')`，checkbox / label 不是 button → 点勾选框会连带展开/收起「今日节奏」。更难看的是 `<label>` 包 `<input>` 时点文字合成两次冒泡 → 切换两次 → 净效果为零；直接点滑块只冒泡一次 → 切换一次。**同一控件点在不同位置行为不同，人工点测会当「偶发」放过**。照 `:1748-1750` 自己 stopPropagation，**不要**去放宽 `:1745` 的判据。

### D9：写回走 client-auth HTTP + 活映射解析；不走 WS，不建绑定表

**绝不走 WS**：`ws-server.ts` 全文无任何鉴权，`session.accountId` 是边缘在 hello 里自己声明的字符串（`edge-client.ts:271-279`）；`publish.approval_action` 的「鉴权」只是 `draft.accountId === session.accountId` 自证比对（`server.ts:2403`）。那对「本地在场的人审自己的稿」够用，对账号级风控配置不够——改一个字符串就能替别人关慢启动。client-auth 侧红线已成文：`accountId is never accepted as an unverified cross-customer selector`（`interaction-customer-api.ts:266-268`）。

**不照抄 read-controls 那条链**（这是最大的隐藏工作量陷阱）：`withAuthorizedInteractionScope`（`client-user-store.ts:656-700`）的 accountId 只能从 `interaction_auth_state` 表 join 出来（`:676-681`），而那张表的唯一写入者链路终点是 `aidcp-edge/src/wechat-channels/runtime.ts:104`——**这张表只有视频号有行**。FB/XHS 环境走这条路 100% 返回 `not_authorized`（404），且报错语义是「你没权限」→ 排查会先去查客户授权。**云端今天不存在 envKey→accountId 的权威持久映射**（memory 记的「写侧租户隔离缺口 61.17」）。

**也不建 `edge_account_binding` 持久表**：① 爆炸半径——为一个勾选框改握手路径，写入一旦抛（唯一约束冲突 / 换机 / PG 抖）就可能把边缘挡在门外；若给 `account_id` 加 UNIQUE + 冲突拒绝握手，会直接把「同账号铺多环境」这个被显式支持的配置打下线（`index.html:95-101` 的 `#same-account-warn` 注释自陈「云端会合并风控/配额」，是正常配置不是冲突）。② 语义更差——持久绑定会陈旧：账号早已从该环境撤走、绑定行还在，客户仍能改一个不归他跑的账号。③ 信任链并不更强——表里的 accountId 同样来自无凭据 hello，只是把「现在自称是谁」冻成「曾经自称是谁」。

**采用**：`ws-server` 已维护活的 edgeId↔accountId 会话表，且已有反方向的 `resolveEdgeIdForAccount(accountId, capability)`（`ws-server.ts:80`，只认 OPEN + 非 stale）。加一个镜像的 `resolveAccountIdForEdge(edgeId)`：同一循环、判据反过来、多条即诚实失败。envKey→edgeId 是确定性的（`fleet.cjs` 的 `ads-${profileId}` ↔ `renderer.js:211` 的 `envKey = selected.profileId`）。授权用已存在的 `ownsEnv(userId, envKey)`（`client-user-store.ts:632-648`）。

路由 `PUT /environments/:envKey/slow-start`，体 `{ enabled: boolean }` 严格 `onlyKeys` 校验（照 `interaction-customer-api.ts:277-282`），**accountId 由云端解析、客户端永不提交**。回执带写后真态 + 生效后的当日上限。

**「边缘不在线就改不了」不是缺陷**：slowStart 状态本身就搭在 `ui.snapshot.dailyUsage` 上，边缘离线时这张卡的数据本来就不更新、开关本来就该禁用。两者是同一件事，不额外损失。解析不出 → 409「该环境当前未连接」，如实说。

**信任边界写进 spec**：accountId 仍是边缘自报的（与风控计数、发布定向同源），但 ownership 是管理员授予的 env_key，且握手已有 platform 一致性校验（`connection-runtime.ts:143` 的 `platform_mismatch`）。客户只能改「自己环境上此刻正在跑的那个账号」。与现状信任模型一致、不新增攻击面——但要写明，不能装作不存在。

### D10：三个必须砍掉的复杂度

- **「已保存 vs 已下发本机」二态不做**：read-controls 需要它（`interaction-workspace.js:979-981`）是因为那个开关要下发到边缘核心执行。慢启动的执行体在云端 `effectiveQuotas` 内——只要 D3 的 provider 现读做对，PUT 200 = 本云端已生效。照抄一个不存在的状态同样是撒谎。**两者绑定**：若偷懒做成构造期读入，这个简化立刻变谎言。
- **expectedVersion CAS 不做**：单值 + 单写入口，last-write-wins 无丢失更新的实际危害。read-controls 需要 CAS 是因为两个独立开关共用一个版本号会互相覆盖，慢启动没有这个结构。
- **定时轮询不做**：字段挂 dailyUsage 白拿 60s 推送（D7）。

### D11：单写红线

慢启动是 `effectiveQuotas` 的**输入**，不是风控状态。MUST NOT 进 `risk_state`、MUST NOT 碰 `setQuotaLevel` / `applySignal`、MUST NOT 进 `risk-controller.ts:144-152` 的 mutationChain。

### D12：第一版平台闸只放 facebook / xiaohongshu

视频号禁用勾选并如实说明原因。理由：`applyColdStartClamp` 的平台分叉（`risk-controller.ts:203-207` 视频号走 XHS 曲线 + dm_reply 豁免、`cold-start-planner.ts:44` FB 专属曲线）因默认关在生产几乎从未执行过——开关一放开就是首次批量生效。零成本的风险削减。

## Risks / Trade-offs

- **[勾了什么都没压，用户以为在压]（D6）** → `binding` 布尔如实下发 + UI 明说「当前档位已更严，不额外限制」；验收 MUST 用 FB 号 + normal/aggressive 档（那里数字必变），XHS conservative 号另跑一条专验 `binding=false` 文案。
- **[新字段被两道手写白名单静默吞掉]** → `ui-event-lines.ts:100-120` 与 `main.cjs:1675-1700` 都是 `Record<string, unknown>` 手工组装、typecheck 抓不到，与 C3残留2.1「FB 早带回却被未声明事件类型丢弃」逐位同型 → tasks 里列成显式逐个勾选项 + 两仓 AC-PROTO 往返断言。**注意 `ui-event-lines.ts:100-104` 的隐式耦合**：`totals` 为空即整块返 null，会把 slowStart 一起吞掉。
- **[直接改库回滚不生效]** → 内存镜像只在「服务写入的那个进程」里刷新（`quota-config-store.ts:197` 的形状，全仓无 setInterval/watch），`UPDATE accounts SET slow_start_since=NULL` 改了库但镜像不刷 → 必须有 `AIDCP_SLOW_START_DISABLED=true` 全局停用闸（重启即生效）。
- **[dev/OL 共库：验收点击就是生产改动]** → `docs/deployment-environments.md:62` ol 与 dev 共读写同一 PG。「新列默认 NULL 所以零回归」只证到了**部署那一刻**；只要验收账号同时在 OL 跑，dev 上一次勾选就会让 OL 生产上同一个号被夹到 FB D1 `view≤20`。**验收账号与 OL 在跑账号的排他核对是前置硬项**。
- **[dev 客户端根本发不出这个请求]** → `main.cjs:551` 第一行 `if (!clientAuthEnabled()) return ... 503 '当前构建未启用 customer-auth API'`；`:303-304` 注释自陈「未配置（现有运营装机 / dev）行为与从前完全一致」。验收时会把 503 读成「provider 没现读」→ 去改一个没坏的东西。**客户端必须是烘焙包或显式配 `AIDCP_CLIENT_AUTH_URL`**，列为前置硬项。
- **[与已合并 spec 正面冲突]** → `interaction-risk-gating:432` 把 env 钉成唯一开启条件，`:438-439` 还有 Scenario。`openspec validate --strict` 与 typecheck 对散文 MUST 均无感；不写 delta 就是让归档后的 specs 描述一个与代码相反的系统，下一个接手的人会照着 `:432` 把新功能当 bug 修掉。→ spec delta 为必交付项。
- **[热点文件并行冲突]** → 本 change 动两份 `protocol.ts` + `risk-controller.ts`（CLAUDE.md §7 明列单写者热点）→ **标记串行，不与其它 fleet session 并行**，否则 rebase 时两份 protocol.ts 漂移 → `AC-PROTO-*` 红。
- **[毕业静默消失]** → 第 8 天 clamp 自动失效而库里开关仍为真。若徽章静默消失，运营不知道限额是哪天放开的——而那正是最该被告知的时刻。→ 显式 `graduated` 态：「慢启动 · 已完成（X 月 X 日起上限已放开）」，由运营手动取消勾选后消失。反过来也不行：UI 显示未勾而库里是开 = 用第二个谎盖第一个。
- **[断连时字段不会变缺省]** → `main.cjs:3512` 是 `if (evt.dailyUsage)` 不清空、`:1728` bumpDailyUsage 展开保留 → 断连时 slowStart 只是停止更新而非消失。「字段缺省 = 不渲染」不足以覆盖断连，还要按既有连接态降级（灰化 +「云端已断开，状态可能已过期」）。

## Migration Plan

1. **加列**：`ACCOUNTS_SCHEMA_SQL`（`account-store.ts:27-52`）末尾照 `:44-50` 已有三条自愈 ALTER 的先例追加 `ADD COLUMN IF NOT EXISTS slow_start_since TIMESTAMPTZ`。**必须走 ADD COLUMN IF NOT EXISTS**——本仓无迁移执行器，只写进 CREATE TABLE 的话 dev/OL 那张早已存在的表永远拿不到它。配一份 `migrations/00XX_*.sql` 作文档。
2. **部署顺序无耦合**：新列默认 NULL、env 路径不动 → cloud 先上、edge 后上均可；edge 旧版收到未知字段照旧忽略（白名单机制天然向后兼容）。
3. **回滚**：`AIDCP_SLOW_START_DISABLED=true` + restart（秒级、无视所有账号级开关）。库列保留、不删（删列要停机）。
4. **验证**：Phase 0 落地后即可用 SQL/console 在 dev 造态、经后台仪表盘 `effectiveQuotas().day`（`panel-server.ts:646` 是天然观测点）验证 clamp 按新起点生效——不依赖 UI。

## Open Questions

无阻塞项。两个曾阻塞的语义已由用户 2026-07-17 拍板：① 慢启动语义 = 取更严的（min），`binding=false` 时如实说明；② 勾选框落客户端，接受「边缘不在线时开关禁用」与「accountId 源自边缘自报（与现状风控计数、发布定向同源）」两条代价。
