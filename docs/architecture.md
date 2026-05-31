# AIDCP 架构

本文给出 AIDCP 的组件划分、组件图与端到端数据流。两层（边缘 / 云端）通过
WebSocket 协议解耦，协议本身见 [`protocol.md`](protocol.md)。

## 1. 组件总览

```
┌───────────────────────────────────────────────────────────────────────────┐
│                              aidcp-cloud (云端)                              │
│                                                                             │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────────────────────┐   │
│   │  Planner     │   │   LLM        │   │   PgAnchorCache              │   │
│   │ (SimplePlanner)│  │ (QwenClient) │   │   PostgreSQL 主缓存 + 暂存    │   │
│   │ 目标→步骤      │   │ Qwen HTTP    │   │   反污染晋升                  │   │
│   └──────┬───────┘   └──────┬───────┘   └──────────────┬───────────────┘   │
│          │                  │                          │                   │
│          └──────────┬───────┴──────────────────────────┘                   │
│                     ▼                                                       │
│         ┌────────────────────────────────────┐                            │
│         │  EdgeCloudServer (ws)               │                            │
│         │  + DefaultMessageHandler (路由)      │                            │
│         └──────────────────┬─────────────────┘                            │
└────────────────────────────┼──────────────────────────────────────────────┘
                             │  WebSocket（边-云协议，见 protocol.md）
                             │  hello/plan/select/anchor.get/anchor.report …
┌────────────────────────────┼──────────────────────────────────────────────┐
│                             ▼            aidcp-edge (边缘端)                 │
│         ┌────────────────────────────────────┐                            │
│         │  LocatingEngine (五层编排 + 三道闸)  │                            │
│         │                                    │                            │
│         │  guard → cache/match → select →    │                            │
│         │  execute → post-validate           │                            │
│         └───┬───────────┬──────────┬─────────┘                            │
│             │           │          │                                       │
│   ┌─────────▼──┐  ┌─────▼─────┐ ┌──▼──────────┐  ┌──────────────────────┐ │
│   │ extractor  │  │ matcher   │ │ AnchorCache │  │  guard / selector    │ │
│   │ (DOM抽取)   │  │ (一致性消歧)│ │ (内存命中)   │  │                      │ │
│   └─────────┬──┘  └───────────┘ └─────────────┘  └──────────────────────┘ │
│             │ 作用于通用 DOM                                                 │
│   ┌─────────▼──────────────────────────────────────────────────────────┐ │
│   │  CDP 接入层（原生 WebSocket，非 Playwright）                          │ │
│   │  CdpDomProvider  ── Runtime.evaluate(outerHTML) → jsdom Document     │ │
│   │  CdpActionExecutor ── 结构路径→XPath，浏览器侧 click/input/scroll     │ │
│   │  CdpClient / targets / session                                      │ │
│   └─────────────────────────────────┬──────────────────────────────────┘ │
└─────────────────────────────────────┼────────────────────────────────────┘
                                      │ CDP over WebSocket (:9222)
                                      ▼
                              ┌───────────────┐
                              │  Chrome 浏览器 │  (--remote-debugging-port)
                              └───────────────┘
```

## 2. 组件职责

### 2.1 边缘端 aidcp-edge

| 组件 | 文件 | 职责 |
| --- | --- | --- |
| LocatingEngine | `src/locating/engine.ts` | 五层编排（守卫→定位→执行→校验）+ 三道闸 |
| extractor | `src/locating/extractor.ts` | 把 DOM（或作用域）内可交互元素抽成结构化清单 |
| matcher | `src/locating/matcher.ts` | 多信号一致性打分，唯一且分差达标才判 hit |
| AnchorCache | `src/locating/cache.ts` | 内存锚点缓存（read-write/read-only/write-only）+ 暂存晋升 |
| selector | `src/locating/selector.ts` | 缓存缺口时让文本 LLM"做选择题"，校验编号防幻觉 |
| guard | `src/locating/guard.ts` | 操作前扫描并清除偶现干扰（弹窗/遮罩/登录过期…） |
| CdpDomProvider | `src/cdp/dom-provider.ts` | 实现 `DomProvider`：从真实页面取 DOM 快照 |
| CdpActionExecutor | `src/cdp/action-executor.ts` | 实现 `ActionExecutor`：原子操作落到真实页面 |
| CdpClient | `src/cdp/client.ts` | 原生 WebSocket 的 CDP RPC 客户端 |

> 关键接口 `DomProvider` / `ActionExecutor` 定义在 `engine.ts`，单测下由 jsdom
> 充当 DOM 源、由内存桩充当执行层；真实环境由 CDP 层实现同一接口——**接口不变，
> 实现可换**，这正是定位层能脱离浏览器完整单测的原因。

### 2.2 云端 aidcp-cloud

| 组件 | 文件 | 职责 |
| --- | --- | --- |
| SimplePlanner | `src/planner/simple-planner.ts` | 规则优先 + LLM 兜底，把目标拆成 PlanStep[] |
| QwenClient | `src/llm/qwen.ts` | Qwen（DashScope 兼容 OpenAI）HTTP 客户端 |
| PgAnchorCache | `src/cache/pg-anchor-cache.ts` | PostgreSQL 主缓存 + 暂存表 + 反污染晋升 |
| EdgeCloudServer | `src/comm/ws-server.ts` | WebSocket 服务端，解析信封并路由 |
| DefaultMessageHandler | `src/comm/handler.ts` | 把协议消息接到 planner/llm/cache |
| protocol | `src/comm/protocol.ts` | 边-云消息类型 + 信封 + 解析/校验 |

## 3. 数据流

### 3.1 规划阶段

1. 边缘把用户高层目标封成 `plan.request` 发往云端。
2. 云端 `SimplePlanner`：先试规则模板（点赞/关注/搜索…），未命中再用 Qwen 拆解
   并严格校验输出（op 合法、字段齐全，防幻觉）。
3. 云端回 `plan.response`，含有序 `PlanStep[]`（每步 `actionId` / `op` / `goal`）。

### 3.2 单步执行阶段（边缘 LocatingEngine，每步循环）

1. **守卫层**：扫描 DOM 干扰，能清则清，不能清→升级 `guard_blocked`。
2. **定位（缓存优先）**：
   - 本地 `AnchorCache` 命中 → `matcher` 在作用域内消歧；唯一且分差达标→拿到元素；
   - 未命中 → 可向云端 `anchor.get` 取主缓存锚点；仍无 → 走 LLM 选择。
3. **LLM 选择（缺口路径）**：把作用域内元素清单 `select.request` 发云端，Qwen 选编号，
   云端校验编号在范围内后回 `select.response`。
4. **执行层**：`CdpActionExecutor` 把 `op` 落到真实页面。
5. **后置校验（第一道闸）**：`PostValidator` 验证业务结果真发生。
6. **回写 / 上报**：
   - 缓存来源且校验通过 → `recordHit`；失败 → `recordFailure` 并强制下次走 LLM。
   - LLM 来源且校验通过 → 暂存候选锚点，连续确认才晋升（**第三道闸：反污染**）。
   - 通过 `anchor.report` 把上述结果同步给云端 PG 主缓存。
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

## 4. 关键设计取舍

- **DOM 快照而非 CDP DOM 树**：`CdpDomProvider` 用 `Runtime.evaluate` 取
  `outerHTML` 再交 jsdom 解析，直接复用既有 DOM-first 抽取逻辑（纯函数，一个操作
  周期内 DOM 稳定即可）。
- **结构路径执行而非坐标点击**：`CdpActionExecutor` 用 `tag[n]` 结构路径转 XPath，
  在浏览器侧 `document.evaluate` 重定位，触发原生事件序列，比坐标更抗改版。
- **协议与定位结构对齐**：`RemoteElement` / `RemoteAnchor` 是 `ElementDescriptor` /
  `Anchor` 的网络投影，云端只做"规划/选元素/缓存"，原子操作始终留在边缘。
