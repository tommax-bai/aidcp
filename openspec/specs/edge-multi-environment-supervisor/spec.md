# edge-multi-environment-supervisor Specification

## Purpose
TBD - created by archiving change edge-multi-environment-fleet. Update Purpose after archive.
## Requirements
### Requirement: 桌面外壳按环境监督一组独立子进程

`adspower` 模式下，Electron 桌面外壳 SHALL 按环境 id 监督一组按需自动化引擎（`Map<envId, EnvHandle>`）。每个正在启动、等待或执行自动化的环境 SHALL 使用一个绑定该分身的独立操作系统子进程和 automation WebSocket；客户仅登录或管理数据时 MUST NOT 因环境在 roster 中而创建普通子进程。外壳 SHALL 支持对单个环境独立启动、暂停、恢复、关闭和异常恢复，各环境互不牵连。既有单实例锁 SHALL 保留为“一台机一个客户端监督器”。

#### Scenario: 多个环境按需启动独立引擎

- **WHEN** 运维对两个及以上环境启动自动化
- **THEN** 外壳分别 spawn 绑定各自分身的独立引擎、建立各自 automation WebSocket 并准备浏览器，互不共享进程内存

#### Scenario: roster 环境不自动产生引擎

- **WHEN** 客户登录后 roster 含十六个环境但未启动任何自动化
- **THEN** 外壳建立十六个可管理环境句柄但不 spawn 十六个普通引擎或浏览器

#### Scenario: 单环境关闭不牵连兄弟

- **WHEN** 运维对某一个环境点“关闭自动化”
- **THEN** 仅该环境的引擎和浏览器被停止，其余环境的引擎与浏览会话继续运行、状态不受影响

### Requirement: 每环境 MUST 携带唯一稳定的边缘身份、绝不回落共享常量

外壳为每个环境 spawn 子进程前 SHALL 注入该环境专属的冻结环境变量，使其边缘身份（edgeId）**唯一且跨重启稳定**（`adspower` 模式为 `ads-<分身id>`）：SHALL 设置该环境的 `AIDCP_ADS_USER_ID`，SHALL 删除 `AIDCP_ACCOUNT_ID`（身份由登录读出、绝不由启动方指派），SHALL 删除 `AIDCP_CDP_PORT` / `AIDCP_CHROME_PROFILE`（AdsPower 每分身动态返回调试端口、自管目录）。外壳 MUST NOT 让任何环境回落到基于主机名的共享 edgeId；若某环境无法派生唯一稳定身份，SHALL 诚实拒绝启动该环境。两个环境 MUST NOT 共用同一 edgeId（云端会将其判为同节点重连而互踢、致串号）。

#### Scenario: 注入唯一稳定身份
- **WHEN** 外壳为某分身环境 spawn 子进程
- **THEN** 该子进程的 edgeId 为 `ads-<该分身id>`、跨重启不变，`AIDCP_ACCOUNT_ID` 未注入（身份从登录读出）

#### Scenario: 无法派生稳定身份则拒绝启动
- **WHEN** 某环境既无分身 id、又无可派生唯一稳定身份的依据（将回落主机名）
- **THEN** 外壳诚实拒绝启动该环境并说明原因，MUST NOT 以主机名共享身份起跑

### Requirement: 并发启动 / 停止 MUST 错峰串行以避开 AdsPower 本地 API 限频

外壳对 AdsPower 本地 API 的生命周期调用（`browser/start` / `browser/stop` / `browser/active`）SHALL 经一条外壳级串行队列**错峰下发**（相邻调用间隔 ≥ 1.1s），使「全部启动」/「全部停止」/ 逐环境启停 / 重登不会在同一时刻突发多次而触碰 AdsPower ~1req/s 的本机限频。启动多个环境时各环境 SHALL 独立经过启动中 → 运行 / 需登录 / 错误的迁移，某一环境的启动失败 MUST NOT 阻塞队列中其余环境。

#### Scenario: 全部启动错峰下发
- **WHEN** 运维点「全部启动」拉起 N 个离线环境
- **THEN** 外壳把 N 个 `browser/start` 经串行队列每 ≥1.1s 释放一个，界面如实呈现「k/N 启动中 · 下一个 Ns 后」，MUST NOT 同一时刻突发全部启动

#### Scenario: 单环境启动失败不阻塞队列
- **WHEN** 队列中某环境启动失败（如分身未登录致诚实非零退出）
- **THEN** 该环境如实进入错误态，队列继续释放其余环境的启动，互不牵连

### Requirement: 子进程 MUST 非 detached 且退出时优雅全停、重启时对账防孤儿

外壳 spawn 的环境子进程 SHALL 为**非 detached**、随外壳退出而终止；应用退出时 SHALL 对全部在跑环境执行优雅「全部停止」（经串行队列下发 `browser/stop` 并确认关闭），MUST NOT 留下孤儿浏览器进程。外壳重启时，为某分身 spawn 前 SHALL 先经 `browser/active` 对账该分身是否已在运行，已在运行则接管 / 不重复 spawn，MUST NOT 重复拉起同一分身而造成 edgeId 撞车（致云端互踢）与内存堆积。

#### Scenario: 退出时全部优雅停止不留孤儿
- **WHEN** 运维在有环境运行时关闭应用
- **THEN** 外壳先对全部在跑环境有序执行停止并确认浏览器关闭、再退出，不留下孤儿 Chrome / AdsPower 进程

#### Scenario: 重启前对账已在运行的分身
- **WHEN** 外壳重启，某分身在上次异常退出后仍被 AdsPower 标记为运行中
- **THEN** 外壳经 `browser/active` 对账后接管 / 不重复 spawn 该分身，MUST NOT 造成同一 edgeId 的第二个连接被云端互踢

### Requirement: 每环境有界重起并对连续失败诚实放弃、不牵连兄弟

外壳 SHALL 对每个环境独立应用有界重起策略（复用既有重起退避 / 放弃语义）：某环境子进程异常退出时仅重起该环境、按退避与上限重试；连续失败达上限 SHALL 停手、把该环境标为终态错误并在其行如实呈现，MUST NOT 无限重起抖动、MUST NOT 因某环境失败而中止或重起其他环境。

#### Scenario: 单环境崩溃只重起自己
- **WHEN** 某环境的浏览器崩溃 / 核心异常退出
- **THEN** 外壳仅对该环境按退避重起，其余环境不受影响

#### Scenario: 连续失败达上限诚实放弃
- **WHEN** 某环境连续启动 / 运行失败达到重起上限（如分身持续未登录）
- **THEN** 外壳停止重起、把该环境标为「错误 · 已放弃重启」终态并如实呈现，提供人工重试入口，MUST NOT 继续抖动

### Requirement: 配图临时目录 MUST 按环境隔离、启动清扫不得误删兄弟在途文件

多环境并行下，配图上传临时目录 SHALL 按环境（分身 id / 进程）命名空间隔离；某子进程启动时的临时目录清扫 SHALL 只清自己名下的目录，MUST NOT 删除同机其他在跑环境正在使用的在途上传目录。任何跨环境的临时目录清扫误删都可能致兄弟环境的发布半截 / 损坏，属「静默假成功」红线，MUST NOT 发生。

#### Scenario: 启动清扫只清自己名下目录
- **WHEN** 某环境子进程启动并执行崩溃残留临时目录清扫
- **THEN** 仅清除该环境自身命名空间下的残留目录，同机其他环境正在写入的在途上传目录不被触碰

#### Scenario: 兄弟发布在途不被误删
- **WHEN** 环境 A 正在写入配图临时目录、环境 B 此时启动做清扫
- **THEN** 环境 A 的在途上传文件完好，其发布不因 B 的清扫而半截或损坏

### Requirement: 全部启动 MUST 做内存上限预检、超限诚实拦阻而非拖垮

考虑到每个有界面（headful）环境约占 ~1GB 内存，外壳在「全部启动」/ 批量拉起前 SHALL 预检「预计在跑数 × 单环境内存估值」是否超过本机可用内存；预计超限 SHALL 诚实提示并暂缓 / 让运维确认，MUST NOT 直接超额拉起而致换页抖动 / OOM 把某环境浏览器杀掉、再让它看起来像「莫名其妙的不稳定」。

#### Scenario: 预计超限时诚实拦阻
- **WHEN** 运维点「全部启动」而预计在跑数 × ~1GB 超过本机可用内存
- **THEN** 外壳先诚实提示内存可能不足、暂缓或让运维确认，MUST NOT 无提示地超额拉起

### Requirement: 同一账号被铺到多个环境时 MUST 告警

外壳 SHALL 检测并告警「两个及以上环境解析到同一账号」的配置：由于云端对同账号多连接会合并风控 / 配额预算、并把发布 / UI 定向到最早登记的那条边缘，同账号铺到多个环境的两行并非相互独立。外壳 SHALL 在加入 / 启动时如实提示该情形，引导「一个环境 = 一个独立账号」，MUST NOT 静默把它们当作两个独立预算的环境。

#### Scenario: 同账号多环境给出告警
- **WHEN** 运维选中的两个环境登录 / 解析到同一账号
- **THEN** 外壳如实告警「这两个环境是同一账号、风控与配额会合并、发布只发最早那条」，引导改为不同账号，MUST NOT 静默当作两个独立环境

### Requirement: 每环境的外壳态 MUST 隔离、路由键贯穿广播与 IPC

外壳内的按环境态 SHALL 全部以 envId 为键隔离：各环境 SHALL 各持一份活动流 / 计数解析器实例、状态投影、浏览器停放控制与持久化 UI 态；主进程→渲染层的状态 / 活动广播与渲染层→主进程的控制 IPC SHALL 携带 envId 路由键，使并发环境交织的子进程输出被如实归属到正确环境、控制指令定向到正确子进程，MUST NOT 出现跨环境串流 / 误控。

#### Scenario: 并发输出按环境正确归属
- **WHEN** 多个环境子进程同时产生活动 / 计数事件
- **THEN** 每条被归属到其所属环境的活动流与计数，界面上不同环境的动态与数字互不串号

#### Scenario: 控制指令定向到正确子进程
- **WHEN** 运维对某环境行点启动 / 暂停 / 恢复 / 停止
- **THEN** 该 IPC 携带其 envId、只作用于对应子进程，MUST NOT 误控其他环境

### Requirement: offboard 恢复 MUST 使用无浏览器的受限清理会话

未完成的 offboard 清理 SHALL 使用 Cloud 签发并绑定 `offboardId/envKey/accountId/edgeId` 的短期单用途凭证启动受限核心会话。该会话仅可领取和回报对应清理命令，MUST NOT 注册普通任务能力、恢复通用客户会话、调用 `queueStartEnv` 或启动浏览器。凭证过期、已使用或绑定不匹配时 MUST 诚实失败并进入人工处理。

#### Scenario: 客户端重启后恢复 offboard 清理

- **WHEN** 客户端重启时发现一个持久化的未完成 offboard 清理且凭证仍有效
- **THEN** 监督器启动受限浏览器无关会话完成清理和回执，浏览器状态全程保持 `closed`

#### Scenario: 清理凭证与环境不匹配

- **WHEN** 受限会话携带的凭证绑定到另一个环境或已经过期
- **THEN** Cloud 拒绝清理命令，客户端不得降级为普通环境启动或打开浏览器重试

### Requirement: 监督器 SHALL 分别监督每环境自动化引擎与浏览器执行器

桌面监督器 SHALL 为每个环境维护自动化意图、可选引擎句柄和浏览器执行器句柄。只有意图为启动/恢复时才 SHALL 启动或有界恢复普通引擎；意图为暂停/停止时引擎退出 MUST NOT 触发自动重启。浏览器退出只更新执行器和受影响页面任务，不得把客户端数据面投影为离线。引擎与浏览器使用独立故障原因，浏览器槽位只限制页面执行器。

#### Scenario: 暂停后的引擎退出不自动重启

- **WHEN** 自动化完成暂停回报并停止普通引擎
- **THEN** 监督器保持 `paused`，不得按崩溃退避重启引擎；客户 HTTP 操作继续可用

#### Scenario: 浏览器故障不把客户端数据面置为离线

- **WHEN** 引擎运行期间浏览器执行器崩溃
- **THEN** 监督器只回收/重排执行器并诚实更新页面任务，客户端客户会话和 HTTP 数据入口不受影响

### Requirement: 拉起核心子进程 MUST 是原子提交点、与取消复核之间不得有等待

外壳把某环境的核心子进程拉起来这一步 SHALL 与「取消闸复核」构成一个**中间不含任何等待的原子提交点**：复核（当前操作代次、停止意图、已移出、客户端退出中）→ `spawn` → 登记子进程所有权，三者之间 MUST NOT 存在任何 await / 回调让渡。任何需要等待的准备工作（读分身运行状态、代理与网络准备、身份与产物校验）SHALL 全部前移到提交点之前完成。

因此取消意图只有两种落点：落在提交点之前 ⇒ MUST NOT 拉起子进程；落在提交点之后 ⇒ 该子进程 MUST 已被登记为本环境所有，从而对关闭路径可见、可关。MUST NOT 存在「取消已生效但仍会产生一个无人认领的子进程」的第三种落点。

#### Scenario: 准备期间收到关闭则不拉起

- **WHEN** 某环境已通过取消复核、正在做拉起前的分身状态读取与代理准备，期间用户点「关闭」
- **THEN** 该趟启动 MUST NOT 拉起核心子进程，MUST 归还启动排队名额并让出串行启动队列，环境停在关闭意图所对应的状态

#### Scenario: 关闭晚于提交点则关闭看得见这个子进程

- **WHEN** 用户的关闭意图在核心子进程已被登记为本环境所有之后到达
- **THEN** 关闭 MUST 走「有子进程」的关闭路径（下发关闭指令 / 必要时终止），MUST NOT 走「当前无子进程 → 无事可停」分支

### Requirement: 核心子进程所有权登记 MUST 经统一准入闸、被拒即终止并归还名额

所有会拉起核心子进程的路径（手动启动 / 崩溃重起 / 待机唤醒 / 排期任务 / 无浏览器控制面 bootstrap / 受限离场清理）SHALL 共用同一处所有权登记入口，该入口 SHALL 就地执行准入判定。准入判据 SHALL 由调用方按本次启动意图提供且为**必填**——新增启动路径未提供判据时 MUST 当场失败，MUST NOT 默认放行。

准入被拒时，外壳 SHALL 先完成所有权登记与退出观测者安装、再终止该子进程，使其退出经既有退出路径收敛（清所有权、归还浏览器执行名额、放行等槽位队列）；MUST NOT 在未登记所有权的情况下持有一个仍在运行的子进程。被拒 SHALL 如实记入原始日志（环境、拒收原因），MUST NOT 投影为失败态、MUST NOT 消耗有界重起预算——用户主动关闭不是故障。

#### Scenario: 已被要求停止的环境不得留下运行中的子进程

- **WHEN** 某环境已被要求停止 / 已移出 / 客户端正在退出，而一个核心子进程在此刻抵达所有权登记
- **THEN** 外壳 MUST 立即终止该子进程并归还其占用的启动排队与浏览器执行名额，界面 MUST NOT 出现该环境的运行态或「关闭中」滞留

#### Scenario: 无浏览器的特殊会话不被通用停止意图误杀

- **WHEN** 受限离场清理核心或无浏览器控制面 bootstrap 核心在环境已被移出 / 已停止的语境下抵达所有权登记
- **THEN** 准入 SHALL 按该启动意图自己的取消条件判定并放行，MUST NOT 因通用停止意图被误杀

### Requirement: 停止意图 MUST 覆盖在途启动、绝不把「此刻没有」当作「不会有」

关闭 / 暂停在判断「当前有没有核心子进程」时，SHALL 把该环境是否存在**在途启动**一并纳入意图的持续有效范围：停止意图 SHALL 持续有效直到显式启动重新建立，且 SHALL 被拉起前的提交点复核与所有权登记准入闸同时读取。外壳 MUST NOT 因为「按下关闭的那一刻没有子进程」就认定此后不会再产生子进程，也 MUST NOT 在存在未被覆盖的在途启动时宣布浏览器已确认关闭。

#### Scenario: 关闭后不得再冒出核心子进程

- **WHEN** 用户在某环境启动流水线的任意阶段点「关闭」，外壳据此宣布该环境已关闭并确认浏览器已关闭
- **THEN** 此后 MUST NOT 再由这一趟启动产生任何存活的核心子进程；若已产生 MUST 被立即终止（见所有权准入闸）

### Requirement: 仍归本环境所有的子进程输出 MUST 全量落原始日志

外壳对核心子进程输出的丢弃判据 SHALL 分成两层：**原始日志** SHALL 按所有权收——该子进程仍归本环境所有时其每一行输出 MUST 落入原始日志；**界面运行态投影** SHALL 保留操作代次门，防止被取代的操作代次把界面写回去。

操作代次不一致时 MUST NOT 整段丢弃输出：该行 SHALL 原样落入原始日志并标注它来自已被取代的操作代次。MUST NOT 存在「一个仍在运行、仍归本环境所有的子进程，其存在与行为在原始日志中完全没有痕迹」的状态。

#### Scenario: 代次已被取代但子进程仍在运行

- **WHEN** 某环境的操作代次因关闭 / 暂停 / 重启而推进，而上一代次的核心子进程仍在运行并持续输出
- **THEN** 这些输出 MUST 逐行落入原始日志并标注来自已被取代的代次，MUST NOT 被静默丢弃；界面运行态 MUST NOT 被这些输出改写

### Requirement: 启动就绪超时 MUST 如实呈现且 MUST NOT 写成失败

某环境超出「浏览器起来 + 云端连上」的就绪预算时，外壳 SHALL 放行串行启动队列的下一个环境，并 SHALL 在该环境状态上如实呈现三件事：已超出就绪预算、启动队列已放行下一个、本环境仍在继续自己启动。该呈现 MUST NOT 写成失败态或终态——超时既不代表失败也不代表停手，MUST NOT 只写进控制台而界面无痕。

#### Scenario: 超出就绪预算时界面如实说明

- **WHEN** 某环境自拉起后超过就绪预算仍未就绪，串行启动队列放行下一个环境
- **THEN** 该环境状态 MUST 如实呈现「已超预算 / 队列已放行下一个 / 本环境仍在继续启动」，MUST NOT 被标记为失败、错误或已放弃

### Requirement: The supervisor SHALL observe a spawned child before fallible post-spawn setup

Immediately after `spawn()` returns, the desktop supervisor SHALL assume ownership of that child, create its launch-readiness waiter, and register IPC message, `error`, `exit`, and `close` observers plus any available stdout and stderr observers before proxy-authority pipe delivery, queue release, or status publication. A synchronous exception during later setup MUST settle that launch as failed, release its waiting reservation, expose a stable lifecycle-scoped failure, and best-effort terminate the child while retaining ownership until a terminal observer reaps it. A setup failure MUST remain retryable under the bounded respawn policy even when the cleanup signal produces a graceful `code=0` exit.

#### Scenario: Initial status projection throws after spawn

- **WHEN** the child exists but initial post-spawn status construction or publication throws synchronously
- **THEN** launch readiness settles as failed, the child is asked to terminate, and its observed terminal event clears the handle and advances waiting work
- **AND** the environment MUST NOT remain indefinitely `starting` without a live child, queue position, or scheduled retry

#### Scenario: Spawn fails without stdio streams

- **WHEN** `spawn()` returns a child that has no stdout or stderr stream and then emits a pre-spawn `error`
- **THEN** the already-installed spawn-error observer handles the terminal failure exactly once and releases the environment through the existing bounded failure or respawn path

#### Scenario: Already-spawned child reports a kill or send error

- **WHEN** a child with confirmed process ownership emits `error` because a kill or IPC send could not be delivered
- **THEN** the supervisor records that delivery failure but MUST retain child ownership and MUST NOT start a replacement until `exit` or `close` confirms process termination

#### Scenario: Known proxy setup terminal is reaped

- **WHEN** the proxy-authority pipe is unavailable after spawn and the cleanup signal later terminates the child
- **THEN** the supervisor preserves the actionable proxy failure, clears the child through the common finalizer, and MUST NOT reinterpret cleanup `SIGTERM` as a retryable crash

#### Scenario: Exit arrives but stdio close is delayed

- **WHEN** the child OS process exits and inherited stdout or stderr delays `close`
- **THEN** launch readiness and execution capacity are released immediately, while terminal log classification remains bounded by the existing close-drain grace period

