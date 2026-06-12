# AIDCP 架构

本文给出 AIDCP 的组件划分、组件图与端到端数据流。两层（边缘 / 云端）通过
WebSocket 协议解耦，协议本身见 [`protocol.md`](protocol.md)。

> **架构演进提示**：云端已从早期"单体 `Planner` → `PlanStep[]` 单线规划"重构为
> **事件驱动多 Agent 编排**——`RoleDispatcher` 注册 15 个角色（`BaseRole`），通过
> 进程内 `EventBus` 协作，角色产出的语义动作经 `command-bridge` 翻译为
> [协议 v2](protocol.md) 指令下发边缘。同时落地了 `RiskController` 风控状态机、
> `PublishOrchestrator` 发布角色管道、飞书 Bot（含 `/bind` 与审批卡片）等。
> 边缘端则新增了 `browse`（浏览执行层）、`humanize`（拟人化）、`flows/publish-post`
> （发布流程）与 `electron`（桌面打包）。本文已对齐当前代码。

## 1. 组件总览

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                              aidcp-cloud (云端 · 重)                              │
│                                                                                  │
│   ┌─────────────────── orchestrator / agents / event-bus ──────────────────┐    │
│   │  RoleDispatcher ── 注册 15 角色，启动 feed.entered 闭环                   │    │
│   │   ContentEvaluator/FeedScroller/NoteOpener/DeepReader/ContentCurator/    │    │
│   │   InteractionAppraiser/AuthorEvaluator/ProfileOpener/ProfileBrowser/     │    │
│   │   FollowAgent/SearchScroller/SearchEvaluator/SearchExecutor/BackToFeed/  │    │
│   │   SessionMonitor   ── 全部经 EventBus（typed）解耦协作，SessionContext 存态 │    │
│   └────────────┬──────────────────────────────────┬────────────────────────┘    │
│                │ 角色事件                           │ 读 Soul 人设 / 调 LLM        │
│        ┌───────▼─────────┐  ┌──────────┐  ┌────────▼──────┐  ┌──────────────┐    │
│        │ RiskController  │  │ Planner  │  │  QwenClient   │  │  Soul        │    │
│        │ 状态机+滑窗+配额  │  │(Simple)  │  │ (DashScope)   │  │  soul.yaml   │    │
│        │ +冷启动+时间窗    │  │目标→步骤  │  │  文本 LLM     │  │  人设/兴趣    │    │
│        └───────┬─────────┘  └────┬─────┘  └───────┬───────┘  └──────────────┘    │
│   ┌────────────▼─────────┐       │                │      ┌─────────────────────┐ │
│   │ PublishOrchestrator  │       │                │      │  feishu Bot         │ │
│   │ 6 角色管道:scout→     │       │                │      │  长连接/卡片/命令    │ │
│   │ creator→director→    │       │                │      │  /bind/审批信号      │ │
│   │ assembler→gatekeeper │       │                │      └──────────┬──────────┘ │
│   │ →executor +万象配图   │       │                │                 │            │
│   └────────────┬─────────┘       │                │                 │            │
│                └────────┬────────┴────────┬───────┘                 │            │
│                         ▼                 ▼                         │            │
│        ┌────────────────────────┐  ┌──────────────────────────────┐│            │
│        │ command-bridge          │  │  PgAnchorCache / ConceptStore ││            │
│        │ EdgeCommand→Envelope     │  │  BotChatStore / pg-risk-store ││            │
│        └───────────┬────────────┘  └──────────────┬───────────────┘│            │
│        ┌───────────▼─────────────────────────────────────────┐     │            │
│        │  EdgeCloudServer (ws) + DefaultMessageHandler (路由)  │◄────┘            │
│        │  pushToEdges() 下发；emit 上报事件到 EventBus          │                 │
│        └───────────────────────┬─────────────────────────────┘                 │
└────────────────────────────────┼────────────────────────────────────────────────┘
                                 │  WebSocket（边-云协议 v2，见 protocol.md）
                                 │  hello/plan/select/anchor · note.*/browse.* · interaction.*
                                 │  page.cards/note.detail · session.budget/risk.canDo · publish.*
┌────────────────────────────────┼────────────────────────────────────────────────┐
│                                ▼            aidcp-edge (边缘端 · 轻)              │
│   ┌──────────────┐  ┌────────────────────────┐  ┌───────────────────────────┐   │
│   │ EdgeClient   │  │  BrowseSession          │  │  LocatingEngine            │   │
│   │ 握手/路由/上报 │──│  云端命令分发 + 拟人化   │──│  五层编排 + 三道闸          │   │
│   │ cloud-selector│  │  feed/modal/note/search │  │  guard→cache/match→select  │   │
│   └──────┬───────┘  └───────────┬────────────┘  │  →execute→post-validate    │   │
│          │                      │               └──────┬───────────┬─────────┘   │
│   ┌──────▼──────┐  ┌────────────▼──────┐  ┌────────────▼──┐  ┌─────▼─────────┐   │
│   │ publish/    │  │ humanize/          │  │ flows/        │  │ extractor /   │   │
│   │ approval-gate│ │ 停顿/鼠标/键盘/     │  │ anchors/      │  │ matcher /     │   │
│   │ 审批信号等待  │  │ 滚动/疲劳曲线       │  │ like/publish  │  │ cache/guard   │   │
│   └─────────────┘  └────────────────────┘  └───────────────┘  └───────────────┘   │
│   ┌──────────────────────────────────────────────────────────────────────────┐  │
│   │  CDP 接入层（原生 WebSocket，非 Playwright）                               │  │
│   │  CdpDomProvider ── Runtime.evaluate(outerHTML) → jsdom Document            │  │
│   │  CdpActionExecutor ── 结构路径→XPath，浏览器侧 click/input/scroll          │  │
│   │  CdpClient / targets / session / chrome-launcher / stealth-injector       │  │
│   └─────────────────────────────────┬────────────────────────────────────────┘  │
│   （Electron 打包：src/electron/ 系统托盘 + Chrome 网关 + 控制面板 UI）            │
└─────────────────────────────────────┼────────────────────────────────────────────┘
                                      │ CDP over WebSocket (:9222)
                                      ▼
                              ┌───────────────┐
                              │  Chrome 浏览器 │  (--remote-debugging-port)
                              └───────────────┘
```

## 2. 组件职责

### 2.1 云端 aidcp-cloud

| 组件 | 文件 | 职责 |
| --- | --- | --- |
| **RoleDispatcher** | `src/orchestrator/role-dispatcher.ts` | 事件驱动角色调度器：注册 15 角色、`setup()` 订阅、`feed.entered` 启动闭环、把 Edge 上报喂数据层、把角色事件翻译成 `EdgeCommand` 下发 |
| **15 个角色（Agent）** | `src/agents/*.ts` | 继承 `BaseRole`，各订阅/发布特定事件：`ContentEvaluator`（卡片价值）/`FeedScroller`/`SearchScroller`（翻页）/`NoteOpener`（开卡）/`DeepReader`（深读）/`ContentCuratorRole`（质量关卡）/`InteractionAppraiserRole`（点赞收藏决策）/`AuthorEvaluator`/`ProfileOpener`/`ProfileBrowser`/`FollowAgent`（主页与关注）/`SearchEvaluator`/`SearchExecutor`（搜索）/`BackToFeed`（返回）/`SessionMonitorRole`（会话守护：动作数/时长/预算超限即发 `session.should_end` 结束会话） |
| **EventBus** | `src/event-bus/index.ts`、`types.ts` | 进程内 typed EventEmitter，`emit` fire-and-forget、`emitAsync` 等待、`onAny` 通配；角色间唯一通信渠道 |
| **SessionContext** | `src/agents/session-context.ts` | 当前会话态（当前笔记/来源页/已访问/连续滚动计数），取代旧 Blackboard；浏览预算（likes/collects/follows/searches）由 RoleDispatcher 持有 |
| **RiskController** | `src/risk/risk-controller.ts` | 风控权威：`explain(action)` 判定 allow/deny；组合状态机 + 滑窗 + 配额 + 比例 |
| **RiskStateMachine** | `src/risk/risk-state-machine.ts` | 账号状态机 `normal→warned→restricted→frozen`，含恢复窗口（warned 7d / restricted 3d）；信号种类 light/quota_exceeded/confirmed/fatal/recovered/manual_unfreeze |
| 风控配套 | `src/risk/{sliding-window-counter,quotas,cold-start-planner,time-scheduler,session-budget,interaction-dedup,search-frequency-limiter,pg-risk-store}.ts` | 滑动窗口计数（分/时/日）、三档配额、冷启动养号、作息时间窗、会话预算、互动去重、搜索频控、PG 持久化 |
| **PublishOrchestrator** | `src/publish-agent/publish-orchestrator.ts` | 发布角色管道：`ContentScout→ContentCreator→ImageDirector→ContentAssembler→ApprovalGatekeeper→PublishExecutor`，`pipeline-context` 串联，`wanxiang-client` 万象生图，`publish-log-store` 落库 |
| **feishu Bot** | `src/feishu/{ws-receiver,messenger,commands,cards,bot-chat-events,handler,token}.ts` | 官方 SDK 长连接收事件；`/status /pause /resume /publish-test /bind` 命令路由；审批卡片构建 + 回调写信号文件；进退群自动入库 |
| **SimplePlanner** | `src/planner/simple-planner.ts` | 规则优先 + LLM 兜底，把"一句话目标"拆成 `PlanStep[]`（定向场景；浏览闭环走角色驱动） |
| **QwenClient** | `src/llm/qwen.ts` | Qwen（DashScope 兼容 OpenAI）HTTP 客户端，仅用全局 `fetch` |
| **Soul** | `src/soul/loader.ts` | 从 `soul.yaml` 装载人设（身份/兴趣/行为准则/会话上限），驱动各角色人格化决策 |
| **PgAnchorCache / ConceptStore / BotChatStore** | `src/cache/*.ts` | PG 锚点主缓存 + 暂存晋升、概念池、Bot 群绑定 |
| **AccountStateManager** | `src/account-state.ts` | 账号 active/paused 内存状态（暂停时跳过笔记处理） |
| **EdgeCloudServer / DefaultMessageHandler / command-bridge** | `src/comm/{ws-server,handler,command-bridge}.ts` | WS 服务端 + 消息路由 + `EdgeCommand→Envelope` 翻译 |
| protocol | `src/comm/protocol.ts` | 边-云消息类型（v2，41 个）+ 信封 + 解析/校验 |

### 2.2 边缘端 aidcp-edge

| 组件 | 文件 | 职责 |
| --- | --- | --- |
| LocatingEngine | `src/locating/engine.ts` | 五层编排（守卫→定位→执行→校验）+ 三道闸 |
| extractor | `src/locating/extractor.ts` | 把 DOM（或作用域）内可交互元素抽成结构化清单 |
| matcher | `src/locating/matcher.ts` | 多信号一致性打分，唯一且分差达标才判 hit |
| AnchorCache | `src/locating/cache.ts` | 内存锚点缓存（read-write/read-only/write-only）+ 暂存晋升 |
| selector | `src/locating/selector.ts` | 缓存缺口时让文本 LLM"做选择题"，校验编号防幻觉 |
| guard | `src/locating/guard.ts` | 操作前扫描并清除偶现干扰（弹窗/遮罩/登录过期…） |
| **EdgeClient** | `src/client/edge-client.ts` | 边-云 WS 客户端：握手、命令路由、结果回传；`cloud-selector` 委托选元素、`like-runner` 点赞执行 |
| **BrowseSession** | `src/browse/browse-session.ts` | 浏览会话编排：分发云端命令、结构化上报、拟人化；`feed-scroller`/`modal-controller`/`note-extractor`/`search-handler`（`card-filter` 已 `@deprecated`，开/跳决策上移至云端 `ContentEvaluator`） |
| **humanize** | `src/humanize/*.ts` | 拟人化：`timing` 对数正态停顿、`mouse-path` 贝塞尔、`keyboard-rhythm`、`scroll-physics`、`reading-time`、`session-rhythm` 疲劳曲线 |
| **flows** | `src/flows/{anchors,like-post,publish-post}.ts` | 垂直业务流程：业务锚点常量、点赞流程、发布六步（进入→标题→正文→标签→提交→校验） |
| **publish/approval-gate** | `src/publish/approval-gate.ts` | 发布审批：生成 requestId、构造/校验/轮询信号文件、等待授权 |
| CdpDomProvider | `src/cdp/dom-provider.ts` | 实现 `DomProvider`：从真实页面取 DOM 快照 |
| CdpActionExecutor | `src/cdp/action-executor.ts` | 实现 `ActionExecutor`：原子操作落到真实页面 |
| CdpClient / chrome-launcher / stealth-injector | `src/cdp/*.ts` | 原生 WebSocket CDP RPC、Chrome 启动/登录检测、反检测脚本注入 |
| **electron** | `src/electron/{main,preload,chrome-launcher}.cjs` + `renderer/` | 桌面打包：系统托盘、Chrome 启动网关、控制面板 UI（状态/暂停恢复/重登） |

> 关键接口 `DomProvider` / `ActionExecutor` 定义在 `engine.ts`，单测下由 jsdom
> 充当 DOM 源、由内存桩充当执行层；真实环境由 CDP 层实现同一接口——**接口不变，
> 实现可换**，这正是定位层能脱离浏览器完整单测的原因。

## 3. 数据流

### 3.1 浏览会话闭环（v2 主路径：事件驱动多 Agent）

```
边缘 BrowseSession                         云端 RoleDispatcher + EventBus
  page.cards 上报 ────────────────────────► handler emit → ContentEvaluator
                                            有价值→NoteOpener发note.open / 无价值→FeedScroller发page.scroll
  执行 note.open / page.scroll ◄──────────── command-bridge 翻译角色事件
  note.detail 上报 ───────────────────────► ContentCurator 质量关卡（quality.pass/reject）
                                            → InteractionAppraiser 决策 like/collect/pass
                                            → AuthorEvaluator/ProfileOpener/FollowAgent 主页链
  interaction.like / navigation.back ◄────── 
  action.completed 上报 ──────────────────► 记账；BackToFeed 发 feed.entered 续刷
                                            SessionMonitor 超时/超预算 → onSessionEnd
  session.end ◄──────────────────────────── 
```

会话由 `feed.entered` 事件启动、并在"互动/返回"后再次 `feed.entered` 形成**闭环往复**，
直到 `SessionMonitorRole` 判定结束——而非一次性 `plan.response` 跑完即止。

### 3.2 单步定位（规划 / 锚点 / 选择，每步循环）

1. **守卫层**：扫描 DOM 干扰，能清则清，不能清→升级 `guard_blocked`。
2. **定位（缓存优先）**：
   - 本地 `AnchorCache` 命中 → `matcher` 在作用域内消歧；唯一且分差达标→拿到元素；
   - 未命中 → 走 LLM 选择（`select.request`）。（协议保留 `anchor.get` 取云端主缓存锚点，当前边缘使用进程内缓存，尚未接入云端 `anchor.get`。）
3. **LLM 选择（缺口路径）**：把作用域内元素清单 `select.request` 发云端，Qwen 选编号，
   云端校验编号在范围内后回 `select.response`。
4. **执行层**：`CdpActionExecutor` 把 `op` 落到真实页面（穿插 `humanize` 拟人化节奏）。
5. **后置校验（第一道闸）**：`PostValidator` 验证业务结果真发生。
6. **回写 / 上报**：
   - 缓存来源且校验通过 → `recordHit`；失败 → `recordFailure` 并强制下次走 LLM。
   - LLM 来源且校验通过 → 暂存候选锚点，连续确认才晋升（**第三道闸：反污染**）。
   - （规划中）`anchor.report` 协议消息可将命中/校验结果同步给云端 PG 主缓存；当前边缘 `LocatingEngine` 使用进程内 `AnchorCache`，尚未把锚点结果上报云端。
7. **重试上限（第二道闸）**：连续失败到 `maxAttempts` → `escalated(systemic_revision)`，
   **绝不静默成功**。

### 3.3 锚点生命周期（反污染晋升）

```
LLM 新解析锚点 ──stage──► 暂存区(staging)
                              │ 连续 confirmStaged 成功 ≥ confirmThreshold
                              ▼
                         主缓存(main / anchors 表) ──► 边缘 read 命中
   校验失败任意一次 ──dropStaged──► 丢弃（不污染主缓存）
```

边缘内存缓存（`AnchorCache`）与云端 PG 缓存（`PgAnchorCache`）采用**同构**的
暂存→确认→晋升策略；区别仅在边缘是进程内、单会话，云端是持久化、跨边缘节点共享。

### 3.4 风控判定与发布审批

- **风控**：边缘互动前可发 `risk.canDo`，`RiskController.explain()` 依据状态机（frozen/restricted）
  + 滑窗配额（minute/hour/day）+ 点赞比例（≤35%）判 allow/deny；成功后 `risk.record` 落账。
  云端角色侧亦受 `RoleDispatcher` 浏览预算约束（likes/collects/follows/searches），由各角色经 `consumeBudget()` 扣减、`SessionMonitorRole` 在 likes/collects/searches 耗尽时判定结束。
  - **现状提示**：边缘 `EdgeClient` 已实现 `canDo`/`requestSessionBudget`/`recordRiskAction`，云端也实现了 `risk.canDo`/`risk.record` 响应与 `interaction.occurred→RiskController.record` 订阅；但当前事件驱动浏览闭环**尚未在边缘调用**这些方法、`interaction.occurred` **暂无发射点**——风控配额对浏览动作的实时拦截/记账尚未接通，浏览侧约束目前主要由上面的 RoleDispatcher 浏览预算承担（`risk.canDo`/`risk.record` 协议通道已就绪，待接线）。
- **发布**：`PublishOrchestrator` 6 角色管道产出内容 → 下发 `publish.request` → 边缘发
  `publish.approval_request` → 云端飞书发审批卡片 → 运营点授权 → 卡片回调写信号文件
  `/tmp/aidcp-publish-approve-<requestId>.json` → 边缘读到 `approved=true` 执行
  `flows/publish-post` 六步 → `publish.result` 回传。

## 4. 关键设计取舍

- **事件驱动取代单体规划**：浏览不再"先规划一串步骤再执行"，而是边缘**结构化上报**、
  云端 15 角色**按事件实时决策**单个动作。好处：贴近真人"看一条想一下"的节奏、易插拔
  新角色（只需 `subscribe` EventBus）、单角色失败不阻塞全局（`emit` fire-and-forget）。
- **DOM 快照而非 CDP DOM 树**：`CdpDomProvider` 用 `Runtime.evaluate` 取 `outerHTML`
  再交 jsdom 解析，直接复用既有 DOM-first 抽取逻辑（纯函数，一个操作周期内 DOM 稳定即可）。
- **结构路径执行而非坐标点击**：`CdpActionExecutor` 用 `tag[n]` 结构路径转 XPath，
  在浏览器侧 `document.evaluate` 重定位，触发原生事件序列，比坐标更抗改版。
- **协议与定位结构对齐**：`RemoteElement` / `RemoteAnchor` 是 `ElementDescriptor` /
  `Anchor` 的网络投影，云端只做"规划/选元素/缓存/编排"，原子操作始终留在边缘。
- **风控权威单写**：账号风控状态只由云端 `RiskController` 写入，边缘只询问（`risk.canDo`）
  与上报（`risk.record`），不自行决断"能不能做"。
