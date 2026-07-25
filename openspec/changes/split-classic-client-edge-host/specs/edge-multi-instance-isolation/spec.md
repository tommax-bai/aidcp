## REMOVED Requirements

### Requirement: 并存的运营前置约束

**Reason**: 该需求把三条并存前置里的两条降级为运营口头约定，并明文写着「本能力不提供跨实例保护」。
拆仓后这两条由 `@aidcp/edge-host` 的 MachineRuntimeCoordinator 在代码里强制：「两实例的 AdsPower
分身集合不重叠」由物理环境租约在触碰 Core 或浏览器之前具名拒绝取代；「先启动一个实例、待机器全局
AdsPower 本机服务稳定后再启第二个」由跨进程 runtime-init 串行化取代。原「分身重叠（被禁止的配置）」
场景描述的后果（两实例驱动同一个物理浏览器窗口而互相干扰）已被证实低估——见下方 ADDED 需求。
第三条「两实例 SHALL 保持默认 AdsPower 浏览器模式」不属于被取代的部分，已原样并入下方
「并存实例的机器级执行资源 MUST 由 Host 强制排他」继续保留，仍由运营保证。

**Migration**: 无数据或配置迁移。行为差异是：同一分身出现在两个并存实例的名册中，从「运营明令禁止、
代码不管」变为「第二个 owner 在启动 Core、浏览器或任何 AdsPower 生命周期动作之前被具名拒绝」。
运营侧不再需要人工保证分身集合不重叠，但仍需保证默认浏览器模式。

## ADDED Requirements

### Requirement: 并存实例的机器级执行资源 MUST 由 Host 强制排他

当两个或以上监督者实例使用不同 userData 目录并存时，`@aidcp/edge-host` SHALL 在启动任何 Core、
浏览器或 AdsPower 生命周期动作前，对目标物理执行环境取得跨 userData、跨客户端进程的机器级排他
租约。租约键 SHALL 基于不可变物理身份（`adspower` 模式至少包含分身 id），MUST NOT 仅使用可重命名
展示名、Cloud target 或客户端局部 envId。不同物理环境可分别被不同实例持有；同一物理环境即使分别
指向 dev 与 ol，也 MUST 具名拒绝第二个 owner 为 `environment_in_use`，不得静默接管、重复拉起或
仅依赖运营保证分身不重叠。

**该租约 MUST 覆盖全部「不经拒启即可拿到浏览器」的入口，而不只是启动入口。** 已核实同机双驱有
两道门，且两道都不经过会被指纹浏览器拒绝的启动调用：其一是分身已报告活跃时直接取调试端口附着；
其二是分身报告非活跃、但缓存目录里的调试端口仍然存活时的孤儿接管。只在启动调用上加闸对这两道门
完全无效。**租约判定 MUST 前置于「取端口」这一步本身**，而不是前置于启动调用。

**误判的代价是对方的浏览器被关掉，而不只是两边同时驱动。** 已核实：经上述任一道门附着上来的实例，
会把该浏览器记为「由本节点启动或接管」，从而在自己退出时对它执行停止与强制终止回收。因此第二个
owner 拿不到租约时的正确行为是**完全不碰**：MUST NOT 停止、MUST NOT 强制终止、MUST NOT 调试附着。
这与既有「不可重起终局」红线一致，本需求把该红线的约束时点从「处置一个已被识别的拒启终局时」
前移到「决定是否附着时」。

**呈现语义 SHALL 复用既有词汇，不另起一套。** 面向运营的原因 SHALL 呈现为「环境被其它端占用」，
其终局性质 SHALL 按「不可重起终局」处置：立即诚实停止、不计入有界重起预算、不显示「稍后自动重启」
之类与之矛盾的倒计时文案。

**本租约与实例级单实例锁是两层，MUST NOT 互相替代。** 单实例锁按 userData 目录划分、保护的是
同一个客户端实例不被重复启动；本租约按物理分身划分、保护的是同一个浏览器不被两个实例驱动。
不同 userData 的两个实例仍 SHALL 可以并存，只是不能落到同一个物理分身上。

租约 SHALL 使用跨进程原子排他机制，并记录不含凭证的 owner 摘要供用户解释冲突。正常关闭 SHALL
在受监督资源停止后释放自己的租约。**异常退出后的回收 MUST 同时满足两个条件**：证明原 owner 进程
已不存活，**且**从浏览器侧证明该物理环境的浏览器确已不在。只满足前者 SHALL 判定为孤儿租约并拒绝
接管——因为客户端进程死亡不会带走浏览器，此时接管等于合法地拿到一个半驱动状态的浏览器。
MUST NOT 只按超时或 PID 文件静默夺取租约。一个实例 MUST NOT 删除、终止或释放另一个存活实例
拥有的资源。

并存实例 SHALL 继续保持默认 AdsPower 浏览器模式；该项仍由运营保证，本能力不落代码强制，但它
不再与分身互斥混为一谈。

#### Scenario: 两实例使用不同分身

- **WHEN** 两个并存实例分别启动两个不同 AdsPower 分身
- **THEN** 两者分别取得自己的物理环境租约并可并行运行，互不因客户端单实例锁或 Host 租约被拦

#### Scenario: 第二个实例遇到已被持有且已活跃的分身

- **WHEN** 第二个实例请求一个已被第一个实例持有、且指纹浏览器报告为活跃的分身
- **THEN** 第二个实例在读取调试端口之前即被租约拒绝，呈现「环境被其它端占用」与非敏感 owner 摘要，且 MUST NOT 附着、停止或强制终止该浏览器；第一个实例继续运行且其浏览器不被关闭

#### Scenario: 第二个实例遇到已被持有但报告非活跃的分身

- **WHEN** 第二个实例请求一个已被第一个实例持有、但指纹浏览器报告为非活跃、而其缓存目录中的调试端口仍存活的分身
- **THEN** 孤儿接管路径同样先受租约拦截，第二个实例 MUST NOT 因为「端口校验通过、确实是这个分身的浏览器」就接管——端口校验只能证明浏览器身份，永远不能证明没有别人正在驱动它

#### Scenario: 同一分身分别指向 dev 与 ol

- **WHEN** 一个实例已用某分身连接 dev，另一个实例尝试用同一分身连接 ol
- **THEN** Host 仍将两者识别为同一物理执行资源并拒绝第二个 owner，MUST NOT 以 Cloud target 不同为由双开

#### Scenario: owner 进程已死但浏览器仍在

- **WHEN** 持有租约的客户端进程异常退出，其驱动的浏览器仍在运行，新的实例随后请求相同环境
- **THEN** Host 判定为孤儿租约并拒绝接管，具名呈现「环境被其它端占用」，MUST NOT 启动任何执行资源，也 MUST NOT 停止或附着那个浏览器

#### Scenario: owner 进程已死且浏览器确已不在

- **WHEN** 持有租约的客户端进程异常退出，且从浏览器侧证明该物理环境的浏览器确已不存在
- **THEN** Host 在两个条件都满足后回收租约并可正常启动，回收判据 MUST NOT 退化为仅按超时

### Requirement: MachineRuntimeCoordinator MUST coordinate the machine-level AdsPower runtime across Host processes

Every `@aidcp/edge-host` process SHALL use one MachineRuntimeCoordinator backed by cross-process atomic
primitives before it stages, starts, inspects or uses the machine-level AdsPower runtime. The coordinator
SHALL serialize runtime initialization, publish non-secret owner/version diagnostics and ensure concurrent
Host processes resolve one authoritative compatible Local API base. Separate in-memory single-flight
promises in each Host process MUST NOT be treated as machine-level coordination.

The coordination primitive SHALL be atomic exclusive file creation. The coordinator MUST NOT introduce a
resident coordination process, lock service, message broker or any additional network listener. Operating
system advisory locks that release automatically on process death MUST NOT be used for the profile lease,
because the resource being protected is a browser owned by a separate daemon and it outlives the client
process; automatic release would hand the second client a lease over a still-running browser. A short
critical section guarded by a timestamp file MAY be used for the global rate gate, where bounded timeout
takeover is safe because only a number is protected; that takeover rule MUST NOT be reused for the profile
lease.

#### Scenario: Two Hosts start on a cold machine

- **WHEN** two Host processes concurrently request different profiles before the AdsPower daemon is running
- **THEN** one process performs the bounded runtime stage/start while the other waits and then adopts the same verified compatible runtime/base without starting a second daemon

#### Scenario: Runtime initialization fails

- **WHEN** the Host holding the runtime-init lock cannot stage or start the packaged runtime
- **THEN** it publishes a named factual failure, releases only its coordination ownership and the waiting Host MUST NOT infer that the daemon is ready

### Requirement: A healthy compatible machine runtime MUST NOT be reset by a starting Host

A Host preparing the machine-level AdsPower runtime SHALL first determine whether a registered daemon is
already running and whether it is healthy and version-compatible. If it is, the Host SHALL adopt it and
MUST NOT stop, restart or restage over it. Stopping an existing daemon SHALL be permitted only when it is
proven unhealthy or version-incompatible and it has no live owner and no active profile. Host shutdown
MUST NOT stop the machine-level daemon merely because that Host is exiting.

This requirement exists because the pre-split behaviour is the opposite: the first successful runtime
preparation of each application session stops whatever registered daemon it finds and restarts it, with no
ownership, health or in-use check inside that branch. With two coexisting instances that means the second
instance's startup pulls the daemon out from under the first instance's running work.

#### Scenario: A second instance starts while the first is driving a profile

- **WHEN** a second Host process prepares the runtime while a healthy compatible daemon is already running and the first Host is driving a profile through it
- **THEN** the second Host adopts the running daemon, MUST NOT stop or restart it, and the first Host's profile keeps running uninterrupted

#### Scenario: The running daemon is unhealthy and unowned

- **WHEN** the registered daemon does not answer health probes and no Host holds a profile lease against it
- **THEN** the starting Host MAY stop and restart it, recording that it did so in non-secret diagnostics

### Requirement: AdsPower Local API pacing MUST be global across Host processes

The MachineRuntimeCoordinator SHALL enforce the configured AdsPower Local API minimum interval across every
Host and Core process using the shared daemon. It SHALL serialize the relevant lifecycle/write calls with a
cross-process rate gate and authoritative last-call fact. Per-process `1.1s` queues MAY remain as local
admission helpers but MUST NOT be the only protection, and MUST NOT be removed as part of this change.

#### Scenario: Different Hosts start different profiles concurrently

- **WHEN** Host A and Host B each pass their distinct profile lease and request Local API lifecycle writes at the same time
- **THEN** the machine rate gate releases the calls in one globally paced sequence, so the distinct profile leases do not create a Local API burst

### Requirement: An active incompatible machine runtime MUST fail closed without replacement

Host SHALL compare the running AdsPower runtime/protocol version with its embedded Host manifest. Compatible
Hosts MAY share the daemon. If the runtime is incompatible and has a live owner or active profile, the new
Host SHALL fail as `ads_runtime_version_conflict`; it MUST NOT stop, replace, restage over or start a competing
daemon. Host shutdown MUST NOT run machine-level `ads stop` merely because that Host is exiting.

#### Scenario: New Classic embeds an incompatible runtime while an old Host is active

- **WHEN** the new Host detects a different incompatible runtime/protocol version and the old Host still owns an active profile
- **THEN** the new Host reports `ads_runtime_version_conflict` and leaves the old daemon, profile and owner untouched

#### Scenario: One of two compatible Hosts exits

- **WHEN** two compatible Host processes share the daemon and one shuts down
- **THEN** the exiting Host closes only its Core/profile resources and releases its locks while the machine daemon and the other Host remain available
