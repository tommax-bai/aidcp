## ADDED Requirements

### Requirement: 每个账号在任一时刻只归属一个执行目标

系统 SHALL 为每个账号维护一个「归属执行目标」事实（`accounts.execution_target`，取值 `dev` / `ol` / 未归属）。该事实 MUST 由服务端按本机部署配置注入，MUST NOT 从客户端请求、自然语言、`envKey` 或边缘上报推导——与其它按 `executionTarget` 隔离的持久异步工作同一条规则。

同一账号 MUST NOT 同时被两个 target 的自动化进程驱动。非归属 target 收到该账号的边缘握手时 MUST 以可区分的拒绝码（`execution_target_mismatch`）诚实拒绝，MUST NOT 放行后只在风控写入时才失败，MUST NOT 把它伪装成通用离线或连接失败。

归属为空时，首个在其上真实握手成功的 target MUST 以原子条件写占位（仅当归属为空时才写入），占位竞争落败方 MUST 转为只读并告警，MUST NOT 覆盖已有归属。迁移期 MUST NOT 用默认值批量回填归属——把全部存量账号回填成任一 target 会把另一 target 的生产账号静默划走。

#### Scenario: 非属主 target 的握手被诚实拒绝

- **WHEN** 某账号归属 `ol`，其边缘节点连到 `dev` 的自动化端点
- **THEN** 握手 MUST 被拒绝，拒绝信息 MUST 含真实归属 target 与处理办法
- **AND** 该连接 MUST NOT 被登记为可派活节点，MUST NOT 产生任何该账号的风控写

#### Scenario: 未归属账号由首次真实驱动占位

- **WHEN** 某账号归属为空，其边缘节点在 `dev` 上首次握手成功
- **THEN** `dev` MUST 以「仅当归属为空」的条件写占位为 `dev`
- **AND** 占位成功后该账号的计数 MUST 被重新回放一次

#### Scenario: 并发占位只有一方成功

- **WHEN** 同一未归属账号几乎同时在 `dev` 与 `ol` 上握手
- **THEN** 只有一方占位成功，另一方 MUST 观察到已被占位并转为拒绝（或观察模式下的告警），MUST NOT 覆盖

#### Scenario: 迁移不批量回填归属

- **WHEN** 引入归属字段的迁移在共库环境上执行
- **THEN** 存量账号的归属 MUST 保持为空并由运行时自证收敛
- **AND** MUST NOT 用统一默认值回填

### Requirement: 归属变更必须显式且不得与活跃会话重叠

账号归属的变更 SHALL 是显式的运维动作。系统 MUST 在变更前校验该账号在原属主上没有活跃边缘会话；存在活跃会话时 MUST 以可区分的拒绝（`owner_change_blocked_by_active_session`）拒绝变更，MUST NOT 强改。

变更生效后，原属主进程缓存的该账号控制器 MUST 失效：其下一次状态写 MUST 被属主谓词拒绝，并 MUST 触发缓存驱逐与告警。原属主 MUST NOT 继续用陈旧的内存状态为该账号做准入判定，MUST NOT 据此下发新的真实平台动作。

面板与控制台 MUST 按归属呈现可写 / 只读：非属主账号的风控写口 MUST 返回可区分拒绝，MUST NOT 返回成功状态码；界面 MUST 显示真实归属 target，未归属 MUST 显示为「未归属」而不是伪装成当前 target。

#### Scenario: 有活跃会话时改归属被拒

- **WHEN** 运营为一个在原属主上仍有活跃边缘会话的账号发起归属变更
- **THEN** 变更 MUST 被拒绝并说明原因
- **AND** 归属 MUST 保持不变

#### Scenario: 变更后原属主的写被挡住并驱逐缓存

- **WHEN** 归属从 `dev` 改到 `ol` 之后，`dev` 进程仍持有该账号的缓存控制器并尝试写状态
- **THEN** 该写 MUST 被属主谓词拒绝
- **AND** `dev` MUST 驱逐该账号的缓存控制器并告警，MUST NOT 重试覆盖

#### Scenario: 面板对非属主账号只读

- **WHEN** 运营在 `dev` 面板上对一个归属 `ol` 的账号点击风控信号或配额档位写入
- **THEN** 服务端 MUST 返回可区分拒绝并带上真实归属 target
- **AND** 界面 MUST 显示为失败并指向正确的后台，MUST NOT 显示成功或静默无反应
