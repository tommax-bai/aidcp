## Context

现有入口按动作各自直连执行器：Feishu `/publish` 同步等生成候审结果，`/comment` 受理后异步跑 `CommentScheduler`，精选行级 API 直接触发参照创作/定向评论，`ContentScheduler` 则按小时格启动同一批 scheduler。这些路径已经具备账号昵称、平台事实源、人审、边缘租约、目标去重和诚实结果卡，但缺少一个能跨入口表达“业务目标、数量、期限和剩余部分”的持久化上层。

相关并行变更给出三条硬边界：

- `lease-strict-preemption` 正在独立 worktree 修改两端协议、edge 协调器/`main.ts` 和 cloud `command-sequencer`。本 change 不触碰这些热点，只使用已公开的 scheduler/lease 优先级接口；用户委托的异步执行始终映射为 `automatic`。
- `runtime-progress-card` 已落默认分支，它证明客户端可以投影真实数据，但其职责仍是浏览探索进度。委托任务使用独立卡片，不复用或伪造浏览进度。
- `fb-publish-fill-deadline` 的源码防线已合入，但真机长正文/清场/端到端验收仍未完成。Facebook 普通发布只能处于显式 Beta + runtime gate，不能因为代码路径存在就宣称稳定可用。

第一阶段不新增模型供应商或消息协议。cloud 是任务事实源；Edge/Feishu/console 都只创建、确认、控制和读取同一个 task id。

## Goals / Non-Goals

**Goals:**

- 用一个持久化模型表达账号、平台、目标数量、尝试预算、时间约束、来源/目标约束、人审、优先级、状态、进度、暂停/取消和诚实终态。
- 所有公共写入口都先落 `awaiting_confirmation`，确认后才可 `queued`；旧 slash command 保持兼容。
- 复用现有 PublishScheduler / CommentScheduler / curated / publish-draft 能力，通过适配器获得可验证终态，不重写浏览或发布执行器。
- 批量任务遵守自动化风险额度，只有平台验证成功才为评论累计成功；候选不足或过期时诚实部分完成。
- 让内容排期与委托任务共享 ownership，避免同账号同动作双重执行。
- 小红书完整首发，Facebook 仅开放可由注册表和运行时闸证明的受限动作。

**Non-Goals:**

- 不实现第二批长期偏好/规则系统、规则版本、学习或通知分类。
- 不新增平台，不实现收到评论的回复、私信、通知/Inbox、作者主页访问/关注或自动治理动作。
- 不修改 RiskController 写者边界，不实现新的抢占协议，不中断在途输入/点击。
- 不构建/发布 Edge 安装包，不部署 OL。

## Decisions

### 1. `DelegatedTask` 是独立领域事实，不把 scheduler 回执当任务本身

cloud 新增 `delegated_tasks` 与 `delegated_task_events`：前者保存当前投影，后者保存追加式状态/进度事件。主记录至少包含：

| 类别 | 字段 |
| --- | --- |
| 身份 | `id`, `accountId`, `accountNameSnapshot`, `platform`, `source`, `sourceRef` |
| 目标 | `action`, `targetSuccessCount`, `maxAttempts`, `sourceConstraints`, `targetConstraints` |
| 时间 | `notBefore`, `deadlineAt`, `executionWindow`, `nextEligibleAt` |
| 控制 | `approvalMode`, `priority`, `pauseRequested`, `cancelRequested`, `dedupeKey` |
| 投影 | `status`, `successCount`, `attemptCount`, `skippedCount`, `failureCount`, `currentStep`, `terminalOutcome`, `version` |

状态迁移由 store 的 compare-and-set 方法集中约束：

`draft → awaiting_confirmation → queued → planning → waiting_approval | executing → completed | partially_completed | deferred | cancelled | failed`。

`waiting_approval` 可回 `queued`/`executing`；暂停请求在安全动作结束后落 `deferred`，恢复后回 `queued`。`cancelled` 仅表示未执行剩余部分已取消；已经平台验证成功的计数保留。

另建 `delegated_task_attempts`，在任何下游 dispatch 前先持久化 `attemptId`、规范化目标键、阶段与幂等证据；dispatch 后追加验证结果。worker 重启发现 `dispatched` 但无终态的 attempt 时，必须先用评论去重账本、publish_log 或 candidate version 进行 reconciliation，不能直接重试。

选择独立模型而不是扩展 `publish_log` 或 scheduler 内存集合，是因为任务可跨多次评论/多份候选稿，并且必须跨进程重启保留截止时间、剩余量、取消意图与“已派发未记账”的 attempt。

### 2. 所有入口都只生成同一种规范化意图

新增 `DelegatedTaskService.createDraft()`，输入为 `DelegatedTaskIntent`。入口适配器负责的事情被严格限制为：

1. 解析自然语言或表单；
2. 用账号昵称或 Edge 当前环境解析唯一 account；
3. 从 `accounts.platform` 回读平台，拒绝调用方自报平台不一致；
4. 通过平台动作注册表校验能力与限制；
5. 生成结构化确认摘要并落 `awaiting_confirmation`。

确认接口带 task id + 版本号，store 用 CAS 将其置为 `queued`。重复确认返回当前真态，不重复入队。Feishu 卡片、Edge 卡片和 console 对话框共享相同摘要字段。

旧 `/publish`、`/comment` 的**语法、昵称解析与单次人工语义**保持兼容，但写命令同样先创建单次 `awaiting_confirmation` DelegatedTask；用户确认后 adapter 才调用原 scheduler，并可保留单次 manual override。`/status` 等只读命令仍原路执行。这样兼容的是用户入口，不是绕过“公共写操作先确认”的旧副作用。

### 3. 确定性解析优先，无法唯一结构化时 fail-closed

Phase 1 的 Feishu 解析器使用受测的中文模式和显式快捷词，不引入 LLM 自由抽取：评论数量、动作、昵称、时间、精选 id/候选稿 id 均必须可确定解析。缺账号昵称、昵称重名、时间无法解释、平台动作受限或关键目标缺失时返回澄清卡，不创建可执行任务。

这比用 LLM 猜参数更保守，但能保证确认卡中的字段来自用户原话，且不会把“Facebook 某帖子”误解释为允许任意 URL 评论。

### 4. 单 worker + PG claim 提供持久化队列，任务内逐动作串行

`DelegatedTaskWorker` 周期性 claim 到期且 eligible 的任务。claim 使用 `FOR UPDATE SKIP LOCKED`/带租约字段的原子更新，服务重启后过期 claim 可恢复。排序为：显式 `priority=high`、最早 deadline、创建时间；但边缘租约仍一律申请 `automatic`，避免“用户点了优先”被误解为可以抢占人工/风控动作。

单任务一次只运行一个原子业务动作。dispatch 前先落 attempt，完成/对账后更新 attempt/event，再检查暂停、取消、deadline、maxAttempts 和目标成功数。这样“完成当前安全动作后暂停”天然发生在 scheduler/adapter 返回之后，不需要中断输入或提交。

### 5. ownership 同时覆盖委托任务、现有 scheduler 和内容排期

新增账号级 `DelegatedTaskOwnership` 视图，key 至少为 `(accountId, actionFamily)`，其中 `comment`/`contact_comment` 共享评论槽，`publish`/`candidate_generation` 共享发布生成槽。worker 在调用现有 scheduler 前同时检查：

- PG 中是否已有另一活跃委托 ownership；
- `CommentScheduler.isRunning(accountId)`；
- `PublishScheduler.isBusy(accountId)`；
- 账号平台是否仍与任务快照一致。

`ContentScheduler` 增加注入式 `hasDelegatedOwnership(accountId, action)`；命中时本 tick 诚实跳过并不消耗/重复触发。委托 worker 遇到已有排期在途则置 `deferred`/`nextEligibleAt`，不把 busy 计为尝试。`waiting_approval` 不占 edge 执行租约，但继续占发布草稿/同目标去重 ownership，防止另一来源生成同用途草稿；deadline 到达只终结任务投影，不自动批准、删除或提交仍待审候选。

幂等 key 由账号、动作、规范化目标、来源和用户给定窗口组成。只对非终态任务唯一；相同确认重复提交返回已有 task。

### 6. 执行适配器复用现有链路，但把“受理”升级为可等待的真实结果

- **评论**：给 `CommentScheduler.triggerManual/triggerTargeted` 增加可选终态回调/Promise 适配口。批量/异步委托使用 `priority=automatic`、`manualOverride=false`、默认 `approvalMode=review`；由旧 slash command 生成的单次、已确认任务可显式 `manualOverride=true`。XHS 通用评论复用既有搜索/甄选/人审；精选定向评论复用 noteId 精确路径。Facebook 只复用已配置群/目标范围及既有加群评论 adapter，不接任意 URL。只有 `commented` 且平台确认/服务器确认成立时增加 `successCount`；无候选计 `skippedCount`，提交失败计失败。
- **发布/候选**：给 `PublishScheduler` 增加 `triggerDelegated`，先经过 `risk.status===normal` 与 `canDo('publish')`，再进入现有生成候审链。普通发稿/今日灵感默认 `review`；候选生成以真实持久化的 `pending_approval` draft id 计候选成功，但绝不计为平台发布成功。Facebook 今日灵感由 registry 禁止。
- **候选操作**：通过现有 publish draft preflight/edit/approval signal 适配器执行。批准、驳回、修改都要求候选仍为 `pending_approval` 且版本匹配；任务只在回读真态后完成。
- **Facebook 群组任务**：只接既有加入指定/下一个已配置群后评论链，要求群归属与配置账本校验；不新增群发现、全站搜索或越过人审/配额的批量路径。

不直接调用 RiskController.record；平台成功事件仍由既有执行链写风险计数，保持 RiskController 唯一写者。

### 7. 成功计数按 action 绑定验证证据

事件表的每次 attempt 保存 `verificationKind` 与 `evidenceRef`：

- 评论：平台/服务器确认的 comment receipt + target id；
- 发布：`publish_log.status=published` 或提交后现有诚实终态；处于 `pending_approval` 只进入 `waiting_approval`，不计发布成功；
- 候选生成：持久化 `pending_approval` draft id；
- 候选批准/驳回/修改：版本化写操作的回读记录。

达到目标数才 `completed`。deadline/maxAttempts/cancel 结束时若 `successCount>0` 且未达标，则 `partially_completed`；完全无成功并非一律 failed：无候选/风险额度暂不可用可用 `deferred`，不可恢复错误才 `failed`。

### 8. 平台注册表显式声明委托动作成熟度

cloud 与 edge registry 增加同构 `delegatedActions` 元数据，但不进入协议枚举：

- XHS：评论、精选定向评论、普通发布、今日灵感、候选、审批、控制为 supported。
- Facebook：配置范围评论/群组任务、普通发布、候选/审批/控制为 beta；任意帖子 URL 评论、全站搜索、今日灵感为 unsupported；发布 beta 额外依赖真机验收/客户端能力闸。

cloud registry 是准入事实源；edge registry 仅用于客户端展示和本地 fail-closed。任务创建与执行前都复核账号平台，防止任务等待期间账号平台被改后混跑。

### 9. Edge 使用 HTTP 控制面桥，不改边云协议

Electron 主进程从已选择的 cloud WS URL 派生 panel HTTP base，暴露最小 IPC：create draft、confirm、list/detail、pause/resume/cancel。renderer 永远用当前 selected environment 的真实 `status.account.id/name` 与平台；没有选中环境时入口禁用。

公共写 API 的第一次调用只创建 `awaiting_confirmation`，renderer 展示结构化字段并要求第二次确认。客户端轮询任务投影并显示成功/尝试/跳过/失败原因。由于本 change 不构建安装包，部署 cloud 后只有 Feishu/console 入口可立即使用；Edge 源码能力必须标记“安装端尚未发布”。

### 10. console 精选动作改为两步确认并复用现有候选编辑面

精选行按钮先 POST task draft，收到确认摘要后打开 modal；确认后入队。console 不再把 `triggered=true` 当作最终成功。候选稿的编辑/批准/驳回继续复用当前内容页控件，只把动作结果关联 task id 与版本证据。

## Risks / Trade-offs

- [并行 lease 变更尚未合入] → 本 change 避开协议、协调器、edge `main.ts` 页面执行与 cloud `command-sequencer`；优先只影响队列排序，租约优先级固定 automatic。
- [worker 重启发生在等待人审期间] → task/event 持久化，claim 有过期恢复；发布/评论适配器恢复时先查持久化证据/去重账本，不能盲重投提交未知动作。
- [旧 scheduler 主要返回触发态] → 只增加可选终态观察口，旧调用签名/回执保持兼容；任务计数只读终态观察口。
- [Facebook 发布能力代码与真机交付不等价] → registry 标 beta 且依赖 runtime gate；未满足时 task `deferred/failed` 带明确原因，不展示可稳定交付。
- [HTTP panel 当前是运营控制面] → API 仍受既有部署边界；Edge 客户鉴权 token 可透传但本 phase 不扩大客户权限模型。写操作仍有 task 确认 + 账号/platform 校验，不能靠调用方自报。
- [单 worker 吞吐有限] → Phase 1 以账号安全串行为目标；PG claim 允许未来水平扩展，但默认只启一实例。

## Migration Plan

1. 先部署 cloud 的幂等 schema、task API 与 dormant worker（默认关闭执行），同时保持旧 console 可解析的响应字段，验证旧只读命令/排期零回归。
2. cloud 与 console 在同一 dev 发布窗口切换精选两步确认，避免旧 console 把 task draft 当作已触发成功；启用 Feishu 写命令/自然语言确认卡。
3. 在 dev 显式开启 XHS 委托 worker，运行 acceptance/full/typecheck 与 task API 健康检查。
4. Edge 仅提交源码，不打包。
5. Facebook 保持 beta gate，只有现有配置目标和现有客户端能力满足时执行；真机未验收项继续记录 backlog。

回滚时先关闭 worker/入口开关，保留任务表和事件表供审计；旧 `/publish`、`/comment` 和内容排期不依赖新表，可独立继续运行。schema 为新增表/索引，无需破坏性回滚。

## Open Questions

无阻塞实施的问题。Facebook 普通发布能否从 beta 升级为正式可交付，取决于现有真机验收 backlog 与新 Edge 安装包发布，不由本 change 的代码完成状态自动改变。
