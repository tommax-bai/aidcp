## ADDED Requirements

### Requirement: 部署序列必须施加并核对数据库迁移

`dev` 与 `ol` 的部署流程 SHALL 在重启服务之前包含一个迁移步骤：先以只读方式查询迁移账本状态，确认没有异常且没有未审阅的待应用迁移；存在待应用迁移时 MUST 由操作者审阅后显式应用，MUST NOT 带着未应用的迁移重启服务。

迁移步骤失败时部署 MUST 中止，MUST NOT 继续 rsync 或重启。

部署后的健康检查 SHALL 除现有的服务状态与端口检查外，额外确认启动日志中出现 schema 版本校验通过行并含账本最高版本 id。仅确认进程处于运行状态 MUST NOT 被视为通过。

schema 版本校验在强制模式下把「账本落后于代码」表现为启动失败。该失败 SHALL 被视为预期行为，处置 MUST 是补跑迁移；MUST NOT 通过关闭校验或回滚代码来绕过。

#### Scenario: 待应用迁移未审阅时不重启服务

- **WHEN** 部署前的账本状态查询显示存在待应用迁移
- **THEN** 部署停在该步，等待操作者审阅并显式应用迁移，不执行服务重启

#### Scenario: 迁移失败中止部署

- **WHEN** 迁移应用过程中任一条失败
- **THEN** 部署中止并报出失败版本与原始数据库错误，不重启服务

#### Scenario: 健康检查确认 schema 版本

- **WHEN** 服务重启后执行健康检查
- **THEN** 检查项包含启动日志中的 schema 版本校验通过行与账本最高版本 id，而不只是进程运行状态

#### Scenario: 启动失败于版本落后时补迁移而非绕过

- **WHEN** 服务因账本版本低于代码所需版本而拒绝启动
- **THEN** 处置为补跑缺失迁移，不关闭版本校验、不回滚代码来掩盖

## MODIFIED Requirements

### Requirement: Dev and ol runtime state must be isolated

`ol` SHALL use a dedicated production PostgreSQL boundary for durable aidcp state. The dedicated boundary MAY be PostgreSQL local to `ol` or managed RDS, but it MUST NOT silently share mutable runtime state with `dev` for normal online operation.

A temporary `ol` to `dev` PostgreSQL bridge MAY be used only as a bootstrap or smoke-test step. Before such a bridge is used, `dev` PostgreSQL network access MUST be restricted to local connections plus the specific ol source, and docs/tasks MUST mark the bridge as temporary. The bridge MUST NOT be treated as the final online topology.

在 `dev` 与 `ol` 共用同一个数据库期间，数据库 schema SHALL 只有一条库级版本序列。迁移账本 MUST 是库级单表；执行目标 MUST 只作为审计信息记录，MUST NOT 用于为两个目标维护各自的版本序列。按 `execution_target` 隔离的规则适用于行级持久任务数据，MUST NOT 被套用到 schema 版本上。

共库期间的迁移 SHALL 只做扩张。收缩类迁移（删表、删列、重命名、类型收窄、加非空约束、约束收紧）MUST 需要显式授权才能应用，并 MUST 作为独立变更与独立部署交付。本约束是本文档破坏性 DDL 冻结条款在拆分与迁移期的延伸，不是新增护栏。

由于两个目标共用一条版本序列，`dev` 应用一条新的扩张迁移后，`ol` 侧运行的旧代码会观察到账本版本高于自己认识的最高版本。该情形 SHALL 由操作者逐次显式放行并记录，MUST NOT 通过永久开关一次性关闭该判定。

#### Scenario: Normal ol uses dedicated database

- **WHEN** `ol` is marked ready for online service
- **THEN** its cloud process SHALL connect to an ol-owned database boundary rather than the dev development database

#### Scenario: Temporary bridge requires allowlist

- **WHEN** `ol` is configured to connect to `dev` PostgreSQL for bootstrap or smoke testing
- **THEN** `dev` PostgreSQL access MUST be restricted away from `0.0.0.0/0`
- **AND** only local dev access plus the ol source SHALL be allowed for the aidcp app role
- **AND** the deployment note SHALL state that the bridge is temporary

#### Scenario: Shared mutable state is not final topology

- **WHEN** dev and ol cloud processes would both process real traffic against the same database
- **THEN** the setup MUST be treated as a temporary bridge or rejected
- **AND** it MUST NOT be documented as the steady-state online architecture

#### Scenario: 共库下 schema 只有一条版本序列

- **WHEN** dev 与 ol 连接同一个数据库，且一次迁移由其中一个目标施加
- **THEN** 账本只记一条，另一目标读到该迁移为已应用并跳过，不按目标维护第二条版本序列

#### Scenario: 共库期收缩迁移需要显式授权

- **WHEN** 共库期间待应用集合中出现收缩类迁移
- **THEN** 应用被默认拒绝，需要显式授权并记录授权者，且该迁移必须作为独立变更与独立部署交付

#### Scenario: ol 观察到账本超前时逐次放行

- **WHEN** `dev` 应用一条新的扩张迁移后，`ol` 上运行的旧代码启动时发现账本版本高于自己认识的最高版本
- **THEN** 操作者填写具体的放行版本 id 逐次放行并记录，不使用永久开关关闭该判定
