# publish-dispatch-resilience Specification

## Purpose
TBD - created by archiving change parallel-rewrite-drafts. Update Purpose after archive.
## Requirements
### Requirement: 下发失败按副作用分界——离线回待审，序列失败终态

下发失败处理 SHALL 按「是否已对平台产生副作用」分界，且分界 SHALL 细到**三档**，MUST NOT 把前两档并进第三档。

**分档的第一级判据 SHALL 是「提交指令有没有推出去」，MUST NOT 是失败原因串。** 该标志
SHALL 在推送提交指令**之前**置位。仅凭「云端没收到成功回执」MUST NOT 被当作「那一下没按下去」的证据——
提交指令已推送而回执超时或边缘断连时，两者都为假，而平台可能已经收下。判据搞错方向即构成一条双发路径。

1. **零副作用 · 可恢复**——提交指令确定未推出，且**无法证明重来结果必然相同**
   （边缘离线、被严格高档位抢占、提交前的导航/就绪/探测类失败、**配图全部失败**、
   以及**未识别的提交前原因**）：草稿回 `pending_approval` + **保留授权**
   （离线档按既有约定作废该次授权信号并通知重批）+ 素材归还而非隔离 + **不计熔断** + 事件驱动重投。
   关掉「批准后恰逢一次抖动即烧稿」的窗口、保住生成与生图成本。
   配图全部失败归此档：它由逐张上传失败累计而来，典型成因是图源侧系统性瞬态而非稿件本身不可发。
2. **零副作用 · 结构性**——提交指令确定未推出，且**重来必然同样结果**（正文超长、未授权、排期非法）：
   落 `failed` 终态，MUST NOT 自动重投，回执 SHALL 写清「为什么重来也不会变」。
3. **页面状态未知**——提交指令已推出（无论是否拿到回执）、或控制面故障导致无法证明未推出
   （含卡死写者不停手）：保持 `failed` 终态处置，MUST NOT 自动重试（自动重跑有重复发帖风险）。

第 1 档的自动重投 SHALL 有界（默认 2，env 可配）；耗尽后落 `failed` 终态，且通知与日志
SHALL 表述为「重试 N 次未成」而非「做不到」。该重投计数 MUST 只由第 1 档的失败消费，
MUST NOT 被抢占重投或槽位等待重试递减。

提交前失败的分档 MUST NOT 存在「其余全归它」的兜底返回值：未被任何具名档接住的原因
SHALL 以具名的「未识别提交前原因」露出、按第 1 档处置，并把原始原因串带进日志。

三条路径都 MUST 如实通知，绝不静默。

#### Scenario: 离线失败草稿可重批
- **WHEN** 授权到达时该账号无在线边缘节点
- **THEN** 草稿回到待审、该次授权信号被作废、运营收到「边缘离线请稍后重批」通知；边缘恢复后重批即可下发，内容零重生成

#### Scenario: 提交前抖动不烧稿
- **WHEN** 发布序列在提交动作派发**之前**因导航失败 / 页面未就绪 / 探测超时而中断，且序列器已证明提交点未跨过
- **THEN** 草稿保持 `pending_approval`、授权签名保留、Facebook 素材归还而非隔离、**不计入下发熔断**，并由事件驱动自动重投

#### Scenario: 未识别的提交前原因不落终态
- **WHEN** 提交前失败带一个当前分档表未收录的原因串，且序列器已证明提交点未跨过
- **THEN** 该次失败 SHALL 按可恢复档处置并有界重投，日志 SHALL 具名标注「未识别提交前原因」并带上原始串；MUST NOT 被折进任何已有的终局失败值

#### Scenario: 可恢复重投有上限
- **WHEN** 同一草稿的可恢复提交前失败连续发生并耗尽重投上限
- **THEN** 草稿落 `failed` 终态，通知与日志表述为「重试 N 次未成」，MUST NOT 表述为「做不到」

#### Scenario: 结构性提交前失败仍是终态
- **WHEN** 提交前失败原因为正文超长 / 配图全部失败 / 未通过授权
- **THEN** 草稿落 `failed` 终态且 MUST NOT 自动重投，回执写清重来也不会改变结果

#### Scenario: 序列失败不自动重跑
- **WHEN** 发布指令序列执行到中途失败（如选择器落空），或提交动作已派发但未拿到确认
- **THEN** 该草稿判 `failed` 终态并如实通知；MUST NOT 对同一草稿自动重跑整条序列

### Requirement: 同账号连续下发失败熔断，人工重批确认清除

同一账号连续 N 次（默认 2，env 可配）**「页面状态未知」档**的下发失败 SHALL 触发该账号下发熔断：
停止 drain 该账号已批队列（兜底扫描跳过、新下发拒绝且 MUST NOT 消耗授权信号）+ 发飞书告警——
防一次系统性边缘故障连环烧掉整批获批草稿（自愈不自残；多稿同窗获批无间隔节流的现状下，熔断是防连环烧的唯一闸）。

**零副作用档（可恢复与结构性）MUST NOT 计入熔断计数**，但两者的理由不同，不得混为一谈：

- **可恢复档不烧稿**——草稿留在待审、授权保留，计熔断只会让一次网络抖动停掉整批已批准草稿、
  要求运营重新逐条批准。
- **结构性档确实烧稿，但停整批 drain 救不了任何一稿**——该档剩余成员（正文超长、未授权、排期非法）
  都是**单稿自身属性**，不是系统性故障；停 drain 只是把一批本来能发的好稿也一起挡住。
  凡成因可能是系统性瞬态的（如配图全部失败）SHALL 归可恢复档，不留在结构性档。

熔断守的是「一次系统性边缘故障连环烧掉整批获批草稿」——因此它只计「页面状态未知」这一档。

熔断清除 MUST 接通人工确认路径且不得死锁：对熔断中账号的**任一**批准动作（含对已批草稿重复点击批准、
命中 first-writer-wins 已决分支的情形）SHALL 视为人工确认、清除熔断并触发一次兜底扫描；
熔断计数为内存态，重启即清（故障未修复时最多再烧 N 篇后重新熔断，有界代价）。

#### Scenario: 连续两败停链告警
- **WHEN** 某账号两份草稿的下发接连以「页面状态未知」档失败
- **THEN** 第三份已批草稿不被自动下发（授权信号保留不烧），飞书收到熔断告警说明账号与原因

#### Scenario: 提交前抖动不触发熔断
- **WHEN** 某账号连续多份草稿都在提交点之前失败且已证明零派发
- **THEN** 熔断计数不递增，该账号已批队列继续 drain，MUST NOT 因此要求运营重新批准整批草稿

#### Scenario: 重批清熔断恢复下发
- **WHEN** 运营排除边缘故障后，对该账号任一草稿再次点击批准（即使其授权信号已存在、走已决分支）
- **THEN** 熔断清除、兜底扫描恢复 drain 该账号已批队列；MUST NOT 出现「批了也不发、又无路可清熔断」的死锁

### Requirement: 兜底扫描不被单账号下发阻塞

已批草稿的兜底扫描 SHALL 对逐条下发采用发起即返回（fire-and-forget，幂等由既有在途去重与账号链尾保证），MUST NOT 串行等待单条下发完成——多稿同窗获批时一个账号的多篇背靠背下发（每篇 1-3 分钟）会拖死跨账号的整轮扫描。

#### Scenario: 一账号连发不拖累他账号
- **WHEN** 账号 A 的多份已批草稿在链尾逐篇下发中，兜底扫描同时发现账号 B 有已批草稿
- **THEN** B 的下发即时推进，不等 A 的队列清空

### Requirement: 授权仍是发布的必要条件（AC-PUB 契约重述）

引入熔断与离线回待审后，「授权通过即下发」契约 SHALL 重述为「授权通过即下发；熔断中授权保留不烧、人工确认后恢复」——授权 MUST 仍是发布的必要条件，无 `approved === true` 永不下发；熔断与回待审只能**延后或阻止**发布，MUST NOT 使任何未授权内容被发布，也 MUST NOT 静默丢弃有效授权（熔断挂起 / 信号作废均如实可见）。相关验收断言 MUST 按新契约重述而非删除。

#### Scenario: 韧性机制不放行未授权
- **WHEN** 审视熔断挂起、清除恢复与离线回待审的全部代码路径
- **THEN** 每条真正驱动边缘发布的路径都以有效授权信号 + 版本一致为前提；韧性机制不引入任何绕过人审的旁路

### Requirement: 同窗多批背靠背连发登记为已知缺口

同账号多份草稿同窗获批时下发按账号链尾**无间隔**背靠背连发（每篇 1-3 分钟）——最小发布间隔机制经产品定案本期不建，节奏暂由运营错峰批准自行控制。该行为 SHALL 在运营侧文档如实登记为已知缺口（含平台侧连发行为指纹风险与「后续按需补间隔机制」的路线），MUST NOT 被表述为已有节流保护。

#### Scenario: 缺口如实可见
- **WHEN** 运营查阅多稿挑选发布的使用说明 / 交接文档
- **THEN** 「同窗批准多张会背靠背连发、请自行错峰批准」被明确写出，不被遗漏或美化

### Requirement: Browser-control-unavailable publish acquisition SHALL requeue truthfully

When cloud receives `task.released{reason:'cdp_unhealthy'}` while acquiring a publish lease, it SHALL fail acquisition immediately with a distinct browser-control-unavailable result. The publish dispatcher SHALL invalidate that authorization, return the draft to pending approval, and send an operator notice stating that the client may still be online but browser control is unavailable and no publish command was dispatched. It MUST NOT describe this result as edge offline, a normal acquire timeout, or a failed publish sequence.

#### Scenario: Connected edge rejects a publish lease because CDP is unhealthy
- **WHEN** a publish lease receives `cdp_unhealthy` before `task.acquired`
- **THEN** the draft returns to pending approval, the authorization is invalidated, the notice confirms no publish command was sent, and re-approval is required after browser control recovers

#### Scenario: Existing acquisition failures remain distinct
- **WHEN** a lease fails because no edge is online, normal acquisition times out, or a publish sequence fails after acquisition
- **THEN** cloud preserves the existing offline, acquire-timeout, and post-acquire failure semantics rather than reporting `cdp_unhealthy`

### Requirement: 浏览器槽位等待 SHALL 保留发布授权并自动重试

当发布租约在任何发布业务命令下发前收到 `browser_wake_failed` 时，Cloud SHALL 将其视为可恢复的浏览器槽位/唤醒等待：草稿 MUST 保持 `pending_approval`，有效授权信号 MUST 保留，MUST NOT 计入发布序列失败或熔断，并 SHALL 由既有已批准草稿补偿扫描再次尝试。该行为 MUST NOT 绕过 `approved === true` 与内容版本一致闸。

#### Scenario: 槽位已满时保留授权等待
- **WHEN** 目标客户端在线、目标浏览器缺席且本机槽位暂时已满，发布 lease 在零发布命令阶段收到 `browser_wake_failed`
- **THEN** 草稿保持待审、授权保留、没有发布命令下发，操作员看到“已批准，等待浏览器槽位，稍后自动重试”

#### Scenario: 浏览器稍后启动后自动发布
- **WHEN** 上述环境仍在本地 FIFO 队列中并在其他浏览器让出槽位后启动
- **THEN** 既有补偿扫描重新取得 lease，并在再次校验授权和内容版本后只执行一次发布序列，无需重新批准

#### Scenario: Cloud 重启后恢复等待发布
- **WHEN** Cloud 在 `browser_wake_failed` 后、成功取得 lease 前重启
- **THEN** 持久待审草稿与授权信号仍能被补偿扫描发现，发布等待继续，MUST NOT 因进程内队列丢失而静默遗失

### Requirement: 槽位等待重试 MUST 保持失败分类与副作用边界

只有明确的 `browser_wake_failed` 可以保留授权自动重试。真实无在线 Edge、`cdp_unhealthy`、正常 `acquire_timeout`、控制面故障及任何发布序列已经开始后的失败 SHALL 保持既有作废授权、人工处理或未知结果语义，MUST NOT 被重新标记为槽位等待。

#### Scenario: acquire 无响应不伪装成槽位等待
- **WHEN** Cloud 已发送 acquire 但直到 Cloud 超时仍未收到 acquired 或 `browser_wake_failed`
- **THEN** dispatcher 保持既有 `acquire_timeout_requeued` 语义，作废授权并要求重批，MUST NOT 自动延后发布

#### Scenario: 发布序列开始后绝不因槽位机制重跑
- **WHEN** lease 已取得且发布序列已经开始，随后页面写入失败或提交结果未知
- **THEN** dispatcher 按既有失败/未知结果契约收敛，MUST NOT 保留授权后自动重跑整个序列

### Requirement: 浏览器槽位等待通知 SHALL 有界去重

同一发布记录在同一 Cloud 进程内连续因 `browser_wake_failed` 被补偿扫描重试时，dispatcher SHALL 只在首次进入该等待状态时通知操作员；成功取得 lease 或记录不再可下发后 SHALL 清除该去重状态。进程重启后 MAY 再通知一次恢复上下文，但 MUST NOT 在每个扫描周期重复刷屏。

#### Scenario: 周期扫描不重复通知
- **WHEN** 同一已批草稿连续三轮扫描都收到 `browser_wake_failed`
- **THEN** 操作员只收到一条等待槽位通知，三次都不作废授权且不计熔断

#### Scenario: 取得 lease 后重新武装
- **WHEN** 草稿等待后成功取得 lease，之后因新的独立发布生命周期再次进入槽位等待
- **THEN** 旧去重标记已清除，新等待可以产生一条新的诚实通知

### Requirement: 批准后跨进程 trigger SHALL 只返回短应答

API 在批准决策落库后 SHALL 通过版本化内部 HTTP 端口向 automation 发送发布触发，请求 MUST 携带 `requestId`、授权 `revision`、`executionTarget` 与 `kind`；`kind` 只能是首写授权的 `decision_recorded` 或已决授权上的人工重批 `human_reconfirm`。automation SHALL 在完成版本、target、请求字段校验并受理唤醒或识别重复后立即返回 `accepted` 或 `duplicate`，MUST NOT 等待 dispatcher、Edge 指令、平台提交或平台发布完成。

`accepted` 与 `duplicate` 只表示本次内部 trigger 已受理或已去重，MUST NOT 被映射或展示为 `dispatching`、`submitted`、`published` 或任何发布成功状态；网络超时或非成功响应同样 MUST NOT 被改写成发布失败或发布成功。

#### Scenario: 首次 trigger 快速受理
- **WHEN** API 为本环境一条新落库的批准决策发送 `decision_recorded`，automation 完成请求校验并登记一次唤醒
- **THEN** automation 返回 `accepted`，响应不等待该草稿真正下发，草稿的 dispatch、submit 与 publish 状态保持由各自持久生命周期决定

#### Scenario: 重复 trigger 不冒充下发
- **WHEN** API 因 HTTP 结果未知而重发同一 `requestId + revision + decision_recorded`
- **THEN** automation 返回 `accepted` 或 `duplicate` 且只保留一次等价唤醒，调用方 MUST NOT 因任一短应答把草稿标为已下发、已提交或已发布

#### Scenario: target 不匹配时拒绝受理
- **WHEN** trigger 的 `executionTarget` 与 automation 本地目标不一致或本地目标缺失无效
- **THEN** automation 拒绝受理且不唤醒 dispatcher，MUST NOT 返回 `accepted` 或 `duplicate`

### Requirement: 直接 trigger SHALL 只是持久授权补偿链的低延迟加速器

`publish_approval_decision`、与批准决策同事务写入的 `PublishApproved` outbox，以及按本地 `executionTarget` 过滤的 pending-approval scan SHALL 继续承担不丢任务与重启恢复。直接 HTTP trigger 只能缩短正常路径延迟，MUST NOT 成为授权事实、唯一投递通道或删除持久补偿扫描的理由。

直接 trigger 失败或结果未知时，API MUST 保留已经提交的授权决策与 outbox；automation MUST 能通过 outbox 消费或 pending scan 重新发现仍可下发的授权。补偿路径在真正驱动发布前 MUST 重新校验授权 revision、内容版本与本地 target，MUST NOT 因曾经收到 trigger 而绕过这些闸门。

#### Scenario: trigger 丢失后由持久链补投
- **WHEN** 批准决策与 `PublishApproved` outbox 已在同一事务提交，但 API 到 automation 的直接 trigger 在送达前断链
- **THEN** 授权不回滚且不被标为发布失败，automation 随后通过 outbox 或 target-filtered pending scan 发现该授权，并在重校验后推进一次等价下发

#### Scenario: automation 重启不丢已批草稿
- **WHEN** automation 在直接 trigger 受理后、真正下发前重启
- **THEN** 进程内唤醒丢失不影响持久授权，重启后的 pending scan 仍能恢复该草稿，且短应答本身不被当作已消费证据

### Requirement: 首写授权与人工重批 trigger SHALL 保持不同语义

API SHALL 对首次写入授权的路径发送 `decision_recorded`，对人工操作者再次批准一条已经 first-writer-wins 决定的授权发送 `human_reconfirm`。automation MUST NOT 仅以 `requestId + revision` 的首写去重吞掉 `human_reconfirm`；每次有效人工重批 SHALL 执行幂等的账号熔断清除并唤醒一次 pending scan，即使同一 revision 的 `decision_recorded` 已经处理。

自动批准只能产生 `decision_recorded`，MUST NOT 伪造 `human_reconfirm`，也 MUST NOT 清除账号下发熔断。HTTP 重试可以重复执行幂等唤醒，但 MUST NOT 重复消费授权或启动并行发布序列。

#### Scenario: 已决授权上的人工重批清除熔断
- **WHEN** 账号处于下发熔断中，运营再次批准一条已经存在同 revision 授权的草稿
- **THEN** API 发送 `human_reconfirm`，automation 不被既有 `decision_recorded` 去重挡住，幂等清除该账号熔断并触发 pending scan，同时仍由持久授权与版本校验决定哪些草稿可以下发

#### Scenario: 自动批准不得清除熔断
- **WHEN** 自动批准为熔断中账号写入新授权并发送 `decision_recorded`
- **THEN** automation 可以记录唤醒但保持该账号熔断，授权信号继续持久挂起且不被消费，直到后续有效人工重批明确清除熔断

#### Scenario: 人工重批重试不产生并行发布
- **WHEN** 同一次人工重批因 HTTP 结果未知被重复投递
- **THEN** 熔断清除与 scan 唤醒保持幂等，既有在途去重与账号链仍保证同一授权不会启动并行发布序列

### Requirement: publish approval authority SHALL 通过内部 HTTP 暴露 revision CAS

API 作为 publish approval authority 的所有者 SHALL 通过版本化、内部鉴权且 target 隔离的 HTTP 端口提供 `getApproval`、`listPendingDispatch`、`voidApproval`、`markDispatching`、`markConsumed`、`releaseToPending` 与 `setBlockedReason`；automation MUST 通过该端口读取和推进授权，MUST NOT 直接连接或写入 API 的授权表。

每个状态推进请求 MUST 携带 `requestId`、期望 `revision` 与 `executionTarget`，API 只能在当前有效授权的 revision 和 target 同时匹配时执行条件更新。revision 冲突、记录不存在、target 不匹配、authority 不可达与 transport 结果未知 MUST 保持可区分，MUST NOT 被折叠为空列表、默认授权、成功推进或发布终态。

#### Scenario: 当前 revision 推进成功
- **WHEN** automation 对本地 target 的有效授权以匹配 revision 调用 `markDispatching`
- **THEN** API 原子推进该 revision 并返回更新后真态，automation 才能继续相应下发阶段

#### Scenario: 旧 revision CAS 不修改新授权
- **WHEN** automation 使用过期 revision 调用 `voidApproval`、`markConsumed`、`releaseToPending` 或 `setBlockedReason`
- **THEN** API 返回可识别的 revision conflict，当前新 revision 保持不变，automation MUST 重新读取授权而不是把冲突当成功

#### Scenario: authority 不可读时不可逆发布 fail closed
- **WHEN** automation 在驱动不可逆平台动作前无法从 approval authority 读取有效授权，或读取结果为 transport unknown
- **THEN** automation 不下发平台发布命令、不伪造授权或终态，并保留可补偿状态与可观测错误供后续重试或人工处理

#### Scenario: 另一 target 的旧全局唯一键冲突不得串用授权
- **WHEN** approval 首写被现存全局 `requestId` 唯一键拒绝，且按本地 `executionTarget` 查不到活跃授权
- **THEN** API 以稳定错误 fail closed，不得返回另一 target 的 `alreadyDecided` 或 revision，也不得据此发送 `human_reconfirm`
- **AND** 解除该跨 target liveness gap 的物理键替换必须作为独立 contract migration 交付，MUST NOT 混入本 change 的 expand migration

