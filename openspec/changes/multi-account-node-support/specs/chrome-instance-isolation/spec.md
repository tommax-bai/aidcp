## ADDED Requirements

### Requirement: 每个 edge 节点驱动独立的 Chrome 实例

每个 edge 节点 SHALL 驱动**自己专属的 Chrome 实例**，由一对**独立的调试端口与独立的用户数据目录**唯一确定；同机多节点 MUST NOT 共用同一调试端口或同一用户数据目录。用户数据目录 SHALL 可按 `<accountId>-<节点号>` 区分，使不同账号（以及为后续 Change B 预留的同账号不同节点）各自持有独立登录态与缓存。

#### Scenario: 两节点两浏览器互不干扰
- **WHEN** 同一台机器启动两个 edge 节点，各自分配了不同的调试端口与不同的用户数据目录
- **THEN** 启动出两个独立的 Chrome 进程（两个 PID、两个端口可独立应答），各自的登录态/cookie 互不影响、跨重启各自持久

### Requirement: 绝不静默接管或复用其它节点的浏览器

当 edge 探测到目标调试端口上已有存活的 Chrome 时，MUST NOT 静默 attach 复用它（那会让本节点驱动陌生账号的浏览器并伪装成功，违反「绝不静默假成功」）。默认行为 SHALL 是**诚实报错并停手**；仅当显式置 `AIDCP_CDP_ALLOW_REUSE` 时才允许复用。崩溃后残留的浏览器单例锁 MUST 仅在确认无存活进程持有时才清理，MUST NOT 盲目删除致并发损坏。

#### Scenario: 端口被占用时诚实失败而非接管
- **WHEN** 某节点要在调试端口 X 上拉起 Chrome，但端口 X 上已有另一个节点存活的 Chrome，且未设 `AIDCP_CDP_ALLOW_REUSE`
- **THEN** 该节点诚实报错并停止启动，不接管那个浏览器、不上报成功

#### Scenario: 残留单例锁仅在无活进程时清理
- **WHEN** 某节点的用户数据目录残留一个单例锁，但其指向的进程已不存在
- **THEN** 该节点在确认无存活进程持有后清理该锁并正常启动；若锁仍被某存活进程持有，则诚实失败而非强删

### Requirement: 多节点编排留在 edge 之外，保持边缘薄

节点的端口 / 用户数据目录 / 账号与节点身份（`AIDCP_ACCOUNT_ID` / `AIDCP_EDGE_ID`）的**分配与多进程拉起** SHALL 由 edge 核心之外的启动器承担，edge 核心 MUST NOT 内建账号循环 / 进程池 / 编排逻辑。**本能力本身不引入第三方指纹浏览器**——其默认浏览器为 edge 自起的真实指纹 Chrome；同机不同账号防关联（独立设备指纹 / 独立 IP）**经后续 change `adspower-browser-provider` 以显式 opt-in 的可插拔浏览器 provider 接入，非本 change 范围**。

#### Scenario: 编排不进 edge 核心
- **WHEN** 审查 edge 核心代码
- **THEN** 找不到为多账号/多节点而设的账号循环或进程池，端口/目录/身份均来自外部注入（环境变量），编排在 edge 之外
