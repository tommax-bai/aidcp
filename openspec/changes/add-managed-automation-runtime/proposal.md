## Why

AIDCP 已经具备浏览、搜索、互动、创作、发布和回复等单点能力，但这些能力目前分散在会话内角色、排期器、委托任务和发布管线中，缺少一套能够表达“为什么启动、按什么步骤推进、由谁占用账号、如何证明外部动作结果”的统一运行模型。随着 Agent 客户端和全托管运营进入设计阶段，需要先把 Automation 定义为稳定的自动化运营控制面，而不是继续把跨步骤逻辑堆进 Agent、Edge 或新的 Workflow 服务。

## What Changes

- 在一个 `aidcp-automation` 仓库内定义九个职责明确的内部模块：`managed-cycle-runtime`、`trigger-registry`、`workflow-runtime`、`account-work-arbiter`、`edge-gateway`、`policy-risk`、`execution-ledger`、`reconciler`、`decision-trace`；它们是逻辑模块，不要求拆成九个服务或进程。
- 引入 `ManagedPlan → ManagedCycle → AutomationRun → WorkflowStep → ExecutionAttempt` 的分层运行模型，区分长期运营计划、有界周期、单次业务运行、步骤进度和一次平台尝试。
- 引入类型化、版本化的 Automation Definition 和显式 Trigger Binding；Agent 只能提出结构化计划或变更建议，不能生成任意脚本、直接调用 Edge 或订阅所有事件形成自治循环。
- 为同一账号/阵地建立工作仲裁，支持优先级、截止时间、安全暂停点和恢复，同时明确它与机器级浏览器槽位调度是两层不同资源管理。
- 把可见授权、实时安全闸、平台风险、配额、冷却和三类预算统一为执行准入；全托管权限按动作域分别配置，不能由一个总开关隐式扩大。
- 以执行账本记录幂等键、不可变意图快照、派发、回执和证据；外部写动作采用 `prepared → dispatched → platform_confirmed | submitted_unknown` 语义，取消是前向请求，未知结果只能通过对账确认，不能盲目重试或伪造成功。
- 为搜索浏览、创作、评论、发布、回复和全托管日周期定义同一套跨服务走向：API 持有客户授权，Content 持有内容事实与创作任务，Agent 提出计划，Automation 编排和执行，Edge Host 只执行已准入的本地原子能力。
- 定义决策追踪、因果链、版本冻结/替换、DEV/OL 隔离、保留与删除、可观测投影及渐进迁移要求；保留现有单动作任务和会话浏览循环作为迁移适配入口，不新增独立 Workflow 服务。

## Capabilities

### New Capabilities

- `managed-automation-plans`: 全托管计划、周期、触发绑定、版本冻结、替换和有界派生的生命周期合同。
- `managed-automation-workflow-runtime`: 类型化工作流定义、运行/步骤状态、等待点、跨服务子任务及恢复语义。
- `automation-account-work-arbitration`: 账号级工作优先级、截止窗口、安全暂停/恢复和机器浏览器槽位边界。
- `automation-execution-ledger`: 外部动作尝试、幂等派发、平台确认、未知结果、取消和对账合同。
- `automation-policy-decision-trace`: 分动作授权、实时安全准入、预算以及可解释决策追踪合同。

### Modified Capabilities

无。本变更先建立目标运行时及其集成合同；现有排期、发布、评论、委托任务和浏览循环的用户行为在迁移阶段通过适配器保持，若后续迁移确需改变其行为契约，应在实施前增加对应 delta spec。

## Impact

- **Repositories**: 目标实现主要属于未来独立的 `aidcp-automation`；`aidcp-cloud` 的 API、Content 和现有 automation 进程需要渐进迁移或适配；`aidcp-edge`/Edge Host 只增加版本化能力声明和原子命令适配；未来 Agent Service 与客户端只通过 API/Agent 合同发起计划或查询投影。
- **Data and events**: 需要新增计划、周期、运行、步骤、尝试、决策追踪及触发绑定的持久模型；跨服务命令/事件走 Outbox/Inbox，并保留服务端注入的 `execution_target=dev|ol`。
- **Protocols**: 后续实现若新增 Edge 命令或回执，必须同步 Cloud/Automation 映射、Edge 活跃路由、类型和 `docs/protocol.md`；未知能力必须返回 `unsupported`，不得静默回退。
- **Migration**: 现有 `delegated_tasks`、发布派发器、内容排期器、`RoleDispatcher` 和浏览器槽位调度继续作为迁移来源，但不直接扩展成通用多步骤工作流。
- **Operations**: 需要按模块配置 worker 归属、指标、告警、数据保留和分阶段切流；本设计文档本身不创建运行服务、不部署，也不改变现有生产行为。
