# AIDCP

AIDCP（AI-Driven Control Plane）是一套面向真实社交平台页面的浏览器自动化控制平面。
它把页面执行留在边缘端，把编排、模型决策、风控、持久化和运营入口放在云端，并通过
WebSocket 协议协作。

系统的基本原则是 DOM-first、边轻云重、事件驱动和诚实回执：定位不到、平台未确认、
账号受限或执行结果不明确时，必须返回真实状态，不能用“已受理”冒充“已完成”。

## 仓库边界

| 仓库 | 默认分支 | 角色 |
| --- | --- | --- |
| `aidcp`（本仓） | `main` | 架构、协议、OpenSpec、产品与运维文档、编排脚本 |
| `aidcp-edge` | `master` | Electron 客户端、AdsPower/CDP 接入、页面读取与动作执行、平台适配 |
| `aidcp-cloud` | `master` | 事件编排、模型调用、风控、任务与发布、持久化、边云服务和管理 API |
| `aidcp-console` | `master` | 客户端与管理后台 Web 界面 |

四个仓库通常位于同一目录层级。开始修改前先运行：

```bash
./scripts/task-preflight
```

本仓不是应用 checkout，不在根目录运行 `npm test`、`npm run build` 或 `npm run lint`。
业务代码的测试和类型检查应在对应 sibling repo 中执行。

## 系统主路径

```text
运营入口 / 客户端 / 飞书
             │
             ▼
aidcp-cloud：账号与环境真态、任务编排、角色事件、风控、审批与持久化
             │  WebSocket protocol v2
             ▼
aidcp-edge：浏览器会话、页面结构读取、平台动作、后置验证与真实结果回传
             │  CDP / AdsPower
             ▼
真实平台页面
```

浏览主循环由 Cloud 的 `RoleDispatcher` 和 `EventBus` 按 Edge 上报的结构化页面事实逐动作
决策；定向任务和发布任务通过明确命令及 edge task lease 串行使用页面写能力。角色和协议
消息会持续演进，准确枚举以 Cloud/Edge 的类型定义及协议契约测试为准，文档不复制易漂移
的数量。

## 文档入口

先读 [文档导航与维护规则](docs/README.md)。常用入口：

- [系统架构](docs/architecture.md)
- [边云 WebSocket 协议](docs/protocol.md)
- [部署环境与安全边界](docs/deployment-environments.md)
- [风控模型](docs/risk-control.md)
- [验证策略](docs/acceptance-tests.md)
- [真机验收待办](docs/real-machine-acceptance-backlog.md)
- [并行开发与 worktree](docs/parallel-dev-worktrees.md)

当前能力和进行中的工作不要从日期快照推断：使用 `openspec list` 查看活跃 change，使用
`openspec list --specs` 查看已合并契约，再以对应 sibling repo 的代码、测试和目标环境运行态
作最终核验。
