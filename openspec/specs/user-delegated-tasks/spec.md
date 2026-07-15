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

### Requirement: 公共写操作必须先结构化确认

自然语言、Edge 快捷入口和 console 行级动作等公共写入口 SHALL 先创建 `awaiting_confirmation` 任务并展示结构化确认摘要；只有带 task id 与当前版本的明确确认才能进入 `queued`。重复确认 MUST 幂等返回当前真态，MUST NOT 重复入队。任务创建时 SHALL 从账号事实源回读平台，调用方自报平台不一致 MUST 拒绝。

#### Scenario: 重复点击确认不产生双任务
- **WHEN** 用户对同一确认卡重复点击“确认执行”
- **THEN** 只有第一次有效版本转换为 `queued`
- **AND** 后续点击返回同一 task id 的当前状态，不新增执行

#### Scenario: 平台事实不一致时拒绝
- **WHEN** 入口把 Facebook 账号声明为小红书以请求小红书定向评论
- **THEN** 系统以 accounts 平台事实源拒绝该草稿或确认
- **AND** MUST NOT 将任务路由到另一平台执行器

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

单次旧人工命令 MAY 保留既有 manual override；`targetSuccessCount>1`、跨账号或异步委托 MUST 使用自动化额度与风险闸，MUST NOT 为每次 attempt 传 `manualOverride=true`。RiskController SHALL 继续是账号风险状态唯一写者。公开评论和发布默认 SHALL 使用 `review`，除非既有受控配置明确允许其他模式。

#### Scenario: 批量评论不能循环绕额度
- **WHEN** 用户确认一个 5 条评论的委托任务
- **THEN** 每次评论尝试按自动化路径检查风险/配额且 `manualOverride=false`
- **AND** 额度不足时任务 deferred 或诚实部分完成，不得循环伪装成五次单次人工命令

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

