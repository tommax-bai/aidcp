# AIDCP

**AIDCP**（AI-Driven Control Plane）是一套 **DOM-first** 的浏览器自动化控制平面。
它把"高层意图 → 在真实页面上稳定执行"拆成**边缘端**与**云端**两层，通过
**WebSocket** 协议协作，目标是：在页面频繁改版、存在重复元素与偶现弹窗的真实
环境里，既能"自愈"（找新锚点）又**绝不"自残"**（静默点错还报成功）。

## 仓库构成（多仓拆分）

| 仓库 | 角色 | 关键能力 |
| --- | --- | --- |
| **aidcp**（本仓） | 总览 / 文档 | 架构、协议、数据流文档 |
| [**aidcp-edge**](../aidcp-edge) | 边缘端 | 定位层引擎（DOM-first）+ CDP（原生 WebSocket）页面接入 + 浏览执行 + 拟人化 + 发布 + Electron 打包 |
| [**aidcp-cloud**](../aidcp-cloud) | 云端 | 事件驱动多 Agent 编排（RoleDispatcher + 约 32 角色）+ 风控状态机 + 多模型 LLM（通义千问 / 火山方舟）+ PG 锚点缓存 + 边-云 WS 服务端 + 面板 API（管理后台后端）+ 飞书 Bot |
| [**aidcp-console**](../aidcp-console) | 管理后台前端 | 统一 Web 控制台（React + Vite + TS + AntD）；只读云端面板 API + 经 `/api` 下发指令，绝不直连边缘 |

> 相对路径（四仓同级）：`../aidcp-edge`、`../aidcp-cloud`、`../aidcp-console`（可能尚未在当前机器 clone）。
> 部署铁律：cloud 只跑在 ECS（见 `docs/handoff-2026-06-05.md`），本地只起 edge 连 ECS。

## 设计主张

1. **DOM 优于像素 VL**：用 DOM 的包含关系（作用域 scope）天然区分重复元素
   （"当前这条笔记"内的点赞按钮），而非靠坐标/截图猜。
2. **语义锚点 + 缓存**：业务语义 `actionId`（永不变）映射到当前页面的语义指纹
   （role/text/scope/稳定属性，**不依赖混淆 class**），命中即复用，零模型调用。
3. **三道闸防自残**：
   - **后置校验**：操作后必须验证业务结果真的发生，否则判失败；
   - **重试上限 + 升级**：连续失败到顶 → 判系统性改版 → 停手升级，绝不静默成功；
   - **反污染回写**：LLM 新锚点先暂存，连续确认成功才晋升主缓存。
4. **边轻云重**：边缘只做定位/执行/拟人化/本地命中；规划、事件驱动编排、模型推理、风控、持久化锚点在云端。
5. **轻量优先**：CDP 走**原生 WebSocket**（不用 Playwright）；边-云通信用
   **WebSocket**（协议 v2）；不引入重型框架。
6. **事件驱动而非单线规划**：浏览会话由云端 `RoleDispatcher` 调度约 32 个角色（核心浏览闭环 / 会话守护 / 评论支线 / 通知巡视 / 概念抽取，准确清单以 `event-bus/types.ts` 的 `RoleName` 与 `role-dispatcher.ts` 注册为准）经 `EventBus`
   实时决策——边缘**结构化上报**（page.cards / note.detail），云端**逐动作下发**（interaction.like / page.scroll），
   贴近真人"看一条想一下"的节奏。

## 端到端流程（简述）

**浏览会话闭环（v2 主路径，事件驱动）**：

```
边缘 BrowseSession                          云端 RoleDispatcher + EventBus + 约 32 角色
  page.cards 上报 ─────────────────────────► ContentEvaluator 评估价值
  note.open / page.scroll  ◄──────────────── 有价值开卡 / 无价值翻页（command-bridge 翻译）
  note.detail 上报 ────────────────────────► ContentCurator 质量关卡 → InteractionAppraiser 决策
  interaction.like / navigation.back ◄────── 角色事件下发
  action.completed 上报 ───────────────────► BackToFeed 续刷 / SessionMonitor 判结束
  session.end ◄───────────────────────────── （穿插 publish.* 发布审批；risk.canDo 风控通道已就绪、浏览闭环待接线）
```

**定向定位（plan/anchor/select，每步循环，v1 兼容路径）**：

```
[云端 SimplePlanner] ──plan.response──► 有序 PlanStep[]
[边缘 LocatingEngine] 逐步执行：
   守卫层 → 缓存命中? ──是──► 匹配消歧 ──► 执行 ──► 后置校验
                    └─否─► 取云端锚点(anchor.get) / 文本LLM选元素(select.request)
                                              │
                                  执行 ──► 后置校验 ──► 反污染上报(anchor.report)
```

> 注：当前边缘 `LocatingEngine` 使用进程内 `AnchorCache`，缓存未命中直接走 `select.request`
> （文本 LLM 选元素）；`anchor.get`/`anchor.report` 为协议保留的云端主缓存同步通道，尚未在边缘接线。

详见 [`docs/architecture.md`](docs/architecture.md)（组件图 + 数据流）与
[`docs/protocol.md`](docs/protocol.md)（边-云 WebSocket 协议 v2）。

## 各仓快速开始

```bash
# 边缘端（本地只跑 edge）
cd ../aidcp-edge && npm install && npm test

# 云端（本地仅做代码级验证；正式运行在 ECS，本地勿起 cloud）
cd ../aidcp-cloud && npm install && npm test
```

## 文档索引

- [架构与数据流](docs/architecture.md)
- [边-云 WebSocket 协议](docs/protocol.md)
- [验收测试用例（全功能矩阵）](docs/acceptance-tests.md)
- [风控模型设计](docs/risk-control.md)
- [反检测与登录态维持方案](docs/anti-detection.md)
