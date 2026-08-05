# AIDCP 架构

本文给出 AIDCP 的组件划分、组件图与端到端数据流。两层（边缘 / 云端）通过
WebSocket 协议解耦，协议本身见 [`protocol.md`](protocol.md)。

## 客户端交互边界（架构红线）

Electron 应用就是客户端；普通 Edge 子进程是按需自动化引擎，浏览器/CDP 是页面执行器。客户端与 Cloud 有两条语义不同、不得混用的路径：

| 路径 | 模型 | 允许内容 | 禁止内容 |
|---|---|---|---|
| customer-auth HTTP 数据面 | 客户端像 Web 网站一样主动拉取/提交；逐请求鉴权与结果 | 今日进展、最近发布、人设、配置、稿件、审批、环境管理、内容工作区等 AIDCP 自有数据 | 依赖引擎/浏览器在线；以全局 Cloud 长连接状态准入 |
| automation WebSocket | 已启用自动化引擎的双向任务通道；Cloud 可定向推送 | 自动化控制、外部平台 API 自动化、浏览器生命周期、页面自动化 | 管理后台向客户端推送普通数据读写或“应用配置”命令 |

判断标准是“谁执行什么”，不是是否需要浏览器：自动读取/修改外部平台仍是自动化，可经引擎推送，但 API-only 操作不得取得浏览器槽位；AIDCP 自有数据即使由后台修改，也应先持久化，再由客户端 HTTP 拉取。若以后需要数据实时提示，应建立独立用户级 notification/invalidation 通道，只通知客户端重新拉取，不直接携带非自动化写命令，也不以某个环境引擎在线代表客户端在线。

客户端首页也遵守同一边界：`今日进展`、当前发布态和最近一次确认发布统一从环境级 HTTP 概览读取。环境切换、窗口聚焦、展开详情、低频轮询或自动化结果事件只会触发重新拉取；自动化事件本身不直接改写业务计数或发布历史。首次读取失败显示未知/失败，不显示假 0 或“从未发布”；已有确认缓存时保留缓存并显示陈旧状态。

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
                                 │  automation WebSocket（边-云协议 v2，见 protocol.md）
                                 │  hello/plan/select/anchor · note.*/browse.* · interaction.*
                                 │  page.cards/note.detail · session.budget/risk.canDo · publish.*
┌────────────────────────────────┼────────────────────────────────────────────────┐
│                                ▼            aidcp-edge (边缘端 · 轻)              │
│     EdgeClient ── 握手 / 命令路由 / 上报 / 客户端鉴权                           │
│          │                                                                      │
│          ▼                                                                      │
│     ★ Native 页面引擎（Rust 子进程）── 现役，且是唯一的页面智能                 │
│       命令 → 定位 → 拟人化动作 → 后置校验 → 结构化诚实回执                      │
│       页面规则分片编进二进制（facebook-router / xhs-command-router）            │
│          │                                                                      │
│          ▼                                                                      │
│     CDP 接入层（原生 WebSocket，非 Playwright）                                 │
│       CdpClient / targets / session / chrome-launcher / stealth-injector        │
│       cdp/browser-provider ── 指纹浏览器生命周期；execution ── 页面单写         │
│       humanize ── 节奏参数；wechat-channels ── API-only 旁路（不占浏览器）      │
│                                                                                 │
│     ⚠ 退役并已从生产 dist 剪除：locating/ · browse/ · publish/ ·                │
│       facebook/ 的 reader | executor | consent | identity 等，共 35 个模块。    │
│       名单事实源 = aidcp-edge/scripts/native-engine-inventory.cjs 的            │
│       RETIRED_DIST_MODULES；本文 §2.2 / §3.2 / §3.3 已按此标注。                │
│                                                                                 │
│     （Electron 客户端：客户会话 + HTTP 数据面 + 按需引擎监督 + 控制面板 UI）    │
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

> **要判断「边缘某职责该归本地还是该由云端接管」，看 [`edge-addressing-layers.md`](edge-addressing-layers.md)。**
> 那份文件定义了边缘按**编址单位**分的四层（宿主＝机器 / 环境＝分身 / 翻译＝环境→账号 / 账号＝账号，
> 前三层权威在本地、只有账号层在云端）与四条归属判据，并附三个已裁决判例。
> 它是**裁决依据、不是归属表**——「这块归谁」由既有归属台账回答，且**MUST NOT 据它另起一张表**。

> **⚠ 读这一节前必须知道的一件事（2026-08-05 据实修订）：页面智能已整体迁进 Native 引擎，
> 原来的那套 TypeScript 页面实现虽然还在仓里，但已被生产构建剪除。**
>
> **判据是「核心入口到不到得了」，不是「有没有人 import 它」。** 生产 `dist` 由两道机制共同裁剪：
> ① 一张显式退役名单（`aidcp-edge/scripts/native-engine-inventory.cjs` 的
> `RETIRED_DIST_MODULES`，35 条，**这是事实源**）；② 从核心入口出发的可达性剪枝——
> 名单外但已无人可达的模块同样被删掉（`src/locating/` 除 `engine.ts` / `cache.ts` 之外的几个模块正是这样消失的）。
>
> **后果对写代码的人最要紧**：在退役模块上实装，**代码会写完、测试会全绿、发版会成功，
> 而运营机上跑的仍是 Native 引擎那一套**——改动零生产效果，且没有任何东西会警告你。
> 这已经让至少两份提案的立论整个落空（一份被裁定删除，一份的落点须重写，见
> `docs/deferred-defect-proposals-2026-08-05.md` §5）。
>
> 下表按此拆成两半。**「已从生产剪除」那半仍可作实现参照**（很多正确写法与真机经验只留在那边，
> 各 change 的 `oracle.md` 就是干这个的），**但 MUST NOT 当作现役落点**。

**现役（在生产 `dist` 里）**

| 组件 | 文件 | 职责 |
| --- | --- | --- |
| **Native 页面引擎** | `native/page-engine/`（Rust，编成子进程二进制） | **现役唯一的页面智能**：定位、拟人化动作、后置校验、诚实回执全在引擎内；平台页面规则以分片形式编进二进制，明文不落盘 |
| **native-page-engine 宿主** | `src/native-page-engine/{client,runtime,browse-session,command-mapper,publish,identity,facebook-auth,identity-guard,diagnostic-forwarder}.ts` | 引擎子进程的监督与通道：开会话 / 下发命令 / 收回执 / 诊断转发；命令映射与发布、身份等编排落在这一层 |
| **EdgeClient** | `src/client/edge-client.ts` | 边-云 WS 客户端：握手、命令路由、结果回传、客户端鉴权与生命周期 |
| **EdgeTaskCoordinator** | `src/execution/{edge-task-coordinator,commit-window,takeover}.ts` | 同一 edge/CDP 页面写任务单写：浏览命令边界 quiesce、陈旧队列取消、任务优先级/FIFO、taskId owner 校验、租约到期与队列清空后单次恢复；提交窗口预算与接管 |
| **humanize** | `src/humanize/*.ts` | 拟人化节奏参数：`timing` 对数正态停顿、`mouse-path` 贝塞尔、`keyboard-rhythm`、`scroll-physics`、`reading-time`、`session-rhythm` 疲劳曲线 |
| CdpClient / targets / session | `src/cdp/{client,targets,session}.ts` | 原生 WebSocket CDP RPC、目标枚举与会话 |
| browser-provider / chrome-launcher / stealth-injector | `src/cdp/*.ts` | 指纹浏览器与 Chrome 生命周期、登录检测、反检测脚本注入、代理运行时观测 |
| CdpDomProvider / CdpActionExecutor | `src/cdp/{dom-provider,action-executor}.ts` | 仍在生产，但**已不再服务已退役的定位引擎**；现由 `cdp/` 内部与少量工具路径使用 |
| **wechat-channels** | `src/wechat-channels/*.ts` | 视频号 API-only 运行时（浏览器只作一次性登录旁车，不占浏览器槽位） |
| **electron** | `src/electron/*` + `renderer/` | 桌面客户端：系统托盘、浏览器启动网关、控制面板 UI、按需引擎监督 |

**已从生产剪除（退役，仅留仓中作实现参照）**

| 组件 | 文件 | 原职责 | 现由谁承担 |
| --- | --- | --- | --- |
| LocatingEngine / AnchorCache | `src/locating/engine.ts`、`cache.ts` | 五层编排 + 三道闸、内存锚点缓存与暂存晋升 | Native 引擎内的定位与校验 |
| extractor / matcher / selector / guard | `src/locating/*.ts` | 元素抽取、多信号打分、LLM 选择题、干扰清除 | 同上（这几个是**可达性剪枝**掉的，不在显式名单里） |
| BrowseSession 及其执行件 | `src/browse/{browse-session,feed-scroller,modal-controller,note-extractor,search-handler,notification-monitor}.ts` | 浏览会话编排与结构化上报 | `src/native-page-engine/browse-session.ts` + 引擎分片 |
| cloud-selector / like-runner | `src/client/*.ts` | 委托云端选元素、点赞执行 | 引擎内定位与动作 |
| Facebook 读写件 | `src/facebook/` 的 `*-reader` / `*-executor` / `consent` / `identity` / `cta-labels` / `post-identity` / `facebook-session` 等 | Facebook 页面读取与写动作 | `native/page-engine/src/facebook-router/` 分片 + `facebook/*.rs` |
| flows | `src/flows/{anchors,like-post,publish-post,publish-command-handlers}.ts` | 业务锚点、点赞、发布原子指令 | 引擎内平台分片（`src/flows/` 只剩 `bounded-poll` / `image-uploader` / `ui-event-lines` 现役） |
| publish/approval-gate | `src/publish/approval-gate.ts` | 发布审批信号文件的构造 / 校验 / 轮询 | **注意：审批链正在迁移**（活跃 change `publish-approval-signal-to-database` + 客户端内审批）。根 `CLAUDE.md` §4 仍把该文件写成边侧契约端点，**该指针已滞后**，随那条 change 收口时一并订正 |

> **关键接口 `DomProvider` / `ActionExecutor` 的现状**：它们定义在已退役的 `src/locating/engine.ts` 里，
> 且是 TypeScript 接口——**编译后不留任何运行时痕迹**。所以「接口不变、实现可换」这套
> jsdom ↔ CDP 可替换的单测结构，**描述的是退役那一代**。
> Native 引擎自己的等价能力靠 Rust 侧的 trait 与假 CDP 服务端实现（见
> `native/page-engine/tests/fake_cdp.rs`），脱离浏览器单测的性质没变，但换了落点。

页面内 JavaScript 只负责只读定位、提取和返回唯一目标坐标。对于会推进工作流、展开后续输入面或触发平台写入的控件，
`HTMLElement.click()` 返回不构成已点击证据；Native 必须在动作前重取唯一坐标，通过 CDP
`Input.dispatchMouseEvent(mouseMoved → mousePressed → mouseReleased)` 执行真实指针点击，并以同一目标的后置页面状态确认结果。
这四种情形都**绝不静默成功**，但**分两类处置**（判据见 [`stop-or-continue.md`](stop-or-continue.md) §4）：

- **候选不唯一 / 目标移动 = 身份不成立**（再动手就可能写到另一个对象）：动作诚实失败，
  **不得回落 DOM 点击、不得改点别的控件、不放宽**。
- **坐标缺失 / 后置状态未出现 = 可能只是水合与时序**：先按**可恢复**处理，允许**有界**重取 / 重等后再判；
  预算耗尽才失败，且回执写「重试 N 次未成」而不是「做不到」。

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

### 3.2 单步定位（规划 / 锚点 / 选择，每步循环）—— ⚠ **退役路径，已不在生产**

> **2026-08-05 据实修订。** 本节描述的是 TypeScript 那一代的定位循环。它依赖的
> `src/locating/engine.ts`、`cache.ts` 与 `client/cloud-selector.ts` **都已从生产构建剪除**，
> 「每步把元素清单发云端、让文本模型做选择题」这条路径**在迁移中整条消失**。
> 保留本节是因为它仍是那套机制的完整记述（各 change 的 `oracle.md` 会引用它），
> **MUST NOT 当作现役行为读**。
>
> **现役是什么**：Native 引擎用**编译进二进制的固定选择器**定位（`native/page-engine/src/` 的
> 平台分片），没有每步的模型选择，也没有非确定性锚点来源。
>
> **⚠ 三道闸的现役状态必须分开说，别把「落点搬了」读成「能力还在」**：
> 引擎侧 `native/page-engine/src/locating.rs` 是三道闸的**新落点**，但该模块自己的文档注释写明
> ——**本轮只造原语、尚未接进任何平台命令**；且**第三道闸（反污染晋升）在当前引擎里必然空转**，
> 因为固定选择器不产生任何需要暂存确认的新锚点。
> 也就是说：**后置校验与有界重试的语义活在各平台分片自己的实现里，
> 而「统一的三道闸落点」目前是待接线状态**。红线本身不变（见根 `CLAUDE.md` §2），
> 但**不得据此把「定位自愈已恢复」当成事实**。

**以下为退役路径原文：**

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
   **绝不静默成功**。**该升级描述的是「本步」已耗尽重试**，**MUST NOT** 被上层翻译成
   「该任务结构上做不到」而落持久终态——跨层义务见 [`stop-or-continue.md`](stop-or-continue.md) §4。

### 3.3 锚点生命周期（反污染晋升）—— ⚠ **边缘侧已随 §3.2 退役**

> **2026-08-05 据实修订。** 下图与末段描述的边缘侧机制（`AnchorCache` 的暂存→确认→晋升）
> 随 `src/locating/cache.ts` 一并从生产剪除。**云端 `PgAnchorCache` 仍在**，但它服务的是
> 已退役的每步定位循环，边缘不再向它回写（协议里的 `anchor.get` / `anchor.report`
> 本就是保留通道、从未接线，见 [`protocol.md`](protocol.md)；边缘客户端里那个
> `anchor.get` 请求辅助方法虽仍在编译产物中，但它的调用方——定位引擎——已经不在了）。
>
> **引擎侧的对应物是空转的**：固定选择器不产生非确定性锚点，暂存区恒为空（依据同 §3.2）。

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
