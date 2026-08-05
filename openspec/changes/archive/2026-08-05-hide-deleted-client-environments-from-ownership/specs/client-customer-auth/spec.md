## MODIFIED Requirements

### Requirement: Admin environment registry and multi-user assignment

系统 SHALL 向运营提供一个受**内部**面板 JWT 保护的**端用户环境归属候选读口**，列出系统已知且生命周期不是 `deleted` 的环境及其**被分配到的客户清单**。生命周期为 `deleted` 的环境 MUST NOT 出现在该读口；完整删除历史 SHALL 继续由独立环境资产读口提供。该归属候选读口 MUST NOT 被客户令牌访问，也 MUST NOT 成为客户可达接口（不得注入客户鉴权服务）——客户侧可达的环境读**仍只有**吃 userId 的 scoped 方法（N2 不变量不被削弱）。

系统 SHALL 允许把同一个可分配环境显式归属给**多个**客户（多对多）；给某客户加入一个已归属其他客户的环境 MUST NOT 改变其他客户的归属集合。运营界面 SHALL 对被 ≥2 个客户归属的环境给出「多人」可见标识，并可查看具体客户名。

运营为某客户维护归属时 SHALL 能从候选池**勾选**环境加入，并可按「相对该客户是否已归属」筛选（待分配 / 已分配），默认展示待分配。

#### Scenario: 归属候选读口列出每环境的归属客户

- **WHEN** 运营持内部面板令牌请求端用户环境归属候选读口
- **THEN** 返回生命周期不是 `deleted` 的系统已知环境，每个环境带其被归属到的客户清单（含客户名）与归属人数

#### Scenario: 已删除环境不进入端用户归属候选池

- **WHEN** 一个环境的权威生命周期为 `deleted`，运营请求端用户环境归属候选读口
- **THEN** 响应 MUST NOT 包含该环境，环境归属抽屉的待分配与已分配候选均不可见该环境

#### Scenario: 完整删除历史仍由环境资产读口提供

- **WHEN** 同一个 `deleted` 环境仍保留在权威注册表供审计，运营请求独立环境资产读口
- **THEN** 响应仍包含该环境及其 `deleted` 生命周期真态

#### Scenario: 归属候选读口不可被客户令牌访问

- **WHEN** 持客户令牌请求端用户环境归属候选读口
- **THEN** 请求被拒（401），且客户侧不存在任何返回跨客户环境归属的接口

#### Scenario: 同一环境可归属多个客户且互不影响

- **WHEN** 运营把一个已归属客户 B 的可分配环境也加入客户 A 的归属集
- **THEN** 该环境同时出现在 A 与 B 的可见环境中，且客户 B 的归属集合不因此发生任何改变

#### Scenario: 被多客户共享的环境显示「多人」

- **WHEN** 某个可分配环境被 2 个或以上客户归属
- **THEN** 运营界面对该环境显示「多人」标识，并可查看归属它的具体客户名

### Requirement: Standalone environment registry decoupled from assignment

系统 SHALL 维护一张**独立于归属**的环境注册表 `client_environments`（env_key 主键 + label/platform/source），使环境可以「只登记、不归属任何客户」。管理侧端用户归属候选全集 MUST 先由「注册表 ∪ 归属表」形成并集，再排除权威生命周期为 `deleted` 的环境；生命周期不是 `deleted` 且未分配给任何客户的环境（assigneeCount=0）MUST 被列出，供后台「待分配」池呈现。label/platform MUST 优先取归属行最新非空值、回落注册表登记值。该表 MUST 由 `init()` 的 `CREATE TABLE IF NOT EXISTS` 自建（无迁移器），MUST NOT 加 FK 到 accounts 热点表。

该候选全集读为**跨用户聚合**，MUST 只接入受内部 JWT 的面板端点，MUST NOT 注入客户鉴权服务（N2 结构性无泄漏不变）。缺表（首启竞态）MUST fail-closed 回落空数组。独立环境资产读口 SHALL 保留注册表中的完整生命周期历史，不受归属候选过滤影响。

#### Scenario: 未分配且未删除的环境出现在待分配池

- **WHEN** 一个环境已登记进注册表、尚未归属任何客户且生命周期不是 `deleted`
- **THEN** 端用户归属候选全集 MUST 列出该环境，其 assigneeCount 为 0（后台呈现为「待分配」）

#### Scenario: 已归属但不在注册表的可分配环境不丢

- **WHEN** 某 env_key 只在归属表出现、注册表尚无，且没有 `deleted` 生命周期事实
- **THEN** 并集读 MUST 仍列出该环境，并带其真实归属客户与人数

#### Scenario: 已删除注册环境从归属候选并集中排除

- **WHEN** 某 env_key 存在于注册表或归属表，且注册表权威生命周期为 `deleted`
- **THEN** 端用户归属候选全集 MUST 排除该环境，但独立环境资产读口 MUST 继续保留其历史行

#### Scenario: 跨用户聚合不越权

- **WHEN** 持客户令牌的请求试图取得端用户归属候选全集
- **THEN** 客户侧 MUST 无此能力（只有吃 userId 的 scoped 读），候选全集只经内部面板端点
