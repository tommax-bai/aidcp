# edge-task-execution-coordination Specification

## Purpose
TBD - created by archiving change edge-task-execution-coordinator. Update Purpose after archive.
## Requirements
### Requirement: 同一 edge/CDP 由任务级租约单写

系统 SHALL 以 `edgeId/CDP` 为边界维护唯一页面写执行权。浏览、发布、评论、通知巡视、加群以及会触发导航/点击/输入/滚动的恢复动作 MUST 经同一边缘任务协调器；任一时刻至多一个独占任务持有租约。只读探针 MAY 不持租约，但一旦需要页面写动作 MUST 升级成任务，MUST NOT 从旁路直接写 CDP。

#### Scenario: 发布与评论不交错
- **WHEN** 同一 edge 的发布任务正在持有租约，同时收到评论任务申请
- **THEN** 评论任务排队等待，发布从第一条到最后一条命令之间不出现评论或普通浏览写动作

#### Scenario: 两个发布命令按任务而非原子动作交错
- **WHEN** 同一 edge 同时有发布正文 A 与另一发布正文 B
- **THEN** A/B 按任务顺序整段执行，MUST NOT 出现 `A.navigate_entry → B.navigate_entry → A.select_mode` 的原子命令交错

#### Scenario: 只读探针触发恢复须升级
- **WHEN** 只读 watcher 发现页面需要重新导航或点击恢复
- **THEN** 恢复动作申请 `system_recovery` 租约后执行，MUST NOT 以 watcher 名义绕过协调器写页面

### Requirement: cloud 必须等待 edge acquired/quiesced 再发首条业务命令

protocol v2 SHALL 提供 `edge.task.acquire`、`edge.task.acquired`、`edge.task.release`、`edge.task.released`。cloud 发出 acquire 后 MUST 等 edge 回 `acquired`；该回执同时表示当前浏览原子动作已到安全边界、未开始的普通浏览命令已取消且租约已经生效。未收到 acquired 时 MUST NOT 下发该任务第一条业务命令。每个 acquire MUST 携可选的本地等待时长；edge MUST 从收到申请起在该时长内完成 quiesce 并授予租约，逾期仍未授予时 MUST 取消该排队申请，MUST NOT 在 cloud 已超时后再授予无主租约。

#### Scenario: 在途 navigation.back 先收尾
- **WHEN** `navigation.back` 已在 edge 执行中，cloud 申请发布租约
- **THEN** edge 等该原子动作收敛到安全边界后才回 `edge.task.acquired`，cloud 随后才发 `navigate_entry`

#### Scenario: acquire 超时不越权发布
- **WHEN** 目标 edge 离线、协议过旧或在超时内未回 acquired
- **THEN** 发布/评论任务诚实失败或保持可重试状态，且零条业务写命令被下发，MUST NOT 回退到无租约执行

#### Scenario: edge 等待期届满不授予陈旧任务
- **WHEN** 普通浏览原子动作持续到 acquire 的本地等待上限之后
- **THEN** edge 移除该未获授任务、回到可继续协调的状态，MUST NOT 在上限之后发送 `acquired` 或持有该任务租约

### Requirement: 抢占浏览取消陈旧待执行命令而非排空队列

普通浏览 SHALL 是低优先级、可抢占执行流。独占任务申请到达时，edge MUST 允许已经开始的原子动作完成或在其定义的安全取消点中止；所有尚未开始且不属于当前租约的普通浏览命令 MUST 被取消，MUST NOT 为了“FIFO”先排空旧浏览队列。任务释放后 MUST 依据当前真实页面重新上报并由 cloud 重决策，MUST NOT 重放被取消的旧命令。

#### Scenario: 队列中旧滚动被取消
- **WHEN** 当前动作执行中且队列还等待 `page.scroll`、`navigation.back`，此时发布申请租约
- **THEN** 当前动作到安全边界后发布获租约，两个未开始命令被取消且释放后不重放

#### Scenario: 释放后以新快照恢复
- **WHEN** 独占任务结束且没有下一独占任务等待
- **THEN** edge 回到可浏览页面、上报新 `page.cards`/页面快照，cloud 基于新状态生成后续动作

### Requirement: 任务命令必须归属于当前租约

独占任务的每条页面写命令 SHALL 携 `taskId`。edge MUST 只执行 `taskId` 等于当前租约所有者的命令；无 `taskId`、错 `taskId`、已释放或已过期租约的命令 MUST 被拒绝或丢弃并留下可观测失败，MUST NOT 改写页面。发布原子命令 MUST 返回明确失败结果；无逐命令回执的浏览协议命令由 cloud 有界等待超时收敛为失败。

#### Scenario: 迟到的发布命令不污染下一任务
- **WHEN** 发布 A 已释放，发布 B 已获租约，随后到达 A 的迟到 `publish.command`
- **THEN** edge 返回 `task_lease_mismatch` 且不执行该命令，B 的页面状态不被污染

#### Scenario: 租约期间普通浏览命令被挡住
- **WHEN** 发布租约有效时到达一个没有 `taskId` 的 `page.scroll`
- **THEN** edge 不执行、不入待重放队列并记录被租约抑制，发布序列继续独占

### Requirement: 任务优先级与同级 FIFO 可预测

协调器 SHALL 至少支持 `system_recovery`、`human`、`automatic` 三档优先级，顺序为系统恢复高于人工任务、人工任务高于自动任务；同优先级 MUST 按 edge 收到 acquire 的顺序 FIFO。正在执行且已产生副作用的独占任务 MUST NOT 被另一业务任务强杀；高优先级只影响下一次授予顺序。

#### Scenario: 人工评论先于排期发布
- **WHEN** edge 当前任务释放时队列中同时等待人工评论与自动排期发布
- **THEN** 人工评论先获得租约，自动发布继续等待

#### Scenario: 两个人工任务 FIFO
- **WHEN** 人工批准的发布正文先申请、人工批准的评论后申请且优先级相同
- **THEN** 发布正文先完整执行，评论随后执行

#### Scenario: 恢复任务不强杀已提交动作
- **WHEN** 系统恢复申请到达时当前发布原子动作已点击提交并正在校验
- **THEN** 当前原子动作先在安全边界收敛，系统恢复成为下一授予任务，MUST NOT 在提交中途导航离开

### Requirement: 发布完整序列持有同一租约

发布任务 SHALL 从 `navigate_entry` 开始，到上传、填充、元数据、`submit_publish` 与提交后捕获结束，全程持有同一个 `taskId`。既有同账号 `accountTail` 串行 MUST 保留；它负责业务顺序，edge 租约负责同 CDP 跨任务互斥。发布已真实提交后 MUST 继续遵守“后续超时不得翻成 failed”的既有红线。

#### Scenario: 浏览不能插入发布原子序列
- **WHEN** 发布已执行 `navigate_entry`、尚未执行 `select_mode`
- **THEN** 普通浏览、评论 prepare、通知巡视均不能获得执行权或改写页面，直到该发布释放租约

#### Scenario: 同账号连续发布仍按序
- **WHEN** 同账号两篇已批准草稿进入派发
- **THEN** 既有 `accountTail` 保证业务 FIFO，每篇分别持有完整 edge 租约，前一篇释放后后一篇才发送首命令

### Requirement: 评论人审前后分段持有租约

小红书评论任务 SHALL 把边缘写操作拆为 prepare 与 commit 两个租约阶段。prepare 负责搜索/定位/打开/读取并产出稳定 `noteId` 快照；cloud 的候选甄选、LLM 撰写、去 AI 味和飞书人审期间 MUST 释放边缘租约；仅在 approved 后申请 commit 租约，按稳定 `noteId` 重新打开并复检目标/去重状态后提交。拒绝或超时 MUST NOT 申请 commit。

#### Scenario: 人审等待不占浏览器
- **WHEN** 评论 prepare 已获得目标快照并进入飞书人审等待
- **THEN** prepare 租约已经释放，edge 可继续浏览或执行其他排队任务

#### Scenario: approved 后重开复检再评论
- **WHEN** 人审批准时 edge 已浏览到别的页面
- **THEN** commit 重新获租约，按稳定 noteId 重开并校验目标后才发评论，MUST NOT 对当前随机页面提交

#### Scenario: 目标变化诚实失败
- **WHEN** 人审期间目标被删除、不可达或去重账本已显示评论过
- **THEN** commit 不提交并诚实回目标不可用/已处理，MUST NOT 按旧 DOM 位置或当前页面兜底

### Requirement: 释放、断线与超时有界且幂等

租约 SHALL 有 idle/absolute 有界期限，匹配任务命令 MAY 刷新 idle 期限。cloud 的任务体 MUST 在 `finally` 发送 release；edge 对重复 acquire/release MUST 按 `taskId` 幂等。同 edge 重连、cloud 断线、租约到期或执行异常 MUST 使旧租约最终失效并收敛到下一任务或安全浏览状态，MUST NOT 永久冻结。cloud acquire 超时前尚未收到 `acquired` 时，MUST 主动发送该 `taskId` 的 release；若随后收到相同 edge 的迟到 `acquired`，MUST 再次发送 release，直到 edge 收敛或取消记录到期。

#### Scenario: 任务抛错仍释放
- **WHEN** 发布或评论任务体中途抛异常
- **THEN** cloud finally 发送 release，edge 回 released 并授予下一等待任务或恢复浏览

#### Scenario: release 回执丢失可自愈
- **WHEN** cloud 已发送 release 但回执丢失
- **THEN** 重复 release 不产生副作用，且 edge 不会因一次丢包永久持有租约

#### Scenario: acquire 已超时但 acquired 迟到
- **WHEN** cloud 已因 acquire timeout 终止等待，edge 随后才回相同 taskId 的 `acquired`
- **THEN** cloud 不下发业务命令并再次发送 release，edge 释放该租约；任务不会一直占用浏览器直到自然 lease expiry

#### Scenario: 同 edge 重连不继承旧所有权
- **WHEN** 持有租约的 edge 连接断开并以同 edgeId 重连
- **THEN** 旧连接租约失效，cloud 在途任务诚实失败/重试；新连接从无租约安全状态开始，MUST NOT 静默续跑旧命令

### Requirement: 浏览只在独占任务队列收敛后恢复

系统 SHALL 以 edge 协调器的当前租约与等待队列为浏览恢复事实源。任一发布/评论自己的 `finally` MUST NOT 无条件重启浏览；仅当没有当前独占租约且没有应立即接续的独占任务时，edge 才解除冻结并恢复页面快照上报。

#### Scenario: 发布结束时评论已排队不闪回 feed
- **WHEN** 发布释放时评论 commit 已在等待队列
- **THEN** edge 直接把租约授予评论，不在两者之间恢复普通浏览或执行一个滚动

#### Scenario: 最后一个任务结束才恢复
- **WHEN** 等待队列最后一个独占任务释放
- **THEN** edge 恢复浏览并重新上报；恢复动作恰好发生一次

### Requirement: Browser-control-unavailable acquisition SHALL fail immediately and explicitly

Before quiescing browse or granting a task lease, edge task coordination MUST check browser-control readiness. If control is recovering or unavailable, it MUST NOT acquire task ownership, MUST NOT dispatch a page-writing command, and MUST emit `edge.task.released` with reason `cdp_unhealthy` for the requested task id. This negative acknowledgement SHALL be idempotent and MUST NOT leave a queued or active lease behind.

#### Scenario: Human publish arrives during CDP recovery
- **WHEN** a human-priority publish lease request arrives while browser control is recovering
- **THEN** the edge immediately returns `edge.task.released{reason:'cdp_unhealthy'}` without calling browse quiescence and without waiting for the normal acquire timeout

#### Scenario: Duplicate release after unhealthy rejection
- **WHEN** cloud later sends a release for a task already rejected as `cdp_unhealthy`
- **THEN** the edge responds idempotently and MUST NOT resume or freeze browse because of that duplicate release

### Requirement: 云端受理超时必须容得下一次浏览器唤醒，且生效值不得与声明的默认值漂移

云端等待 edge `acquired` 的受理超时 SHALL 大于 edge 的浏览器唤醒死线（edge 为停泊账号原地重开浏览器，含冷启与串行启动队列排队，死线 180s），使 edge **正在正常唤醒**的过程 MUST NOT 被云端提前判为失败——否则任务在浏览器起来前一分钟就被判死，浏览器随后起来却无人认领。

该超时的**生效值** SHALL 只有一处事实源。构造 edge 任务租约客户端时，实现 MUST NOT 在注入点硬编码一个与类默认值不同的回落值；未配置环境变量时 MUST 采用类默认值。任何「抬高默认值却未改注入点」的改动都会使该默认值成为死代码、修复零生效，这是 MUST NOT 的反模式。

受理超时**不是**发现故障的主要手段：边端离线由连接层即时发现（投递到 0 个边缘即刻失败），浏览器控制面故障（`cdp_unhealthy`）与唤醒失败（`browser_wake_failed`）均为即时回执。该超时仅兜「边缘完全失声」这一种情形。

#### Scenario: 停泊账号唤醒期间不被提前判死

- **WHEN** 云端向一个浏览器处于冷待机的 edge 申请租约，edge 开始原地重开浏览器（耗时超过 45 秒但在其唤醒死线内）
- **THEN** 云端 MUST 继续等待直到 edge 回 `acquired` 或 `browser_wake_failed`，MUST NOT 在唤醒途中先行判为 acquire 超时

#### Scenario: 未配置环境变量时采用类默认值

- **WHEN** 部署环境未设置受理超时的环境变量
- **THEN** 生效值等于类默认值（容得下唤醒死线），MUST NOT 因注入点的硬编码回落值而低于它

#### Scenario: 边端离线仍即时失败

- **WHEN** 租约申请投递到 0 个在线边缘
- **THEN** 云端即时失败并归因为边端离线，MUST NOT 因受理超时被抬高而空等

