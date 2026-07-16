# user-delegated-tasks Specification

## Purpose
TBD - created by archiving change user-delegated-tasks-phase-1. Update Purpose after archive.
## Requirements
### Requirement: DelegatedTask 必须完整表达用户业务目标与执行边界

系统 SHALL 以统一 `DelegatedTask` 表达用户委托，不得为每个入口建立互不兼容的任务形状。任务 MUST 包含账号 id 与可读账号名快照、平台、动作、目标成功数、最大尝试数、截止时间或执行窗口、来源与目标约束、人审模式、优先级、状态、进度、暂停/取消意图和诚实终态。任务状态 SHALL 覆盖 `draft`、`awaiting_confirmation`、`queued`、`planning`、`waiting_approval`、`executing`、`partially_completed`、`completed`、`deferred`、`cancelled`、`failed`。

#### Scenario: 创建完整任务草稿
- **WHEN** 用户要求账号“小萝北”在今晚前完成 5 条有效评论且最多尝试 8 次
- **THEN** 系统创建包含账号、平台、动作、5 个成功目标、8 次尝试上限、截止时间、人审与来源约束的 `awaiting_confirmation` 任务
- **AND** MUST NOT 在确认前执行任何平台写动作

### Requirement: 成功数量必须来自动作对应的真实验证证据

`targetSuccessCount` SHALL 表示业务结果成功数而非尝试数。评论任务只有在平台/服务器结果验证成功后才能增加 `successCount`；触发成功、候选选中、已输入文本、已点击提交或结果未知均不得计成功。候选稿生成任务只有在候选持久化且可回读后计候选成功；发布任务的待审稿不得计为平台发布成功。

#### Scenario: 五次尝试只有三条评论验证成功
- **WHEN** 目标为 5 条评论，5 次尝试中仅 3 条得到平台成功验证，另 2 条无候选或提交未确认
- **THEN** `successCount=3`、`attemptCount=5`
- **AND** 任务 MUST NOT 显示为完成 5/5

#### Scenario: 发布稿等待人审不计发布成功
- **WHEN** 发布任务已生成 `pending_approval` 稿件并发送审批卡但尚未批准
- **THEN** 任务进入 `waiting_approval`
- **AND** 发布成功数保持 0

### Requirement: 下游派发必须先记 attempt 并在恢复时先对账后重试

系统 MUST 在调用评论/发布/候选写适配器前持久化唯一 attempt id、规范化目标键与阶段。进程在派发后、记录结果前崩溃时，恢复流程 SHALL 先查询平台去重证据、publish_log 或候选版本；结果已成功 SHALL 补记成功，结果未知 SHALL 保持未知并禁止自动重试同一目标，只有可证明未提交时才可重试。

#### Scenario: 评论成功后 cloud 在记账前崩溃
- **WHEN** 平台已验证评论成功，但 cloud 在更新 task successCount 前重启
- **THEN** worker 根据 attempt target 与评论去重/成功账本补记一次成功
- **AND** MUST NOT 再发一条相同目标评论

### Requirement: 所有任务必须有有界尝试、截止时间与诚实部分完成

每个可执行任务 MUST 有有限 `maxAttempts` 和 `deadlineAt` 或有界执行窗口。达到成功目标 SHALL `completed`；耗尽尝试、到期或取消剩余部分时，若已有真实成功但未达目标 SHALL `partially_completed` 并保留真实计数；零成功时 SHALL 按可恢复性进入 `deferred`、`cancelled` 或 `failed`，不得为凑数换不符合约束的目标。

#### Scenario: 候选不足时三比五部分完成
- **WHEN** 用户要求完成 5 条评论，但在期限和 8 次尝试内只有 3 个符合来源/目标约束的候选成功评论
- **THEN** 任务以 `partially_completed` 终结并显示 3/5、8 次尝试、跳过原因
- **AND** MUST NOT 降低相关性、跨出目标范围或重复评论来凑成 5/5

### Requirement: 立即、定时、下一安全空档和优先执行必须映射为可解释的排队语义

任务 SHALL 支持立即、指定时间、下一安全空档和优先执行。指定时间在 `notBefore` 前不得执行；下一安全空档在账号没有更高优先级/在途 ownership 且风险闸允许时才可开始；“优先执行”只提升委托队列内排序，MUST NOT 把异步用户任务提升为 `human` 或抢占人工/风控动作。

#### Scenario: 优先任务不抢占正在输入的人工动作
- **WHEN** 用户将一个异步评论任务设为优先执行，而同账号正执行人工命令的文本输入
- **THEN** 任务在委托队列中提前，但向边缘申请时仍使用 `automatic`
- **AND** MUST NOT 在输入中途强停当前动作

### Requirement: 暂停和取消只在安全业务动作边界生效

“完成当前安全动作后暂停” SHALL 记录暂停意图并在当前 scheduler/adapter 返回后进入 `deferred`；“取消尚未执行的剩余部分” SHALL 保留已验证成功与已发生尝试，只阻止后续新动作。已提交但结果未知的动作 MUST 保持未知语义，不得因取消改写为失败或未执行。

#### Scenario: 当前评论结束后暂停
- **WHEN** 用户在一条评论已进入提交/验证期间请求暂停
- **THEN** 系统允许本次动作沿既有安全链路收敛，再停止发起下一候选
- **AND** MUST NOT 在文本输入或提交点击中途终止

#### Scenario: 取消剩余部分保留已完成数量
- **WHEN** 5 条评论任务已验证成功 2 条后用户取消剩余部分
- **THEN** 后续 3 条不再发起，任务以保留 2/5 的 `partially_completed` 或 `cancelled` 终态收敛
- **AND** 已有两条成功不得被清零

### Requirement: 用户委托与定时任务必须共享 ownership、优先级和去重

同账号同动作族的委托任务与 `PublishScheduler`、`CommentScheduler`、内容排期 SHALL 共享可观察 ownership 和幂等键。已有在途动作时另一来源 MUST 等待/跳过，MUST NOT 双重执行；平台提交结果未知时 MUST NOT 自动重试同一目标。

#### Scenario: 排期评论与委托评论同时命中
- **WHEN** 内容排期准备为某账号触发评论，而该账号已有执行中的委托评论任务
- **THEN** 排期本 tick 诚实跳过且不启动第二条评论链
- **AND** 委托任务不得被重复计数

### Requirement: 批量和异步委托必须遵守自动化风险额度并保留人审

**精确单次操作员命令**（`source=legacy_command` 且 `targetConstraints.manualSingle=true`，含 `/publish` 与 `/comment`）SHALL 以操作员全权执行——越过风控 status / canDo 与配额闸（发帖侧透传 `operatorOverride=true`，评论侧 `manualOverride=true`），但**发布前 / 评论前的人审 MUST 仍强制**（越权只越风控 / 配额，绝不越人审）。`targetSuccessCount>1`、跨账号、自然语言（`source=feishu`）或结构化（`source ∈ {edge,console,api}`）委托 MUST 使用自动化额度与风险闸（`governed`），MUST NOT 置 `operatorOverride` / 为每次 attempt 传 `manualOverride=true`。RiskController SHALL 继续是账号风险状态唯一写者。公开评论和发布默认 SHALL 使用 `review`，除非既有受控配置明确允许其他模式。

#### Scenario: 批量评论不能循环绕额度
- **WHEN** 用户确认一个 5 条评论的委托任务
- **THEN** 每次评论尝试按自动化路径检查风险/配额且 `manualOverride=false`
- **AND** 额度不足时任务 deferred 或诚实部分完成，不得循环伪装成五次单次人工命令

#### Scenario: 精确 /publish 在风控受限账号仍以操作员全权执行
- **WHEN** 管理群对一个风控非 normal 或当天已达发布配额的账号发送 `/publish <昵称>`（`source=legacy_command`、`manualSingle`）
- **THEN** 系统越过风控 status/canDo 与配额生成草稿并发出发布人审卡（`operatorOverride=true`）
- **AND** MUST NOT 因风控/配额把该精确命令 blocked→deferred→静默判失败
- **AND** 发布前人审 MUST 仍强制，越权 MUST NOT 越过人审

#### Scenario: 自然语言与结构化发帖不得越风控
- **WHEN** 委托发帖来自自然语言（`source=feishu`）或结构化入口（edge/console/api）
- **THEN** 系统走 `governed` 路径，风控非 normal / canDo 拒时诚实 blocked
- **AND** MUST NOT 置 `operatorOverride`，MUST NOT 让结构化发帖跳过风控闸

### Requirement: 第一批动作必须统一接入并回报真实进度

Phase 1 SHALL 接入：完成 N 条有效评论、发布一篇稿件、参考今日灵感发布一篇稿件、对指定精选内容发起评论、生成多个候选稿但暂不发布、批准/驳回/修改候选稿、Facebook 已配置范围内的群组任务，以及任务查询/暂停/恢复/取消。进度投影 MUST 显示成功数、尝试数、跳过数、失败数和真实失败原因。

#### Scenario: 候选稿生成后暂不发布
- **WHEN** 用户要求生成 3 个候选稿但暂不发布
- **THEN** 系统生成并持久化最多 3 个可回读候选，保留待审/可编辑状态
- **AND** MUST NOT 自动批准或向平台提交

#### Scenario: 版本过期的候选修改被拒
- **WHEN** 用户基于旧版本确认卡修改已被他人更新的候选稿
- **THEN** 系统以版本冲突拒绝并回读当前候选真态
- **AND** MUST NOT 覆盖较新的修改

#### Scenario: Facebook 群组任务只用既有配置目标
- **WHEN** 用户确认一个 Facebook 加群后评论任务
- **THEN** 系统只从该账号既有目标/成员账本选择或使用经归属校验的指定群
- **AND** MUST NOT 自动发现新群或跨账号复用群目标

### Requirement: 小红书正式支持而 Facebook 仅在声明范围内 Beta

小红书 SHALL 支持 Phase 1 全部动作。Facebook SHALL 仅支持已有配置目标范围内的评论/群组相关任务、普通发布、候选/审批和任务控制，并显式标记 Beta；MUST NOT 承诺全站搜索、任意 Facebook 帖子 URL 评论或“参考今日灵感发稿”。Facebook 发布在真机验收或客户端能力闸未满足时 MUST deferred/拒绝并说明原因，MUST NOT 把源码存在描述成稳定交付。

#### Scenario: 请求任意 Facebook URL 评论
- **WHEN** 用户给出一个不属于已配置目标范围的 Facebook 帖子 URL 并要求评论
- **THEN** 系统在确认前以 `unsupported_target_scope` 拒绝
- **AND** MUST NOT 回落到全站搜索或其他帖子

#### Scenario: Facebook 今日灵感发稿未开放
- **WHEN** 用户要求 Facebook 参考今日灵感发稿而平台化创作模板/语言/素材策略尚未完成
- **THEN** 系统以明确受限原因拒绝或 deferred
- **AND** MUST NOT 走小红书 prompt 形状生成后宣称 Facebook 已支持

### Requirement: 命令触发的委托任务必须捕获来源会话并回投操作员向卡片

当一个委托任务由飞书**命令事件**创建（该事件带真实来源会话 `chatId`）时，系统 SHALL 把该来源会话作为该任务的一等字段持久化（与偏向 `messageId`、参与去重键的 `sourceRef` 解耦），并在该任务产出**操作员向卡片**时把来源会话作为投递目标。操作员向卡片当前包含：内容审批卡、发帖终态失败 / 部分完成结果卡。

无来源会话的委托任务（console / api / edge 等非飞书入口，或事件未带 `chatId`）SHALL 回落既有默认 / 团队路由，行为逐字不变。该字段的持久化 MUST 覆盖异步执行与进程重启——终态卡可能在命令之后很久、甚至重启之后才发出。

系统 MUST NOT 因来源会话不可达而谎报投递成功：投递失败 SHALL 记日志并保持诚实态（审批卡失败保持诚实待审），MUST NOT 当成功。

#### Scenario: 私聊命令触发的委托发帖，卡片回私聊

- **WHEN** 飞书私聊里 `/publish <昵称>` 创建委托发帖任务，事件带 `chatId=P`
- **THEN** 该任务持久化来源会话 `P`
- **AND** 其内容审批卡与终态失败 / 部分完成结果卡 SHALL 投递到 `P`
- **AND** MUST NOT 投递到默认管理群或账号团队群

#### Scenario: 群聊命令触发的委托发帖，卡片回该群

- **WHEN** 飞书某群里 `/publish <昵称>` 创建委托发帖任务，事件带 `chatId=G`
- **THEN** 其内容审批卡与终态失败结果卡 SHALL 投递到 `G`

#### Scenario: 无来源会话的委托任务回落既有路由

- **WHEN** 一个委托任务由 console / api / edge 等无飞书来源会话的入口创建（`originChatId` 为空）
- **THEN** 其审批卡 SHALL 走既有默认审批群解析
- **AND** 其账号维度业务结果卡 SHALL 走既有账号→团队群路由
- **AND** 行为与本变更前逐字一致

#### Scenario: 来源会话投递失败保持诚实

- **WHEN** 任务的来源会话拒收其审批卡或终态卡
- **THEN** 系统 SHALL 记录该失败（带任务 / 记录上下文）
- **AND** MUST NOT 谎报卡片已成功送达

### Requirement: 委托层通知由底层业务结果卡承担、发帖失败兜底、无变化对账静默

委托层 MUST NOT 为任务的常规状态迁移（`queued`、`executing`、`completed`、`waiting_approval`）主动推送自有的任务进度卡。每个任务的执行结果 SHALL 由其底层动作的**正常业务结果卡**承担：评论由评论链的结果卡回报；发帖成功由发布人审卡自证（成功不重复报绿）；发帖等待人审由发布人审卡本身承担。

**终态失败兜底**（红线：绝不静默失败）——没有独立业务结果卡的终态失败，委托层 MUST 补一张诚实卡：

- **发帖类终态失败**（`failed`，或仍有缺口的 `partially_completed`）：MUST 补发失败 / 部分完成结果卡。
- **评论类「起跑前触发闸失败」**（`failed`、0 成功、终态码 `non_retryable_failure`——人设未绑 / 联系方式缺 / 平台不支持 / 未接线等在异步任务起跑前早退，评论链从未起跑、`postResultCard` 从未发过）：MUST 补发一张诚实失败卡。
- **评论类起跑后失败**（`max_attempts` / `deadline` 等，评论链已发结果卡）：MUST NOT 由委托层补发（避免与 `postResultCard` 双发）。

精确旧 slash 写命令（`source=legacy_command`）直接排队时 SHALL **静默受理**——只保留已读表情，MUST NOT 发送队列提示卡；结果由该任务自身的业务结果卡回报。自然语言委托仍先展示结构化确认卡（不受影响）；用户主动请求的控制命令（查看 / 暂停 / 取消）与卡片按钮回卡不受影响。

委托任务处于 `waiting_approval` 时保留有界的审批结果对账，但当审批、真实进度、控制意图和终态结果均未变化时，MUST NOT 发送新的用户通知或递增用于卡片控制的 task version；内部 claim/lease MAY 更新，但不得把无变化心跳呈现为新的业务进度。

#### Scenario: 发帖失败仍诚实通知
- **WHEN** 一个委托发帖任务达到最大尝试仍 0 成功 → `failed`
- **THEN** 委托层补发一张红色失败结果卡（含真实完成数 0/N），MUST NOT 静默

#### Scenario: 评论起跑前触发闸失败仍诚实通知
- **WHEN** 一个委托评论任务在异步任务起跑前因人设未绑 / 联系方式缺 / 平台不支持 / 未接线而以非重试失败终结（`failed`、0 成功、终态码 `non_retryable_failure`）
- **THEN** 委托层补发一张红色「评论任务未触发」结果卡（含起跑失败的人类可读原因），MUST NOT 静默

#### Scenario: 评论起跑后失败不重复报卡
- **WHEN** 一个委托评论任务已起跑到终态失败（评论链已按账号发出结果卡），终态码为 `max_attempts` / `deadline`
- **THEN** 委托层 MUST NOT 再叠加一张失败卡（避免与评论链 `postResultCard` 双发）

#### Scenario: 发帖成功不重复报绿
- **WHEN** 委托发帖经人审通过并发布 → `completed`
- **THEN** 委托层 MUST NOT 再发绿色成功卡（成功由发布人审卡自证）

### Requirement: 自然语言入口先结构化确认；结构化精确入口直接入队

只有**自然语言**委托入口（`source=feishu`）SHALL 先创建 `awaiting_confirmation` 任务并展示结构化确认摘要——账号 / 数量 / 截止 / 尝试均为从散文**推断**、可能解析错，需人过目；只有带 task id 与当前版本的明确确认才能进入 `queued`。**结构化精确入口**（console 行级动作 / Edge 快捷入口 / api / 旧 slash 命令，即 `source ≠ feishu`）参数已在调用处显式给定、无可推断歧义，SHALL 在创建时直接确认入队（`awaiting_confirmation → queued`），MUST NOT 展示结构化确认卡。

**结构化入口的客户端请求体对 `approvalMode` 不可信**：免审（`auto_approve`）只由账号级授权授予，客户端体 MUST NOT 自带、系统 MUST NOT 原样采信。系统 SHALL 在 HTTP 建草稿边界把客户端体的 `approvalMode` 收口——缺省保持未定（交由按动作的默认，如 `generate_candidates → draft_only`）、`draft_only` 放行、其余（含 `auto_approve` 与任何未来模式）夹成 `review`。**服务端自建 intent**（后台洗稿 / 候选控制已显式传 `review`、飞书 parser 已硬编码 `review`）不经此收口、不受影响。

两类入口的人审都不受影响（发布 / 评论仍在下游内容审批处保留人审），昵称重名或找不到仍 fail-closed 拒绝。重复创建（去重命中）MUST 幂等返回当前真态，MUST NOT 重复入队。任务创建时 SHALL 从账号事实源回读平台，调用方自报平台不一致 MUST 拒绝。直接入队 ≠ 已执行：worker 接管前不得有任何一次尝试或平台副作用。

#### Scenario: 客户端体自带 auto_approve 被夹成 review

- **WHEN** 结构化建草稿路由（面板 / 客户端）收到请求体带 `approvalMode:'auto_approve'`
- **THEN** 系统在创建前把该字段夹成 `review`，任务以必审入队
- **AND** MUST NOT 让内容以免审绕过下游人审直达平台，即使该账号未开启账号级免审

#### Scenario: 结构化精确入口不出确认卡但保留人审

- **WHEN** 管理后台对一条精选图文点「洗稿」（`source=console`，服务端自建 intent 传 `review`）
- **THEN** 系统直接确认入队（状态 `queued`），MUST NOT 展示确认卡
- **AND** 其 `review` 授权不经客户端收口、保持不变，下游人审仍强制

#### Scenario: 自然语言委托仍先结构化确认

- **WHEN** 飞书管理群发送自然语言业务目标
- **THEN** 系统仍先创建 `awaiting_confirmation` 任务并展示结构化确认摘要，明确确认后才 `queued`

#### Scenario: 重复创建幂等、不产生双任务

- **WHEN** 同一结构化精确动作在去重窗口内被重复触发
- **THEN** 去重命中返回同一 task id 的当前真态，MUST NOT 重复入队或重复执行

