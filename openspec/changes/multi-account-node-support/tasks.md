# Tasks — multi-account-node-support

> 进度按 sub-repo 分节回写本仓；代码改动落 edge / cloud / console。完成项用 HTML 注释标 `<!-- <repo> <sha> 备注 -->`。安全红线回归须全过：`AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*`（见 §3、§5）。
>
> **实装状态（2026-06-24）**：§1–§6 全部实装 + 验证（cloud typecheck 干净、663 测试全过含 26 条 AC-* 红线 + 22 条新增多租户用例；edge 336 测试全过；console typecheck+build 过）。经一道对抗式评审发现并修复诚实人设闸「只挡 start、反应链仍在默认人设上空跑」红线（gap fix `a38fb96`）。**遗留**：§0.1（ECS 预种人设行）与 §7.1/§7.3（真机 E2E + ECS 部署）= **显式放行后再做**（生产 ECS 与 isales 同机、full-master 快照）。
>
> **提交说明**：本 change 的实装被并发会话的宽 `git add` 连带提交进 cloud `497d1bc` / edge `842ff30` / console `771378e`（混在 publish-history 等提交里，代码完整无损）；诚实闸红线的修复为独立提交 cloud `a38fb96`。

## 0. 前置 / 迁移（必做，先于开闸）

- [ ] 0.1 盘点 ECS 现存真实账号，给每个**预种 `persona_config` 有效 soul 行**（否则上线诚实闸后它们突变「未绑定、拒启动」回归）；`default` 无需（豁免）  <!-- DEFERRED：生产迁移，与 §7.3 部署一并、显式放行后做（SSH + PG，不盲跑） -->
- [x] 0.2 与并行 change 错峰协调：`safety-quota-config`（共改 `interaction-risk-gating`）、`account-real-nickname`（共改 `account-store.ts` / panel DTO）——确认对方落点、改动加性、不互相覆盖  <!-- safety-quota-config 核心已合入 master(dd43691)：它管「配额数字」(QuotaProvider)、本 change 管「用哪个账号的 controller」，正交叠加，未碰其文件；account-real-nickname 未启动(0/22)：本 change 的 personaBound 派生自 persona_config 行存在、零新增列/迁移，避开其 0012 迁移与 PanelAccount 字段撞车 -->
- [x] 0.3 核实改「每连接私有通道」后，后台看板扇出从「订阅一条总线」改为「聚合 N 条私有通道」的接法，且概念池 / SessionMonitor 等**不依赖单一全局总线做跨连接协调**（决策 1）  <!-- 接法=每连接私有总线 onAny tee 进全局观测总线(observerBus)，panel-ws 仍 onAny 订阅 observerBus 零改动；风控记账亦订 observerBus 按 evt.accountId 路由；SessionMonitor 为每 dispatcher 私有(随会话激活启停)，不跨连接协调。对抗评审 console-panel-api 段确认不漏不重 -->
- [x] 0.4 给现存默认账号的 edge 启动器**显式设 `AIDCP_ACCOUNT_ID=default`**（上线「拒绝缺 accountId 握手」后不显式声明会被拒，决策 4）  <!-- edge 842ff30：scripts/dev-run.sh 设 AIDCP_ACCOUNT_ID=${AIDCP_ACCOUNT_ID:-default}；新 scripts/launch-multinode.ts 要求每节点显式 accountId -->

## 1. aidcp-cloud — 按连接多租户编排核心

- [x] 1.1 `comm/handler.ts` 的 `edge.hello` 事件载荷加 `accountId`；`event-bus/types.ts` 事件类型同步加字段  <!-- cloud 497d1bc：handler onHello emit edge.hello{edgeId,accountId,ts}；event-bus/types.ts edge.hello 加 accountId? -->
- [x] 1.2 为每个 edge 连接建立一束**独立运行时**（**私有 `EventBus`** + `RoleDispatcher` + `SessionContext`(+SessionMonitor)），按 `sessionId/edgeId` 持有、握手创建断连拆除；入站消息只灌本连接私有通道、出站只发本 `edgeId`（决策 1）  <!-- cloud 497d1bc：新增 orchestrator/connection-runtime.ts(ConnectionRuntimeRegistry)；server.ts buildDispatcher 工厂 + ws-server onClose 拆除；handler busFor(session) 路由所有入站 emit -->
- [x] 1.3 去掉 `currentAccountId='default'` 钉死，改为由连接运行时按真实 `accountId` 设入；`restartSession()` 只重建**当前连接**会话，不动其它连接  <!-- cloud 497d1bc：role-dispatcher.setCurrentAccountId + onHelloEvent 从 edge.hello payload 设入；每 dispatcher 私有，restartSession 只动自身 -->
- [x] 1.4 `sendCommand` 闭包捕获本连接 `edgeId`，调 `pushToEdges(env, edgeId)` 定向下发（不再广播）；单连接行为保持等价（非 BREAKING）  <!-- cloud 497d1bc：buildDispatcher sendCommand → server.pushToEdges(envelope, ctx.edgeId)；单连接=定向到唯一连接，等价旧广播 -->
- [x] 1.5 连接生命周期：**同 `edgeId` 重连顶替**该账号下旧连接；「同账号 + 不同 `edgeId` + 旧连接仍活」= **真并行第二节点**（交 §6，**不再硬拒**，决策 2）  <!-- cloud 497d1bc：connection-runtime onHandshake 同 edgeId 不同 sessionId → server.closeEdge(old)；不同 edgeId 并存。test 覆盖 -->
- [x] 1.6 验证两连接（不同账号）决策上下文互不污染、互不重置；指令不串号  <!-- test/integration/connection-runtime.test.ts：隔离+tee+顶替+并行+断连拆除(7)；对抗评审 multi-tenant-orchestration 段全 satisfied -->

## 2. aidcp-cloud — 诚实人设启动闸 + 新账号登记

- [x] 2.1 在会话启动前加**独立绑定判据** `PersonaStore.getForAccount(accountId)!==null`（**不走会回落默认的解析器**，解析器回落语义保持不动）  <!-- cloud 497d1bc：server.ts isPersonaBound=personaStore.getForAccount(id)!==null 注入 dispatcher；createPersonaResolver 回落语义未动 -->
- [x] 2.2 未绑（且非 `default`）→ 不 `startSession`、不 emit 巡刷信号、在角色重订阅**之前**短路；置账号 `needs_persona_setup` 态 + 飞书告警  <!-- cloud 497d1bc canStartSession 在 restartSession 前短路 + onNeedsPersonaSetup 飞书告警(去重)。**红线补强 a38fb96**：把角色订阅/反应链/看门狗从 setup() 移到会话激活，未绑账号连边缘自发 page.cards 也不接线→不在默认人设上空跑(对抗评审发现+回归测试坐实) -->
- [x] 2.3 `default` 账号**硬豁免**；握手**缺/空 `accountId` → 拒绝握手当配置错误**，不建会话、不塞 `default`（决策 4）  <!-- cloud 497d1bc：canStartSession default 豁免；connection-runtime onHandshake 缺/空 accountId → onConfigError + ok:false；handler onHello 回 error 信封不建会话 -->
- [x] 2.4 `account-store.ts` 加 `ensureAccount(accountId)` 幂等 upsert（INSERT ON CONFLICT DO NOTHING，不覆盖已配置行、不默认 active 作为就绪信号）  <!-- cloud 497d1bc：account-store.ensureAccount 仅插入不覆盖；status DB 默认 active=运营暂停维度，就绪由派生 personaBound 独立判定(见 §4.1) -->
- [x] 2.5 账号「人设绑定状态」派生字段以 `persona_config` 行存在为准；`accounts.persona_ref` 保留不用  <!-- cloud 497d1bc：panel-store personaBound 派生自 persona_config 行存在且非空；persona_ref 仅 DDL 留存、零读取 -->
- [x] 2.6 验证：原有账号复用已绑人设直接启动、新账号未绑被诚实拒绝且出现在主表、`default` 永不被拒  <!-- test/integration/persona-gated-start.test.ts(7 含 2 条反应链回归)；对抗评审 persona-gated-session-start 段：start 路径全 satisfied，反应链红线经 a38fb96 闭合 -->

## 3. aidcp-cloud — 限频闸对齐 + 安全回归

- [x] 3.1 限频闸由钉死 `getController('default')` 改为按连接真实账号 `riskRegistry.getController(accountId)`；闸与记账落同一真实账号、不分叉  <!-- cloud 497d1bc：buildDispatcher 的 getRiskStatus/canInteract/getCommentDailyRemaining/getCommentLikeDailyRemaining 全绑 ctx.controller(真实账号)；handler controllerFor(session) 供 budget/risk 通道；记账 interaction.occurred 按 session.accountId 路由 -->
- [x] 3.2 安全红线回归：`npm run test:acceptance`（AC-RISK/PROTO/PUB）+ 全量 `npm test` + `npm run typecheck`  <!-- cloud a38fb96 后：typecheck 0 错；test:acceptance 26 全过(AC-PROTO/PUB/RISK/SEARCH)；npm test 663/663 -->

## 4. aidcp-console — 人设绑定状态可见

- [x] 4.1 cloud `panel-store.ts` 的 `GET /api/accounts`(+`/:id`) 暴露 `personaBound`/`needsPersonaSetup`（沿用既有 JWT）  <!-- cloud 497d1bc：PanelAccount+AccountJoinRow+toAccount+ACCOUNT_SELECT LEFT JOIN persona_config 派生；DTO 实际在 panel-store.ts(非 panel/types.ts) -->
- [x] 4.2 console `src/types/api.ts` 镜像该 DTO 字段（两处手工同步）  <!-- console 771378e：types/api.ts PanelAccount 加 personaBound/needsPersonaSetup -->
- [x] 4.3 console `AccountsTable.tsx` 账号列表加「需设置人设 / 已绑人设」状态标 + 跳转 `/persona` 链接（复用 account-persona-config 人设页）  <!-- console 771378e：AccountsTable 加「人设」列，需设置→warning Tag+Link to /persona、已绑→green、default→中性 -->
- [x] 4.4 console `npm run typecheck` / build 通过；未带 JWT 请求 `GET /api/accounts` 返回 401  <!-- console typecheck + vite build 过；JWT 守护未改(panel-server 既有鉴权链)，对抗评审确认无新增免鉴权入口 -->
- [x] 4.5 cloud 看板事件扇出改为**跨每连接私有通道聚合**，对外仍单一全局只读流、不漏不重，仍 JWT 守护、不碰边缘 socket  <!-- cloud 497d1bc：每私有总线 tee→observerBus，panel-ws 仍 onAny observerBus(零改)；对抗评审确认不漏不重、单连接等价 -->

## 5. aidcp-edge — 每节点独立 Chrome

- [x] 5.1 `cdp/chrome-launcher.ts` 探测到端口已有 Chrome 时**默认拒绝复用、诚实报错**；仅 `AIDCP_CDP_ALLOW_REUSE` 显式开启才复用  <!-- edge 842ff30：reuse 分支默认 throw「拒绝静默接管」，allowReuse 经 env('1'/'true'/'yes') 才复用 -->
- [x] 5.2 残留单例锁清理：仅在确认指向进程已不存活时清，否则诚实失败，**绝不盲删**  <!-- edge 842ff30：clearStaleSingletonLock 仅 pid 死(ESRCH)才 unlink；活进程(含 EPERM)/解析不出/其它主机一律诚实 throw -->
- [x] 5.3 新增 `scripts/` 启动器：按节点序号分配 `AIDCP_CDP_PORT=base+N` + `AIDCP_CHROME_PROFILE=...-<accountId>-<节点号>` + 真实身份，拉起 N 进程（编排留 edge 外）  <!-- edge 842ff30：scripts/launch-multinode.ts + package.json start:multinode；编排在 edge 核心外、不引指纹浏览器 -->
- [x] 5.4 edge `npm run test:acceptance` / `npm test` / `npm run typecheck` 通过；不引入指纹浏览器  <!-- edge：typecheck 0 错；test:acceptance(AC-PROTO/PUB)全过；npm test 336/336(含新增 reuse-reject/allowReuse/锁 6 用例) -->

## 6. aidcp-cloud — 同账号并行（N:1）安全（决策 2）

- [x] 6.1 同账号 N 连接经 per-account 控制器注册表**天然共用同一控制器** → 互动计数按账号合并、共用每日额度（不翻倍）；加测试坐实  <!-- cloud 497d1bc：riskRegistry.getController 按 accountId memoize，buildDispatcher 用 ctx.controller；对抗评审 same-account-parallel 段 satisfied -->
- [x] 6.2 **互动前按账号去重**：下发互动指令前查「该笔记/作者本账号是否已**在途或已完成**同类互动」，命中跳过；**in-flight 占坑**(下发即占、回执/超时释放)；**关注/评论/评论赞尤须覆盖**  <!-- cloud 497d1bc：新增 risk/interaction-guard.ts(InteractionGuard per-account)；role-dispatcher sendCommand 占坑去重、action.completed complete/releaseFailed、TTL 120s 兜底；keyFor: note/author/comment-anchor -->
- [x] 6.3 同账号控制器**记账串行化**（队列/锁），防并发竞争重复扣减/漏记  <!-- 采用：record() 的 canDo→counter.record 临界区为**同步**(其间无 await)，Node 单线程下天然串行、零竞争(对抗评审 same-account「并发记账不竞争」satisfied)；未重构 co-owned safety-quota record()，以同步不变量保证 D7③；in-flight 去重亦从源头防双下发→双记账 -->
- [x] 6.4 验证同账号两节点：共用一控制器、额度合并不翻倍、撞同一笔记/作者不双动、并发记账不竞争  <!-- test/risk/interaction-guard.test.ts(7) + connection-runtime 顶替/并行；对抗评审 same-account-parallel-safety 段 7 场景全 satisfied -->
- [x] 6.5 **被拒/需配置呈现 = 飞书通知 + 后台状态**（决策 3）：未绑/缺身份被拒发飞书 + 置后台状态；**不新增 cloud→edge 命令、不动协议**；被拒节点空转靠飞书叫人补人设  <!-- cloud 497d1bc：onNeedsPersonaSetup/onConfigError 发飞书(去重)；needs_persona_setup 为派生字段(无新状态列)；协议零改(HelloPayload.accountId 早已存在) -->

## 7. 验证 / 部署 / 归档

- [ ] 7.1 E2E 两场景：(a) 两不同账号——两 Chrome PID/端口/数据目录、指令不串、限频各按账号、未绑被诚实拒绝并后台显示、登录各自持久；(b) 同账号两节点——共用一控制器额度不翻倍、撞同一笔记/作者不双动、同 `edgeId` 重连顶替不并列  <!-- DEFERRED：真机 E2E 需多开 Chrome + 连 ECS，显式放行后做。代码级已覆盖：单测 + 对抗评审；单连接等价已验 -->
- [x] 7.2 `openspec validate multi-account-node-support --strict` 通过  <!-- 通过("is valid") -->
- [ ] 7.3 ECS 部署（备份 → rsync --exclude .env/node_modules/.git → systemctl restart → healthcheck active+8787+飞书+PG）；注意 ECS 是 full-master 快照、会连带下游已累积 master，dry-run 先盘点；部署后 grep 关键文件 + 看新启动日志；同机 isales 不可碰  <!-- DEFERRED：显式放行后做。注意 §0.1 预种人设须先于诚实闸生效 -->
- [x] 7.4 进度回写本仓（各 task 标 `[x]` + commit-sha）  <!-- 本次回写完成；archive 待 §0.1/§7.1/§7.3 落定后再 /opsx:archive -->
