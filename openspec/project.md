# Project: AIDCP

AIDCP（AI-Driven Control Plane）是一套 DOM-first 的浏览器自动化控制平面。Edge 负责真实
浏览器读取与动作执行，Cloud 负责编排、模型、风险和持久化，二者通过 WebSocket protocol
v2 协作。系统必须诚实区分请求受理、人工授权、命令下发、Edge 执行和平台确认。

## 仓库拓扑

| 仓库 | 默认分支 | 职责 |
| --- | --- | --- |
| `aidcp`（本仓） | `main` | OpenSpec、架构/协议/产品文档和编排脚本；不承载业务代码 |
| `../aidcp-edge` | `master` | Electron、浏览器环境、CDP、平台读取与动作执行 |
| `../aidcp-cloud` | `master` | 事件编排、模型、风控、任务、持久化、边云和管理 API |
| `../aidcp-console` | `master` | 客户端与管理后台 Web 界面 |

开始任务前运行 `./scripts/task-preflight`。Canonical checkout 保持默认分支，feature work 使用
同名 `codex/<change>` 分支和 `../<repo>.wt/<change>` worktree；不得覆盖并行会话的 dirty/WIP。

## 架构与行为约束

- DOM-first 定位保留前置守卫、后置验证、有界重试/升级和反污染晋升。
- Edge 保持轻量；账号选择、全局排程、主节奏、最终风险状态和业务持久化属于 Cloud。
- Cloud `RiskController` 是最终账号风险状态的单写者。
- 协议 v2 变化同步 Cloud/Edge 类型、Cloud command mapping、Edge active-command routing、契约测试和 `docs/protocol.md`。
- 当前浏览主路径是事件驱动 v2；不要恢复已删除的旧 planner/card-filter 浏览路径。
- 缺少目标、页面异常、平台未确认和结果歧义必须如实返回，禁止伪造成功。
- 不记录密码、token、私钥或其它敏感值。

## OpenSpec 工作流

行为契约、跨仓/模块、协议、风控、发布、部署流程和用户可见行为变化先创建 change，不直接
编辑 `openspec/specs/`：

1. proposal / design / spec delta / tasks；
2. 在 owning sibling repo 实现并验证；
3. 在 `tasks.md` 回写 repo、commit、验证、部署和偏差；
4. `openspec validate <change-name> --strict`；
5. 满足全部验证边界后归档。

拼写、排版、注释和不改变行为语义的文档/开发配置维护可以不创建 change。

## 验证与部署

- 应用测试在 owning sibling repo 运行；本 control repo 根目录不运行应用 test/build/lint。
- 协议、风控和发布改动依次执行聚焦测试、acceptance、全量测试和 typecheck。
- 本地 Cloud 验证仅是代码级；运行态验证在明确的 ECS 目标上完成。
- dev 是开发完成后的默认目标；ol 仅在用户明确要求且使用合格 release 分支时部署。
- SSH/rsync 前先读 `docs/deployment-environments.md` 并运行 `scripts/deploy-target <dev|ol> --check`。
- 自动化、部署和真实平台验证分别记录；未做真机验证时登记到 `docs/real-machine-acceptance-backlog.md`。

## 文档入口

先读 `README.md` 和 `docs/README.md`。架构、协议、部署、风控和验证分别见：

- `docs/architecture.md`
- `docs/protocol.md`
- `docs/deployment-environments.md`
- `docs/risk-control.md`
- `docs/acceptance-tests.md`
