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

**精确单次操作员命令**（`source=legacy_command` 且 `targetConstraints.manualSingle=true`，含 `/publish` 与 `/comment`）SHALL 以操作员全权执行——越过风控 status / canDo 与配额闸（发帖侧透传 `operatorOverride=true`，评论侧 `manualOverride=true`）。发布前人审 MUST 仍强制；评论前人审默认强制，但账号显式 `auto_approve_all` 时 MUST 直接授权，飞书 `/comment` 不得再要求第二次按钮审批。免审通知仅作旁路记录，失败 MUST NOT 阻止提交或回退按钮审批。该账号策略只改变评论授权等待，MUST NOT 改变 `manualOverride` 的风控/配额语义。`targetSuccessCount>1`、跨账号、自然语言（`source=feishu`）或结构化（`source ∈ {edge,console,api}`）委托 MUST 使用自动化额度与风险闸（`governed`），MUST NOT 置 `operatorOverride` / 为每次 attempt 传 `manualOverride=true`。RiskController SHALL 继续是账号风险状态唯一写者。公开评论和发布默认 SHALL 使用 `review`，除非既有受控来源配置或账号全局评论策略明确允许免审。

#### Scenario: 批量评论不能循环绕额度
- **WHEN** 用户确认一个 5 条评论的委托任务
- **THEN** 每次评论尝试按自动化路径检查风险/配额且 `manualOverride=false`
- **AND** 额度不足时任务 deferred 或诚实部分完成，不得循环伪装成五次单次人工命令

#### Scenario: 精确 /publish 在风控受限账号仍以操作员全权执行
- **WHEN** 管理群对一个风控非 normal 或当天已达发布配额的账号发送 `/publish <昵称>`（`source=legacy_command`、`manualSingle`）
- **THEN** 系统越过风控 status/canDo 与配额生成草稿并发出发布人审卡（`operatorOverride=true`）
- **AND** MUST NOT 因风控/配额把该精确命令 blocked→deferred→静默判失败
- **AND** 发布前人审 MUST 仍强制，越权 MUST NOT 越过人审

#### Scenario: 精确 /comment 服从账号全局免审
- **WHEN** 管理群对一个 `auto_approve_all` 账号发送精确 `/comment <昵称>`
- **THEN** 评论沿用 `manualOverride=true` 越过既有手工风险/配额闸，并按账号全局免审直接继续
- **AND** MUST NOT 再发送同意/不发按钮卡或等待第二次人审

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

**结构化入口的客户端请求体对 `approvalMode` 不可信**：免审（`auto_approve`）只由 Cloud 受控配置授予，客户端体 MUST NOT 自带、系统 MUST NOT 原样采信。系统 SHALL 在 HTTP 建草稿边界把客户端体的 `approvalMode` 收口——缺省保持未定（交由按动作的默认，如 `generate_candidates → draft_only`）、`draft_only` 放行、其余（含 `auto_approve` 与任何未来模式）夹成 `review`。**服务端自建 intent**（后台洗稿 / 候选控制已显式传 `review`、飞书 parser 已硬编码 `review`）不经此收口。评论执行到授权边界时仍 SHALL 读取 Cloud 持久化的账号全局评论策略；显式 `auto_approve_all` 可把有效评论模式覆盖为免审，这不等于采信客户端请求体。

两类入口的下游授权都不受确认卡差异影响：发布仍保留人审，评论默认保留人审但服从账号全局评论覆盖；昵称重名或找不到仍 fail-closed 拒绝。重复创建（去重命中）MUST 幂等返回当前真态，MUST NOT 重复入队。任务创建时 SHALL 从账号事实源回读平台，调用方自报平台不一致 MUST 拒绝。直接入队 ≠ 已执行：worker 接管前不得有任何一次尝试或平台副作用。

#### Scenario: 客户端体自带 auto_approve 被夹成 review
- **WHEN** 结构化建草稿路由（面板 / 客户端）收到请求体带 `approvalMode:'auto_approve'`
- **THEN** 系统在创建前把该字段夹成 `review`，任务以必审来源模式入队
- **AND** MUST NOT 因客户端自报而让内容免审直达平台

#### Scenario: 账号策略可在评论授权边界覆盖 review
- **WHEN** 结构化评论任务的客户端体已被夹成 `review`，但执行时账号权威策略为 `auto_approve_all`
- **THEN** Cloud 在授权边界解析有效评论模式为免审并旁路发送通知，MUST NOT 把客户端体当作账号策略事实源

#### Scenario: 结构化精确入口不出确认卡但保留下游授权
- **WHEN** 管理后台对一条精选图文点「洗稿」（`source=console`，服务端自建 intent 传 `review`）
- **THEN** 系统直接确认入队（状态 `queued`），MUST NOT 展示确认卡
- **AND** 其发布 `review` 授权保持不变，下游人审仍强制

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

### Requirement: 委托 worker 并发执行必须有界且准入原子

统一委托 worker SHALL 支持有界的并发执行，使互不冲突的任务不必等待上一条长耗时生成完整收敛。worker 的最大并发 MUST 可配置且默认不得突破发布生成全局默认帽 3。

领取任务、检查 delegated ownership 与 external busy、准备 attempt、标记派发并转为 `executing` 的准入段 MUST 串行完成；只有当前任务已经建立可观察 ownership 后，worker 才能放行下一条准入。执行器的长耗时等待 MAY 并行。系统 MUST NOT 因并发领取使同 lane 两条任务双发，也 MUST NOT 让它们对称观察彼此后双双延后。

`waiting_approval` 的周期对账不是新生成，SHALL 独立进行且 MUST NOT 因另一条兼容 lane 在执行而停止。

#### Scenario: 三条兼容任务并发而各自独立收敛

- **WHEN** worker 依次领取三条 ownership 互不冲突的参照洗稿任务，配置并发为 3
- **THEN** 三条执行器 MAY 同时在途并各自写回 attempt 与任务终态
- **AND** 任一条先收敛 MUST NOT 释放、覆盖或篡改另外两条的 claim 与账本

#### Scenario: 同 lane 并发领取仍只有一条起跑

- **WHEN** 两条 delegated ownership 冲突的任务在相邻 poll 到达
- **THEN** 第一条 SHALL 先建立 executing ownership
- **AND** 第二条 SHALL 观察到该 ownership 后延后
- **AND** MUST NOT 出现两条都执行或两条都因对称冲突而延后的结果

### Requirement: 同环境并发就绪命令必须由单写者队列确定执行顺序

多个委托子命令 MAY 并发准备，但同一 Edge 环境在任一时刻 MUST 只有一个浏览器写任务持有 active lease。当多个请求同时就绪时，系统 SHALL 先按既有任务优先级选择；同优先级请求 SHALL 按 Edge 实际接收申请的单调顺序 FIFO 执行，MUST NOT 并发操作页面，也 MUST NOT 让同优先级任务彼此抢占。

#### Scenario: 两个人工命令几乎同时到达 Edge

- **WHEN** 同一账号的人工发布与人工评论租约请求几乎同时到达 Edge，且两者优先级均为 `human`
- **THEN** Edge SHALL 把先收到的请求授予为唯一 active lease
- **AND** 后收到的请求 SHALL 留在队列中等待前者释放
- **AND** 两个任务 MUST NOT 同时发送页面命令
- **AND** 人工发布 MUST NOT 因等待审批而退化成 `automatic` 后被同批人工评论抢占

#### Scenario: 自动候选的人工审批不改变其原调度档位

- **WHEN** 一个非精确手工 `/publish` 来源的自动候选由运营人工审批
- **THEN** 该候选 SHALL 保持既有 `automatic` Edge 租约优先级
- **AND** 系统 MUST NOT 仅凭“审批动作由人完成”把所有自动候选提升为 `human`

#### Scenario: 同毫秒时间不依赖文本顺序裁决

- **WHEN** 两个同优先级请求具有相同或不可区分的墙钟时间
- **THEN** 系统 SHALL 使用 Edge 单调收包序号作为确定性 tiebreaker
- **AND** MUST NOT 依赖原始分号命令的书写顺序伪造“同时”裁决

### Requirement: 资源等待发生在动作起跑前时不得消耗尝试或失败预算

当执行器能够证明一次延后发生在任何浏览器或平台命令下发之前，系统 SHALL 将其保留为可恢复的排队/延后状态，并 MUST NOT 增加 `attempt_count`、`failure_count` 或 `skipped_count`。资源释放后任务 SHALL 在截止时间内重新竞争执行权；它 MUST NOT 仅因反复等待同一浏览器资源而进入 `max_attempts`。

只有明确标记为“动作未开始”的机器可读结果可以回收临时 attempt。已经发送浏览器命令、进入提交窗口、被抢占或提交结果不明的执行 MUST 保留 attempt 账本并走既有对账/防重复语义。

#### Scenario: 发布占用浏览器时评论排队

- **WHEN** 人工发布持有该账号 Edge lease，而同批人工评论申请执行权
- **THEN** 评论 SHALL 等待或以机器可读的 pre-start defer 重新排队
- **AND** 在零浏览器命令下发的等待期间 `attempt_count`、`failure_count` 与 `skipped_count` SHALL 均保持不变
- **AND** 发布释放后评论 SHALL 在截止时间内自动再次竞争执行权

#### Scenario: 两次 acquire 超时不再产生 max_attempts

- **WHEN** 精确 `/comment` 的两次 Edge acquire 都因另一个合法任务占用而在起跑前超时
- **THEN** 该评论任务 MUST NOT 因默认 `maxAttempts=2` 进入 `max_attempts` 失败
- **AND** 任务 SHALL 保持可恢复延后，直到资源可用、用户取消或任务截止

#### Scenario: 已有副作用可能性的 defer 保留 attempt

- **WHEN** 一个任务已发送浏览器命令后被抢占，或提交结果无法确认
- **THEN** 系统 MUST 保留对应 attempt 账本
- **AND** MUST NOT 把它回收成“从未开始”后自动重试而制造重复发布或重复评论

#### Scenario: 结构性不可执行仍诚实终止

- **WHEN** 子命令因昵称不存在、平台不支持、人设未绑定或缺少必需联系方式而结构上不可执行
- **THEN** 系统 SHALL 独立回报不可执行原因并按既有语义终止
- **AND** MUST NOT 以无限排队掩盖结构性失败

### Requirement: 委托发帖的风控拒绝必须分别展示状态、档位和真实原因

governed 委托发帖在平台动作开始前被风控或配额闸拒绝时，系统 MUST 在已持久化 attempt reason 与用户可见终态回执中分别给出：风控状态 `status`、生效配额档位 `quotaLevel` 与实际拒绝原因。状态和档位 MUST 同时展示稳定英文值及可读中文含义，MUST NOT 再以“风控拒绝（状态 normal）”代替配额原因。

配额拒绝还 MUST 给出命中的 `minute`／`hour`／`day` 窗口、该窗口已用量与生效上限，且这些值 MUST 与同一次 `RiskController.explain()` 判定同源。非 normal 威胁态拒绝 MUST 明确是状态闸，不得伪装成额度已满。未知或历史旧原因 MUST 兼容读取并诚实透传，MUST NOT 猜测补全。

#### Scenario: normal 状态因保守档发布上限为 0 被拒绝

- **WHEN** governed 发帖账号的风控状态为 `normal`、配额档位为 `conservative`，分钟发布已用量为 0 且生效上限为 0
- **THEN** attempt reason SHALL 结构化携带 `status=normal`、`tier=conservative`、`cause=quota:minute`、`used=0`、`limit=0`
- **AND** 用户提示 SHALL 明确表达“风控状态 normal（正常）”“配额档位 conservative（保守）”以及“分钟发布配额 0/0，已达到上限”
- **AND** MUST NOT 只显示“状态 normal”或暗示账号处于平台威胁态

#### Scenario: 非 normal 状态明确显示状态闸与档位

- **WHEN** governed 发帖因 `warned`／`restricted`／`frozen` 状态在配额检查前被拒绝
- **THEN** 用户提示 SHALL 同时显示该风控状态及中文含义、当前配额档位及中文含义
- **AND** SHALL 明确说明本次由风控状态闸暂停发帖，MUST NOT 编造成某个配额窗口已满

#### Scenario: 历史旧原因仍可读

- **WHEN** 终态组装读取到部署前持久化的 `risk_status(<status>)` 或 `risk_denied(status=<status>)`
- **THEN** 系统 SHALL 沿用兼容人话化或原样透传
- **AND** MUST NOT 因缺少档位／窗口字段而抛错、丢失终态卡或虚构字段

### Requirement: worker 重启必须回收上一进程遗留的执行 claim

Cloud 委托 worker 每次启动时 MUST 在接受新任务前回收数据库中属于已退出进程的 `planning` / `executing` claim，MUST NOT 让它们停留到任务 deadline 才释放 ownership。恢复 MUST 写入可审计事件，并保留原状态与旧 claim 事实。

#### Scenario: executing 在 Cloud 重启后进入对账

- **WHEN** Cloud 在一个委托任务处于 `executing` 时重启
- **THEN** 新 worker 在领取普通队列任务前 SHALL 清除旧 claim 并把该任务送入 attempt 对账
- **AND** 该任务 MUST NOT 继续以旧 `executing` 身份占用 ownership

#### Scenario: 当前进程的慢任务不被租约扫描误杀

- **WHEN** 一个真实在跑的生成超过 claim 租约但 Cloud 进程没有重启
- **THEN** worker MUST NOT 仅因租约时刻已过就在周期 poll 中回收该任务

### Requirement: 中断 attempt 必须按派发证据分流

重启恢复 SHALL 使用持久化 attempt 状态区分是否已经派发。`prepared` 证明零派发时 SHALL 撤销临时账本并归还尝试预算；`dispatched` 且缺少可核验终局时 MUST 走结果未知对账并停止盲重试，MUST NOT 编造干净失败或成功。

#### Scenario: prepared attempt 安全返回队列

- **WHEN** 重启遗留任务只有一个 `prepared` attempt，且没有 `dispatched_at`
- **THEN** worker SHALL 丢弃该临时 attempt、归还 attemptCount 并允许任务重新排队
- **AND** MUST NOT 将其描述为已派发或结果未知

#### Scenario: dispatched attempt 无证据时诚实终结

- **WHEN** 重启遗留任务有一个未收敛的 `dispatched` attempt，且执行器无法证明其成功、失败或未动作
- **THEN** worker SHALL 以 `submitted_result_unknown` 诚实终结该 attempt 与任务
- **AND** MUST NOT 自动再派发一次相同动作

### Requirement: Explicit publish rejection is a non-alerting delegated cancellation

当委托发帖进入 `waiting_approval` 后，用户通过受支持的审批入口明确取消或驳回对应候选稿时，系统 SHALL 持久化该决定，并在异步对账中把委托任务收敛为用户取消语义。系统 MUST 保留真实进度和未下发证据，MUST NOT 将该操作报告为发布失败或发送委托层失败/部分完成报警。仅有 `needs_review` 状态而没有明确用户决定证据时，系统 MUST 继续按真实异常失败闭合，不得猜测为用户取消。

#### Scenario: User rejects the only pending publish candidate

- **WHEN** 零成功的委托发帖正在等待候选稿审批，且用户明确取消或驳回该候选稿
- **THEN** 候选稿不向平台下发，委托任务进入 `cancelled`，终态保留用户取消证据，且委托层不发送“发帖任务未成”报警

#### Scenario: User rejects the remaining candidate after earlier success

- **WHEN** 委托任务已有真实发布成功但尚未达到目标，且用户明确取消或驳回当前待审候选稿
- **THEN** 任务保留真实成功数并按既有诚实终态规则收敛，且委托层不发送失败或部分完成报警

#### Scenario: Needs review without user rejection evidence

- **WHEN** 委托对账读取到候选稿为 `needs_review`，但没有持久化的明确用户取消或驳回证据
- **THEN** 系统继续按非重试失败处理并保留既有失败报警，不得把异常静默为用户取消

### Requirement: 委托任务必须绑定可信 Cloud 执行目标

每条委托任务 SHALL 持久化 `executionTarget ∈ {dev,ol}`，表示创建和执行该任务的 Cloud 部署目标。该字段 MUST 由服务端当前运行目标注入，MUST NOT 从客户端请求体、自然语言、命令参数、`envKey`、`sourceRef` 或其他用户可控字段派生或覆盖。

业务来源 `source`、来源引用 `sourceRef`、来源会话 `originChatId` 与 Cloud 执行目标是不同概念，系统 MUST NOT 复用其中任一字段替代 `executionTarget`。

#### Scenario: dev 客户端创建精选创作任务
- **WHEN** dev Cloud 收到已鉴权客户对某环境发起的精选创作请求
- **THEN** 新任务 SHALL 持久化 `executionTarget=dev`
- **AND** 请求体即使携带伪造 target 字段也 MUST NOT 改变该值

#### Scenario: Cloud target 缺失时拒绝装配委托能力
- **WHEN** Cloud 启动时部署目标缺失或不属于 `dev | ol`
- **THEN** 委托任务创建服务和 worker SHALL fail-closed 不可用并留下明确运行日志
- **AND** MUST NOT 猜测或默认该进程为 dev

### Requirement: 委托任务的生命周期必须按 Cloud 执行目标隔离

任务创建去重、读取、列表、精选内容“已创作/未创作”投影、确认、暂停、恢复、取消、ownership 判断、worker 领取、启动中断恢复和到期收敛 SHALL 只处理与当前 Cloud `executionTarget` 一致的任务。一个 Cloud worker MUST NOT 领取、恢复、改变或终结另一个 target 的任务，即使两者共享 PostgreSQL、账号 id、动作、截止时间或去重键。任何依赖委托任务数据的旁路投影在 target 缺失时 SHALL fail-closed，不得执行跨目标查询或猜测为 dev。

同一 target 内的活跃任务去重语义 SHALL 保持不变；不同 target 的相同业务请求 MUST NOT 因共享唯一索引互相去重。

#### Scenario: ol worker 观察到 dev 排队任务
- **WHEN** 共享数据库中存在 `executionTarget=dev` 的 queued 任务，而 ol worker 轮询队列
- **THEN** ol worker SHALL 跳过该任务且不得写入 claim
- **AND** dev worker SHALL 仍可按既有优先级领取该任务

#### Scenario: ol 启动不恢复 dev 的执行中任务
- **WHEN** ol Cloud 重启，而共享数据库中有 `executionTarget=dev` 的 planning 或 executing 任务
- **THEN** ol 的启动恢复 SHALL 不修改这些任务的状态、claim、attempt 或事件

#### Scenario: 两个 target 的相同请求分别幂等
- **WHEN** dev 与 ol 对同一账号创建业务字段及业务去重键相同的任务
- **THEN** 两个 target SHALL 各自保留一条任务
- **AND** 每个 target 内重复创建仍 SHALL 返回本 target 的同一活跃任务

#### Scenario: dev 控制请求不能改变 ol 任务
- **WHEN** dev 的任务查询或控制入口收到一个只存在于 `executionTarget=ol` 的 task id
- **THEN** 系统 SHALL 按本 target 不存在处理
- **AND** MUST NOT 暴露或修改 ol 任务真态

### Requirement: 历史委托任务必须安全回填为 dev

部署本变更前已存在且没有 Cloud 执行目标的所有委托任务 SHALL 幂等回填为 `dev`。回填 MUST 保留任务 id、账号、业务来源、状态、版本、进度、claim、终态、时间戳、attempt 与事件，不得把历史任务重新排队、重新执行或改写业务结论。

回填完成后 `executionTarget` MUST 非空且只允许 `dev | ol`；新任务写入 MUST 显式提供服务端 target，数据库不得依靠永久默认值把未知来源静默归入 dev。

#### Scenario: 旧任务启动迁移
- **WHEN** schema 升级发现没有执行目标的历史委托任务
- **THEN** 系统 SHALL 将这些行的执行目标设为 dev
- **AND** 迁移前后任务总数、各业务状态计数和 attempt 数量 SHALL 保持一致

#### Scenario: 重复启动迁移幂等
- **WHEN** 已完成回填的 Cloud 再次启动并执行同一 schema 自愈
- **THEN** 已有 dev/ol target SHALL 保持不变
- **AND** MUST NOT 再次改变任务状态、版本、claim 或时间戳

