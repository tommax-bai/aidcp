# AIDCP 产品功能全景

> **本文定位**：AIDCP 的**顶层产品全景图**，是所有子设计文档的入口与索引。
> 读完本文你应能一句话回答：**产品做什么、有哪些模块、各模块现在什么状态、未来怎么演进**。
> 细节下钻请走第 6 节[文档索引](#6-文档索引)。

---

## 1. 产品定位与目标

### 一句话描述

**AIDCP 是一套面向小红书的 AI 自动化运营工具**：让 1–5 人的小运营团队，像管理一个真人
矩阵一样，安全、可控地运营 3–10 个小红书账号——AI 负责"刷、看、判断、互动、发布"，
人只负责"定策略、审关键动作、看效果"。

### 目标用户画像

| 维度 | 画像 |
| --- | --- |
| 团队规模 | 1–5 人的运营小组（非大型 MCN，无专职反爬团队） |
| 账号规模 | 3–10 个小红书账号（矩阵号 / 不同人设 / 不同梯队） |
| 痛点 | 人工刷号养号枯燥耗时；纯脚本太机械易封号；多账号难统一管理 |
| 诉求 | 账号**长期存活**优先于短期效率；少量人盯多个号；关键动作可控可审 |

### 核心价值主张：为什么用 AI 而非纯脚本

| 能力 | 纯脚本 | AIDCP（AI 驱动） |
| --- | --- | --- |
| **页面适配** | 选择器写死，改版即崩 | DOM-first 语义锚点 + LLM 兜底选元素，自愈不自残 |
| **内容判断** | 无法判断"这条值不值得互动" | Qwen 按人设（Soul）做互动决策、概念抽取 |
| **内容生产** | 模板填空，一眼营销号 | LLM 按人设生成 + 相似度去重，规避模板化 |
| **拟人化** | 固定 sleep，行为分布规整 | 对数正态停顿 + 贝塞尔鼠标 + 疲劳曲线，统计上像真人 |
| **决策闭环** | 写死流程 | 状态机 + 概念池驱动"自然刷"，越刷越懂账号兴趣 |

> **一句话**：纯脚本解决"能点"，AIDCP 解决"像人在点、且点得对"。

### 与竞品差异

| 对比项 | 传统群控 | Playwright 方案 | **AIDCP** |
| --- | --- | --- | --- |
| 操作粒度 | 坐标/截图点击 | 选择器点击 | **DOM 语义锚点 + 后置校验** |
| 改版抗性 | 极差（坐标飘） | 差（选择器失效） | **强（语义锚点 + LLM 自愈）** |
| 反检测 | 改机/真机，成本高 | 自带自动化特征，易被识别 | **CDP 原生 + stealth 注入 + 拟人化** |
| 防自残 | 无（静默点错） | 弱 | **三道闸：后置校验 / 重试升级 / 反污染** |
| 智能程度 | 纯执行 | 纯执行 | **AI 决策 + 人设驱动 + 概念演化** |
| 适用规模 | 几十上百号 | 单/少账号 | **3–10 号精细化矩阵** |

---

## 2. 功能模块全景（3 大类 12 项）

```mermaid
mindmap
  root((AIDCP))
    技术架构
      浏览器管理策略
      反检测与登录态
      容错与恢复
      Agent 拆分与通信
    产品设计
      多账号管理面板
      飞书交互
      任务编排体验
      异常处理体验
    运营策略
      风控模型
      效果度量体系
      多账号协同
      人机协作与止损
```

### 技术架构（4 项）

1. **浏览器管理策略** — 单机多实例 vs 分布式浏览器池；多账号的 profile / 端口 / 指纹隔离。
2. **反检测与登录态维持** — stealth 注入、指纹一致性、住宅代理、Cookie/Session 持久化。
3. **容错与恢复机制** — CDP 断连重连、验证码/滑块、页面改版自愈、会话崩溃恢复。
4. **Agent 拆分与通信方式** — 边/云各 Agent 职责边界、WebSocket 协议、命令调度。

### 产品设计（4 项）

5. **多账号管理面板与状态监控** — 账号分组、状态一览、人设（Soul）配置与下发。
6. **飞书交互设计** — 消息卡片、审批流、多账号消息归属与通知聚合。
7. **任务编排体验** — 指令下达、批量操作、审批粒度（哪些动作需人工确认）。
8. **异常处理体验** — 掉线恢复提示、风控告警、内容审核失败的人工接管。

### 运营策略（4 项）

9. **风控模型** — 频率限制、作息时间窗、内容去重、冷启动养号、风控状态机。
10. **效果度量体系** — 过程指标（操作量）、效果指标（涨粉/互动）、健康指标（存活/限流）。
11. **多账号协同与差异化定位** — 矩阵号互动策略、账号梯队、差异化人设。
12. **人机协作比例与止损机制** — 自动化程度分级、冻结规则、效果归因。

---

## 3. 各模块当前完成状态

### 统一状态口径

本节统一引用 `./design-gaps-and-models.md` 中定义的双维状态标注法，避免把产品实现状态与文档成熟度混写在同一列。

- 实现状态仅使用 `implemented / designed / planned`，用于描述能力是否已落地。
- 文档成熟度仅使用 `draft / complete / authoritative`，用于描述文档是否可作为实现依据。
- 原表中的“编写中”统一视为文档成熟度，不再作为实现状态使用。
- 若某能力同时包含已实现与未实现子项，则在实现状态中按能力项拆分说明，不再用单一“部分完成”覆盖全部语义。

> 图例：实现状态=`implemented / designed / planned`；文档成熟度=`draft / complete / authoritative`。
> 路径说明：边缘端代码在 `aidcp-edge/`，云端代码在 `aidcp-cloud/`，文档在本仓 `docs/`。

### 3.1 技术架构

| # | 模块 | 实现状态 | 文档成熟度 | 已实现 / 文档与代码位置 | 缺口 |
| --- | --- | --- | --- | --- | --- |
| 1 | 浏览器管理策略 | `implemented` | `complete` | 单机多实例已跑（多份 `edge*.log` / `cloud*.log` 为多实例运行痕迹）；`aidcp-edge/src/cdp/chrome-launcher.ts` 负责按参数拉起 Chrome | 分布式浏览器池、profile×指纹×IP 三元绑定的编排未做 |
| 2 | 反检测与登录态 | `implemented`（stealth/拟人化）+ `designed`（代理/持久化/防泄露） | `complete` | **stealth 注入已实现**：`aidcp-edge/src/cdp/stealth-injector.ts`（webdriver 抹除 / toString 伪装 / plugins / 权限对齐 / console.debug）；设计见 `docs/anti-detection.md` | Cookie/Session 持久化、住宅代理接入、WebRTC/DNS 防泄露、指纹画像表 未做 |
| 3 | 容错与恢复机制 | `implemented`（三道闸）+ `designed`（恢复闭环） | `complete` | LocatingEngine **三道闸**已实现（`aidcp-edge/src/locating/engine.ts`）：后置校验 / 重试升级 / 反污染；守卫层清干扰（`guard.ts`） | CDP 断连自动重连、验证码/滑块识别、会话级 crash recovery 未做 |
| 4 | Agent 拆分与通信 | `implemented` | `authoritative` | edge/cloud 双层 WS 架构已实现；协议 `aidcp-cloud/src/comm/protocol.ts` + `docs/protocol.md`；各 Agent（Locating/Planner/Orchestrator/Publish）边界清晰 | — |

### 3.2 产品设计

| # | 模块 | 实现状态 | 文档成熟度 | 已实现 / 文档与代码位置 | 缺口 |
| --- | --- | --- | --- | --- | --- |
| 5 | 多账号管理面板 | `planned` | `complete` | 人设配置基础已有（`aidcp-cloud/src/soul/`，`soul.yaml` 可装载） | Web 管理面板、账号分组、状态一览、可视化全未做（设计见 `docs/product-dashboard.md`） |
| 6 | 飞书交互设计 | `planned` | `complete` | — | 消息卡片、审批流、多账号归属全未做（设计见 `docs/product-feishu.md`） |
| 7 | 任务编排体验 | `implemented`（编排内核）+ `designed`（运营交互层） | `complete` | 后端编排内核已有：`aidcp-cloud/src/orchestrator/session-orchestrator.ts` + 状态机；CLI 触发 `src/cli/trigger-like.ts`、`src/publish/trigger.ts` | 面向运营的指令下达 UI、批量操作、审批粒度未做（设计见 `docs/product-task.md`） |
| 8 | 异常处理体验 | `designed` | `complete` | 底层信号已有（后置校验失败 / 升级 `systemic_revision`） | 面向人的掉线恢复/告警/接管体验未做（设计见 `docs/product-exception.md`） |

### 3.3 运营策略

| # | 模块 | 实现状态 | 文档成熟度 | 已实现 / 文档与代码位置 | 缺口 |
| --- | --- | --- | --- | --- | --- |
| 9 | 风控模型 | `implemented`（拟人化执行层）+ `designed`（控制器/状态机） | `complete` | **设计完整**：`docs/risk-control.md`（频率/作息/速度/去重/冷启动/状态机）。**拟人化执行层已实现**：`aidcp-edge/src/humanize/`（`timing` 对数正态停顿、`mouse-path` 贝塞尔、`keyboard-rhythm`、`scroll-physics`、`reading-time`、`session-rhythm` 疲劳曲线） | **频率计数器 / 档位 / 风控状态机（normal→warned→restricted→frozen）/ 时间窗口调度 未实现**（仅设计） |
| 10 | 效果度量体系 | `planned` | `designed` | `action.result` 上报通道已有（可作为过程指标数据源）；发布落库 `migrations/0001_publish_log.sql` | 过程/效果/健康三类指标的采集、聚合、看板全未做；统一口径引用 `./design-gaps-and-models.md` 的效果指标字典 |
| 11 | 多账号协同与差异化 | `implemented`（单账号人设）+ `planned`（跨号协同） | `draft` | 单账号人设（Soul）+ 概念池演化已实现（`orchestrator/concept-extractor.ts`、`cache/concept-store.ts`）；多套 soul 可并存 | 矩阵号互动策略、账号梯队、跨号协同调度未做 |
| 12 | 人机协作与止损 | `planned` | `draft` | — | 自动化分级、冻结规则、效果归因全未做（依赖风控状态机 #9 与面板 #5） |

补充口径：运营侧指标统一引用 `./design-gaps-and-models.md` 中的效果指标字典，按**过程指标 / 效果指标 / 健康指标**三类归口。本文只保留路线图层面的能力判断，不在此重复定义指标公式、归因规则与采集频率。

### 3.4 已交付的核心执行能力（横切多模块）

以下为已经**端到端跑通**的能力，构成 Phase 1 的实质内容：

- ✅ **浏览执行层**：feed 滚动 + 弹窗控制 + 内容提取 + 搜索 + 自动浏览循环
  （`aidcp-edge/src/browse/`：`feed-scroller` / `modal-controller` / `note-extractor` / `search-handler` / `browse-session`）。
- ✅ **点赞/收藏 + Qwen 决策**：互动决策器按硬质量门槛 + LLM 判断
  （`aidcp-cloud/src/orchestrator/engagement-decider.ts`），点赞执行 `aidcp-edge/src/client/like-runner.ts`。
- ✅ **Publish Agent**：内容生成 + 后处理 + 发布 + 落库
  （`aidcp-cloud/src/publish/`：`generator` / `post-processor` / `publisher` / `prompts`）。
- ✅ **Soul 人设**：`soul.yaml` + 强类型装载（`soul/loader.ts`）+ 概念提取 + 浏览状态机
  （`orchestrator/state-machine.ts`）。

> **重要校正**：相较早期规划，反检测的**行为拟人化层（humanize/）已落地**，
> 风控的**策略/状态机层仍只有设计文档**。即"怎么做才像人"已做，"做多少、什么时候停"待做。

---

## 4. 实现路线图

```mermaid
graph LR
    P1["Phase 1 · 当前<br/>单账号稳定运行<br/>+ 风控保护"] --> P2["Phase 2<br/>多账号 + 管理面板<br/>+ 效果度量"]
    P2 --> P3["Phase 3<br/>飞书交互 + 任务编排<br/>+ 多账号协同"]
    P3 --> P4["Phase 4<br/>规模化 + 止损<br/>+ 高级策略"]
    style P1 fill:#d4edda,stroke:#28a745
    style P2 fill:#fff3cd,stroke:#ffc107
    style P3 fill:#f8d7da,stroke:#dc3545
    style P4 fill:#e2e3e5,stroke:#6c757d
```

### Phase 1（当前）：单账号稳定运行 + 风控保护

**目标**：一个账号能长期、安全、自然地刷/赞/收/发，不被风控标记。

- ✅ 边/云 WS 架构、DOM-first 定位三道闸、浏览执行层、Qwen 决策、Publish、Soul。
- ✅ stealth 注入 + 拟人化执行层（humanize）。
- ⚠️ **本阶段关键缺口（最高优先级）**：
  - **P0** 风控频率计数器 + 档位 + 状态机（`risk-control.md §1/§6/§7`）——决定账号能否"活下来"。
  - **P0** Cookie/Session 持久化 + 住宅代理（`anti-detection.md §2/§3`）——决定登录态能否长期维持。
  - **P1** CDP 断连重连、验证码/滑块处理。

> **依赖**：风控状态机依赖"信号采集"（复用后置校验/重试升级，已有）；
> 时间窗口调度依赖云端调度器（待建）。

### Phase 2：多账号 + 管理面板 + 效果度量

**目标**：从 1 个号扩到 3–10 个号，运营能在一个面板上看清所有号。

- 多账号进程/端口/profile 隔离编排（依赖 Phase 1 的代理 + profile 绑定）。
- Web 管理面板（#5）：账号分组、状态一览、Soul 配置下发。
- 效果度量体系（#10）：基于 `action.result` 与 publish_log 做过程/效果/健康指标。

> **依赖**：面板依赖效果度量的数据源；多账号依赖反检测的 profile×指纹×IP 三元绑定。

### Phase 3：飞书交互 + 任务编排 + 多账号协同

**目标**：人不用盯屏幕，关键动作走飞书审批；多个号能协同。

- 飞书交互（#6）：消息卡片 + 审批流 + 多账号归属。
- 任务编排体验（#7）：面向运营的指令下达 UI + 批量操作 + 审批粒度。
- 多账号协同（#11）：矩阵号互动策略、账号梯队、差异化定位。

> **依赖**：飞书审批依赖任务编排的"审批粒度"定义；协同依赖 Phase 2 的多账号基础。

### Phase 4：规模化 + 止损 + 高级策略

**目标**：账号数继续扩张，引入自动止损与高级运营策略。

- 规模化反检测（指纹浏览器方案 B、住宅代理池，`anti-detection.md §6`）。
- 人机协作与止损（#12）：自动化分级、冻结规则、效果归因。
- 高级运营策略：跨号内容编排、热点跟进、A/B 人设实验。

> **依赖**：止损依赖效果度量（#10）+ 风控状态机（#9）+ 协同（#11）三者齐备。

---

## 5. 技术架构总览图

```mermaid
graph TB
    subgraph 人["运营团队（1-5 人）"]
        OP["运营"]
    end

    subgraph 交互["交互层（规划中）"]
        WEB["Web 管理面板<br/>账号/状态/人设<br/>(Phase 2)"]
        FS["飞书 Bot<br/>卡片/审批/告警<br/>(Phase 3)"]
    end

    subgraph cloud["aidcp-cloud（云端 · 重）"]
        PLAN["Planner<br/>目标→步骤"]
        ORCH["Orchestrator<br/>状态机+概念池+互动决策"]
        PUB["Publish Agent<br/>生成+后处理+发布"]
        LLM["QwenClient<br/>(DashScope)"]
        SOUL["Soul 人设<br/>soul.yaml"]
        WS["EdgeCloudServer<br/>WS 服务端+路由"]
        RISK["RiskController<br/>(规划中 · P0)"]
    end

    PG[("PostgreSQL<br/>锚点缓存/概念池<br/>publish_log")]

    subgraph edge["aidcp-edge（边缘端 · 轻）"]
        ENG["LocatingEngine<br/>五层编排+三道闸"]
        BROWSE["Browse 执行层<br/>滚动/弹窗/提取/搜索"]
        HUMAN["Humanize<br/>停顿/鼠标/键盘/滚动/疲劳"]
        STEALTH["StealthInjector<br/>反检测注入"]
        CDP["CDP 接入层<br/>原生 WebSocket"]
    end

    CHROME["Chrome（headful）<br/>--remote-debugging-port"]
    XHS["小红书 Web"]

    OP --> WEB
    OP --> FS
    WEB -.-> WS
    FS -.-> WS

    PLAN --> WS
    ORCH --> WS
    PUB --> WS
    ORCH --> LLM
    PUB --> LLM
    ORCH --> SOUL
    PUB --> SOUL
    RISK -.规划.-> ORCH
    WS --> PG
    ORCH --> PG

    WS <==>|"边-云 WS 协议<br/>hello/plan/select/anchor/action"| ENG

    ENG --> BROWSE
    ENG --> CDP
    BROWSE --> CDP
    HUMAN --> CDP
    STEALTH --> CDP
    CDP <==>|"CDP over WS :9222"| CHROME
    CHROME --> XHS

    style RISK stroke-dasharray: 5 5,fill:#fff3cd
    style WEB stroke-dasharray: 5 5
    style FS stroke-dasharray: 5 5
    style cloud fill:#eef6ff
    style edge fill:#f0fff0
```

**读图要点**：

- **边轻云重**：边缘只做定位/执行/拟人化/反检测注入；规划、模型推理、状态、持久化在云端。
- **接口不变、实现可换**：`DomProvider` / `ActionExecutor` 接口固定，CDP 层是其真实实现；
  未来切指纹浏览器时只换 CDP 连接目标，定位/执行逻辑零改动。
- **虚线节点 = 规划中**：`RiskController`、Web 面板、飞书 Bot 尚未实现。

---

## 6. 文档索引

### 已有设计文档

| 文档 | 内容 | 对应模块 |
| --- | --- | --- |
| [`docs/architecture.md`](architecture.md) | 组件划分、组件图、端到端数据流 | #4 Agent 拆分 |
| [`docs/protocol.md`](protocol.md) | 边-云 WebSocket 协议（信封 / 消息类型 / 时序） | #4 通信方式 |
| [`docs/risk-control.md`](risk-control.md) | 风控模型（频率/作息/速度/去重/冷启动/状态机） | #9 风控、#12 止损 |
| [`docs/anti-detection.md`](anti-detection.md) | 反检测与登录态维持（指纹/网络/Cookie/行为指纹） | #2 反检测、#1 浏览器管理 |
| [`docs/design-gaps-and-models.md`](design-gaps-and-models.md) | 统一状态口径、统一事件模型、统一审批对象模型、效果指标字典 | 跨文档统一口径 |
| [`docs/product-overview.md`](product-overview.md) | **本文**——产品全景与文档索引 | 全部 |

### 编写中的产品文档

| 文档 | 内容 | 对应模块 | 状态 |
| --- | --- | --- | --- |
| `docs/product-dashboard.md` | 多账号管理面板与状态监控 | #5 | `complete` |
| `docs/product-feishu.md` | 飞书交互设计（卡片/审批/归属） | #6 | `complete` |
| `docs/product-task.md` | 任务编排体验（指令/批量/审批粒度） | #7 | `complete` |
| `docs/product-exception.md` | 异常处理体验（掉线/告警/接管） | #8 | `complete` |

### 规划中的文档（建议补齐）

| 建议文档 | 内容 | 对应模块 |
| --- | --- | --- |
| `docs/product-metrics.md` | 效果度量体系（过程/效果/健康指标） | #10 |
| `docs/product-matrix.md` | 多账号协同与差异化定位 | #11 |

### 代码仓库

| 仓库 | 角色 | 路径 |
| --- | --- | --- |
| **aidcp**（本仓） | 总览 / 文档 | 当前仓库 |
| **aidcp-edge** | 边缘端：定位 / CDP / 浏览执行 / 拟人化 / 反检测 | `C:\Users\tianx\codes\aidcp-edge` |
| **aidcp-cloud** | 云端：规划 / 编排 / 发布 / LLM / 缓存 / WS 服务 | `C:\Users\tianx\codes\aidcp-cloud` |

---

> **下一步行动建议（按优先级）**：
> 1. **P0** 落地风控 `RiskController`（频率计数器 + 档位 + 状态机）——决定账号存活。
> 2. **P0** Cookie/Session 持久化 + 住宅代理——决定登录态维持。
> 3. **P1** CDP 断连重连 + 验证码处理——决定运行稳定性。
> 4. **P2** Web 管理面板 + 效果度量——进入多账号阶段的前置。
