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

普通浏览 SHALL 是低优先级、可抢占执行流。独占任务申请到达时，edge MUST 允许已经开始的原子动作完成或**在其安全取消点中止**；所有尚未开始且不属于当前租约的普通浏览命令 MUST 被取消，MUST NOT 为了“FIFO”先排空旧浏览队列。任务释放后 MUST 依据当前真实页面重新上报并由 cloud 重决策，MUST NOT 重放被取消的旧命令。

**「安全取消点」SHALL 定义为**：一条命令从进入执行到它**第一次真正改写页面**之前的整段，具体包含且不限于——阻断浮层等待（等验证码 / 登录 / 风控浮层消失）、动作之间的最短间隔、动作前的犹豫停顿、离页前的停留。**这一整段 MUST NOT 计入页面写原子区**：它只消耗时间，平台侧零副作用。

**交接（quiesce）MUST 只等待正在改写页面的动作，MUST NOT 等待任何纯等待。** 停在安全取消点上的命令，MUST 在接管信号到达时当场作废、当场让路。

（该定义是本 change 的核心。前一版 spec 已经写下「或在其定义的安全取消点中止」，但从未定义这个术语——实现遂把「等验证码」也算成了不可中断的原子动作，造成硬死锁：交接无超时地等一条正在等验证码的命令，而那个验证码只有这次交接要授予的协助任务才能点掉。）

#### Scenario: 停在浮层闸上的命令当场让路
- **WHEN** 一条普通浏览命令停在阻断浮层等待里（尚未发生任何页面写），此时验证码人工协助申请租约
- **THEN** 交接 MUST 立即收敛（不等该命令的浮层等待自然结束）；该命令 MUST 零页面副作用地作废并回一条诚实失败回执；接管信号之后 MUST 记录到零次页面改写调用

#### Scenario: 停在离页停留上的命令当场让路
- **WHEN** 一条关闭 / 返回命令正停在离页停留（云端下发了较长的停留预算），此时更高档位任务申请租约
- **THEN** 交接 MUST 立即收敛，MUST NOT 等停留跑满

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

### Requirement: 任务优先级严格生效，高档位任何时刻可抢占低档位

协调器 SHALL 至少支持 `system_recovery`（风控 / 验证码）、`human`（人工指令）、`automatic`（系统自动）三档优先级，顺序为**风控 > 人工 > 系统自动**。

**该顺序 SHALL 在任何时刻生效，而不只是在下一次授予时。** 更高档位的任务申请到达时，协调器 MUST 向当前持有者发出取消信号并在其停止后授予；MUST NOT 让更高档位的任务排在一个已在执行的低档位任务后面等待。

**前一版的「正在执行且已产生副作用的独占任务 MUST NOT 被另一业务任务强杀；高优先级只影响下一次授予顺序」被本条整体推翻。** 那条规则使优先级只在排队瞬间被读一次，其直接后果是：唯一能解救一台卡死机器的系统恢复任务，会被一个已经因同一个浮层而必然失败的发布任务挡在门外。

**同档位之间 MUST NOT 抢占**，仍按 edge 收到申请的顺序 FIFO——先来后到天然防饿死，档内不再引入第二层优先级。

被抢占的任务 SHALL 按下面「被抢占的任务必须诚实分档回执」终结。被抢占 MUST NOT 计入任何熔断计数：它是一个调度事件，不是一次业务失败。

#### Scenario: 系统恢复抢占进行中的发布
- **WHEN** 一个人工批准的发布正持有租约并已填入标题正文（尚未点击提交），此时验证码人工协助申请 `system_recovery` 租约
- **THEN** 协调器 MUST 向发布执行流发出取消信号、等它真正停止写页面后把租约授予系统恢复；发布 MUST 以「未提交，已中止」终结，MUST NOT 计入发布熔断，MUST NOT 让系统恢复排队等发布自然做完

#### Scenario: 人工抢占自动
- **WHEN** 一个自动排期的评论正持有租约，此时运营手动下发的评论指令申请 `human` 租约
- **THEN** 自动评论被抢占并诚实终结，手动评论立即获得租约

#### Scenario: 同档位不抢占
- **WHEN** 一个人工批准的发布正持有租约，此时另一个人工批准的评论申请租约
- **THEN** 评论排队等待，MUST NOT 抢占发布——同档位仍 FIFO

#### Scenario: 低档位不抢占高档位
- **WHEN** 系统恢复任务正持有租约（运营正在处理验证码），此时自动浏览闭环或自动发布申请租约
- **THEN** 申请排队等待，MUST NOT 抢占系统恢复

### Requirement: 被抢占的任务必须诚实分档回执

被抢占的任务 SHALL 按**抢占发生在不可逆提交之前还是之后**分两档终结，且两档 MUST 使用不同的、机器可读的原因，MUST NOT 混为一谈。

- **抢占发生在不可逆提交之前**（导航、开页、选 tab、上传配图、填标题、逐字输入正文、搜索、打开笔记、输入评论内容…）：平台侧零副作用。回执 SHALL 表示「**未提交，已中止**」。任务 MAY 被安全重排。
- **抢占发生在不可逆提交之后**（已点击发布 / 已点击发送，尚未拿到平台结果确认）：那条帖子或评论**可能真的已经发出去了**。回执 SHALL 表示「**已提交，结果未知**」，MUST NOT 表示为「失败」，MUST NOT 自动重试，SHALL 提示人工确认。

将第二档表示为「失败」是**静默假成功的镜像——静默假失败**：系统声称什么都没发生，而平台上可能已经多了一条内容。它撞的是本仓贯穿全部 spec 的核心红线，也与既有的「发布已真实提交后，后续超时 MUST NOT 翻成 failed」是同一条要求。

正因为第二档**不自动重试**，抢占 MUST NOT 引入重复发帖 / 重复评论——因此系统 MUST NOT 为了规避重复而设立「不可抢占窗口」；抢占在任何时刻都成立。

被抢占的任务 MUST NOT 计入熔断计数。被抢占是调度结果，不是业务失败；否则少数几次验证码即可停掉一个账号的整条发布队列。

#### Scenario: 逐字输入中被抢占
- **WHEN** 发布正在逐字输入正文时被系统恢复抢占
- **THEN** 回执为「未提交，已中止」；稿件回到可重发状态；发布熔断计数不变

#### Scenario: 已点提交后被抢占
- **WHEN** 发布已点击提交、正在等待平台结果确认时被系统恢复抢占
- **THEN** 回执为「已提交，结果未知」；系统 MUST NOT 自动重发该稿件；MUST 向运营发出需人工确认的提示

#### Scenario: 评论提交后被抢占不重复评论
- **WHEN** 评论已点击发送、未拿到回执时被抢占
- **THEN** 回执为「已提交，结果未知」，MUST NOT 自动重试；去重账本 MUST NOT 因此被当作「未评论过」而放行下一次评论

#### Scenario: 重开发布前必须确保干净起点
- **WHEN** 一次被抢占的发布留下了半截草稿，随后该稿件被重新发布
- **THEN** 发布流程 MUST 在填充前确保编辑器为空（或丢弃残留草稿），MUST NOT 在残留草稿之上追加内容而产出重复正文

### Requirement: 被抢占的执行流必须真正停止写页面

抢占 SHALL 以「被抢者已停止改写页面」为完成条件，而非以「已发出取消信号」为完成条件。协调器 MUST NOT 在被抢者可能仍在写页面时授予新租约。

所有会改写页面的执行流 MUST 登记在同一套页面写记账中，并 MUST 认同一个取消令牌——包括**发布执行流**（当前跑在主进程一个独立上下文里、不在浏览会话的页面写记账体系内，协调器的交接对它完全无感）。

未纳管的执行流是抢占的**双写风险源**：抢占者以为对方停了，实际它仍在向同一个浏览器控制端口派发输入，两者的动作交错打进同一个页面。

#### Scenario: 抢占发布不产生双写
- **WHEN** 系统恢复抢占一个正在逐字输入的发布
- **THEN** 在系统恢复的第一次页面写之前，发布执行流 MUST 已停止向浏览器控制端口派发任何输入；两者 MUST NOT 交错写同一个页面

#### Scenario: 未纳管的执行流不得存在
- **WHEN** 任一会改写页面的执行流（发布、评论、巡视、加群、恢复动作）被启动
- **THEN** 它 MUST 已登记在页面写记账中且 MUST 认取消令牌，MUST NOT 从旁路直接写浏览器控制端口

### Requirement: 交接必须有界，未收敛时绝不授予

交接（等待被抢者真正停止写页面）SHALL 有墙钟上界。在上界内未收敛时，协调器 MUST NOT 授予租约、MUST NOT 谎称已收敛、MUST NOT 停留在让位态。

未收敛时协调器 MUST：① 以诚实终态终结排队中的申请；② **回滚自己在交接开始时置下的普通浏览冻结标志**；③ 回到可继续协调的状态，使普通浏览恢复、冷待机可再次进入。

不回滚冻结标志，等于把停摆从「让位态」搬到「浏览冻结态」——症状相同但更难诊断：协调器看上去完全健康，而云端的浏览命令逐条被静默丢弃，且没有任何事件会再来清除该标志。

云端的受理预算 MUST 大于边缘的交接上界加一个往返余量。否则边缘按时交接了、云端已经判死走人，修好的路照样白跑。

#### Scenario: 交接超时不授权、不停摆
- **WHEN** 被抢占的执行流在交接上界内仍未停止写页面
- **THEN** 协调器 MUST NOT 授予租约；MUST 给排队申请一个诚实终态；MUST 解除普通浏览冻结；随后普通浏览 MUST 恢复、冷待机 MUST 可再次进入

#### Scenario: 云端受理预算容得下交接上界
- **WHEN** 边缘的交接上界为 T
- **THEN** 云端等待授予的受理预算 MUST 大于 T 加一个消息往返余量，MUST NOT 在边缘仍在合法交接的过程中先行判死

### Requirement: 让位超时升级为控制面回收，且是人工动作而非自愈

被抢者收到取消信号后在交接上界内仍不停止写页面，SHALL 被判为**控制面故障**（不是普通业务失败、也不是可自愈的瞬态）。系统 MUST 用一个与「良性可恢复」明确可区分的、机器可读的原因（`yield_timeout`）表达它，MUST NOT 与「浏览器停泊唤不醒」「CDP 暂不可用」这类可自动重试的原因混为一谈。

该原因通向的是一个**人工动作——「请运营重启浏览器客户端」**，MUST NOT 触发自动重试 / 自动重投 / 自动归还排队额度。把它当作可重试的受理失败，会让系统对着一台已经卡死的浏览器一轮轮空转，而运营那头既没有被告警、也不知道要去重启。

#### Scenario: 写者不停手升级为人工重启
- **WHEN** 一个页面写执行流收到取消信号后，在交接上界内仍未停止写页面
- **THEN** 协调器 MUST 以 `yield_timeout` 终结该任务与排队申请；云端 MUST NOT 把它判成「未开始」并归还排队额度、MUST NOT 自动重投；运营看到的 MUST 是「浏览器不听话，请重启客户端」，而不是一句神秘的租约失败

### Requirement: 通知巡视按窗口保护，其不可逆消费段不可被抢占

通知巡视点开分类栏目的那一刻，平台未读即被消费，且该未读**只在从无到有翻转时上报一次**、两端都无副本、无可回退游标。因此点分类栏目到未读回传之间 SHALL 被视为一个**不可逆提交窗口**：在该窗口内协调器 MUST 拒绝抢占（回「窗口占用中 + 剩余预算」），MUST NOT 在窗口内注入安全取消点。

窗口内允许抢占 = 一整波未读永久丢失（既没写进任何账本，也无法再次上报）。这与发布/评论的提交窗口保护同构，但巡视的窗口**恰恰缺席安全取消点**：安全取消点的定义（操作到第一次真正改写页面之前皆可中止）在此不成立，因为「点分类栏目」这一下本身就是不可逆的平台副作用。

**本保护 MUST 由实际执行巡视的运行时开窗，并随执行运行时更换而迁移。** 页面动作的执行体从一个运行时搬到另一个（例如页面智能迁入已编码的页面引擎）MUST NOT 使该窗口失效：搬家后仍必须有人在消费动作的正前方开窗、在未读回传的终态关窗。协调器的窗口探针在该段内 MUST 报「忙 + 剩余预算」；探针在真实不可逆消费进行中报「无窗口」即视为违反本条，无论是哪个运行时在执行。

#### Scenario: 点开分类栏目后抢占被拒
- **WHEN** 通知巡视已点开某分类栏目、未读尚未回传，此时更高档位任务申请租约
- **THEN** 协调器 MUST 拒绝抢占并回「窗口占用中、剩余 ≤20s」，MUST NOT 在该窗口内中止巡视命令（否则已消费未上报的未读永久丢失）

#### Scenario: 执行运行时更换后窗口仍在
- **WHEN** 通知巡视的页面动作由新的执行运行时承担，一次分类消费正在进行
- **THEN** 协调器的窗口探针 MUST 报「忙 + 剩余预算」，抢占 MUST 被拒
- **AND** MUST NOT 因为「窗口参数没有传到新执行体」而退化成无窗口的可抢占段

### Requirement: 页面任务协调 SHALL 仅接收已分类的 page_automation 操作

页面任务租约、同账号排他、CDP 准入和浏览器槽位协调 SHALL 仅用于注册表中声明为 `page_automation` 的操作。`local` 和 `cloud_data` 操作 MUST NOT 依赖自动化引擎；`automation_control` 与 `platform_api_automation` SHALL 依赖引擎但 MUST NOT 创建页面任务租约、等待浏览器槽位或因 `browser_control_unavailable` 被拒；`browser_lifecycle` 只协调执行器生命周期，不得冒充页面任务成功。

#### Scenario: API-only 自动化不取得页面租约

- **WHEN** 已登记为 `platform_api_automation` 的互动同步被触发且同账号页面任务正在运行
- **THEN** API-only 操作按其自身并发与身份合同经引擎执行，MUST NOT 等待页面任务租约或抢占浏览器槽位

#### Scenario: API-only 自动化不在引擎停止时偷偷执行

- **WHEN** 自动化状态为 `stopped` 或 `paused`
- **THEN** 新的 `platform_api_automation` 外部平台动作不得执行，但 `cloud_data` HTTP 操作继续可用

#### Scenario: 页面自动化仍受同账号租约保护

- **WHEN** 两个已登记为 `page_automation` 的任务同时请求同一账号
- **THEN** 系统仍按既有租约合同串行或拒绝，自动化引擎生命周期不得放宽同账号并发保护

### Requirement: Native task takeover SHALL block only the ordinary browse lane
After an edge has confirmed acquisition of a page-task lease, the Native page session MUST admit commands whose task ID matches the active lease and MUST continue to reject commands with no task ID or a different task ID until release.

#### Scenario: Current task command executes while ordinary browse is quiesced
- **WHEN** a Native page session has quiesced ordinary browsing for task `T` and receives a page command owned by task `T`
- **THEN** Edge SHALL execute the command under Native owner `T` rather than returning `native_session_quiesced`

#### Scenario: Ordinary browse remains blocked during the lease
- **WHEN** task `T` owns the page lease and a command without a task ID arrives
- **THEN** Edge SHALL reject or suppress that command without touching the page

#### Scenario: Stale task remains blocked during the lease
- **WHEN** task `T` owns the page lease and a command carrying task ID `U` arrives
- **THEN** Edge SHALL reject or suppress that command without touching the page

### Requirement: 被任务租约抑制的命令必须回执，不得静默丢弃

当一条云端下发的页面命令因租约归属不符（含释放与下发在同一瞬间竞态）而不被执行时，边缘 SHALL 向云端回一条如实的「未执行」回执，写明抑制原因与当时的租约归属。边缘 MUST NOT 只打日志后直接返回。

云端 SHALL 能据此立即区分「命令被抑制、未触达页面」与「命令已执行但页面无结果」，并按自己的策略重试或诚实终止；MUST NOT 依赖步超时到点才发现这条命令从未执行。该回执 MUST NOT 被表述为成功或部分成功。

#### Scenario: 释放与命令同毫秒竞态
- **WHEN** 一条浏览命令与其所属任务的租约释放在同一毫秒到达
- **THEN** 边缘回一条具名的未执行回执
- **AND** 云端在毫秒级得知该命令未触达页面，而不是等满步超时

#### Scenario: 归属他人租约的命令
- **WHEN** 命令携带的任务标识与当前持有的租约不一致
- **THEN** 边缘拒绝执行并回执说明当前租约归属
- **AND** 页面状态不被该命令改动

#### Scenario: 回执不得冒充成功
- **WHEN** 命令被租约抑制
- **THEN** 回执的成功位为假、原因具名
- **AND** 云端不得把它计入任何已完成动作或配额

### Requirement: Browser-absent edge 的任务 SHALL 触发唤醒并得到终局回执

Cloud 在 Edge 控制面在线但浏览器缺席时 SHALL 允许需要浏览器的任务进入 acquire/wake 流程。Edge MUST 在唤醒完成且身份复核成功后才授予浏览器执行租约；唤醒失败或死线到达 SHALL 返回明确终局并保持后续可重试。

#### Scenario: 控制面在线任务唤醒浏览器
- **WHEN** Cloud 向 browser-absent edge 派发一个需要浏览器的任务且其在死线内取得槽位
- **THEN** Edge 完成浏览器启动、身份复核与租约 acquired 后才接收首条业务命令

#### Scenario: 排队超出唤醒死线
- **WHEN** 任务等待浏览器槽位超过调用方死线
- **THEN** Cloud 收到 `browser_wake_failed` 类可恢复终局并可按策略重试
- **AND** MUST NOT 把它记录为 edge offline、成功或无回执

#### Scenario: 浏览器缺席时业务命令不得静默丢弃
- **WHEN** 浏览器缺席期间仍收到一条需要页面的业务命令
- **THEN** Edge 返回明确的 browser-unavailable/wake-required 失败
- **AND** MUST NOT 只写本地日志而让 Cloud 看门狗超时

### Requirement: 浏览器执行器获取失败 MUST 与客户端数据面和引擎连接状态分离

页面任务申请执行器失败时，协调器 SHALL 返回槽位排队、provider 启动失败、CDP 附着失败或身份不匹配等可区分状态；MUST NOT 把这些状态投影为客户会话或 HTTP 数据面离线。若引擎仍连接，失败只影响当前页面执行和浏览器状态；执行器释放后 SHALL 释放页面租约与槽位，是否继续保持引擎连接由自动化意图决定。

#### Scenario: 槽位已满时页面任务排队

- **WHEN** 页面任务需要浏览器而所有槽位已占用
- **THEN** 自动化进入真实 `waiting_resource`，HTTP 数据管理继续可用，MUST NOT 显示客户端离线或正在执行

#### Scenario: CDP 附着失败

- **WHEN** provider 已启动但 CDP 在时限内不可用
- **THEN** 协调器诚实回报 `cdp_unavailable` 并回收本次执行器资源，MUST NOT 宣称页面操作成功或破坏客户会话

### Requirement: Cross-platform Native commands preserve one-writer task ownership
Every Facebook page command and WeChat browser-session capture command SHALL carry the active Edge task identity, unique command identity, and bounded deadline through Native IPC. Native MUST reject stale tasks, duplicate dispatch, concurrent page writers, and platform/session mismatches before browser input.

#### Scenario: Stale Facebook task sends a write
- **WHEN** Edge has transferred the browser lease to a new task and the old task submits a Facebook interaction command
- **THEN** Native rejects the stale task before any CDP input

#### Scenario: Duplicate write identity is received
- **WHEN** Native receives a Facebook command identity it already completed
- **THEN** it returns the recorded terminal result or rejects the duplicate without redispatch

### Requirement: Cross-platform cancellation cannot erase ambiguous effects
Cancellation, timeout, process exit, or reconnect across Facebook and WeChat Native commands SHALL preserve the declared safe-point and effect-phase rules. Edge MUST NOT infer not-started merely because the Native process lost in-memory state.

#### Scenario: Native exits after possible Facebook submit
- **WHEN** the process exits after a publish/comment submit may have been dispatched and no terminal proof exists
- **THEN** Edge preserves an ambiguous outcome and does not replay the write

#### Scenario: WeChat capture is cancelled
- **WHEN** cancellation is observed during read-only WeChat session capture
- **THEN** Native stops at a safe point, closes its session, and returns a bounded cancelled result without fabricated material

### Requirement: Every irreversible Xiaohongshu page write SHALL open a commit window

Each Xiaohongshu page action whose platform-side effect cannot be undone or replayed SHALL be wrapped in a commit window for the duration between the last cancellable point and the terminal receipt. At minimum this covers:

- comment submission (the submit keystroke that publishes the comment),
- notification-sweep consumption of the comment category,
- notification-sweep consumption of the like/follow categories,
- publish submission.

The window MUST be requested by the runtime that actually performs the write, at the point immediately before dispatch, and MUST be released at the terminal outcome (success, failure, or budget expiry). Wrapping a whole command instead of the write is not compliant: it converts "protect the irreversible write" into "forbid preemption for the entire command" and silently disables preemption for navigation, locating and waiting.

While a window is open, the coordinator MUST refuse preemption and answer with a busy verdict plus the remaining budget, and MUST NOT inject a cancellation safe point inside the window.

If the window cannot be obtained — request denied, no window facility wired, or the facility unavailable — the write MUST NOT be dispatched and the receipt MUST report a truthful not-started outcome. The absence of in-flight cancellation for write commands MUST NOT be treated as protection: an unprotected write that happens not to be torn today is unprotected, and the coordinator's window probe reporting "no window" during a live irreversible write is itself the defect.

#### Scenario: Preemption during comment submission is refused

- **WHEN** a Xiaohongshu comment submission has opened its commit window and a higher-priority task requests the lease
- **THEN** the coordinator refuses preemption and returns a busy verdict with the remaining budget
- **AND** it does not abort the in-flight submission and does not inject a cancellation safe point inside the window

#### Scenario: Notification consumption is protected like the comment write

- **WHEN** a Xiaohongshu notification sweep is about to consume a category's unread state
- **THEN** the executing runtime opens a commit window before the consuming action and releases it at the terminal receipt
- **AND** the coordinator's window probe reports busy with remaining budget throughout that interval

#### Scenario: No window means no write

- **WHEN** an irreversible Xiaohongshu write requests a commit window and the request is denied or the facility is unavailable
- **THEN** the write is not dispatched and the receipt reports a truthful not-started outcome
- **AND** the runtime does not proceed on the grounds that the write would probably not be interrupted

#### Scenario: Window is released at the terminal outcome

- **WHEN** an irreversible Xiaohongshu write reaches success, failure, or budget expiry
- **THEN** its commit window is released
- **AND** a later preemption request is answered on the coordinator's ordinary terms rather than by a leaked permanently-busy window

### Requirement: Task and command ownership MUST cross Native IPC

Every Native page command SHALL carry the active Edge `taskId`, a unique per-session `commandId`, and a bounded deadline. Native MUST reject stale task identities, duplicate command identities, and concurrent page writers before CDP dispatch. Edge remains the lease authority and MUST NOT consider IPC acceptance equivalent to platform execution success.

#### Scenario: Duplicate command identity is received
- **WHEN** Native receives a `commandId` already accepted in the current session
- **THEN** it rejects the duplicate or returns the already-recorded terminal result without redispatching browser input

#### Scenario: Lease changes between commands
- **WHEN** Edge grants the page executor to a new `taskId`
- **THEN** subsequent commands from the old task are rejected before dispatch

### Requirement: Cancellation and preemption MUST preserve effect truth

Edge cancellation/preemption SHALL be forwarded to Native and acknowledged only at a declared safe point. Native MUST finish any already-started atomic input region, classify the resulting effect phase, and stop before the next dispatch. Neither cancellation nor deadline expiry may turn a possibly dispatched write into a clean failure.

#### Scenario: Cancel before dispatch
- **WHEN** Native observes cancellation at a safe point before platform input
- **THEN** it returns `not_started` with cancellation reason and performs no write

#### Scenario: Cancel after submit dispatch
- **WHEN** cancellation arrives after a publish/comment/interaction submit may have been dispatched
- **THEN** Native performs only bounded verification and returns `confirmed` or `ambiguous`
- **AND** Edge MUST NOT retry or use JavaScript fallback

### Requirement: Native restart MUST NOT replay unfinished writes

If the Native process exits or is restarted, the supervisor SHALL create a new session identity and SHALL NOT replay an unfinished command automatically. Recovery MAY re-read current platform state for an explicit reconciliation command, but it MUST NOT infer `not_started` from missing in-memory Native state.

#### Scenario: Engine restarts after ambiguous interaction
- **WHEN** the previous process exited after possible dispatch and no terminal proof exists
- **THEN** Edge preserves an ambiguous outcome and requires existing reconciliation/manual handling rather than resending the interaction

