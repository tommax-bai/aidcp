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

当一个委托任务由飞书**命令事件**创建（该事件带真实来源会话 `chatId`）时，系统 SHALL 把该来源会话作为该任务的一等字段持久化（与偏向 `messageId`、参与去重键的 `sourceRef` 解耦），并在该任务产出**操作员向卡片**时把来源会话作为投递目标。

操作员向卡片 SHALL 覆盖该任务产出的**全部**面向操作员的卡片，与动作族无关，具体包含：发帖内容审批卡、发帖终态失败 / 部分完成结果卡、**评论审批卡（「待审核评论」）**、**评论终态结果卡**。任何**一个**动作族的操作员向卡片漏接来源会话 MUST 视为本要求未满足——同一条命令的多张卡分投不同会话，与「配错了」在运营视角不可区分。

来源会话 SHALL 由**类型层面**贯穿到每个卡片目标解析点：承接委托触发的各调度器端口 MUST 声明该 chat 目标字段，MUST NOT 依赖调用点各自记得透传一个可选参数——缺字段时漏传是合法编译、静默回落，类型检查抓不到。

无来源会话的委托任务（console / api / edge 等非飞书入口，或事件未带 `chatId`）SHALL 回落 `feishu-notification-routing` 定义的共享解析（账号团队群 → 默认群）。该字段的持久化 MUST 覆盖异步执行与进程重启——终态卡可能在命令之后很久、甚至重启之后才发出。

系统 MUST NOT 因来源会话不可达而谎报投递成功：投递失败 SHALL 记日志并保持诚实态（审批卡失败保持诚实待审），MUST NOT 当成功。

#### Scenario: 私聊命令触发的委托发帖，卡片回私聊

- **WHEN** 飞书私聊里 `/publish <昵称>` 创建委托发帖任务，事件带 `chatId=P`
- **THEN** 该任务持久化来源会话 `P`
- **AND** 其内容审批卡与终态失败 / 部分完成结果卡 SHALL 投递到 `P`
- **AND** MUST NOT 投递到默认管理群或账号团队群

#### Scenario: 群聊命令触发的委托发帖，卡片回该群

- **WHEN** 飞书某群里 `/publish <昵称>` 创建委托发帖任务，事件带 `chatId=G`
- **THEN** 其内容审批卡与终态失败结果卡 SHALL 投递到 `G`

#### Scenario: 私聊命令触发的委托评论，审批卡与终态卡都回私聊

- **WHEN** 飞书私聊里 `/comment <昵称>`（含 `--join` / `--contact` / `--force` 等任意开关）创建委托评论任务，事件带 `chatId=P`
- **THEN** 其「待审核评论」审批卡 SHALL 投递到 `P`
- **AND** 其评论终态结果卡 SHALL 投递到 `P`
- **AND** 两张卡 MUST NOT 分投不同会话，MUST NOT 投递到默认管理群或账号团队群

#### Scenario: 无来源会话的委托任务回落共享解析

- **WHEN** 一个委托任务由 console / api / edge 等无飞书来源会话的入口创建（`originChatId` 为空）
- **THEN** 其审批卡与业务结果卡 SHALL 走 `feishu-notification-routing` 的共享解析（账号团队群 → 默认群）
- **AND** MUST NOT 因缺来源会话而被硬绑默认群

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

### Requirement: 预算耗尽的零成功终态必须携带真实失败原因

预算耗尽（`max_attempts` / `deadline`）而零成功的终态，其 `terminalOutcome.message` MUST 在既有预算记账之后追加**真实失败原因**，取自该任务已 settle 且 `reason` 非空的最后一条 attempt。

「已达到最大尝试次数」「已到截止时间」是**为什么停**的记账，不是**为什么没成**的原因。只给记账等同于静默失败——卡发出来了，但运营无法判断该重试、该改配置、还是该等。原因在 attempt settle 时即已持久化，终态 MUST 读它，MUST NOT 凭空另拼一句只含记账的模板。

既有前缀 SHALL 原样保留（追加而非替换），既有的诚实部分完成语义不受影响。

#### Scenario: 尝试后失败的终态带上最后一次原因

- **WHEN** 一个委托发帖任务耗尽 `maxAttempts`，其最后一条 settle 的 attempt 状态为 `failed`、`reason` 非空
- **THEN** `terminalOutcome.message` SHALL 保留 `已达到最大尝试次数；真实完成 0/1。` 前缀
- **AND** SHALL 追加该 attempt 的原因（经人话化）
- **AND** 该原因 SHALL 出现在飞书终态失败卡正文中

#### Scenario: 无原因可取时保持现状而非编造

- **WHEN** 预算耗尽终态下，该任务不存在任何 settle 且 `reason` 非空的 attempt
- **THEN** `terminalOutcome.message` SHALL 与本变更前逐字一致
- **AND** MUST NOT 补一句「原因未知，可能是……」之类的推测

#### Scenario: 到期终态同样带原因

- **WHEN** 一个委托任务因 `deadlineAt` 到期而零成功终结，且存在带原因的已 settle attempt
- **THEN** `terminalOutcome.message` SHALL 在 `已到截止时间；真实完成 N/M。` 之后追加该原因

### Requirement: 终态必须区分「尝试后失败」与「从未真正开始」

预算耗尽的零成功终态 MUST 区分两种截然不同的局面，MUST NOT 让二者产出同一句话：

- **从未真正开始**：SHALL 明说 N 次均未真正开始及其原因，MUST NOT 使用任何可被读成「已经发过 / 已经动过手」的措辞。
- **其余一切局面**：SHALL 表述为最后一次未成的原因。

此区分为红线「绝不静默假成功」在终态回执上的落点：让开同样消耗尝试预算，若与真实失败同文表述，运营会误以为系统已在平台上动过手。

**但「从未真正开始」本身是一个关于「平台没被碰过」的断言，故 MUST 由证据支撑、MUST NOT 由计数器推断**：尝试的「跳过」状态同时覆盖两种截然不同的经过——① 动作真正开始前就被让开（执行器根本没跑）；② 执行器跑了、驱动了浏览器（搜词、开页），最终判定不写入。二者的跳过计数完全相同。因此系统 MUST 在「让开」发生时留下**可区分的验证证据**，并且**仅当每一条已了结的尝试都带有该证据时**才作此断言；证据不全时 SHALL 回落到「最后一次未成原因」的中性表述。否则即为红线「绝不编造」所禁的、拿不出证据的断言。

#### Scenario: 全程被让开而耗尽预算

- **WHEN** 一个委托发帖任务的 2 次 attempt 全部因执行前闸（风控状态、并发占用等）被让开，每条都留下了「未真正开始」的验证证据
- **THEN** `terminalOutcome.message` SHALL 表述为「2 次均未真正开始」并带上原因
- **AND** MUST NOT 表述为「最后一次未成原因」或任何暗示已发生平台写入的措辞

#### Scenario: 执行器跑过但判定不写，绝不宣称没开始

- **WHEN** 一个委托评论任务的每次 attempt 都真正驱动了浏览器（搜词、开页），最终判定无强候选而不评、settle 为跳过——其跳过计数与「全程被让开」完全相同
- **THEN** `terminalOutcome.message` MUST NOT 出现「均未真正开始」
- **AND** SHALL 回落为「最后一次未成原因」的中性表述

#### Scenario: 混合局面只报最后一次并标注总次数

- **WHEN** 一个任务的多次 attempt 中既有真实失败也有让开，原因各异
- **THEN** `terminalOutcome.message` SHALL 报最后一次未成的原因并标注总尝试次数
- **AND** MUST NOT 做原因聚类统计（超出本变更范围）

### Requirement: 原因人话化必须只翻译已知码、未知码原样透传

原因字符串在同一字段内混装三种语域（机器码 snake_case、中文人话句、上游抛出的英文异常文本），无判别字段。人话化 SHALL 按白名单把已知机器码翻成中文；**未命中白名单的 MUST 原样透传**，MUST NOT 猜测其含义、MUST NOT 美化成听着像诊断而实际是编造的句子。超长文本 SHALL 裁剪并保留可辨识的原文片段。

#### Scenario: 已知码翻成人话

- **WHEN** 最后一条 attempt 的 `reason` 为白名单内的机器码（如风控状态类、人设未配置类）
- **THEN** 终态 message 中 SHALL 出现对应中文表述

#### Scenario: 未知码原样出现在卡上

- **WHEN** 最后一条 attempt 的 `reason` 是白名单未覆盖的字符串
- **THEN** 该字符串 SHALL 原样出现在终态 message 中
- **AND** MUST NOT 被替换成任何未经证据支持的表述

#### Scenario: 非重试终态同样说人话

- **WHEN** 一个任务因不可重试的配置问题（人设未绑等）在起跑前早退而终结——此类原因**只走**非重试终态、从不经预算终态
- **THEN** 其终态 message SHALL 同样经过人话化
- **AND** MUST NOT 把机器码原样甩给运营（除非该码不在白名单内，此时按上一条原样透传）

### Requirement: 到期终态必须与其他终态一样触发通知

任务因**到达截止时间**而终结时，MUST 与耗尽尝试的终态走同一条通知路径。到期是任务失败最常见的收场之一（全程等不到安全空档、执行器从未成功领到任务等），若它是唯一一条不发卡的终态，红线「绝不静默失败」就在最常见处被绕过——终态原因被写进库却永远无人看见。

#### Scenario: 到期失败必须发出结果卡

- **WHEN** 一个委托发帖任务未达成功目标即到达截止时间而终结
- **THEN** 系统 SHALL 触发与耗尽尝试终态相同的通知路径，使其终态失败卡照常投递
- **AND** 该卡 SHALL 携带按本 spec 其余要求组装的真实原因
- **AND** MUST NOT 只写库而不通知

### Requirement: 结果未知的在途派发绝不可被终结为干净失败

任务到期时若仍有**已派发、未了结**的尝试（如租约失效或进程重启导致终态回执永远未达），该命令**可能已在平台上写入**。此时 MUST 以「已提交、结果未知」终结并标记未知，MUST NOT 判为干净失败，更 MUST NOT 拿更早那次尝试的原因充当本次结局——那是反向的假确定性：把一个可能已生效的动作报成确定没生效。

#### Scenario: 到期时派发仍在途

- **WHEN** 一个任务到达截止时间，且它有一条尝试仍停在已派发未了结状态，同时更早的尝试留有良性原因
- **THEN** 终态 SHALL 标记为「已提交、结果未知」
- **AND** MUST NOT 把更早那次尝试的原因渲染为本次结局
- **AND** MUST NOT 自动重试（防重复写入）

### Requirement: 失败原因的精度不得超过已落库的证据

终态回执的原因精度 SHALL 以**已持久化的证据**为上限。发布派发阶段的分步失败细节（定位失败、内容超长、配图全失败等）当前未落库，仅塌成一个状态枚举——因此该类失败的终态回执 SHALL 表述到「稿件在发布派发阶段失败」这一层并携带可追证据引用，**MUST NOT** 渲染成具体的边缘失败原因。

抬高该精度天花板（把分步失败落库）属独立变更，MUST NOT 在本变更中以推测填补。

#### Scenario: 派发期失败只说到阶段

- **WHEN** 一个委托发帖任务的 attempt 因发布派发阶段失败而 settle，DB 中仅有状态枚举、无分步细节
- **THEN** 终态 message SHALL 说明失败发生在发布派发阶段并带上稿件记录引用
- **AND** MUST NOT 声称具体是哪一步、哪个控件或哪条平台文案导致失败

