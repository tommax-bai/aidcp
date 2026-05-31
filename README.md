# AIDCP

**AIDCP**（AI-Driven Control Plane）是一套 **DOM-first** 的浏览器自动化控制平面。
它把"高层意图 → 在真实页面上稳定执行"拆成**边缘端**与**云端**两层，通过
**WebSocket** 协议协作，目标是：在页面频繁改版、存在重复元素与偶现弹窗的真实
环境里，既能"自愈"（找新锚点）又**绝不"自残"**（静默点错还报成功）。

## 仓库构成（多仓拆分）

| 仓库 | 角色 | 关键能力 |
| --- | --- | --- |
| **aidcp**（本仓） | 总览 / 文档 | 架构、协议、数据流文档 |
| [**aidcp-edge**](../../codes/aidcp-edge) | 边缘端 | 定位层引擎（DOM-first）+ CDP（原生 WebSocket）页面接入 |
| [**aidcp-cloud**](../../codes/aidcp-cloud) | 云端 | 任务规划 + Qwen LLM + PG 锚点缓存 + 边-云 WS 服务端 |

> 物理路径：`C:\Users\tianx\codes\aidcp-edge`、`C:\Users\tianx\codes\aidcp-cloud`。

## 设计主张

1. **DOM 优于像素 VL**：用 DOM 的包含关系（作用域 scope）天然区分重复元素
   （"当前这条笔记"内的点赞按钮），而非靠坐标/截图猜。
2. **语义锚点 + 缓存**：业务语义 `actionId`（永不变）映射到当前页面的语义指纹
   （role/text/scope/稳定属性，**不依赖混淆 class**），命中即复用，零模型调用。
3. **三道闸防自残**：
   - **后置校验**：操作后必须验证业务结果真的发生，否则判失败；
   - **重试上限 + 升级**：连续失败到顶 → 判系统性改版 → 停手升级，绝不静默成功；
   - **反污染回写**：LLM 新锚点先暂存，连续确认成功才晋升主缓存。
4. **边轻云重**：边缘只做定位/执行/本地命中；规划、模型推理、持久化锚点在云端。
5. **轻量优先**：CDP 走**原生 WebSocket**（不用 Playwright）；边-云通信用
   **WebSocket**；不引入重型框架。

## 端到端流程（简述）

```
用户高层目标
   │  plan.request（WS）
   ▼
[云端 Planner] ──► 有序步骤 PlanStep[]（actionId / op / goal）
   │  plan.response（WS）
   ▼
[边缘 LocatingEngine] 逐步执行：
   守卫层 → 缓存命中? ──是──► 匹配消歧 ──► 执行 ──► 后置校验
                    └─否─► 取云端锚点(anchor.get) / 文本LLM选元素(select.request)
                                              │
                                  执行 ──► 后置校验 ──► 反污染上报(anchor.report)
```

详见 [`docs/architecture.md`](docs/architecture.md)（组件图 + 数据流）与
[`docs/protocol.md`](docs/protocol.md)（边-云 WebSocket 协议）。

## 各仓快速开始

```bash
# 边缘端
cd C:\Users\tianx\codes\aidcp-edge && npm install && npm test

# 云端
cd C:\Users\tianx\codes\aidcp-cloud && npm install && npm test
```

## 文档索引

- [架构与数据流](docs/architecture.md)
- [边-云 WebSocket 协议](docs/protocol.md)
- [风控模型设计](docs/risk-control.md)
- [反检测与登录态维持方案](docs/anti-detection.md)
