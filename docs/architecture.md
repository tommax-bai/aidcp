# AIDCP 架构

本文给出 AIDCP 的组件划分、组件图与端到端数据流。两层（边缘 / 云端）通过
WebSocket 协议解耦，协议本身见 [`protocol.md`](protocol.md)。

> **架构演进提示**：浏览主路径已从早期"单体 `Planner` → `PlanStep[]` 单线规划"演进为
> **事件驱动多 Agent 编排**——`RoleDispatcher` 按平台 capability 与配置注册浏览闭环、
> 会话守护、评论、通知、概念和平台专题角色；准确枚举以 `event-bus/types.ts` 的 `RoleName`
> 与 `role-dispatcher.ts` 的 `setup()` 为准。角色通过
> 进程内 `EventBus` 协作，角色产出的语义动作经 `command-bridge` 翻译为
> [协议 v2](protocol.md) 指令下发边缘。同时落地了 `RiskController` 风控状态机、
> `PublishOrchestrator` 发布角色管道、飞书 Bot（含 `/bind` 与审批卡片）等。
> 边缘端则新增了 `browse`（浏览执行层）、`humanize`（拟人化）、`flows/publish-post`
> （发布流程）与 `electron`（桌面运行时）。本文只维护稳定边界，易变枚举以代码为准。

## 1. 组件总览

```
┌────────────────────────────────────────────────────────────────────────────────┐
│                              aidcp-cloud (云端 · 重)                              │
│                                                                                  │
│   ┌─────────────────── orchestrator / agents / event-bus ──────────────────┐    │
│   │  RoleDispatcher ── 按 capability 注册角色，驱动 feed.entered 闭环          │    │
│   │   ContentEvaluator/FeedScroller/NoteOpener/DeepReader/ContentCurator/    │    │
│   │   InteractionAppraiser/AuthorEvaluator/ProfileOpener/ProfileBrowser/     │    │
│   │   FollowAgent/SearchScroller/SearchEvaluator/SearchExecutor/BackToFeed/  │    │
│   │   SessionMonitor   ── 全部经 EventBus（typed）解耦协作，SessionContext 存态 │    │
│   └────────────┬──────────────────────────────────┬────────────────────────┘    │
│                │ 角色事件                           │ 读 Soul 人设 / 调 LLM        │
│        ┌───────▼─────────┐  ┌──────────┐  ┌────────▼──────┐  ┌──────────────┐    │
│        │ RiskController  │  │ Planner  │  │ Text LLM      │  │  Soul        │    │
│        │ 状态机+滑窗+配额  │  │(Simple)  │  │ provider路由  │  │  soul.yaml   │    │
│        │ +冷启动+时间窗    │  │目标→步骤  │  │  文本 LLM     │  │  人设/兴趣    │    │
│        └───────┬─────────┘  └────┬─────┘  └───────┬───────┘  └──────────────┘    │
│   ┌────────────▼─────────┐       │                │      ┌─────────────────────┐ │
│   │ PublishOrchestrator  │       │                │      │  feishu Bot         │ │
│   │ 多阶段发布角色图       │       │                │      │  长连接/卡片/命令    │ │
│   │ scout→creator→       │       │                │      │  /bind/审批信号      │ │
│   │ 图规划/生图→审批→    │       │                │      └──────────┬──────────┘ │
│   │ executor+图片provider │       │                │                 │            │
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
| **RoleDispatcher** | `src/orchestrator/role-dispatcher.ts` | 事件驱动角色调度器：按平台 capability、功能开关和依赖可用性注册角色，订阅事件，以 `feed.entered` 启动浏览闭环，把 Edge 上报转换为内部事实并将角色语义动作翻译成 `EdgeCommand` |
| **角色（Agent）** | `src/agents/*.ts`、`src/event-bus/types.ts` | 角色按浏览与搜索、内容判断、互动、评论、通知、会话守护、身份与平台专题等职责订阅/发布事件。`RoleName` 是角色名枚举，实际注册集合由 `RoleDispatcher.setup()` 和运行配置共同决定；文档不复制易漂移的类名和数量 |
| **EventBus** | `src/event-bus/index.ts`、`types.ts` | 进程内 typed EventEmitter，`emit` fire-and-forget、`emitAsync` 等待、`onAny` 通配；角色间唯一通信渠道 |
| **SessionContext** | `src/agents/session-context.ts` | 当前会话态（当前笔记/来源页/已访问/连续滚动计数），取代旧 Blackboard；浏览预算（likes/collects/follows/searches）由 RoleDispatcher 持有 |
| **RiskController** | `src/risk/risk-controller.ts` | 风控权威：`explain(action)` 判定 allow/deny；组合状态机 + 分/时突发窗 + 自然日配额 + 比例 |
| **RiskStateMachine** | `src/risk/risk-state-machine.ts` | 账号状态机 `normal→warned→restricted→frozen`，含恢复窗口（warned 7d / restricted 3d）；信号种类 light/quota_exceeded/confirmed/fatal/recovered/manual_unfreeze |
| 风控配套 | `src/risk/{sliding-window-counter,quotas,cold-start-planner,time-scheduler,session-budget,interaction-dedup,search-frequency-limiter,pg-risk-store}.ts` | 分钟/小时滑动窗口计数、Asia/Shanghai 自然日配额、三档配额、冷启动养号、作息时间窗、会话预算、互动去重、搜索频控、PG 持久化 |
| **PublishOrchestrator** | `src/publish-agent/publish-orchestrator.ts` | 多阶段发布角色图，覆盖选题、创作、视觉规划与生成、清洗与质量判断、元数据、审批和执行；实际注册角色见 `src/server.ts`。`pipeline-context` 串联阶段，发布账本落库；`CommandSequencer` / `PublishDispatcher` / `ScheduledPublishReconciler` 分别负责原子指令顺序、提交落态和定时稿到期对账 |
| **feishu Bot** | `src/feishu/` | 长连接接收入站事件，处理命令、通知、审批卡片、群与团队路由；准确命令和卡片动作以当前 router/types 为准 |
| **SimplePlanner** | `src/planner/simple-planner.ts` | 规则优先 + LLM 兜底，把"一句话目标"拆成 `PlanStep[]`（定向场景；浏览闭环走角色驱动） |
| **LLM 文本出口与厂商注册表** | `src/llm/{qwen,providers,index}.ts` | 根据角色配置解析文本模型、provider 和思考模式，通过统一客户端调用；厂商、模型和凭据来源以注册表与运行配置为准。视觉理解和图片生成使用各自的显式 provider 边界 |
| **Soul** | `src/soul/loader.ts` | 从 `soul.yaml` 装载人设（身份/兴趣/行为准则；Facebook 可带受控 `writing_language`），驱动各角色人格化决策与账号对外文本语言 |
| **PgAnchorCache / ConceptStore / BotChatStore** | `src/cache/*.ts` | PG 锚点主缓存 + 暂存晋升、概念池、Bot 群绑定 |
| **AccountStateManager** | `src/account-state.ts` | 账号 active/paused 内存状态（暂停时跳过笔记处理） |
| **EdgeCloudServer / DefaultMessageHandler / command-bridge** | `src/comm/{ws-server,handler,command-bridge}.ts` | WS 服务端 + 消息路由 + `EdgeCommand→Envelope` 翻译 |
| protocol | `src/comm/protocol.ts` | 边云消息的 `PROTOCOL_VERSION=2`、`MessageType`、payload、信封与解析/校验；消息枚举由两端协议类型和 acceptance 契约测试共同守护，本文不复制数量 |
| **Panel API（管理后台后端）** | `src/panel/{panel-server,jwt,auth,panel-ws,panel-store}.ts` | console 前端的进程内后端：HTTP `/api` + JWT 鉴权 + 浏览器 WS；独立端口、与 8787 边-云 ws 物理隔离 |

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
| **EdgeTaskCoordinator** | `src/execution/edge-task-coordinator.ts` | 同一 edge/CDP 页面写任务单写：浏览命令边界 quiesce、陈旧队列取消、任务优先级/FIFO、taskId owner 校验、租约到期与队列清空后单次恢复 |
| **humanize** | `src/humanize/*.ts` | 拟人化：`timing` 对数正态停顿、`mouse-path` 贝塞尔、`keyboard-rhythm`、`scroll-physics`、`reading-time`、`session-rhythm` 疲劳曲线 |
| **flows** | `src/flows/{anchors,like-post,publish-post,publish-command-handlers}.ts` | 垂直业务流程：业务锚点常量、点赞流程、发布原子指令；小红书定时链路在内容/话题/其它选项之后设置并正证据校验定时时间，再精确点击“定时发布” |
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
3. **LLM 选择（缺口路径）**：把作用域内元素清单 `select.request` 发云端，由当前配置的文本 LLM 选编号，
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

- **风控**：Cloud 在计划或调度真实动作前调用账号对应的 `RiskController.canDo()` / `explain()`，
  组合最终风险状态、窗口配额、自然日配额、慢启动和动作专题规则；拒绝时不下发动作，也不
  消耗“已执行”计数。`RoleDispatcher` 还持有会话级预算并在动作完成后推进会话。
  Edge 回传的真实 `action.completed` 由 Cloud 转成 `interaction.occurred`，再由
  `RiskController.record()` 记账。协议中的 `risk.canDo` / `risk.record` /
  `session.budget.request` 目前是兼容保留通道，Edge 主路径不调用；不得据此推断 Edge 自己
  决定风控放行。
- **发布**：`PublishOrchestrator` 多阶段角色图产出内容并落 `pending_approval`；运营在控制台或飞书审核，草稿编辑通过 `content_version` CAS 防止旧版本误批。授权后 `CommandSequencer` 持有 edge task lease，按「进入创作页 → 标题/正文/图片/话题及其它选项 → 发布方式 → 提交 → 捕获」下发原子指令。
  - 立即发布：`submit_publish → capture_postId`；捕获到公开 id/URL 即 `published`，否则保留既有 `submitted` 待确认语义。
  - 小红书定时发布：`set_schedule` 验证 1 小时至 14 天北京时间窗口及“定时发布”按钮后提交，`capture_scheduled` 只捕获平台内部定时句柄并落 `scheduled`，不当作公开帖子、不计发布次数。`ScheduledPublishReconciler` 在目标时间后复用账号绑定和 edge lease 做有界对账；取得真实公开 id/URL 后以 CAS 转 `published` 并只记一次，未公开则退避，耗尽转 `needs_review`。

## 4. 关键设计取舍

- **事件驱动取代单体规划**：浏览不再"先规划一串步骤再执行"，而是边缘**结构化上报**、
  云端多个角色**按事件实时决策**单个动作。好处：贴近真人"看一条想一下"的节奏、易插拔
  新角色（只需 `subscribe` EventBus）、单角色失败不阻塞全局（`emit` fire-and-forget）。
- **DOM 快照而非 CDP DOM 树**：`CdpDomProvider` 用 `Runtime.evaluate` 取 `outerHTML`
  再交 jsdom 解析，直接复用既有 DOM-first 抽取逻辑（纯函数，一个操作周期内 DOM 稳定即可）。
- **结构路径执行而非坐标点击**：`CdpActionExecutor` 用 `tag[n]` 结构路径转 XPath，
  在浏览器侧 `document.evaluate` 重定位，触发原生事件序列，比坐标更抗改版。
- **协议与定位结构对齐**：`RemoteElement` / `RemoteAnchor` 是 `ElementDescriptor` /
  `Anchor` 的网络投影，云端只做"规划/选元素/缓存/编排"，原子操作始终留在边缘。
- **风控权威单写**：账号风控状态只由云端 `RiskController` 写入，边缘只询问（`risk.canDo`）
  与上报（`risk.record`），不自行决断"能不能做"。
