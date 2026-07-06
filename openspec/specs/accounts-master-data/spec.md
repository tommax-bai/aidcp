# accounts-master-data Specification

## Purpose
TBD - created by archiving change aidcp-console-panel-mvp. Update Purpose after archive.
## Requirements
### Requirement: 真账号主表替换单硬编码账号，seed 一个 default 行

系统 SHALL 引入一张真 `accounts` 主表，替换今天唯一硬编码的 `default` 账号。迁移 SHALL **先 seed 恰好一个 `account_id='default'` 行**，与现有字面量对齐，使已按账号 keyed 的表（`risk_state` / `risk_counters` / `risk_interactions`）瞬间获得父行、零行为变化。表 SHALL 至少含：`account_id`（PK）、`label`、`platform`、`persona_ref`（指向版本控制 YAML 的路径）、`quota_level`、`status`（`active`/`paused`）、`paused_at`、`machine_label`（可空）、`group_label`（可空）、`created_at`。`account→machine` 映射 SHALL 放在该表上，MUST NOT 在 MVP/V1 另起 `edge_bindings` 表（近静态，YAGNI）。

#### Scenario: seed default 后运行闭环不变
- **WHEN** 账号表迁移执行并 seed 了一个 `default` 行
- **THEN** 运行中的边缘浏览闭环行为不变，已按账号 keyed 的风控表获得父行，无可见副作用

### Requirement: 运营暂停态持久化，去掉默认 active 回退，暂停跨重启存活

运营暂停态 SHALL 持久进 `accounts.status`/`paused_at`，折叠掉今天非持久的内存 `AccountStateManager`。系统 MUST 去掉「未知账号默认 active」回退——一个无显式 `status` 的账号行 MUST NOT 被默认成 `active`，否则一个被有意暂停的账号会在重启后静默复活。运营暂停态 MUST 与传输层 `pausedEdges`（验证码门控）保持区分（运营意图 vs 验证码门控）。

#### Scenario: 暂停账号重启后仍暂停
- **WHEN** 一个账号被运营暂停，随后 cloud 进程重启
- **THEN** 该账号从 `accounts.status` 读回仍为 `paused`，不静默复活为 active

#### Scenario: 运营暂停不等于验证码硬停
- **WHEN** 一个账号被运营暂停、同时其边缘并未触发验证码
- **THEN** 运营暂停态与 `pausedEdges` 各自独立，互不混淆

### Requirement: RiskControllerRegistry 每账号单写并提供 listStates

系统 SHALL 引入 `RiskControllerRegistry`（`Map<accountId, RiskController>`），从既有风控存储按账号懒加载一个 controller，并提供 `listStates()` 供面板总览。最终风控状态 SHALL 仍**按账号**经该账号的 controller 单写，registry 只做路由、MUST NOT 成为跨账号多路复用的 god-object。`interaction.occurred` SHALL 按事件上的 `accountId` 路由到对应 controller。

#### Scenario: 总览读多账号状态
- **WHEN** 面板请求账号总览且存在多个账号
- **THEN** registry 的 `listStates()` 返回各账号状态，每账号状态仍只由其自身 controller 写

#### Scenario: 事件按账号路由到正确 controller
- **WHEN** 一个带 `accountId` 的 `interaction.occurred` 到达
- **THEN** registry 把它路由到该 `accountId` 的 controller，单写按账号保持

### Requirement: publish_log 与 concepts 增 account_id 隔离列、自动回填

`publish_log` 与 `concepts` 表 SHALL 各增一列 `account_id TEXT NOT NULL DEFAULT 'default'`，为 additive 迁移、经默认值自动回填，使按账号隔离成为可能。概念**查询** SHALL 保持账号无关，直到隔离搜索记忆成为被证实的需求（YAGNI）。

#### Scenario: 增列自动回填
- **WHEN** 对 `publish_log` / `concepts` 执行增 `account_id` 列的迁移
- **THEN** 已有行经 `DEFAULT 'default'` 自动回填，无需手工数据迁移，现有读路径不被破坏

### Requirement: 账号平台真实昵称由云端角色驱动本人主页访问采集(edge 纯执行)

系统 SHALL 采集**当前登录账号自身**的小红书真实昵称用于后台展示,且**采集由云端角色驱动、edge 仅执行**:云端角色决定何时采、命令 edge 打开本人主页、解析上报的主页 DOM、单写持久化;**edge MUST NOT 做任何昵称相关决策**(不判定、不挑选、不门控)。该昵称只在账号**本人主页**可读(feed 页不含),故采集 SHALL 经一次「访问本人主页」完成。

采真名是**登录后的固定引导步骤**,与浏览会话/人设解耦:

- **触发与幂等(云端)**:当某连接的账号是真实平台 userid(非占位 `default`)**且** `accounts.nickname` 为 NULL 时,云端角色 SHALL 在**该账号登录后(edge hello)**驱动**恰好一次**本人主页访问;`nickname` 已非空则 MUST NOT 再绕路(无写放大)。该触发 **MUST NOT 被诚实人设启动闸阻断**——未绑人设、被启动闸拦下不开浏览会话的账号,登录后**仍** SHALL 采一次真名。绑了人设的账号经会话开始(`session_start`)触发同一采集体,行为不变。
- **红线:采集不等于浏览**。登录引导采集路径 **MUST** 只驱动「访问本人主页」这一个动作(经 `profile.open{direct}` + 读 `profile.detail` + 单写),**MUST NOT** 接入浏览反应链;未绑人设的账号采完真名后 **MUST** 闲置,**MUST NOT** 在默认人设上浏览/点赞/关注/评论/搜索。
- **执行(edge,纯操作)**:edge SHALL 按云端命令打开指定主页 id(`/user/profile/<id>`)、原样上报主页 DOM(含昵称;读不到则诚实置空,亦可由页面标题兜底),**MUST NOT** 含「这是不是自己」之类判定。
- **持久化(云端,单写、诚实)**:云端 SHALL **仅当**上报昵称非空时经单写接口 upsert 到该账号行;空(诚实失败)MUST NOT 覆盖已有真名、DB 保持 NULL 以便下次有界重试。
- **有界**:~20s 兜底超时(edge 静默/未登录不困死会话/连接);采空 K 次后退避,不永绕。`profile.open` 采集 MUST NOT 触发风控/预算/节奏。
- **调度开关**:全局调度关闭时 MUST NOT 驱动边端(连登录引导采集也不动)。
- **展示**:面板 API SHALL 暴露 `nickname`;console 一切展示账号名处 SHALL 按 `nickname → label → accountId` 回落(无真名回落运营标识,MUST NOT 展示假名)。

该要求 MUST NOT 改变 `account_id` 作为主键,MUST NOT 影响已按账号 keyed 的风控/发布/概念表,MUST NOT 新增协议消息类型(经已有 `profile.open` 命令的可选字段 + 已有 `profile.detail` 上报)。

#### Scenario: 真实账号且昵称未知 → 登录后(不经人设闸)驱动一次本人主页采集并持久化

- **WHEN** 某连接账号是真实 userid(非 `default`)且 `accounts.nickname` 为 NULL,该账号登录(edge hello)
- **THEN** 云端角色在**登录引导**(不要求开浏览会话、不要求绑人设)命令 edge 打开本人主页(`profile.open{authorId=accountId, direct}`),读上报的主页昵称,经单写接口持久化,且全程不浏览

#### Scenario: 未绑人设账号登录 → 仍采真名但绝不浏览(红线)

- **WHEN** 账号未绑人设、被诚实人设启动闸拦下(不开浏览会话),但库内昵称为 NULL 且全局调度开着,该账号登录
- **THEN** 云端**仅**驱动一次本人主页采集(恰一次 `profile.open{direct}`),采到非空昵称即持久化;**MUST NOT** 产生任何浏览指令(open_note/like/collect/follow/comment),采完即闲置

#### Scenario: 昵称已知 → 不再绕路

- **WHEN** `accounts.nickname` 已非空,该账号登录或会话开始
- **THEN** 云端不尝试昵称采集(无写放大、零扰动)

#### Scenario: 全局调度关闭 → 不驱动边端

- **WHEN** 全局调度开关关闭(运营显式暂停),未绑人设账号登录
- **THEN** 云端 MUST NOT 驱动任何命令(连登录引导采集也不动)

#### Scenario: 上报空昵称(诚实失败)→ 不写、有界重试

- **WHEN** edge 上报空昵称(未登录/读不到)
- **THEN** 云端 MUST NOT 写入,`accounts.nickname` 保持原值(NULL 则下次有界重试),采集经 ~20s 超时兜底干净收尾

#### Scenario: edge 纯执行,不新增协议

- **WHEN** 昵称采集链路运行(无论经会话开始还是登录引导)
- **THEN** edge 仅打开云端指定的主页 id 并原样上报主页 DOM(含标题兜底),不含任何昵称判定/自身识别;采集不新增协议消息类型

### Requirement: 握手时自动登记新账号

云端 SHALL 在 edge 以一个未登记的 `accountId` 握手时，对 `accounts` 主表做一次**幂等 upsert**，使该账号以一个**显式状态**出现在主表（从而在后台账号列表即时可见、等待配置人设）。该 upsert MUST NOT 覆盖一个已被运营配置过的同名账号行（不抹掉既有 `status`/标签/绑定），MUST NOT 把无显式状态的行默认成 `active`（与既有「去掉默认 active 回退」一致）。

#### Scenario: 新账号握手后出现在主表
- **WHEN** 一个此前不存在于 `accounts` 的 `accountId` 首次握手接入
- **THEN** 该账号以显式状态被登记进主表，后台账号列表可见，且不被默认成 `active`

#### Scenario: 已配置账号不被握手 upsert 覆盖
- **WHEN** 一个已被运营配置（如已暂停、已绑人设）的账号再次握手
- **THEN** 其既有行不被 upsert 抹掉或重置，配置保持

### Requirement: 账号人设绑定状态为派生字段

账号是否已绑人设 SHALL 作为一个**派生字段**对外暴露，以**人设存储中是否存在该账号的人设行**为唯一判据。死列 `accounts.persona_ref` MUST NOT 被用作绑定指针（保留不用）。

#### Scenario: 绑定状态以人设行存在为准
- **WHEN** 计算某账号的人设绑定状态
- **THEN** 有人设行 → 已绑，无人设行 → 未绑；不读取/不依赖 `persona_ref` 列

### Requirement: 账号以登录态读出的稳定 id 为主键登记，昵称仅作显示名

当节点在登录后读出真实账号身份并握手时，系统 SHALL 以该**登录态读出的稳定 id**（如平台 userid）作为账号主表主键自动登记该账号，MUST NOT 以运营外部指派的标签或可变昵称作为主键。账号昵称 SHALL 仅作显示名（与 `account-real-nickname` 协调：昵称=显示，稳定 id=主键）；昵称变化 MUST NOT 改变账号主键或其人设/风控绑定。该登记仍为幂等 upsert（不覆盖已配置行、不默认就绪态），与既有"握手时自动登记新账号"一致。

#### Scenario: 真实账号按稳定 id 登记进主表
- **WHEN** 一个此前不存在的真实账号在某节点登录后首次握手（携带登录态读出的稳定 id）
- **THEN** 该账号以其稳定 id 为主键登记进主表，显示名取其昵称（若可读），后台账号列表可见、等待配置人设

#### Scenario: 昵称改变不改主键与绑定
- **WHEN** 一个已登记账号在平台改了昵称
- **THEN** 其主表主键（稳定 id）与人设/风控绑定不变，仅显示名随之更新

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

