## ADDED Requirements

### Requirement: accounts.platform 作为运行时平台事实源

`accounts.platform` SHALL 成为账号所属平台的运行时单一事实源。cloud 在按账号调度、选择平台 profile、校验 edge 连接、枚举平台账号时 MUST 读取该字段；平台信息 MUST NOT 在 soul/persona、环境变量、scheduler 局部配置中形成第二份权威副本。既有默认账号在未显式迁移前 SHALL 保持 `xiaohongshu` 平台语义。

#### Scenario: 按账号读取平台路由
- **WHEN** cloud 准备为某账号启动平台相关任务
- **THEN** cloud 从 `accounts.platform` 读取该账号平台，并据此选择对应 platform profile/registry 项

#### Scenario: 默认账号保持 xhs 语义
- **WHEN** 既有 `default` 账号未被运营显式改为其他平台
- **THEN** 该账号按 `xiaohongshu` 处理，现有 xhs 运行路径保持不变

### Requirement: edge 平台与账号平台不一致时诚实拒绝

edge 握手或任务接管时 SHALL 上报自身装配的平台。cloud MUST 校验该平台与目标账号的 `accounts.platform` 一致；不一致时 MUST 拒绝派发平台动作并暴露配置错误，MUST NOT 让 xhs edge 操作 Facebook 账号或反向混跑。

#### Scenario: 平台匹配则允许接管
- **WHEN** edge 上报平台 `xiaohongshu`，目标账号 `accounts.platform` 也是 `xiaohongshu`
- **THEN** cloud 允许该 edge 作为该账号的可路由节点

#### Scenario: 平台不匹配则拒绝派活
- **WHEN** edge 上报平台 `xiaohongshu`，但目标账号 `accounts.platform` 为 `facebook`
- **THEN** cloud 拒绝向该 edge 派发该账号的平台动作，并记录/暴露平台不匹配错误，MUST NOT 静默继续

### Requirement: 账号存储提供平台访问与枚举接口

cloud 账号存储 SHALL 提供读取单账号平台与按平台枚举账号的接口，供调度器、cron 和平台 registry 使用。枚举结果 MUST 尊重账号状态与既有账号主表约束；调用方 MUST NOT 通过手写 SQL 或本地缓存绕过账号存储形成不一致平台集合。

#### Scenario: 按平台枚举 Facebook 账号
- **WHEN** 后续 Facebook cron 需要找出可调度账号
- **THEN** 它通过账号存储按 `platform='facebook'` 枚举账号，而非扫描 persona 或读取局部 env 列表
