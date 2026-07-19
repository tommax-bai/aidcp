# publish-dispatch-resilience Specification

## Purpose
TBD - created by archiving change parallel-rewrite-drafts. Update Purpose after archive.
## Requirements
### Requirement: 下发失败按副作用分界——离线回待审，序列失败终态

下发失败处理 SHALL 按「是否已对边缘产生副作用」分界：**边缘离线**（指令未发出、零副作用）→ 草稿回 `pending_approval` + 作废该次授权信号 + 通知重批——关掉「批准后恰逢离线即烧稿」的窗口、保住生成与生图成本；**指令序列中途失败**（页面状态未知）→ 保持 `failed` 终态，MUST NOT 自动重试（自动重跑有重复发帖风险）。两条路径都 MUST 如实通知，绝不静默。

#### Scenario: 离线失败草稿可重批
- **WHEN** 授权到达时该账号无在线边缘节点
- **THEN** 草稿回到待审、该次授权信号被作废、运营收到「边缘离线请稍后重批」通知；边缘恢复后重批即可下发，内容零重生成

#### Scenario: 序列失败不自动重跑
- **WHEN** 发布指令序列执行到中途失败（如选择器落空）
- **THEN** 该草稿判 `failed` 终态并如实通知；MUST NOT 对同一草稿自动重跑整条序列

### Requirement: 同账号连续下发失败熔断，人工重批确认清除

同一账号连续 N 次（默认 2，env 可配）序列执行失败 SHALL 触发该账号下发熔断：停止 drain 该账号已批队列（兜底扫描跳过、新下发拒绝且 MUST NOT 消耗授权信号）+ 发飞书告警——防一次系统性边缘故障连环烧掉整批获批草稿（自愈不自残；多稿同窗获批无间隔节流的现状下，熔断是防连环烧的唯一闸）。熔断清除 MUST 接通人工确认路径且不得死锁：对熔断中账号的**任一**批准动作（含对已批草稿重复点击批准、命中 first-writer-wins 已决分支的情形）SHALL 视为人工确认、清除熔断并触发一次兜底扫描；熔断计数为内存态，重启即清（故障未修复时最多再烧 N 篇后重新熔断，有界代价）。

#### Scenario: 连续两败停链告警
- **WHEN** 某账号两份草稿的下发接连序列失败
- **THEN** 第三份已批草稿不被自动下发（授权信号保留不烧），飞书收到熔断告警说明账号与原因

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

When cloud receives `edge.task.released{reason:'cdp_unhealthy'}` while acquiring a publish lease, it SHALL fail acquisition immediately with a distinct browser-control-unavailable result. The publish dispatcher SHALL invalidate that authorization, return the draft to pending approval, and send an operator notice stating that the client may still be online but browser control is unavailable and no publish command was dispatched. It MUST NOT describe this result as edge offline, a normal acquire timeout, or a failed publish sequence.

#### Scenario: Connected edge rejects a publish lease because CDP is unhealthy
- **WHEN** a publish lease receives `cdp_unhealthy` before `edge.task.acquired`
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

