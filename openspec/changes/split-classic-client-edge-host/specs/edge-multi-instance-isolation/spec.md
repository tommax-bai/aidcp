## MODIFIED Requirements

### Requirement: 并存实例的机器级执行资源 MUST 由 Host 强制排他

当两个或以上监督者实例使用不同 userData 目录并存时，`@aidcp/edge-host` SHALL 在启动任何 Core、
浏览器或 AdsPower 生命周期动作前，对目标物理执行环境取得跨 userData、跨客户端进程的机器级排他
租约。租约键 SHALL 基于不可变物理身份（`adspower` 模式至少包含分身 id），MUST NOT 仅使用可重命名
展示名、Cloud target 或客户端局部 envId。不同物理环境可分别被不同实例持有；同一物理环境即使分别
指向 dev 与 ol，也 MUST 具名拒绝第二个 owner 为 `environment_in_use`，不得静默接管、重复拉起或
仅依赖运营保证分身不重叠。

租约 SHALL 使用跨进程原子排他机制，并记录不含凭证的 owner 摘要供用户解释冲突。正常关闭 SHALL
在受监督资源停止后释放自己的租约；异常退出后的恢复 MUST 证明旧 owner 已不存活，MUST NOT 只按
超时或 PID 文件静默夺取租约。一个实例 MUST NOT 删除、终止或释放另一个存活实例拥有的资源。

#### Scenario: 两实例使用不同分身

- **WHEN** 两个并存实例分别启动两个不同 AdsPower 分身
- **THEN** 两者分别取得自己的物理环境租约并可并行运行，互不因客户端单实例锁或 Host 租约被拦

#### Scenario: 两实例使用同一分身

- **WHEN** 第二个实例尝试启动已被第一个实例持有的 AdsPower 分身
- **THEN** 第二个实例在触碰 Core 或浏览器前收到 `environment_in_use` 与非敏感 owner 摘要，第一个实例继续运行且不被接管

#### Scenario: 同一分身分别指向 dev 与 ol

- **WHEN** 一个实例已用某分身连接 dev，另一个实例尝试用同一分身连接 ol
- **THEN** Host 仍将两者识别为同一物理执行资源并拒绝第二个 owner，MUST NOT 以 Cloud target 不同为由双开

#### Scenario: owner 异常退出

- **WHEN** 持有租约的客户端进程异常退出且新的实例随后请求相同环境
- **THEN** Host 仅在原子锁已由操作系统释放或已证明旧 owner 不存活后取得新租约，并在取得前不启动任何执行资源
