## ADDED Requirements

### Requirement: Isolated customer token domain

对外客户鉴权 SHALL 使用独立签名密钥 `AIDCP_CLIENT_JWT_SECRET`,与内部面板密钥 `AIDCP_PANEL_JWT_SECRET` 物理隔离。系统 MUST 在启动时断言该密钥非空、非默认占位、且不等于面板密钥;断言不过 MUST 拒绝启动客户鉴权服务(不影响内部面板与边云主链)。客户令牌 MUST NOT 能通过内部面板的令牌校验,内部令牌 MUST NOT 能通过客户鉴权的令牌校验。

#### Scenario: 密钥缺失或与面板相同则拒启

- **WHEN** `AIDCP_CLIENT_JWT_SECRET` 为空、为默认占位、或等于 `AIDCP_PANEL_JWT_SECRET`
- **THEN** 客户鉴权服务 MUST 不启动并记录原因,内部面板与边云主链不受影响

#### Scenario: 客户令牌无法越权访问内部接口

- **WHEN** 持有效客户令牌的请求打向内部面板受保护端点
- **THEN** 校验以签名不匹配失败、返回 401,且不泄漏任何内部数据

### Requirement: Customer login with name and key

系统 SHALL 提供 `POST /login`,以 `{name, key}` 换取客户令牌 `{token, expiresIn}`。key 校验 MUST 用常量时间比较;name 未命中时 MUST 仍执行一次诱饵(decoy)哈希再返回 401,以抹平"用户是否存在"的时间差。登录 MUST 按 name 与来源 IP 双维限流,超阈返回 429。凭据错误 MUST 以统一的不可区分错误返回(不区分 name 不存在 vs key 不对)。

#### Scenario: 正确凭据签发客户令牌

- **WHEN** 提交的 name 存在、状态 enabled 且 key 正确
- **THEN** 返回 `{token, expiresIn}`,令牌 `sub` 为该客户内部 id

#### Scenario: 错误凭据不区分且防枚举

- **WHEN** name 不存在,或 key 不正确
- **THEN** 返回统一 401,且响应时延不因 name 是否存在而可区分

#### Scenario: 登录暴力尝试被限流

- **WHEN** 同一 name 或来源 IP 的失败尝试超过阈值
- **THEN** 后续尝试返回 429 直至冷却结束

### Requirement: Customer key is never stored or returned in plaintext

客户 key MUST 以加盐 scrypt 派生的哈希存储,系统 MUST NOT 落库或回传任何 key 明文。key 由系统高熵生成(不由客户自选),明文 MUST 仅在创建或轮换的那一次响应中回显一次,此后任何接口 MUST NOT 能读回明文。

#### Scenario: 创建时一次性回显明文

- **WHEN** 运营创建一个客户
- **THEN** 该次响应回显生成的明文 key 一次,库内只存其哈希与盐

#### Scenario: 事后无法读回明文

- **WHEN** 任何后续读取客户信息的请求
- **THEN** 响应 MUST NOT 包含 key 明文或哈希

### Requirement: Authoritative per-customer environment visibility

系统 SHALL 提供 `GET /my-environments`(需客户令牌),仅返回归属于该客户的环境清单。该端点 MUST 为环境可见性的**权威过滤点**:范围过滤 MUST 只在服务端按客户归属执行,MUST NOT 信任客户端传入的环境标识。每次请求 MUST 在验签后回库重新读取客户启用状态与当前归属(范围 MUST NOT 内嵌于令牌),以保证停用或改归属即时生效。

#### Scenario: 只返回本客户归属环境

- **WHEN** 客户 A 持有效令牌请求 `/my-environments`
- **THEN** 仅返回归属 A 的环境,绝不含其他客户的环境

#### Scenario: 改归属即时生效

- **WHEN** 运营移除客户 A 对某环境的归属后,A 再次请求
- **THEN** 该环境不再出现在返回清单中(无需等令牌过期)

#### Scenario: 停用客户令牌即时失效

- **WHEN** 客户被停用后,其未过期令牌再次请求任一受保护端点
- **THEN** 请求被拒(401/403),不返回任何数据

### Requirement: Fail-closed environment ownership

客户与环境的归属 SHALL 以独立显式归属记录表达,MUST NOT 复用可变的账号分组字段。未被显式归属的环境 MUST 默认不属于任何客户(fail-closed)。系统 MUST NOT 因新环境出现或分组字段变化而自动使其对某客户可见。

#### Scenario: 新环境默认不可见

- **WHEN** 一个新环境出现且未被任何客户显式归属
- **THEN** 它不出现在任何客户的 `/my-environments` 返回中

### Requirement: Customer disable and key rotation

系统 SHALL 支持停用客户与轮换客户 key。停用 MUST 为即时 kill switch(下次请求即失效)。轮换 MUST 使旧 key 立即无法登录并回显一次新明文 key;已签发的未过期令牌 MAY 存活至自然过期(以短 TTL 兜底)。

#### Scenario: 停用即时阻断登录与访问

- **WHEN** 客户被停用
- **THEN** 该客户 MUST 无法再登录,且其在途令牌下次请求即被拒

#### Scenario: 轮换使旧 key 失效

- **WHEN** 运营轮换某客户 key
- **THEN** 旧 key 立即登录失败,新明文 key 一次性回显

### Requirement: Internal-only customer management endpoints

系统 SHALL 提供受**内部**面板 JWT 保护的客户管理端点:列出客户(MUST NOT 含 key/哈希)、创建、改名/启停、轮换 key、读取与整批替换某客户的环境归属。这些端点 MUST NOT 被客户令牌访问。

#### Scenario: 客户令牌不可访问管理端点

- **WHEN** 持客户令牌请求任一客户管理端点
- **THEN** 请求被拒(401),不执行任何管理操作

#### Scenario: 整批替换归属为事务写

- **WHEN** 运营为某客户整批设置环境归属
- **THEN** 系统以事务替换其归属集合,写后回读真态,绝不部分落库

### Requirement: Auto-attribution of client-created environments

当已登录客户在客户端创建/添加新环境时,系统 SHALL 以该客户令牌把新环境显式归属到该客户;归属后运营 MAY 在后台调整。未在登录态创建的环境 MUST NOT 被自动归属。

#### Scenario: 登录态新建环境自动归属

- **WHEN** 客户 A 在登录态下新建一个环境
- **THEN** 该环境被显式登记为归属 A,并立即出现在 A 的 `/my-environments`
