# Project: AIDCP

AIDCP（AI-Driven Control Plane）是一套 **DOM-first** 的浏览器自动化控制平面，把"高层意图 →
在真实页面稳定执行"拆成**边缘端**与**云端**两层，经 **WebSocket 协议 v2** 协作。设计主张是
"自愈不自残"：能找新锚点，但绝不静默点错还报成功。

## 仓库拓扑（本仓为中控）

- `aidcp`（本仓，`.`，分支 `main`）：中控 / 总览。契约（架构 / 协议 /
  产品设计）+ openspec changes + 测试与部署编排。**不承载业务代码**。
- `aidcp-edge`（`../aidcp-edge`，分支 `master`）：边缘端。CDP 接入 / 定位引擎
  三道闸 / 浏览执行 / 拟人化 / 反检测 / 发布 flow / Electron 打包。
- `aidcp-cloud`（`../aidcp-cloud`，分支 `master`）：云端。协议 / 事件驱动多 Agent
  编排（RoleDispatcher + 15 角色 + EventBus）/ 风控状态机 / Qwen LLM / PG 锚点缓存 / 飞书 Bot。

边-云通过 `docs/protocol.md` 定义的 WebSocket 协议 v2 通信。

## 关键约束（写 change 时必须遵守）

- **部署铁律**：cloud 只部署在命名 ECS 目标，本地只跑 edge 连 ECS。`dev=121.89.85.150`
  用于主干高频验证，`ol=123.56.253.183` 用于稳定上线；每次 SSH/rsync 前必须明确 target
  并通过 `scripts/deploy-target <dev|ol> --check`。`dev` 同机另有 isales 独立运行，绝不能碰。
- **DOM 优于像素**：用 DOM 作用域区分重复元素，不靠坐标/截图。
- **三道闸防自残**：后置校验 / 重试上限+升级 / 反污染回写。
- **边轻云重**：边缘只做定位/执行/拟人化/本地命中；规划、编排、推理、风控、持久化在云端。
- 不记录任何敏感值（密码 / token / 私钥）。

## 工作流

spec-driven：所有跨 spec 改动走 openspec change（proposal → design → tasks → apply → validate
`--strict` → archive）。代码落 sub-repo，进度回写本中控仓。详见根目录 `CLAUDE.md`。

## 文档索引

`README.md`、`docs/architecture.md`、`docs/protocol.md`、`docs/risk-control.md`、
`docs/anti-detection.md`、`docs/acceptance-tests.md`、`docs/handoff-2026-06-05.md`。
