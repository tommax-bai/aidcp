## Why

AIDCP 已经具备浏览、搜索、互动、创作、发布和回复等单点能力，但这些能力目前分散在会话内角色、排期器、委托任务和发布管线中，缺少一套能够表达“为什么启动、按什么步骤推进、由谁占用账号、如何证明外部动作结果”的统一运行模型。随着 Agent 客户端和全托管运营进入设计阶段，需要先把 Automation 定义为稳定的自动化运营控制面，而不是继续把跨步骤逻辑堆进 Agent、Edge 或新的通用流程服务。

## What Changes

- 在一个 `aidcp-automation` 仓库内定义九个职责明确的内部模块：`managed-cycle-runtime`、`trigger-registry`、`task-runtime`、`account-work-arbiter`、`edge-gateway`、`policy-risk`、`execution-ledger`、`reconciler`、`decision-trace`；它们是逻辑模块，不要求拆成九个服务或进程。
- 引入 `ManagedPlan → ManagedCycle → Task → TaskRun → StepRun → ExecutionAttempt` 的分层运行模型，并以不可变 `ExecutionPlan` 冻结某个 TaskRevision 的实际执行图。
- 区分原子 `CapabilityDefinition`、可复用 `TaskDefinition.executionGraph`、具体 `Task CapabilityScope` 与编译后的 `ExecutionPlan`；单动作和多步骤任务都统一使用 Task/TaskRun，不新增 `CapabilityRun` 或一级 Workflow 对象。
- Agent 先把自然语言解释为 `CreateTask`、`ReviseTask`、`CancelTask`、`QueryTask` 或 ManagedPlan 命令建议；API 授权并记录 TaskRevision，Agent 不能生成任意脚本、直接调用 Capability/Edge 或订阅所有事件形成自治循环。
- 为同一账号/阵地建立工作仲裁，支持优先级、截止时间、安全暂停点和恢复，同时明确它与机器级浏览器槽位调度是两层不同资源管理。
- 把可见授权、实时安全闸、平台风险、配额、冷却和三类预算统一为执行准入；全托管权限按动作域分别配置，不能由一个总开关隐式扩大。
- 以执行账本记录幂等键、不可变意图快照、派发、回执和证据；外部写动作采用 `prepared → dispatched → platform_confirmed | submitted_unknown` 语义，取消是前向请求，未知结果只能通过对账确认，不能盲目重试或伪造成功。
- 为搜索浏览、创作、评论、发布、回复和全托管日周期定义同一套跨服务走向：API 持有客户授权，Content 持有内容事实与创作任务，Agent 提出计划，Automation 编排和执行，Edge Host 只执行已准入的本地原子能力。
- 定义决策追踪、因果链、版本冻结/替换、DEV/OL 隔离、保留与删除、可观测投影及渐进迁移要求；保留现有单动作任务和会话浏览循环作为迁移适配入口，不新增独立通用流程服务。

## Capabilities

### New Capabilities

- `managed-automation-plans`: 全托管计划、周期、触发绑定、版本冻结、替换和有界派生的生命周期合同。
- `managed-automation-task-runtime`: Capability、TaskDefinition、CapabilityScope、ExecutionPlan、TaskRun/StepRun、命令修订、等待点、跨服务子任务及恢复语义。
- `automation-account-work-arbitration`: 账号级工作优先级、截止窗口、安全暂停/恢复和机器浏览器槽位边界。
- `automation-execution-ledger`: 外部动作尝试、幂等派发、平台确认、未知结果、取消和对账合同。
- `automation-policy-decision-trace`: 分动作授权、实时安全准入、预算以及可解释决策追踪合同。

### Modified Capabilities

本变更在**运行模型层**事实上取代或收编了一批已上线能力。逐条对照与 delta 落地时机见 `design.md` 第 24 节「与已上线规格的关系」；此处只列取代/收编面，**未列出的能力视为完全保留、不受本变更影响**。

**A. 运行模型被整体取代**（原能力的对象模型、状态枚举、排队与终态语义整体让位于 `ManagedPlan → ManagedCycle → Task → TaskRun → StepRun → ExecutionAttempt`）

- `user-delegated-tasks`：任务对象、11 态互斥枚举、排队/优先级、有界性与终态语义整体被分层运行模型取代。
- `session-auto-resume`：「单场会话 + 进程内续场计时器」被有界 `ManagedCycle` 取代。
- `multi-tenant-orchestration`：按连接的决策上下文被账号 lane + 冻结执行意图取代。
- `publish-generation-concurrency`：键控单飞、容量帽与多轮簿记被 Trigger Binding 并发策略 + 账号 lane + 持久 claim 取代。
- `publish-account-attribution`：账号归属被 API 权威绑定 + 不可变意图 + 目标隔离取代。
- `publish-dispatch-resilience`：下发韧性被 `missPolicy` + `submitted_unknown` + 有界对账取代。
- `same-account-parallel-safety`：同账号并发安全被账号 lane + 目标域幂等键取代（前提：lane 键必须是平台账号本身，见 §24 冲突表）。

**B. 仅取代其编排、授权与终态语义；平台行为细节保留，转为各平台 Capability 的证据与步骤合同**

- `publish-pipeline`、`publish-submit-integrity`、`publish-post-link-capture`、`xhs-native-scheduled-publish`：授权、版本冻结、派发、平台确认、幂等与终态被取代；标题收口、配图上传、可见范围、编辑器指令序列、原生定时窗口等平台细节保留为能力合同。
- `comment-interaction`、`comment-search-command`、`comment-like-interaction`、`facebook-scheduled-comment`、`facebook-comment-verification`、`facebook-comment-idempotency`、`feed-hot-lead-group-comment`：评论的授权、prepare/commit 占用、幂等、确认证据与终态被取代；目标选取、平台证据与执行细节保留为能力合同。
- `content-schedule`：触发、幂等键、授权档位、跨来源并发与终态被取代；活跃时窗、分钟错峰、平台级必审下限等保留并需回收为新要求。
- `interaction-risk-gating`、`interaction-cooldown`：闸的位置与顺序被两阶段准入取代；风控状态机、单写者、配额窗口口径、兜底与主闸的算术关系保留并需回收。
- `edge-task-execution-coordination`：租约归属与评论两段占用被账号 lane + prepare/commit 取代；安全点定义、抢占与救援优先级存在正面冲突，须先裁决。
- `browse-loop-resilience`、`platform-browse-surface`、`platform-search-activity`、`detail-deep-read`、`deep-read-fidelity`、`feed-depth-refresh`、`note-extraction-fidelity`、`interaction-appraisal`、`read-to-write-note-lane`：闭环驱动、续跑、深读与计数语义被执行图 + 有界步 + 唯一内容计数取代；平台观测与证据细节保留为能力合同。
- `weekly-active-window`、`command-pacing`：运营时段与节奏的归属被收口进 Automation（新方案当前尚无承载条款，须先补齐再取代）。
- `client-core-browser-executor-separation`：操作分类与「受理/平台结果」两阶段表达被 Capability 注册表 + 三种真相投影取代；页面身份准入需回收。

**C. 仅收编其中若干条要求，其余保留**

- `deployment-environments`（2/12：写者实例数与执行目标隔离）
- `console-panel-api`（12/36：投影分层、排队可见性、未确认不得投影为已确认）
- `feishu-notification-routing`（7/11：通知与授权/派发解耦；投递目标解析须回收）
- `llm-output-honesty`（2/5）、`manual-command-override`（3/3，正面冲突）、`browser-cold-standby`（2/8）
- `captcha-incident-handling`、`cdp-control-health-recovery`、`account-identity-resolution`、`alert-manual-resolution`、`accounts-master-data`、`edge-node-supervised-recycle`、`edge-cloud-handshake-admission`、`edge-command-targeting`、`edge-multi-environment-supervisor`、`pluggable-browser-provider`、`client-customer-auth`、`notification-monitoring`、`curated-note-actions`、`interaction-attribution`、`follow-decision`、`publish-multi-image`、`llm-token-usage-stats`、`wechat-channels-interaction`、`wechat-lifecycle-status-honesty`、`wechat-test-reset-completion-honesty`：各收编 1–5 条与准入、证据、恢复或投影相关的要求，其余保留。

**权威规则**

1. **重叠处以本方案为准**（用户 2026-07-25 裁定）。凡上表标注取代或收编的要求，其目标语义以本变更的五份新 capability spec 为准。
2. **迁移期内，已上线规格仍是实现与验收基线**。在某条纵切的 cutover change 落地之前，对应的已上线要求继续对生产行为具有约束力；本变更本身不修改任何 `openspec/specs/` 下的文件，也不改变现有生产行为。
3. **取代不得先于 delta 生效**。每条纵切在启用其 Trigger Binding 之前，必须先创建并落地对应已上线能力的 delta change（MODIFIED/REMOVED），否则视为发布阻塞项。
4. **取代不得静默丢保证**。凡被取代/收编的已上线要求，其中在新方案中无对应表达的实质保证，必须先作为新要求补进五份 delta spec（见本变更 tasks §1.11），或留下具名的「有意放弃」决定与责任人。
5. **冲突项必须先裁决**。已识别的正面冲突（见 `design.md` §24 冲突表）在裁决完成并写入 delta 之前，其所属纵切不得 cutover。

## Impact

- **Repositories**: 目标实现主要属于未来独立的 `aidcp-automation`；`aidcp-cloud` 的 API、Content 和现有 automation 进程需要渐进迁移或适配；`aidcp-edge`/Edge Host 只增加版本化能力声明和原子命令适配；未来 Agent Service 与客户端只通过 API/Agent 合同发起计划或查询投影。
- **Data and events**: 需要新增计划、周期、Task/TaskRevision、ExecutionPlan、TaskRun、StepRun、尝试、决策追踪及触发绑定的持久模型；跨服务命令/事件走 Outbox/Inbox，并保留服务端注入的 `execution_target=dev|ol`。
- **Protocols**: 后续实现若新增 Edge 命令或回执，必须同步 Cloud/Automation 映射、Edge 活跃路由、类型和 `docs/protocol.md`；未知能力必须返回 `unsupported`，不得静默回退。
- **Migration**: 现有 `delegated_tasks`、发布派发器、内容排期器、`RoleDispatcher` 和浏览器槽位调度继续作为迁移来源，但不直接扩展成通用任务图表或第二套运行时。
- **Operations**: 需要按模块配置 worker 归属、指标、告警、数据保留和分阶段切流；本设计文档本身不创建运行服务、不部署，也不改变现有生产行为。
