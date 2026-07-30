# client-customer-auth Specification

## Purpose
TBD - created by archiving change edge-client-customer-auth. Update Purpose after archive.
## Requirements
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

当已登录客户在官方客户端内通过 Electron 主进程的程序化 `user/create` 流程**明确新建**环境时，系统 SHALL 在创建前签发绑定当前客户的短时一次性创建意图；主进程取得 AdsPower 返回的真实 envKey 后，Cloud SHALL 以该意图在同一事务内登记新环境并将其显式唯一归属到当前客户。Cloud 完成归属后，客户端 MUST 重新读取 `/my-environments`；只有该权威读已包含新 envKey，主进程才可把环境加入并落盘运行花名册。加入花名册 MUST NOT 自动启动环境。

该能力只适用于本次程序化新建结果。普通客户请求、renderer、手填分身 ID、“加入已有环境”列表或旧 `POST /environments` MUST NOT 通过提交任意 envKey 创建、替换或恢复 ownership；已登记或已归属环境 MUST NOT 借创建完成端点被认领或转移。未在有效登录态创建的环境 MUST NOT 被自动归属。

创建意图 SHALL 短时过期、一次性且绑定客户；proof MUST 高熵、只回显一次并只以哈希落库。完成写 SHALL 幂等：同一意图与同一 envKey 重试返回相同归属真态，同一意图用于不同 envKey MUST 被拒绝。任一归属失败或权威回读不含该 envKey 时，客户端 MUST 如实说明“本机已创建但未完成分配”，MUST NOT 乐观加入花名册。

#### Scenario: 登录态程序化新建环境自动归属并入册
- **WHEN** 客户 A 在有效登录态下通过客户端“新建环境”触发程序化建号，创建意图有效，AdsPower 返回一个尚未登记的 envKey，Cloud 完成事务写且 `/my-environments` 回读包含该 envKey
- **THEN** 该环境被登记并唯一归属 A，主进程把它加入并落盘运行花名册，环境栏立即出现离线行，且环境不被自动启动

#### Scenario: intent 准备失败时不制造本地孤儿
- **WHEN** 客户鉴权启用但客户端在调用 AdsPower `user/create` 前无法取得有效创建意图
- **THEN** 客户端诚实拒绝本次创建并说明云端归属准备失败，MUST NOT 调用本地 `user/create`

#### Scenario: 本地已创建但权威归属未确认时不入册
- **WHEN** AdsPower 已返回新 envKey，但创建完成请求失败、意图过期、Cloud 拒绝或 `/my-environments` 权威回读不含该 envKey
- **THEN** 客户端标明环境仅在本机创建、未完成分配并给出管理员兜底，MUST NOT 把它加入运行花名册或显示为可启动环境

#### Scenario: 已有环境和任意 envKey 仍不能自认领
- **WHEN** 客户通过旧 `POST /environments`、手填 ID、“加入已有环境”或创建完成端点尝试认领一个已登记或已归属环境
- **THEN** Cloud 拒绝请求且原 owner 不变，客户后续 `/my-environments` 不得因此出现该环境

#### Scenario: 创建完成重试幂等且意图不可换目标
- **WHEN** 同一客户用同一 intent + proof + envKey 重试创建完成，或把同一 intent 改用于另一个 envKey
- **THEN** 前者返回同一成功归属真态且不重复插入，后者返回冲突且不得产生第二个 owner

#### Scenario: 未配代理不阻止归属但不自动启动
- **WHEN** 客户未配置代理即成功新建并完成权威归属
- **THEN** 环境仍被加入花名册并如实提示未配代理，但保持离线，必须由用户显式启动

#### Scenario: 自动入册后添加环境页面显示已加入
- **WHEN** 主进程已将新环境落盘到运行花名册并返回 `rosterJoinedByMain=true`
- **THEN** renderer 在刷新添加环境列表前重新读取主进程花名册，该环境行立即显示“已加入”，后续手动刷新或重开页面仍保持一致，且不得因此自动启动

#### Scenario: 从未绑定的视频号新建环境可以安全删除
- **WHEN** 当前客户删除一个由 completed provisioning intent 创建并归属、平台为视频号、且 Cloud 不存在互动账号绑定的环境
- **THEN** Cloud 在同一事务撤销 active scope、记录来源受限的终态 offboard 与审计，Edge 只有读到 `tombstoned|purged` 后才物理删除本机环境，不得返回 `offboard_binding_missing` 或假称执行过密文清理

#### Scenario: 非创建意图环境缺绑定仍然失败关闭
- **WHEN** 管理员分配或存量视频号环境缺失互动账号绑定，且没有对应的 completed provisioning intent 证明其从未绑定
- **THEN** Cloud 继续返回 `offboard_binding_missing` 并保留 active scope，本地客户端不得物理删除环境

### Requirement: Admin environment registry and multi-user assignment

系统 SHALL 向运营提供一个受**内部**面板 JWT 保护的**全局环境注册表**读口，列出系统已知的全部环境（每个环境至少被一个客户显式归属过）及其**被分配到的客户清单**。该读口 MUST NOT 被客户令牌访问，也 MUST NOT 成为客户可达接口（不得注入客户鉴权服务）——客户侧可达的环境读**仍只有**吃 userId 的 scoped 方法（N2 不变量不被削弱）。

系统 SHALL 允许把同一个环境显式归属给**多个**客户（多对多）；给某客户加入一个已归属其他客户的环境 MUST NOT 改变其他客户的归属集合。运营界面 SHALL 对被 ≥2 个客户归属的环境给出「多人」可见标识，并可查看具体客户名。

运营为某客户维护归属时 SHALL 能从注册表**勾选**环境加入，并可按「相对该客户是否已归属」筛选（待分配 / 已分配），默认展示待分配。

#### Scenario: 全局环境注册表列出每环境的归属客户

- **WHEN** 运营持内部面板令牌请求全局环境注册表
- **THEN** 返回系统已知的全部环境，每个环境带其被归属到的客户清单（含客户名）与归属人数

#### Scenario: 全局环境注册表不可被客户令牌访问

- **WHEN** 持客户令牌请求全局环境注册表读口
- **THEN** 请求被拒（401），且客户侧不存在任何返回跨客户环境归属的接口

#### Scenario: 同一环境可归属多个客户且互不影响

- **WHEN** 运营把一个已归属客户 B 的环境也加入客户 A 的归属集
- **THEN** 该环境同时出现在 A 与 B 的可见环境中，且客户 B 的归属集合不因此发生任何改变

#### Scenario: 被多客户共享的环境显示「多人」

- **WHEN** 某环境被 2 个或以上客户归属
- **THEN** 运营界面对该环境显示「多人」标识，并可查看归属它的具体客户名

### Requirement: Standalone environment registry decoupled from assignment

系统 SHALL 维护一张**独立于归属**的环境注册表 `client_environments`（env_key 主键 + label/platform/source），使环境可以「只登记、不归属任何客户」。管理侧的全局环境全集 MUST 为「注册表 ∪ 归属表」的并集——**未分配给任何客户的环境（assigneeCount=0）也 MUST 被列出**，供后台「待分配」池呈现。label/platform MUST 优先取归属行最新非空值、回落注册表登记值。该表 MUST 由 `init()` 的 `CREATE TABLE IF NOT EXISTS` 自建（无迁移器），MUST NOT 加 FK 到 accounts 热点表。

该全集读为**跨用户聚合**，MUST 只接入受内部 JWT 的面板端点，MUST NOT 注入客户鉴权服务（N2 结构性无泄漏不变）。缺表（首启竞态）MUST fail-closed 回落空数组。

#### Scenario: 未分配环境出现在待分配池

- **WHEN** 一个环境已登记进注册表但尚未归属任何客户
- **THEN** 全局环境全集读 MUST 列出该环境，其 assigneeCount 为 0（后台呈现为「待分配」）

#### Scenario: 已归属但不在注册表的环境不丢

- **WHEN** 某 env_key 只在归属表出现（如历史客户端自建 attach）、注册表尚无
- **THEN** 并集读 MUST 仍列出该环境，并带其真实归属客户与人数

#### Scenario: 跨用户聚合不越权

- **WHEN** 持客户令牌的请求试图取得全局环境全集
- **THEN** 客户侧 MUST 无此能力（只有吃 userId 的 scoped 读），全集读只经内部面板端点

### Requirement: Environment registration is assignment-free and idempotent

系统 SHALL 提供批量登记能力 `registerEnvironments(items, source)`，把环境写入注册表而**不产生任何归属**（MUST NOT 写归属表）。登记 MUST 幂等：冲突时只用**非空**新值补 label/platform（COALESCE，绝不拿 null 覆盖既有非空值），`source` 仅首次插入时定、冲突不降级。空 / 全空白 env_key MUST 跳过；MUST 按 env_key 去重。env_key MUST 为裸 profileId（不带 `ads-` 前缀），与边缘 attach / `/my-environments` 过滤口径逐字一致。

登记来源分三类：一次性导入存量环境（`import`）、边缘握手自动登记（`auto`）、后台手动登记（`admin`）。**任何自动路径 MUST NOT 推断归属**——绝不把环境塞给某个客户（fail-closed 归属边界不破）。

#### Scenario: 边缘连上自动进池但不归属

- **WHEN** 一个 AdsPower 环境（edgeId=`ads-<分身id>`）完成握手注册
- **THEN** 系统 MUST 以裸 profileId 登记该环境进注册表（source=auto），且 MUST NOT 为其创建任何客户归属

#### Scenario: 非分身兜底 edge 不登记

- **WHEN** 握手 edge 的 edgeId 非 `ads-` 前缀（self-/host- 兜底）
- **THEN** 系统 MUST NOT 把它登记为可分配环境

#### Scenario: 幂等登记不覆盖既有好值

- **WHEN** 对已登记环境再次登记、但新值 label 为空
- **THEN** MUST 保留既有非空 label，MUST NOT 用空值覆盖

### Requirement: Add-environment list is scoped to the logged-in customer (fail-closed)

客户端「添加环境 → 加入现有环境」列表 MUST 只展示归属当前登录客户的环境。**客户鉴权启用时,列出本机指纹浏览器环境的出口(`ads:listProfiles`)MUST NOT 存在任何返回本机全量列表的路径**——只有两种安全出口:① 存在有效会话 → 先刷新该客户的可见集,再按可见集(`allowedProfileIds`)收窄**显示**列表;② 无有效会话(含令牌到期但尚未清理)、刷新遇会话失效、或刷新后可见集不可信 → MUST 触发登出并诚实回报失败,MUST NOT 沿用旧集或回落全量。过滤判定 MUST NOT 仅以「会话当前有效」为门(否则令牌到期未清理的窗口期会跳过收窄、泄漏他人环境);可见集为空时展示零个,MUST NOT 因取集失败或缺数据回落为展示全部。未启用客户鉴权时 MUST NOT 过滤(零回归)。

收窄 MUST 只作用于**显示**:花名册孤儿剔除 MUST 按环境在本机指纹浏览器的**物理存在**判定(经出口另行下发的本机全部物理分身 id),MUST NOT 用云端可见集收窄后的显示列表判定——否则「云端降范围但本机仍在」的环境会被误当作已删除而销毁花名册项,并破坏管理员再授权后的自动恢复。

#### Scenario: 已登录客户只看到自己的环境

- **WHEN** 客户鉴权启用、存在有效会话,客户在加入面板拉取/刷新环境列表
- **THEN** 返回显示列表仅含归属当前客户的环境;非归属环境的名字/分组/代理/分身 ID 均不出现

#### Scenario: 令牌到期未清理时不回落全量

- **WHEN** 客户鉴权启用但当前会话已失效(如令牌到期、主窗仍开),客户刷新加入列表
- **THEN** 客户端登出、回登录门并诚实回报失败;MUST NOT 因「未按会话有效收窄」而返回本机全部环境

#### Scenario: 可见集为空则展示零个而非全量

- **WHEN** 当前客户名下无任何归属环境(可见集为空集),或本次刷新取集失败但此前已建立可见集
- **THEN** 加入列表展示零个/按上次已知集,MUST NOT 回落展示本机全部环境

#### Scenario: 降范围环境不被当作孤儿销毁

- **WHEN** 某环境仍物理存在于本机指纹浏览器,但已被管理员移出当前客户的可见集,客户刷新加入列表
- **THEN** 该环境不出现在显示列表,但其花名册项 MUST NOT 被剔除;管理员再授权后 MUST 能自动恢复运行

#### Scenario: 未启用鉴权时不过滤

- **WHEN** 客户鉴权未启用
- **THEN** 加入列表展示本机全部环境,孤儿剔除按物理列表判定,行为与启用前完全一致

#### Scenario: 非归属环境的分身 id 不经 IPC 泄漏给渲染层

- **WHEN** 客户鉴权启用,同机存在他客户的环境,客户刷新加入列表
- **THEN** 回给渲染层的任何字段(含供孤儿剔除的物理存在集)MUST NOT 含他客户环境的分身 id;只含当前客户已合法知晓的 id(归属集 ∪ 本地花名册)

### Requirement: Settings logout replaces the per-environment relogin button

客户端设置界面的原 per-环境「重新登录」按钮 MUST 移除,替换为客户端「退出登录」入口。触发该入口 MUST 清除客户会话、停掉全部在跑环境并返回 name+key 登录门(可重新登录账号),即复用既有客户端登出链路;为防误触停掉在跑环境 MUST 要求二次确认。当客户鉴权启用时该入口 MUST 显示并展示当前登录客户名;未启用客户鉴权时该入口 MUST NOT 出现(零回归)。移除设置按钮 MUST NOT 波及通知巡视引导流的「重检」——「重检」经独立 IPC 触发单环境运行内核重启,是与该设置按钮无关的另一条路径,MUST 保持可用。

#### Scenario: 设置里「退出登录」可退出客户端并重登

- **WHEN** 客户鉴权启用,客户在设置界面点「退出登录」并确认
- **THEN** 客户会话被清除、在跑环境全部停止、界面回到 name+key 登录门,可重新登录账号

#### Scenario: 未启用鉴权时不出现该入口

- **WHEN** 客户鉴权未启用
- **THEN** 设置界面不出现「退出登录」入口(页脚为空),行为与启用前一致

#### Scenario: 通知巡视「重检」不受设置按钮移除影响

- **WHEN** 通知巡视引导流触发某环境「重检」
- **THEN** 仍能经独立 IPC 重启该环境的运行内核(用于该环境账号重登后接上),不受设置「重新登录」按钮移除的影响

### Requirement: 客户只能修改当前环境的互动读取开关

customer-auth SHALL 提供 env-scoped `PUT /environments/:envKey/interactions/read-controls`。请求 MUST 只接受 `expectedVersion`、`commentsReadEnabled` 与 `dmReadEnabled`，并在同一 enabled-user、env ownership、account binding 权威范围内以 CAS 更新；账号写总闸、评论回复、私信发送、图片发送、自动发送和风险配置 MUST 保持原值且不可由客户请求体覆盖。成功后 SHALL 复用 runtime-control 下发链通知所属 Edge，并返回 stored/applied/effective 真态，MUST NOT 把 Cloud 保存成功显示成 Edge 已应用。

#### Scenario: 客户开启两个读取渠道但不能开启写
- **WHEN** 当前环境所有者以正确 expectedVersion 同时开启评论和私信收取
- **THEN** Cloud 只更新两个 read 字段、递增版本并下发所属 Edge，所有 write 字段逐位保持原值

#### Scenario: 客户请求夹带发送字段被拒绝
- **WHEN** 客户请求体额外携带 commentsReplyEnabled、dmSendTextEnabled 或 writePaused
- **THEN** customer-auth 返回校验失败且不修改任何 runtime control

#### Scenario: 旧版本更新不覆盖管理员新配置
- **WHEN** 管理员已更新 controls 版本而客户仍提交旧 expectedVersion
- **THEN** customer-auth 返回版本冲突与当前版本，MUST NOT 用旧快照覆盖管理员修改

### Requirement: 客户互动投影必须包含回复配置就绪状态
interaction list/detail 与 read-controls 成功回包 SHALL 为当前 account/env 返回只读 `replyConfig` 有效配置投影，至少区分 `missing`、`draft_only`、`published`、`unknown`，给出 current/draft/published version，并加性给出非敏感 `source`：`group` 或 `default` 及可展示的 group label。该投影 MUST 通过与回复工作流相同的 scoped resolver 得到，MUST NOT 读取账号旧策略，MUST NOT 包含 scope opaque ID、模板正文、规则条件、完整私信或 internal permission；查询失败 MUST 显示 unknown/fail-closed，不能伪造默认 published 配置。

#### Scenario: 无发布配置时客户端得到明确阻断
- **WHEN** 当前账号目标 group/default scope 不存在、没有 config head 或只有未发布 draft
- **THEN** 客户回包分别返回 missing 或 draft_only及其目标 source，客户端可保持收件箱可读并禁用依赖 published 配置的生成/发送流程

#### Scenario: 已发布配置只暴露版本和来源状态
- **WHEN** 当前账号解析到 immutable published group/default 配置
- **THEN** 客户回包返回 published、版本号与非敏感 source，不返回 scope ID、模板、规则、profile 或审计正文

#### Scenario: 有组缺配置不伪装成默认已发布
- **WHEN** 当前账号具有非空 group label 但该组没有 published 配置，同时 default 已发布
- **THEN** replyConfig 投影仍返回该 group source 的 missing/draft_only 状态，MUST NOT 返回 default published

### Requirement: 客户读取自助不得打通 internal 配置域

客户 JWT SHALL 继续不能访问 internal reply policy/template/rule/profile/preview/publish/audit 路径。客户侧读取开关 API MUST 使用独立 schema 与具名 renderer IPC，MUST NOT 接受任意 URL、internal token 或代理配置写入。

#### Scenario: 客户 token 调用内部配置发布仍被拒绝
- **WHEN** 客户使用有效 customer JWT 调用 internal reply-config/publish
- **THEN** 请求按认证域隔离被拒，已发布版本和 runtime write controls 均不变化

### Requirement: 环境↔账号绑定由握手事实持久供给

系统 SHALL 在环境注册表内持久保存每个环境**上一次握手所声明的平台账号 id**，使「这个环境上跑的是哪个账号」成为一个**不要求边缘此刻在线**即可回答的事实。

该绑定 SHALL 只由**已成功的边缘握手**供给：MUST 在握手被接受、welcome 已回发之后写入，MUST 为 fire-and-forget，**任何绑定写失败 MUST NOT 拒绝、延迟或影响该次握手**。绑定写 MUST NOT 创建、修改或推断任何客户归属（fail-closed 归属边界不破）——它只回答「是谁」，绝不回答「归谁」。

重绑语义 SHALL 为**最后一次握手为准**：每个环境至多一个绑定账号；合并 MUST 为「**来了新值才覆盖**」。系统 MUST NOT 实现成「当前为空才写」——那会把环境永久钉死在它的第一个登录账号上，而换号登录是常规运营动作。

握手声明的账号为退役保留账号 id 时，MUST 归一为「没有新值到达」：MUST NOT 写成绑定，且 MUST NOT 因此擦掉既有绑定。

绑定 SHALL 不追溯：本能力上线时既有环境一律为未绑定，MUST NOT 以任何回填脚本推断历史绑定；每个环境在其下一次握手时自愈。

#### Scenario: 握手落下绑定且不需要边缘持续在线

- **WHEN** 某分身环境的边缘完成一次成功握手并声明账号 A，随后该边缘断开
- **THEN** 环境注册表持有该环境→账号 A 的绑定
- **AND** 边缘离线期间按该环境解析账号 SHALL 仍然解析出 A

#### Scenario: 换号登录后重绑到新账号

- **WHEN** 某已绑定账号 A 的环境改登录账号 B 并再次握手
- **THEN** 该环境的绑定被改写为 B
- **AND** MUST NOT 因「已有绑定」而保留 A

#### Scenario: 握手未声明账号时不擦掉既有绑定

- **WHEN** 某已绑定账号 A 的环境的一次握手未声明账号、或声明的是退役保留账号 id
- **THEN** 该环境的绑定仍为 A，MUST NOT 被置空、MUST NOT 被写成退役保留 id

#### Scenario: 绑定写失败绝不牵连握手

- **WHEN** 边缘握手成功但绑定写入因存储故障失败
- **THEN** 该次握手仍然成功、welcome 已回发、连接正常工作
- **AND** 失败被记录，MUST NOT 抛出到连接主循环

### Requirement: 跨客户绑定冲突 fail-closed

因边缘握手无凭据、其声明的账号 id 是**自报字符串**，把该身份持久化并用于授权读，MUST NOT 放大既有暴露面。系统 SHALL 在**写与读两侧**都拒绝跨客户的绑定冲突。

**写侧**：绑定写入时，若该账号已绑定在**另一个环境**上、且该环境的归属客户与本次环境的归属客户**不同**（未被任何客户归属记作一个与任何客户都不同的值），系统 MUST 拒绝本次绑定写、MUST 保持既有绑定不变、MUST 产生一条可被运维看到的告警。被拒环境 SHALL 在其归属被更正后的下一次握手自愈。

**读侧**：解析某环境的绑定账号时，若同一账号同时绑定在归属**不同客户**的环境上，解析 MUST 失败（fail-closed），MUST NOT 返回该账号的任何数据。读侧闸 MUST 独立存在而不得以写侧闸替代——写侧只在写的那一刻检查，无法看见**事后改归属**造成的冲突。

冲突失败 MUST 与「该环境尚未上报过账号」在协议上**可区分**：前者是安全事件，后者是日常态；两者共用一个错误码 MUST 视为把告警埋进噪声。

同一客户名下的多个环境绑定同一账号 MUST NOT 被视为冲突——没有任何客户边界被跨越。

#### Scenario: 恶意边缘无法把自己环境绑到他人账号上

- **WHEN** 客户 B 拥有的环境握手时声明的账号已绑定在客户 A 拥有的环境上
- **THEN** 该绑定写被拒绝、客户 A 的既有绑定不变、系统发出告警
- **AND** 客户 B 按该环境发起的任何账号态读 MUST NOT 返回客户 A 账号的数据

#### Scenario: 事后改归属造成的争用在读侧被挡

- **WHEN** 两个环境已各自绑定同一账号，管理员随后把其中一个改归属给另一个客户
- **THEN** 两个环境上的账号解析均 fail-closed，返回可区分的冲突失败
- **AND** MUST NOT 有任何一侧读到该账号的精选内容或委托任务

#### Scenario: 同客户内的账号迁移不被误判为冲突

- **WHEN** 同一客户拥有的两个环境先后以同一账号握手
- **THEN** 两次绑定写均被接受，MUST NOT 产生冲突告警

### Requirement: 客户端账号态读 MUST 经绑定解析，未解析绝不伪装成空

客户端提交的环境标识与库内的账号标识是**两个不同的键空间**。客户端账号态的读（精选内容列表与详情、成稿汇总、委托任务列表）SHALL 先经**唯一的绑定解析器**把环境标识翻译为绑定账号，再以该账号查询。系统 MUST NOT 把环境标识直接作为账号 id 传入任何按账号过滤的查询。

解析的正向（环境→账号）与反向（某账号是否可被该客户经其环境触达）SHALL 由**同一个绑定与归属的权威联接**派生，MUST NOT 各自重写一份——两个方向都只是裸字符串，类型检查抓不到它们的漂移。

解析结果 SHALL 为**判别式**，MUST NOT 为「账号或空」——后者会立即退化回「不知道为什么，就当没有数据」。四种不可解析 SHALL 各自诚实回报且**互相可区分**：环境不归属该客户、该环境尚未上报过账号、绑定被跨客户争用、注册表读取不可用。

**任何一种不可解析 MUST NOT 呈现为成功的空结果集。** 只有在绑定解析成功、且该账号在库内确实零行时，才 SHALL 返回成功的空结果。这条约束在语义上等同于本系统「MUST NOT 静默假成功」红线：把失败谎报为「你没有数据」与把失败谎报为成功，同为不诚实。

按任务标识执行的动作 SHALL 以同一权威联接判定归属，MUST NOT 以「任务上的账号 id 是否等于某个环境标识」判定——该比较恒不成立，会对**正当所有者**回报「环境不归你」。

底层精选存储缺表或不可读时，只读接口 MUST 诚实回报服务不可用，MUST NOT 回落为空结果，MUST NOT 回报「未找到」（该行可能存在）。

#### Scenario: 已绑定环境读到本账号的精选内容

- **WHEN** 客户按其拥有且已绑定账号 A 的环境请求精选内容列表，账号 A 在库内有若干行
- **THEN** 返回账号 A 的行与一致的总数
- **AND** 边缘是否在线不影响该读

#### Scenario: 未绑定环境诚实回报而不是空池

- **WHEN** 客户按其拥有但尚未上报过账号的环境请求精选内容列表
- **THEN** 接口以「该环境尚未上报过账号」的可区分失败回报
- **AND** MUST NOT 返回 200 与空结果集
- **AND** MUST NOT 回报「环境不归你」

#### Scenario: 争用绑定与未绑定不共用一个码

- **WHEN** 一个环境的绑定被跨客户争用，另一个环境从未上报过账号，客户分别读取两者
- **THEN** 两次失败携带互相可区分的原因
- **AND** 争用的那次 MUST 可被运维识别为安全事件

#### Scenario: 成稿汇总与委托任务列表不再恒为零

- **WHEN** 客户按其拥有且已绑定账号 A 的环境请求成稿汇总与委托任务列表，账号 A 名下确有成稿与任务
- **THEN** 两者返回账号 A 的真实数量与任务行
- **AND** MUST NOT 因键空间不匹配而恒为 0 或空

#### Scenario: 正当所有者的任务动作不被诬告

- **WHEN** 客户对一条属于其已绑定账号的委托任务执行确认、暂停、恢复或取消
- **THEN** 归属判定通过、动作被执行
- **AND** MUST NOT 回报「环境不归你」

#### Scenario: 缺表回服务不可用而非空池

- **WHEN** 底层精选表缺失或不可读，客户请求精选内容列表或详情
- **THEN** 接口回报服务不可用
- **AND** MUST NOT 返回空结果集、MUST NOT 回报「未找到」

### Requirement: 不可逆写 MUST 由活会话佐证绑定

绑定是**上一次握手的事实**，可能已经陈旧。陈旧绑定在**读与纯云端候审内容生成**上的代价是取到该环境上一个账号的语料或为其生成一份可拒绝的候审稿；在**不可逆平台写**上的代价是**动作已经发生且无法收回**。两者 MUST NOT 适用同一强度。

客户端触发的精选内容洗稿 SHALL 先经唯一的持久绑定解析器解析账号，并以服务端固定的 `review` 模式创建任务；该创建阶段只排队云端生成并落库候审稿，MUST NOT 要求账号此刻存在活边缘会话，MUST NOT 因浏览器未启动返回 `binding_unverified`。客户端仍 MUST NOT 提交或选择 `accountId`，未绑定、跨客户争用、悬空账号或绑定查询失败仍 MUST fail-closed。

客户端触发的其它不可逆或具备发布能力的写，以及洗稿候审稿在审批后的平台下发，SHALL 在真正需要平台执行前要求可定向的活边缘。在线佐证不成立时 MUST 诚实等待或拒绝，MUST NOT 广播、猜测执行端、依据持久绑定宣称平台动作已开始或已经成功。

洗稿任务创建成功只表示任务已入队；生成完成进入 `pending_approval` 只表示候审稿已持久化。两者 MUST NOT 被呈现为平台已经发布。

#### Scenario: 环境停机时仍可发起精选内容洗稿

- **WHEN** 客户对其拥有且已绑定账号 A 的环境发起精选内容洗稿，但账号 A 此刻没有活在该环境上
- **THEN** 云端经持久绑定解析账号 A，并以 `review` 模式为账号 A 创建洗稿任务
- **AND** MUST NOT 因浏览器离线返回 `binding_unverified`，MUST NOT 启动浏览器或宣称已经发布

#### Scenario: 未绑定或争用环境仍不得离线猜账号

- **WHEN** 客户从未上报账号或存在跨客户绑定争用的环境发起精选内容洗稿
- **THEN** 请求按对应绑定失败原因 fail-closed
- **AND** MUST NOT 创建任务、MUST NOT 从其它环境或客户端输入猜测账号

#### Scenario: 洗稿候审稿获批后仍需活执行端

- **WHEN** 离线创建的洗稿任务已生成 `pending_approval` 候审稿，随后收到有效发布审批，但目标账号没有可定向的活边缘
- **THEN** 平台下发 SHALL 诚实等待或失败，MUST NOT 广播到其它边缘
- **AND** MUST NOT 把入队、生成或审批成功表述为平台已发布

#### Scenario: 通用发布类委托仍保留创建时在线闸

- **WHEN** 客户通过通用结构化委托入口创建发布类任务，而绑定账号没有活在所选环境上
- **THEN** 请求仍以 `binding_unverified` 拒绝且不创建任务

#### Scenario: 活体前置绝不外溢到读

- **WHEN** 某环境的边缘完全离线，客户读取精选内容列表、详情、成稿汇总或委托任务列表
- **THEN** 四者均正常返回该绑定账号的数据
- **AND** MUST NOT 因边缘离线而拒绝任何一次读

### Requirement: 命令定向下发 SHALL 继续以边缘活会话为准

「把命令发给哪台边缘」的解析 SHALL 继续基于活会话（OPEN 且非 stale 的连接），无在线节点时 SHALL 诚实失败、MUST NOT 广播。该在线判据 MUST NOT 因慢启动或精选内容离线洗稿改用持久绑定而被一并摘除。

判据 SHALL 为：一道在线前置是**本质的**，当且仅当没有活边缘这件事本身就让该阶段**无法被兑现**。命令下发没有收件人即无法兑现，故其在线判据是本质的；`slow_start_since` 的执行体与洗稿生成阶段在云端，故其在线判据是附带的、SHALL 被摘除。洗稿任务创建不等于命令下发，平台发布阶段仍受本要求约束。

反方向的「某边缘此刻在跑哪个账号」解析器在其最后一个生产调用点消失后 SHALL 被删除，MUST NOT 作为可复用工具留存——留存即为「按自报的活会话猜账号」保留一个现成入口。

#### Scenario: 账号无在线边缘时命令下发仍诚实失败

- **WHEN** 需要向某账号定向下发命令，但该账号没有 OPEN 且非 stale 的边缘连接
- **THEN** 云端诚实失败，MUST NOT 广播给其它边缘，MUST NOT 回落到持久绑定去猜一台机器

#### Scenario: 洗稿生成与平台下发使用不同在线强度

- **WHEN** 精选内容洗稿在浏览器离线时创建并完成候审稿生成，但目标账号仍无活边缘
- **THEN** 候审稿可以保持 `pending_approval`，平台下发的在线前置 MUST 保留
- **AND** MUST NOT 援引离线洗稿能力绕过发布下发闸

#### Scenario: 通用不可逆操作保留在线前置

- **WHEN** 某客户端操作在当前阶段只有活浏览器才能兑现，或通过通用入口创建具备发布能力的委托任务
- **THEN** 其边缘在线前置 MUST 保留

#### Scenario: 一个环境至多解析出一个账号

- **WHEN** 云端为某 `envKey` 解析写入目标账号
- **THEN** 绑定的主键约束 SHALL 保证结果只能是恰好一个账号或没有绑定
- **AND** MUST NOT 存在「多个候选里任取其一」的路径

### Requirement: Authoritative assigned environments default into the client roster

When customer authentication is enabled, the official client SHALL treat the intersection of the logged-in customer's authoritative assigned environments and the complete local physical environment list as the default running roster. Default roster enrollment MUST remain subordinate to authoritative ownership, MUST persist without starting an environment, and MUST preserve a customer-controlled manual exclusion. The client MUST scope the exclusion to the current customer, MUST NOT carry it across customer identities, and MUST fail closed without changing roster or exclusion state when the authoritative or physical list is incomplete or untrusted.

#### Scenario: Assigned local environments become visible by default
- **WHEN** an authenticated customer has multiple authoritatively assigned environments that exist in the complete local physical list
- **THEN** every non-excluded environment is persisted into the running roster and becomes visible as an offline row without being started

#### Scenario: Manual exclusion cannot expand tenant scope
- **WHEN** the renderer saves manual exclusions while customer authentication is enabled
- **THEN** the main process accepts only envKeys in the current authoritative assigned set and MUST NOT let the renderer store another customer's envKey

#### Scenario: Different customer does not inherit exclusions
- **WHEN** a different customer logs in on the same client installation
- **THEN** the new customer starts with no exclusions inherited from the previous customer and their assigned local environments follow the default enrollment rule

#### Scenario: Incomplete truth preserves prior state
- **WHEN** ownership refresh fails, the local profile result is truncated or empty, or the session becomes invalid
- **THEN** the client does not default-enroll, remove, or clear exclusions based on that result and MUST NOT fall back to another customer's or the full local environment set

### Requirement: 客户待审稿读取按授权环境绑定账号隔离

客户鉴权域 SHALL 提供当前授权环境绑定账号的待审稿列表与单条详情只读接口。请求 MUST 逐次从 `envKey` 解析持久账号绑定，并在 SQL 中同时约束 `account_id` 与 `status='pending_approval'`；列表 MUST 使用同一筛选条件返回一致 total、limit、offset。响应 SHALL 只披露审核所需稿件字段，不得返回来源原稿快照、内部 provider/model 诊断、审批凭据、其它账号信息或 panel 专用字段。绑定未知/冲突与跨账号 id MUST fail-closed，不得伪装成空列表或泄漏存在性。

#### Scenario: 当前账号多稿分页

- **WHEN** 已授权环境绑定账号 A 且 A 有 15 条待审稿，客户请求 limit=12 offset=0
- **THEN** 返回 A 的 12 条稿件与 total=15，不出现其它账号或非待审状态记录

#### Scenario: 单条详情按账号与状态过滤

- **WHEN** 客户请求属于其它账号、已发布或不存在的稿件 id
- **THEN** 接口返回同形 404，不泄漏该 id 是否在其它账号或其它状态存在

#### Scenario: 最小披露 DTO

- **WHEN** 列表或详情读取成功
- **THEN** 响应只包含稿件 id、类型、标题、正文/摘要、话题、配图、内容版本、更新时间、平台与发布计划，不包含 sourceReference、视觉模型诊断、审批签名或账号选择字段

#### Scenario: 环境绑定未知不伪装为空

- **WHEN** envKey 属于客户但尚未解析唯一账号或存在跨客户冲突
- **THEN** 接口返回既有稳定绑定拒因，不返回 `items=[]/total=0`

### Requirement: 客户灵感库按持久化洗稿触发记录分类

客户鉴权服务的精选列表新筛选 MUST 接受 `uncreated`、`created` 或 `all`，并 MUST 在客户 JWT、撤销、启用态与环境归属校验所得的账号范围内，通过既有 `delegated_tasks.source_constraints` 真态判断是否曾持久化洗稿触发任务；请求 MUST NOT 接受可绕过归属检查的 `accountId`，另一账号的任务 MUST NOT 改变当前账号归类，任务当前或终态也不得改变该归类。滚动发布期 SHALL 继续接受旧 `creatable`，且 MUST 精确返回 `uncreated ∪ created` 的原可创作集合；新客户端 MUST NOT 再产生该值。其它未知值 SHALL 以具名无效筛选错误拒绝，不得静默回落。

#### Scenario: 已归属环境可读取三种精选筛选

- **WHEN** 客户持有有效客户令牌，以当前仍归属于自己的 `envKey` 请求 `uncreated`、`created` 或 `all` 列表
- **THEN** 服务端只返回该 `envKey` 绑定账号的客户展示字段和与该筛选一致的分页总数

#### Scenario: 触发记录关联保持账号隔离

- **WHEN** 另一账号存在相同来源 id 或精选 id 的洗稿触发任务
- **THEN** 该记录不得改变当前账号灵感在“未创作”或“已创作”中的归类

#### Scenario: 旧客户端筛选保持原语义

- **WHEN** 尚未更新的客户端请求 `mode=creatable`
- **THEN** 服务端返回正文非空的全部图文灵感，不按是否触发洗稿拆分，也不包含视频、评论或空正文

#### Scenario: 未知筛选被明确拒绝

- **WHEN** 客户请求其它未定义筛选值
- **THEN** 服务端返回无效筛选错误，且不触达精选列表查询

#### Scenario: 非归属环境被拒绝且不泄漏内容

- **WHEN** 客户以未归属或刚被移除的 `envKey` 请求列表、详情或参考创作
- **THEN** 服务端拒绝请求，不返回该环境是否存在、精选数量或任意内容字段

#### Scenario: 跨账号单条 id 统一未找到

- **WHEN** 客户提交一个真实存在但属于其它账号的精选内容 id
- **THEN** 单条接口返回与不存在 id 相同的 404 形状，不泄漏该行存在性

### Requirement: 程序化 Facebook 环境归属与默认慢启动原子完成

customer-auth 的程序化环境归属完成接口 SHALL 接受可选布尔字段 `slowStartEnabled`，并保持省略该字段的旧客户端请求兼容。`slowStartEnabled=true` MUST 仅在同一请求的规范平台为 `facebook` 时接受；小红书、视频号、未知平台或非布尔值 MUST fail-closed，且不得部分注册环境或写入归属。

该接口 SHALL 另外接受两个可选的 Facebook 专属创建意图：环境规则模式开启意图与环境评论审批覆盖模式（`source_rules|auto_approve_all`）。两者 MUST 仅在规范平台为 `facebook` 时接受，非 Facebook 平台、非法枚举或非布尔值 MUST 在注册环境前拒绝整个请求。请求体 MUST 继续走严格白名单：夹带白名单之外的任何键 MUST 整块拒绝且不写入。`slowStartEnabled=true` 与规则模式开启意图 MUST NOT 在同一请求中同时为真，同时提交 MUST fail-closed 拒绝，MUST NOT 静默取其一。

首次成功完成 Facebook 创建 intent 时，Cloud SHALL 在同一数据库事务中插入环境、写入唯一客户归属、完成 intent，并按本次提交的意图写入该环境的慢启动起点、规则模式配置与评论审批策略。慢启动起点为服务端当前时刻所属上海自然日的 00:00，同时显式标记初始化完成；未提交开启意图时慢启动字段保持 NULL。慢启动起点 MUST NOT 取 Edge 时钟、账号入库时间、Cookie 时间或 `accounts.slow_start_since`。

已完成 intent 的幂等重试 MUST 只返回既成归属，不得再次写入或重置慢启动起点、规则模式配置或审批策略；若运营在首次完成后手动更改过其中任何一项，陈旧重试 MUST NOT 复原。接口不得修改风控档位、风险状态、账号旧慢启动列或其它环境配置。

#### Scenario: Facebook 创建原子写入 D1 起点

- **WHEN** 有效客户使用待完成 intent 注册一个全新 Facebook 环境并提交 `slowStartEnabled=true`
- **THEN** 环境、归属、intent 完成态与上海当日 00:00 慢启动起点在同一事务中提交

#### Scenario: Facebook 创建原子写入规则模式与免审

- **WHEN** 有效客户在完成请求中提交规则模式开启意图与 `auto_approve_all`
- **THEN** 环境、归属、intent 完成态、该环境规则模式配置与评论审批策略在同一事务中提交
- **AND** 未提交慢启动开启意图时该环境慢启动字段保持 NULL

#### Scenario: 旧客户端省略字段保持兼容

- **WHEN** 有效旧客户端完成环境归属但未提交 `slowStartEnabled`
- **THEN** 请求继续按既有规则成功，环境慢启动字段保持 NULL

#### Scenario: 非 Facebook 开启意图原子拒绝

- **WHEN** 请求以小红书、视频号或未知平台提交 `slowStartEnabled=true`、规则模式开启意图或审批模式字段
- **THEN** Cloud 在注册环境前拒绝整个请求，环境、归属和 intent 均不发生部分写入

#### Scenario: 慢启动与规则模式互斥意图被拒绝

- **WHEN** 同一 Facebook 完成请求同时提交 `slowStartEnabled=true` 与规则模式开启意图
- **THEN** Cloud 在注册环境前拒绝整个请求，MUST NOT 只取其中一项写入

#### Scenario: 完成重试不重置或复活慢启动

- **WHEN** Facebook intent 已成功完成，随后同一 intent/环境被再次提交
- **THEN** Cloud 返回幂等成功但不更新 `slow_start_since`、规则模式配置或审批策略
- **AND** 即使该环境已被运营手动更改，也不得复原为创建时的值

### Requirement: 客户态 Cloud 操作 MUST 逐请求解析环境归属与账号绑定

由客户鉴权直接执行的人设、内容、待审编辑、审批受理、配置及其他 AIDCP 自有数据操作 SHALL 只接收客户令牌上下文、`envKey` 与最小业务入参，并 SHALL 通过逐请求 customer-auth HTTP 执行。Cloud MUST 每次验证客户状态和环境归属并从权威绑定解析 `accountId`，MUST NOT 采信 renderer 或请求体自报账号。该类操作 MUST NOT 以普通自动化引擎进程、automation WebSocket、浏览器登录、CDP 或槽位为准入条件；renderer MUST NOT 获得客户令牌、权威 `accountId` 或通用 HTTP 能力。

#### Scenario: 引擎和浏览器均缺席时生成客户人设

- **WHEN** 客户已登录、拥有环境且其账号绑定可信，但自动化引擎停止、浏览器关闭且无 CDP
- **THEN** Cloud 由 customer-auth HTTP 请求解析账号归属并执行人设生成，MUST NOT 返回“请启动自动化/浏览器”或等待浏览器槽位

#### Scenario: 自动化 WebSocket 离线时审批待审稿

- **WHEN** automation WebSocket 不可用但 customer-auth HTTP 可达，客户批准一份待审稿
- **THEN** Cloud 记录并返回“决定已受理/平台执行待完成”，MUST NOT 因引擎离线拒绝受理，也不得显示已发布

#### Scenario: 客户请求越权环境

- **WHEN** 客户请求中的 `envKey` 不属于当前客户，或该环境绑定无法权威解析
- **THEN** Cloud 以可区分拒因 fail-closed，MUST NOT 使用请求体账号、历史 UI 缓存或浏览器启动来绕过校验

#### Scenario: 环境概览离线于自动化引擎可读

- **WHEN** 客户读取所拥有环境的今日进展与发布摘要，而该环境没有在线 Edge 或浏览器
- **THEN** Cloud SHALL 逐请求解析环境绑定并返回同一账号的权威用量与发布投影，响应 MUST NOT 泄漏 `accountId` 或要求建立 automation WebSocket

### Requirement: 客户稿件编辑与调整接口 SHALL 按环境归属隔离

customer-auth SHALL 提供授权环境下的待审稿 PATCH、调整任务创建和任务状态读取端点。每次请求 MUST 在验签、撤销与客户启用检查后，以路径 envKey 重新解析当前归属和持久账号绑定；SQL/领域写 MUST 同时校验该账号与稿件。请求 MUST NOT 接受 `accountId`、任意 Cloud URL、token、provider 或模型凭据。

#### Scenario: 当前客户编辑自己的环境稿件
- **WHEN** 客户 A 对其授权环境绑定账号的待审稿提交合法版本编辑
- **THEN** 请求进入该账号范围内的稿件 CAS 写且响应不披露 accountId

#### Scenario: 跨客户稿件 id
- **WHEN** 客户 A 通过自己的 envKey 请求编辑或调整客户 B 的稿件 id
- **THEN** Cloud fail-closed 拒绝且不泄露稿件是否存在、正文、图片或任务状态

### Requirement: 调整请求 SHALL 使用显式最小 DTO

创建调整请求只允许 `expectedVersion`、`scope`、`instruction` 和该 scope 所需的 selection；直接编辑只允许标题、正文、话题和 expectedVersion。未知字段、空指令、超长指令、无效位置、非当前图片或不支持 scope MUST 以具名校验错误拒绝，不得静默放宽成整篇调整。

#### Scenario: 单图请求夹带其它图片
- **WHEN** `selected_image` 请求额外提交图片数组或正文
- **THEN** Cloud 以 DTO 校验错误拒绝，不把它升级为整图或整篇修改

### Requirement: 稿件与任务响应 SHALL 最小披露

编辑和调整响应 SHALL 只返回客户审核所需的稿件字段、版本、job 状态、白名单过程和客户可理解错误。响应 MUST NOT 返回原始来源快照、sourceReference 全量、LLM prompt/response、内部审批信号、accountId、execution lease 或数据库诊断。

#### Scenario: 客户读取调整任务
- **WHEN** 客户读取自己环境中一条调整任务
- **THEN** 响应包含 job id、scope、状态、过程摘要、结果版本或公开错误，不包含内部模型与账号字段

### Requirement: 客户内容数据面 SHALL 独立于环境运行状态

待审稿编辑、调整任务创建和任务状态读取 SHALL 通过 customer-auth HTTP 处理，不以浏览器、Edge 自动化进程或 WebSocket 在线作为客户身份与内容数据读写前置。只有图片或文本 provider 不可用、绑定未知、版本冲突等真实领域条件可以拒绝；不得返回伪造的“请先启动浏览器”替代 Cloud 真态。

#### Scenario: 环境停止时调整待审稿
- **WHEN** 客户环境停止但授权、绑定和待审稿版本均有效
- **THEN** 客户仍可创建 Cloud 调整任务，任务不会自动启动浏览器或执行平台写入

### Requirement: Customer can read authoritative risk state for an owned Facebook environment

The customer-auth API SHALL provide an environment-scoped risk-state read. On every request Cloud MUST authenticate the customer, re-check enabled state and current environment ownership, resolve the persistent environment-to-account binding, and verify the bound account platform is Facebook. The response SHALL contain the requested `envKey` and public risk state only; it MUST NOT expose `accountId`, other environments, signal reasons, or internal controller selectors. Unowned, unbound, contended, unavailable, or non-Facebook environments MUST fail closed with distinguishable errors rather than returning a fabricated `normal` state.

#### Scenario: Stopped owned Facebook environment reads persisted restricted state
- **WHEN** a customer requests risk state for an owned, uniquely bound Facebook environment whose Edge is offline and whose persisted Cloud state is `restricted`
- **THEN** Cloud returns that environment's authoritative `restricted` state without requiring a live Edge session
- **AND** the response does not contain `accountId`

#### Scenario: Risk read cannot cross environment ownership
- **WHEN** a customer requests risk state for another customer's environment or a contended binding
- **THEN** Cloud rejects the request and returns no account or risk-state data

#### Scenario: Non-Facebook environment cannot use the Facebook risk surface
- **WHEN** a customer requests the risk-state route for an owned environment bound to a non-Facebook account
- **THEN** Cloud rejects the request as unsupported and does not expose or mutate that account's risk state

### Requirement: Customer restricted recovery is environment-scoped and Cloud-authoritative

The customer-auth API SHALL provide a recovery action that accepts only an empty object and an environment key in the route. The client MUST NOT submit `accountId`, risk signal kind, target status, or audit reason. Cloud SHALL resolve those facts after ownership and Facebook-platform validation, generate the audit reason, and submit a durable restricted-only recovery command to the automation owner. The api process MUST NOT call `RiskController`, write the automation outbox directly, resume Edge on command acceptance, or infer a successful state transition.

Every recovery submission and result read SHALL authenticate the customer, re-check enabled state and current environment ownership, resolve the current persistent environment-to-account binding, and verify that the command belongs to that same environment-bound account and execution target. The customer result endpoint SHALL be scoped as `GET /environments/:envKey/risk-state/recovery-commands/:commandId`; a command from another customer, environment, account, or target MUST be rejected without revealing whether that command exists. Customer responses MUST NOT expose `accountId`, internal controller selectors, outbox rows, or database details.

For a bound account currently in `restricted`, Cloud SHALL submit the asynchronous recovery command and MAY wait only for a bounded quick-completion window. If automation reaches `applied` within that window, Cloud SHALL return the existing `200` write-after receipt. If the command remains `processing`, Cloud SHALL return `202` with only the requested `envKey`, `commandId`, and an explicit processing discriminator; acceptance MUST NOT be described as recovery success. The customer SHALL use the environment-scoped result endpoint to continue reading the same command rather than submitting another recovery merely because the first response was `202`.

Automation SHALL serialize the restricted-only mutation through the bound account's existing `RiskController`. It SHALL change `restricted` to `normal` using `operator_override_recover`, clear the associated signal window through the existing state-machine transition, and persist the write-after state. Only after that mutation is applied SHALL automation resume Cloud command delivery to currently connected edges for the account and record an `applied` result containing the write-after public state, whether it changed, and the actual number of resumed edges. The api process MUST NOT resume Edge before this `applied` result.

An already-`normal` state SHALL remain an idempotent no-op and MAY return the existing `200` write-after receipt without creating a new transition. `warned` and `frozen`, including a state that changes to either before automation applies the command, MUST produce a distinct `refused` result without mutation or Edge resume. A command application or result-recording failure MUST remain `failed`, and a command absent from the authorized account/target ledger MUST remain `unknown`; `refused`, `failed`, and `unknown` MUST NOT be collapsed into `processing`, `applied`, or one generic success response.

#### Scenario: Owner receives a quick write-after recovery receipt
- **WHEN** the authenticated owner confirms recovery for an owned, uniquely bound Facebook environment currently in `restricted` and automation applies the command within the bounded quick-completion window
- **THEN** automation persists `normal`, clears the previous risk signal window, and only then resumes paused Cloud delivery for that account's connected edges
- **AND** Cloud returns `200` with the requested `envKey`, write-after `normal`, `changed:true`, and the real resumed-edge count without exposing `accountId`

#### Scenario: Recovery remains in progress after the quick-completion window
- **WHEN** the restricted-only command is durably accepted but automation has not produced a terminal result before the bounded quick-completion window ends
- **THEN** Cloud returns `202` with the requested `envKey`, `commandId`, and `processing`
- **AND** the response contains no fabricated write-after state, `changed:true`, resumed-edge count, or recovery-success claim

#### Scenario: Authorized polling observes the applied result
- **WHEN** the same enabled customer polls the command through the same owned environment and that environment is still bound to the command's account
- **THEN** `processing` continues to return an explicit non-success in-progress response
- **AND** an automation-recorded `applied` result returns `200` with the write-after public state and real resumed-edge count

#### Scenario: Recovery result cannot cross customer or environment scope
- **WHEN** a customer polls a real command through another customer's environment, a different owned environment, a changed account binding, or another execution target
- **THEN** Cloud rejects the request without revealing whether the command exists, its account, its outcome, or its Edge count

#### Scenario: State changes before the recovery command is applied
- **WHEN** the account was `restricted` at submission but is `warned` or `frozen` when automation serializes the restricted-only mutation
- **THEN** automation records `refused`, leaves the state unchanged, and does not resume any Edge
- **AND** customer-auth returns that refusal distinctly from `failed`, `unknown`, `processing`, and `applied`

#### Scenario: Failed and unknown outcomes remain distinguishable
- **WHEN** an authorized recovery command fails during owner application or result recording
- **THEN** customer-auth reports `failed` with a stable public reason and MUST NOT return recovery success or resume Edge
- **AND** when no command exists for the authorized account and target, customer-auth reports `unknown` rather than `processing` or `failed`

#### Scenario: Repeated recovery after success is idempotent
- **WHEN** the same environment is already `normal` because recovery completed elsewhere
- **THEN** Cloud returns the unchanged authoritative `normal` state with `changed:false` and MUST NOT create a new risk transition

#### Scenario: Warned or frozen cannot be self-recovered by this route
- **WHEN** the bound account is already `warned` or `frozen` when the recovery request is admitted
- **THEN** Cloud rejects the recovery, leaves the state unchanged, and does not submit or apply a recovery command

#### Scenario: Client cannot smuggle account or signal selectors
- **WHEN** a recovery body contains `accountId`, `kind`, `status`, `reason`, or any other key
- **THEN** Cloud rejects the entire request before command submission or mutation

### Requirement: Customer publish queue routes SHALL recheck exact environment ownership

客户鉴权服务 SHALL 提供当前客户已授权环境的发布队列读取和单任务取消路由。每个请求 MUST 在客户 JWT、撤销和启用态校验后，从数据库重新解析路径 `envKey` 的当前归属；取消写还 MUST 读取目标任务并验证其账号与该精确环境解析的账号一致、属于发布动作族且处于允许取消的状态。接口 MUST NOT 接受 `accountId` 作为客户选择器。

#### Scenario: 已归属小红书环境读取队列

- **WHEN** 客户持有效令牌请求自己当前归属的小红书 `envKey` 发布队列
- **THEN** 服务端只返回该环境绑定账号的客户队列投影和响应时间

#### Scenario: 同一客户其它环境的任务 id 不能被当前环境取消

- **WHEN** 客户在环境 A 的取消路径提交一个属于其环境 B 的真实任务 id
- **THEN** Cloud 拒绝取消且任务不变，不因两个环境属于同一客户而放宽精确目标校验

#### Scenario: 非小红书或未归属环境被拒绝

- **WHEN** 客户请求非小红书、未归属、已移除或绑定未确认的环境队列
- **THEN** 服务端拒绝请求且不返回队列数量、任务存在性或账号字段

### Requirement: Customer publish queue DTO SHALL be minimum disclosure

客户发布队列响应 SHALL 只包含首页摘要、客户状态、四阶段状态、可证实进度、客户可见标题/来源、任务取消所需 id/version/cancelRequested 与时间字段。响应 MUST NOT 包含 `accountId`、原始 lifecycle snapshot、stage facts、claim token、模型诊断、内部错误或跨账号数据。

#### Scenario: 客户队列不泄漏内部生命周期

- **WHEN** 内部 journey snapshot 或 delegated task 含账号、角色事实、claim 与诊断字段
- **THEN** 客户 DTO 只返回显式白名单字段，序列化响应中不存在这些内部字段

### Requirement: Customer queue cancellation SHALL use CAS and truthful receipts

客户队列取消 SHALL 要求请求体只含有效整数 `version`，并复用领域取消方法完成状态转换。版本不一致 MUST 返回冲突且不重试写；立即终态 SHALL 返回 `cancelled` 或 `partially_completed`，安全收口 SHALL 返回 `cancelRequested=true` 的非终态。服务端 MUST NOT 把取消请求已记录描述为工作已停止。

#### Scenario: 排队任务立即取消

- **WHEN** 当前版本的 queued 或 deferred 任务被取消且尚无已完成部分
- **THEN** Cloud 返回该任务的最小客户终态 `cancelled`，且只改变目标任务

#### Scenario: 规划任务进入安全取消

- **WHEN** 当前版本的 planning 任务接受取消
- **THEN** Cloud 返回同任务的新版本与 `cancelRequested=true`，状态仍非终态并等待工作器收口

#### Scenario: 陈旧版本不执行取消

- **WHEN** 请求 version 与当前任务版本不一致
- **THEN** Cloud 返回 409 且任务保持当前状态，不自动按新版本执行取消

### Requirement: 客户灵感库 SHALL 最小披露来源发布时间证据

客户鉴权域的精选列表与详情白名单 DTO SHALL 返回 `sourcePublishedAtText`、`sourcePublishedAt`、`sourcePublishedAtPrecision`、`sourcePublishedAtStatus` 和 `sourcePublishedAtObservedAt`，值均来自账号隔离后的精选行。接口 MUST NOT 为缺失字段生成回落时间，MUST NOT 因增加该字段而直出完整内部行或其它账号数据。

#### Scenario: 列表与详情返回同一来源时间

- **WHEN** 当前授权环境读取一条带已解析来源发布时间的灵感列表项和详情
- **THEN** 两个 DTO 返回一致的来源时间证据字段，仍只包含客户白名单字段

#### Scenario: 历史行字段诚实为空

- **WHEN** 当前账号的历史精选行没有来源发布时间证据
- **THEN** 客户 DTO 对应字段为空或省略，不以 `updatedAt` 填充

#### Scenario: 账号隔离不因时间字段减弱

- **WHEN** 客户请求另一账号的精选 id
- **THEN** 仍返回同形未找到响应，不泄漏其来源发布时间原文或标准时间

### Requirement: 客户可按已授权环境离线读取、生成和保存账号人设

客户鉴权 API SHALL 提供按 `envKey` 定位的单账号人设读取、草稿生成和确认保存接口，且这些接口 MUST NOT 要求目标环境的 core、浏览器或边云 WebSocket 在线。每次请求 SHALL 以当前客户令牌复核客户状态与环境归属，再通过权威持久绑定解析真实 `accountId`；客户端请求体 MUST NOT 接受 `accountId`、客户选择器、环境归属或平台自报字段，响应 MUST 回显 `envKey` 但 MUST NOT 暴露 `accountId`。

绑定解析的 `environment_not_owned`、`binding_unknown`、`binding_conflict` 与 `binding_unavailable` MUST 保持可区分并 fail-closed，MUST NOT 把任一失败伪装成 `missing` 或成功空结果。Cloud SHALL 以账号权威平台校验 Facebook 发言语言，以既有人设应用服务执行生成幂等、soul 校验、持久化和首次绑定引导。

#### Scenario: 停止环境读取已有人设

- **WHEN** 客户按自己拥有、已持久绑定账号且当前 core 停止的环境请求人设
- **THEN** API 返回该账号当前真实人设、结构化摘要与更新时间，响应回显 `envKey` 且不含 `accountId`

#### Scenario: 未设置与读取失败严格区分

- **WHEN** 已绑定账号确实没有 `persona_config` 行
- **THEN** API 返回 `state=missing` 且不返回任何默认模板作为当前人设
- **AND** 绑定未知、绑定冲突或存储不可用 MUST 返回各自失败，MUST NOT 返回 `state=missing`

#### Scenario: 环境未启动仍可生成草稿

- **WHEN** 客户为自己已绑定的停止环境提交有界关键词、有效幂等键和平台允许的发言语言
- **THEN** Cloud 以绑定账号记账并生成未落库草稿，目标环境无需启动
- **AND** 同账号同幂等键重试 MUST NOT 重复调用模型或重复记账

#### Scenario: 确认保存走既有单写通道

- **WHEN** 客户为自己已绑定环境确认提交合法非空 soul YAML
- **THEN** Cloud 经既有账号人设校验与持久化单写通道保存，返回写后真态并即时热加载
- **AND** 非法、空白或超限内容被诚实拒绝，库与内存镜像保持原状

#### Scenario: 非所有者无法借环境键访问人设

- **WHEN** 客户提交不属于自己的 `envKey` 读取、生成或保存人设
- **THEN** 三种操作均 fail-closed，不返回人设正文、摘要、账号键或可用于判断他人绑定状态的成功结果

### Requirement: Edge 通过客户鉴权 HTTP 拉取环境维护责任

系统 SHALL 提供客户鉴权 HTTP maintenance poll，使官方 Edge 主进程携带持久化随机 installationId 与本机非敏感 roster 摘要，主动拉取定位给该 installation 的环境删除责任。该能力 MUST NOT 新增 Cloud→Edge WebSocket 删除消息，MUST NOT 把删除加入自动化引擎命令，且维护责任 MUST 与 `/my-environments` 的正常可运行范围分离，使被冻结或已撤权但仍待物理清理的环境不会丢失责任。

#### Scenario: Edge 主动拉取删除责任
- **WHEN** 管理后台已为当前客户环境创建删除申请，且该 Edge installation 是唯一新鲜承载者
- **THEN** Edge 的 HTTP poll 返回匹配 requestId/envKey/version 的维护责任，Cloud 不发送任何新增 WS 删除消息

#### Scenario: 正常可见范围移除后责任仍可拉取
- **WHEN** 环境因删除申请已不再可运行但该客户会话仍承担物理清理
- **THEN** `/my-environments` 不把环境当正常可运行项，而 maintenance poll 仍按 durable request 返回清理责任

### Requirement: 删除责任按 installation 定位并经 HTTP 幂等收敛

Cloud SHALL 记录最近 installation observation，并仅在一个新鲜 installation 声明承载 envKey 时允许其通过 HTTP claim 删除责任。多个新鲜 installation、无定位或 installation 不匹配 MUST fail closed。Edge SHALL 先持久化 AdsPower 删除结果，再以 requestId/version/installationId 和 Idempotency-Key 经 HTTP 回写；Cloud 只接受匹配 claim 的结果，重复相同结果 MUST 幂等返回同一写后真态。

#### Scenario: 多 installation 承载冲突时不领取
- **WHEN** 两个新鲜 installation 都声明管理同一 envKey
- **THEN** Cloud 返回承载冲突并保持等待状态，任何一端都不得执行 AdsPower 删除

#### Scenario: 回执响应丢失后重试
- **WHEN** Edge 已删除 AdsPower profile 并提交 result，但 HTTP 响应在到达本机前丢失
- **THEN** Edge 保留本地 outbox 并用相同幂等键重试，Cloud 返回同一终态且不产生第二次生命周期迁移

#### Scenario: 非承载机器的不存在不算删除证明
- **WHEN** 未匹配 claim 的 installation 回报本机不存在该 envKey
- **THEN** Cloud 拒绝把它作为 `already_missing` 终态证据并保留原删除申请

### Requirement: 客户可为自有已绑定环境设置或清除账号运营别名

客户鉴权 API SHALL 提供仅接受环境键和运营别名的窄写接口。服务端 MUST 验证 token、该环境当前归属该客户、环境绑定无冲突且已解析到真实账号，才可更新该账号运营别名。非空值 trim 后写入；空值清除。成功回包 SHALL 返回 Cloud 解析后的显示名与来源。

#### Scenario: 自有已绑定环境设置别名
- **WHEN** 已登录客户为自己归属且已绑定账号的环境提交非空人工昵称
- **THEN** Cloud 更新绑定账号的运营别名并返回来源 `operator_alias`

#### Scenario: 自有已绑定环境清除别名
- **WHEN** 已登录客户为自己归属且已绑定账号的环境提交空内容
- **THEN** Cloud 清除运营别名并返回按平台昵称、运营标签或账号 ID 回落的显示名与来源

#### Scenario: 越权环境拒绝
- **WHEN** 客户尝试修改不归属自己的环境
- **THEN** API 以 403 拒绝且不修改任何账号记录

#### Scenario: 环境尚未绑定账号
- **WHEN** 客户拥有该环境但 Cloud 尚无可信 `envKey → accountId` 绑定
- **THEN** API 返回可判断的 `account_unbound` 冲突，不猜测账号、不报告成功

### Requirement: Customer interaction scope resolves through the environment binding
Customer interaction APIs SHALL resolve `envKey` to the authoritative video-channel `interaction_auth_state.account_id` binding on every request. They MUST NOT assume that the external finder ID or customer-provided input is the Cloud logical account ID.

#### Scenario: Authorized environment uses an env-key logical account
- **WHEN** an enabled customer owns a video-channel environment whose auth binding maps the environment to a logical account derived from that env key
- **THEN** list, detail, sync, reopen, reply, and offboard operations use the bound account ID and return the same `envKey` without exposing the finder identity as an authorization selector

#### Scenario: Environment ownership exists before identity binding
- **WHEN** a customer owns a video-channel environment but no authoritative interaction auth binding exists yet
- **THEN** read APIs return an honest login/binding-required state or scoped not-ready response and MUST NOT fall back to an unrelated account

### Requirement: Customer auth projections preserve control/application uncertainty
Customer-facing interaction responses SHALL distinguish Cloud-stored runtime controls, Edge-reported effective capabilities, and authorization status. Missing Edge application evidence MUST keep writes disabled.

#### Scenario: Cloud control version exceeds Edge-applied version
- **WHEN** the stored account control version is newer than the latest Edge auth/capability projection
- **THEN** the customer response marks the Edge capability state pending/stale and MUST NOT enable send controls

### Requirement: Customer test-data reset route is narrow and idempotent
customer-auth SHALL expose `POST /environments/:envKey/interactions/test-reset` only when the dev reset capability is enabled. The request MUST require an `Idempotency-Key`, MUST accept exactly `{channel:"comment"|"dm"}`, and MUST execute inside the same enabled-user, authoritative env ownership, and interaction account/platform binding boundary as the inbox APIs. The interaction list response SHALL include only a boolean `testTools.dataResetEnabled` exposure flag and MUST NOT expose deployment credentials or internal feature-flag values.

#### Scenario: Owned dev environment submits valid reset
- **WHEN** an enabled customer sends a valid channel reset for an environment they currently own with a new idempotency key
- **THEN** customer-auth returns the current envKey/accountId, selected channel, deletion counts, action request id and an honest accepted status after the reset command is delivered

#### Scenario: Request contains extra scope
- **WHEN** a reset body includes accountId, wildcard channel, scopeExternalId, or any unknown field
- **THEN** customer-auth rejects it as validation failure without data deletion

#### Scenario: Idempotent replay
- **WHEN** the same actor repeats a completed reset request with the same idempotency key and resource scope
- **THEN** customer-auth returns the stored response without performing a second deletion or dispatch

### Requirement: 内部管理员撤销视频号环境归属必须先收回访问权

内部管理员通过整批替换环境归属移除 `wechat_channels` 环境，或通过停用端用户移除其环境时，Cloud SHALL 在同一事务内写撤权审计、删除 active ownership，并在停用场景写入 disabled。访问撤权 MUST NOT 依赖 interaction account binding 是否已经存在；客户下一次 `/my-environments` 或 interaction 请求 MUST 立即失败关闭。

存在精确 `envKey + accountId + platform` binding 时，Cloud SHALL 创建现有 durable offboard。缺少 binding 时，Cloud SHALL 创建不含虚构 accountId 的 durable cleanup hold，并将成功结果明确报告为“ownership revoked, cleanup binding missing”；MUST NOT 返回整笔失败并保留旧 ownership，也 MUST NOT 声称 Edge 密文、sidecar 或 Cloud interaction 数据已经清理。

#### Scenario: 有 binding 的管理员移除继续进入 offboard
- **WHEN** 管理员从端用户归属中移除一个存在精确 interaction account binding 的视频号环境
- **THEN** active ownership 在事务内删除并创建 `admin_revoked` durable offboard，成功响应同时返回撤权后的 scope 与 offboard cleanup receipt

#### Scenario: 缺 binding 的管理员移除仍即时撤权
- **WHEN** 管理员从端用户归属中移除一个缺少 interaction account binding 的视频号环境
- **THEN** active ownership 在事务内删除，客户下一次请求即时不可访问，Cloud 创建 env-scoped `binding_missing` cleanup hold，响应不得包含伪造 accountId 或已清理状态

#### Scenario: 停用端用户混合处理多个环境
- **WHEN** 管理员停用的端用户同时拥有一个已绑定视频号环境和一个缺 binding 视频号环境
- **THEN** 用户 disabled 与全部 active ownership 在一个事务提交，前者创建 offboard、后者创建 cleanup hold，任一数据库写失败时整笔回滚且不得留下半撤权状态

### Requirement: 未完成的撤权清理必须持续隔离并可自动衔接 offboard

Cloud SHALL 为每个 envKey 至多保留一个 active cleanup hold。hold 或非 purged offboard 存在期间，系统 MUST 阻止该环境重新分配给任何客户，并 MUST 拒绝该 env 的 interaction sync/write 副作用。late auth binding MUST NOT 恢复 ownership 或业务能力；Cloud SHALL 在相同 env advisory lock 下把 hold 转换为使用真实 accountId 的现有 durable offboard，再由既有 Edge cleanup 生命周期处理。

#### Scenario: 清理待定位期间拒绝重新分配
- **WHEN** 管理员尝试分配一个存在 `binding_missing` cleanup hold 的环境
- **THEN** 请求返回可识别的 cleanup-in-progress 冲突，active owner 保持为空且不得覆盖 hold

#### Scenario: late binding 只用于定位清理
- **WHEN** cleanup hold 存在后 Edge 上报该 env 的真实 account binding
- **THEN** customer ownership 保持为空、interaction sync/write 仍被拒，Cloud 创建精确 offboard 并移除 hold，后续按既有 pending/dispatched/tombstoned/purged 流程推进

#### Scenario: 重复撤权不重复创建清理责任
- **WHEN** 管理员因响应丢失重试同一归属集合或重复停用已停用用户
- **THEN** Cloud 不创建第二个 active hold 或 offboard，内部读口仍能返回第一笔真实 cleanup 状态

### Requirement: 内部管理面必须展示撤权与清理的不同真态

内部 scope mutation、端用户停用和全局环境注册表响应 SHALL 暴露最小 cleanup receipt，至少区分 `offboard_pending` 与 `binding_missing`，并提供稳定的 revocation/offboard 标识与 envKey。Console SHALL 将两者分别显示为“归属已撤销，Edge 清理中”和“归属已撤销，清理待定位”，不得统一提示“已清理”或把已成功撤权显示成仍有 ownership。

#### Scenario: 保存归属后显示 binding 缺失真态
- **WHEN** 运营保存归属变更且 Cloud 返回 `binding_missing` cleanup receipt
- **THEN** Console 仍刷新并显示环境已从该用户归属移除，同时展示清理待定位警示而非失败回滚或清理完成

#### Scenario: 客户自助删除语义不被放宽
- **WHEN** 客户对非 completed-provisioning-intent 的缺 binding 环境调用 `DELETE /environments/:envKey`
- **THEN** 仍按既有契约返回 `offboard_binding_missing` 并保留 active scope，本 change 的管理员撤权 receipt 不得被客户令牌调用或读取

### Requirement: 客户灵感库在账号筛选后按固定热度规则分页排序

客户鉴权精选列表 SHALL 接受 `weighted`、`collects`、`likes` 和 `recent` 四种固定排序，并 SHALL 在有效客户令牌、环境归属解析、账号约束与创作状态筛选之后、`LIMIT/OFFSET` 之前由 Cloud 完成排序。省略排序参数 SHALL 使用 `weighted`；其它值 MUST 以具名无效排序错误拒绝并且不得触达精选查询。请求 MUST NOT 接受任意 SQL 字段、方向或可绕过账号隔离的参数。

`weighted` SHALL 使用 `点赞 × 1 + 收藏 × 1.43`，实现等价值 SHALL 为 `点赞 × 100 + 收藏 × 143`。点赞或收藏任一缺失的内容 MUST 排在两者均有证据的内容之后，缺失 MUST NOT 当作零。`collects` 和 `likes` SHALL 分别按对应计数降序并将该计数缺失的内容置后；`recent` SHALL 保持精选记录最近更新时间降序。所有模式 MUST 使用确定性的次级字段，使相同主排序值的分页顺序稳定。

#### Scenario: 综合热度在分页前计算

- **WHEN** 当前账号筛选后有超过一页的灵感且客户请求 `sort=weighted&limit=12&offset=0`
- **THEN** Cloud 在完整筛选结果上按 `点赞 × 100 + 收藏 × 143` 降序选择前 12 条，并返回同一筛选范围的真实 total，而不是只对任意 12 条做客户端排序

#### Scenario: 收藏与点赞排序保持账号隔离

- **WHEN** 客户分别请求 `sort=collects` 或 `sort=likes`，且其它账号存在计数更高的内容
- **THEN** 返回顺序只由当前 `envKey` 绑定账号和当前创作状态筛选中的内容决定，其它账号行不参与排序或总数

#### Scenario: 缺失热度不伪装成零

- **WHEN** 当前筛选同时包含完整赞藏计数、真实零值和缺少任一计数的内容
- **THEN** 综合排序先排列有完整计数证据的内容，真实零参与公式比较，缺失计数内容置后且响应仍保留 null

#### Scenario: 相同热度分页顺序稳定

- **WHEN** 多条灵感具有相同主排序值并跨越分页边界
- **THEN** Cloud 使用确定性的次级时间和 id 顺序，使相同数据库快照下重复请求得到相同页序

#### Scenario: 未知排序在查询前被拒绝

- **WHEN** 客户提交未定义排序、任意字段名或排序方向
- **THEN** 客户鉴权接口返回 `invalid_sort`，不静默回落且不触达精选列表查询

### Requirement: 客户只能为自己的环境开关慢启动，且不依赖账号绑定或边缘在线

customer-auth SHALL 提供 env-scoped `PUT /environments/:envKey/slow-start`。请求体 MUST 只接受 `enabled`，夹带任何其它键 MUST 整块拒绝且不写入。

慢启动配置 SHALL 直接持久化在 `envKey` 对应的环境记录；`accountId` MUST NOT 由客户端提交，也 MUST NOT 作为写入目标选择器。该路由 MUST NOT 依赖环境↔账号绑定、账号是否存在、边缘活会话、浏览器是否运行或环境是否已启动。

授权 SHALL 在同一 enabled-user 与 env ownership 权威范围内进行：客户 MUST 拥有该 `envKey`，否则 fail-closed。写入 SHALL 只修改该环境的 `slow_start_since`；开启时写入对齐运营自然日起点的值，关闭时清空。该路由 MUST NOT 修改当前或历史账号的慢启动字段、风控档位、风控终态、账号写总闸或任何其它账号配置。

成功回包 SHALL 返回写后环境配置真态。有唯一有效当前账号绑定时，回包还 SHALL 返回该账号 controller 依据该环境起点算出的生效状态与当日上限；没有有效绑定时，回包 SHALL 明确标注 `binding_unknown` 且不编造 `binding` 或当日上限。云端环境写入成功即为配置已生效，回包 MUST NOT 引入「已保存 / 待下发边缘」二态；没有账号时 SHALL 表述为当前没有执行对象，而非写入尚未完成。

#### Scenario: 边缘离线且未绑定账号时仍能开启环境慢启动

- **WHEN** 某 `envKey` 的所有者在该环境边缘未连接且没有账号绑定时提交 `{ enabled: true }`
- **THEN** 云端把该环境的 `slow_start_since` 写为对齐运营自然日的起点，并返回已开启的环境配置态
- **AND** 回包标注 `eligible=false` 与 `ineligibleReason=binding_unknown`，MUST NOT 返回伪造的 `binding` 或 `dayQuotas`

#### Scenario: 环境换绑后设置不随旧账号离开

- **WHEN** 已开启慢启动的环境从账号 A 换绑为账号 B
- **THEN** 环境的 `slow_start_since` 逐位保持不变
- **AND** 下一次配额计算中账号 B 使用该环境起点，账号 A 不再因该环境被 clamp，MUST NOT 要求重启

#### Scenario: 请求体夹带账号选择器被拒绝

- **WHEN** 请求体额外携带 `accountId`、`since`、`quotaLevel` 或任何其它键
- **THEN** customer-auth 返回校验失败且不写入任何环境或账号字段

#### Scenario: 非所有者请求 fail-closed

- **WHEN** 某已登录客户对不属于自己的 `envKey` 提交请求
- **THEN** customer-auth fail-closed 拒绝，MUST NOT 写入，MUST NOT 泄露该环境的账号身份或配置

#### Scenario: 环境注册表查询失败 MUST NOT 伪装成未绑定

- **WHEN** ownership 或环境配置写入因数据库不可达或表缺失而失败
- **THEN** customer-auth 返回 `503`，MUST NOT 返回 `binding_unknown`，MUST NOT 把「没写成」表述为配置已保存

#### Scenario: 关闭慢启动只清环境起点

- **WHEN** 环境所有者提交 `{ enabled: false }`
- **THEN** 云端只清空该环境的 `slow_start_since`
- **AND** 当前及历史账号的慢启动旧列、风控档位、风控终态与其它账号配置逐位保持原值

### Requirement: 慢启动状态 SHALL 提供不依赖边缘或账号绑定的 env-scoped 读

customer-auth SHALL 提供 env-scoped `GET /environments/:envKey/slow-start`，在该环境边缘不在线（含从未启动）或尚未绑定账号时也返回该环境的慢启动配置真态。

该读 SHALL 先按 ownership 读取环境自己的 `slow_start_since`。有唯一有效当前账号绑定时，SHALL 复用与 `ui.snapshot` 慢启动投影同一个 controller 产出（同一环境 anchor 解析、同一次 clock），MUST NOT 另行推算绑定性或上限。回包 MUST NOT 包含 accountId 或任何其它账号身份标识。

环境未绑定账号或绑定账号不存在时，该读 SHALL 保留环境配置态：关闭返回 `state=off`；开启返回 `state=active`、`since`、`day` 与 `totalDays`，同时返回 `eligible=false`、`ineligibleReason=binding_unknown`。此时 MUST NOT 编造 `binding`、`dayQuotas` 或“配额已被压低”。ownership/配置读失败 MUST 返回 `503`，MUST NOT 降级为 `binding_unknown`，MUST NOT 返回看起来正常的空投影。

#### Scenario: 从未启动且未绑定的环境也能读到已开启配置

- **WHEN** 某 `envKey` 的所有者读取一个边缘从未连接、没有账号绑定、但环境慢启动已开启的环境
- **THEN** customer-auth 返回 `state=active`、环境起点与当前天数，并标注 `binding_unknown`
- **AND** 回包 MUST NOT 包含 accountId、`binding` 或 `dayQuotas`

#### Scenario: 有绑定时返回与实际 clamp 同源的真态

- **WHEN** 某环境存在唯一有效账号绑定且所有者读取慢启动状态
- **THEN** customer-auth 返回该账号 controller 基于该环境起点得出的慢启动真态与生效后的当日上限
- **AND** 回包 MUST NOT 包含 accountId

#### Scenario: 读路由不得泄露他人环境

- **WHEN** 某已登录客户读取不属于自己的 `envKey`
- **THEN** customer-auth fail-closed 拒绝，MUST NOT 泄露该环境的账号身份或慢启动状态

#### Scenario: 读路由的查询失败同样不得伪装

- **WHEN** ownership、环境配置或 controller 取用因数据库不可达而失败
- **THEN** customer-auth 返回 `503`，MUST NOT 返回 `binding_unknown`，MUST NOT 返回空投影

### Requirement: Customer curated content routes recheck environment ownership

客户鉴权服务 SHALL 提供当前客户已授权环境的精选内容分页、单条详情和参考创作接口。每个请求 MUST 在客户 JWT、撤销和启用态校验后，从数据库重新读取该客户的环境归属，并只以已归属的 `envKey` 作为账号范围；接口 MUST NOT 接受可绕过归属检查的 `accountId`，MUST NOT 暴露内部面板跨账号能力。

#### Scenario: 已归属环境可读取精选内容

- **WHEN** 客户持有效客户令牌，以当前仍归属自己的 `envKey` 请求精选列表或详情
- **THEN** 服务端只返回该 `envKey` 的客户展示字段和一致分页总数

#### Scenario: 非归属环境被拒绝且不泄漏内容

- **WHEN** 客户以未归属或刚被移除的 `envKey` 请求列表、详情或参考创作
- **THEN** 服务端拒绝请求，不返回该环境是否存在、精选数量或任意内容字段

#### Scenario: 跨账号单条 id 统一未找到

- **WHEN** 客户提交一个真实存在但属于其他账号的精选内容 id
- **THEN** 单条接口返回与不存在 id 相同的 404 形状，不泄漏该行存在性

### Requirement: Customer curated DTO is a minimum disclosure projection

客户精选内容响应 SHALL 只包含列表与详情体验所需的显式白名单字段，并保留计数缺失值为 `null`。响应 MUST NOT 包含行所属 `accountId`、内部纳入原因、跨账号统计、删除能力或仅供运营/模型内部使用的诊断字段。

#### Scenario: 客户列表不含运营字段

- **WHEN** 客户请求精选内容列表
- **THEN** 每一项可包含 id、类型、标题、正文摘要、作者、来源链接、话题、计数、参考图、机器人动作标记与时间，但不包含 `accountId` 或 `admitReason`

#### Scenario: 缺失计数不被编造为零

- **WHEN** 某条精选内容的互动计数未采集
- **THEN** 对应字段返回 `null`，客户端可以呈现“暂无数据”，不得返回 `0`

### Requirement: Customer reference creation uses server-owned source snapshots

客户参考创作接口 SHALL 只接受精选内容 id、已授权 `envKey` 和布尔值 `useReferenceImages`。服务端 MUST 以 `id + envKey` 回读精选行，验证其为正文非空的图文内容，并以服务端快照构建结构化 `publish_post` 委派任务；客户端提交的来源正文、图片 URL、作者、账号或任务状态 MUST 被禁止或忽略。

#### Scenario: 文字参照任务直接排队

- **WHEN** 客户对可创作图文提交 `useReferenceImages=false`
- **THEN** 服务端以来源 `edge` 创建结构化委派任务并返回真实排队任务，来源约束显式记录不使用参考图

#### Scenario: 图文参照只使用已存参考图

- **WHEN** 客户提交 `useReferenceImages=true`
- **THEN** 服务端只复制该精选行已经持久化的参考图与视觉分析到任务快照，不使用客户端提供的任意外部图片

#### Scenario: 不可创作内容被诚实拒绝

- **WHEN** id 对应视频、评论或正文为空的精选行
- **THEN** 服务端不创建任务并返回稳定拒绝原因，不宣称排队成功

### Requirement: 客户互动 API 必须逐请求验证 enabled user 与 env ownership

customer-auth SHALL 暴露冻结的 interaction list/detail/draft/approve/send/regenerate/ignore/escalate/sync/auth-reopen 路径。每次请求 MUST 在客户 JWT 验签后，于同一数据库事务锁定并复核 user enabled、权威 `envKey` ownership 与 interaction account binding；thread/message/job 还 MUST 属于同一 env/account。跨环境资源与不存在资源 MUST 返回同一 404，不可枚举。

#### Scenario: 有 token 但无环境归属仍不可读
- **WHEN** enabled 客户携有效 token 请求未归属 env 的互动列表
- **THEN** 返回不可枚举 404，MUST NOT 返回 item 数量、accountId 或最后同步时间

#### Scenario: 归属被移除即时生效
- **WHEN** 管理员移除客户对 env 的归属后其 token 尚未过期
- **THEN** 客户下一次 interaction 请求即被拒，无需等待 token 过期

### Requirement: 客户不得自声明环境归属

`envKey` ownership SHALL 只来自内部权威环境注册与管理员授权；在明确共享授权模型上线前，每个 active env MUST 全局唯一归属一个客户。customer-auth 的 `POST /environments` 或其他客户可控字段 MUST NOT 创建、替换或恢复 ownership。

#### Scenario: 用户 A 不能 attach 用户 B 的环境
- **WHEN** 用户 A 携有效 token 提交用户 B 的 `envKey`
- **THEN** 请求被拒且全局 owner 不变，用户 A 后续 read/act 仍返回不可枚举错误

#### Scenario: 管理员不能把 active env 静默分给第二人
- **WHEN** 内部管理员尝试把仍归属用户 B 的 env 分给用户 A
- **THEN** 返回冲突并保持用户 B ownership，除非先完成显式 revoke/offboard 流程

### Requirement: Customer API 路径和 envelope 必须与共享 schema 一致

客户 API SHALL 实现：`GET /environments/:envKey/interactions`、`GET /environments/:envKey/interactions/:threadId`、`PUT /environments/:envKey/replies/:jobId/draft`、三个 reply POST（approve/send/regenerate）、message ignore/escalate、interaction sync 与 auth/reopen，以及 `DELETE /environments/:envKey`、`GET /offboarding/:offboardId`。成功/错误 envelope、分页 cursor、枚举与字段 MUST 通过 `docs/contracts/wechat-channels-interaction/v1/schemas/customer-auth-api.schema.json`。

#### Scenario: 列表回包携 scope 和真态
- **WHEN** 客户读取当前环境互动列表
- **THEN** 响应 data 明确回带 `envKey/accountId/platform/items/nextCursor` 且 meta 含 requestId/asOf，renderer 可拒绝错 env 回包

#### Scenario: 2xx send 不等于平台 confirmed
- **WHEN** send endpoint 成功把 job 从 approved 转 queued
- **THEN** 响应返回 job 真态 queued，MUST NOT 返回 sent 或让客户端解释为平台成功

#### Scenario: 删除环境返回待清理而非完成
- **WHEN** enabled 客户删除自己权威归属且 account binding 匹配的环境
- **THEN** 同一事务撤权并创建 durable offboard，响应回 `pending_edge|dispatched` 与 envKey/accountId/meta.asOf，MUST NOT 显示凭证或数据已删除

#### Scenario: 用户 A 不能查看用户 B 的 offboard
- **WHEN** 用户 A 读取由用户 B 创建的 offboardId
- **THEN** 返回不可枚举 404，MUST NOT 泄露 envKey/accountId/state

### Requirement: 客户写操作必须使用 CAS 与幂等 header

job draft/approve/send/regenerate/ignore/escalate MUST 携 `expectedVersion`；版本或状态不符 MUST 409 并返回当前 version/state，不执行部分副作用。send/sync/auth-reopen MUST 要求 `Idempotency-Key` header，重复 key MUST 返回既有请求真态。

#### Scenario: 重复点击发送只有一个 attempt
- **WHEN** 客户端以相同 idempotency key 重试 send
- **THEN** Cloud 返回既有 job/attempt 状态，MUST NOT 创建第二 attempt

#### Scenario: 迟到编辑不能覆盖新批准
- **WHEN** 客户用旧 expectedVersion 修改已被另一客户端批准的 job
- **THEN** 服务端返回 version conflict 和当前真态，批准/文本保持不变

### Requirement: 登录失效时历史可读但写 fail closed

只要客户仍有 env ownership，已同步历史 MAY 继续读取；当 auth 非 active、identity mismatch 或 challenge 时，所有 reply/send 写 MUST 返回稳定阻断码，并可通过 auth/reopen 请求原 Edge sidecar。auth/reopen accepted 只表示请求已受理，MUST NOT 表示登录完成。

#### Scenario: Cookie 失效后仍能查看历史
- **WHEN** 当前环境 auth=reauth_required 且客户读取已同步 thread
- **THEN** API 返回历史与 auth 阻断状态，但 approve/send 按门禁拒绝

#### Scenario: Reopen 成功响应不冒充已登录
- **WHEN** Cloud 已接受 auth/reopen 并下发 Edge
- **THEN** API 返回 accepted/requestId，UI 等待后续 auth.status active，MUST NOT立即显示同步正常

### Requirement: Customer browser control API is ownership-scoped and acceptance-only
Customer auth SHALL expose an idempotent browser control operation for an owned video-channel environment. Every request MUST revalidate enabled-user state, environment ownership, and authoritative interaction account binding before routing the exact `envKey + accountId` to one negotiated online Edge. The success response SHALL mean accepted only and MUST NOT represent browser execution success.

#### Scenario: Owner requests browser open
- **WHEN** an enabled customer submits an idempotent open action for an owned video-channel environment with an authoritative interaction binding and one compatible Edge online
- **THEN** Cloud returns an accepted envelope with an action request ID and routes one scoped browser control command
- **AND** the response MUST NOT state that the browser is already open

#### Scenario: Owner requests browser close
- **WHEN** an enabled customer submits an idempotent close action for an owned video-channel environment with one compatible Edge online
- **THEN** Cloud returns an accepted envelope with an action request ID and routes one scoped browser control command
- **AND** the response MUST NOT state that the browser is already closed

#### Scenario: Environment is not owned by the customer
- **WHEN** a customer submits browser control for an environment they do not own
- **THEN** the API rejects the request without resolving or exposing the environment's account, Edge, or browser state

#### Scenario: Compatible Edge is unavailable
- **WHEN** ownership and binding are valid but no uniquely matched negotiated Edge can receive browser control
- **THEN** the API returns a stable unavailable or unsupported error and MUST NOT fall back to another environment, profile, or reauthorization command

### Requirement: 客户端控制面启动引导必须经环境归属与绑定解析

customer-auth SHALL 提供 env-scoped 的最小只读控制面引导。接口 MUST 先验证 enabled customer 与环境归属，再复用权威环境→账号绑定解析器；成功时只返回请求 envKey 与已解析 accountId。该接口 MUST NOT 创建、修改、推断或修复环境归属/账号绑定。

#### Scenario: 已归属已绑定环境取得引导
- **WHEN** 已登录客户请求其拥有且唯一绑定账号 A 的环境 E 的控制面引导
- **THEN** Cloud 返回 `{envKey: E, accountId: A}`
- **AND** 该结果可用于无浏览器核心的首次 hello

#### Scenario: 越权环境 fail-closed
- **WHEN** 客户请求不归其所有的环境
- **THEN** 接口以 `environment_not_owned` 拒绝
- **AND** MUST NOT 暴露该环境是否绑定、绑定到谁或是否在线

#### Scenario: 不可解析原因保持可区分
- **WHEN** 环境尚未绑定、存在跨客户绑定冲突或绑定存储不可用
- **THEN** 接口分别以 `binding_unknown`、`binding_conflict` 或 `binding_unavailable` 拒绝
- **AND** MUST NOT 返回空 accountId、成功空对象或猜测值

### Requirement: 控制面引导 MUST 限于 Electron 主进程客户会话

控制面引导请求 SHALL 使用既有 customer bearer session 并遵守其失效、禁用与轮换边界。renderer MUST NOT 获得 customer token，Cloud MUST NOT 提供未鉴权的 envKey→accountId 查询入口。

#### Scenario: 登录失效后不可继续引导
- **WHEN** 客户已退出、被禁用或 token 已失效
- **THEN** 控制面引导请求被鉴权层拒绝
- **AND** 客户端 MUST NOT 以本地缓存绕过该拒绝建立新的 Cloud 会话

### Requirement: 客户端代理写入必须逐目标绑定当前客户可见环境

客户鉴权启用时，单环境和批量代理写入的主进程入口 SHALL 只接受当前有效客户会话下、最新可信 `allowedProfileIds` 中的明确 `user_id`。批量入口 SHALL 要求非空、去重、有序的 ID 数组，并在第一笔写入前验证每个目标；任一目标越权、重复、缺失，或会话/可见集不可信时 SHALL 整批失败关闭，不调用 AdsPower `user/update`。主进程 MUST NOT 仅依赖 renderer 已过滤列表、当前选中环境或平台筛选作为写权限证据。

未启用客户鉴权的兼容模式 SHALL 保持既有本地运维能力，但仍需明确 ID 和代理输入校验。错误与日志 MUST NOT 泄露其它客户环境名称、代理摘要或凭据。

#### Scenario: 单环境越权目标被拒绝
- **WHEN** renderer 或被篡改调用向单环境代理入口提交不在当前 `allowedProfileIds` 的 `user_id`
- **THEN** 主进程在调用 AdsPower 前拒绝且不返回该环境的名称、代理或其它信息

#### Scenario: 批量任一越权目标使整批失败关闭
- **WHEN** 批量目标中有一个 ID 不属于当前客户可见环境
- **THEN** 主进程在第一笔写入前拒绝整批，不更新其它合法目标，也不回落到本机全量环境

#### Scenario: 会话或可见集不可信时不写代理
- **WHEN** 客户会话失效、刷新可见集失败或 `allowedProfileIds` 未建立
- **THEN** 单个和批量代理入口诚实要求重新登录或重试，MUST NOT 沿用不可信旧集或调用 AdsPower 写接口

#### Scenario: 重复目标在写入前拒绝
- **WHEN** 批量请求包含重复 `user_id`
- **THEN** 主进程在第一笔写入前拒绝该请求，MUST NOT 对同一环境重复改代理

### Requirement: Customer proxy-authority routes SHALL recheck exact environment ownership
Cloud SHALL expose customer-authenticated exact-environment proxy-authority read and compare-and-set write routes. Every request SHALL resolve current ownership from server-side assignment state and SHALL fail closed when ownership is missing, revoked, or ambiguous.

#### Scenario: Owned environment can be read and updated
- **WHEN** an authenticated customer addresses one currently assigned environment
- **THEN** Cloud SHALL permit the exact authority read or revision-checked write

#### Scenario: Revoked assignment cannot reuse an earlier read
- **WHEN** ownership is revoked after a client read but before its write
- **THEN** the write SHALL be rejected even if its revision otherwise matches

### Requirement: Customer environment projections SHALL not disclose proxy credentials
Existing customer environment roster and browser-independent status routes SHALL remain minimum-disclosure projections and SHALL NOT include proxy username or password. Credential-bearing authority data SHALL only be returned from the exact owned authority route.

#### Scenario: Roster remains credential-free
- **WHEN** a customer loads the environment roster
- **THEN** no proxy username or password SHALL be present in the response

### Requirement: 客户只能为自己的环境设置评论审批覆盖，且不依赖账号绑定或边缘在线

customer-auth SHALL 提供 env-scoped 的评论审批覆盖读写路由。写请求体 MUST 只接受模式枚举 `source_rules|auto_approve_all`，夹带 `accountId`、`updatedBy` 或任何其它键 MUST 整块拒绝且不写入。

策略 SHALL 直接持久化在 `envKey` 对应的环境记录；`accountId` MUST NOT 由客户端提交，也 MUST NOT 作为写入目标选择器。该路由 MUST NOT 依赖环境↔账号绑定、账号是否存在、边缘活会话、浏览器是否运行或环境是否已启动。

授权 SHALL 在同一 enabled-user 与 env ownership 权威范围内进行：客户 MUST 拥有该 `envKey`，否则 fail-closed 且不泄露该环境的账号身份或现有策略。写入 SHALL 只修改该环境的审批策略字段，MUST NOT 修改当前或历史账号的审批策略、风控档位、风控终态、账号写总闸或任何其它账号配置。客户来源的审计署名 MUST 与后台管理员可区分。

成功回包 SHALL 返回写后环境策略真态。没有唯一有效当前账号绑定时，回包 SHALL 明确标注当前没有执行对象，MUST NOT 编造绑定或生效评论行为。云端环境写入成功即为配置已保存，回包 MUST NOT 引入「已保存 / 待下发边缘」二态。

#### Scenario: 边缘离线且未绑定账号时仍能设置免审

- **WHEN** 某 `envKey` 的所有者在该环境边缘未连接且没有账号绑定时提交 `auto_approve_all`
- **THEN** 云端写入该环境策略并返回已保存的环境配置态
- **AND** 回包标注当前没有执行对象，MUST NOT 返回伪造的绑定或生效评论态

#### Scenario: 请求体夹带账号选择器被拒绝

- **WHEN** 请求体额外携带 `accountId`、`updatedBy` 或任何其它键
- **THEN** customer-auth 返回校验失败且不写入任何环境或账号字段

#### Scenario: 非所有者请求 fail-closed

- **WHEN** 某已登录客户对不属于自己的 `envKey` 提交请求
- **THEN** customer-auth fail-closed 拒绝，MUST NOT 写入，MUST NOT 泄露该环境的账号身份或现有策略

#### Scenario: 环境注册表查询失败 MUST NOT 伪装成未配置

- **WHEN** ownership 或环境策略写入因数据库不可达或表缺失而失败
- **THEN** customer-auth 返回 `503`，MUST NOT 返回「按来源规则」，MUST NOT 把「没写成」表述为配置已保存

#### Scenario: 关闭免审只改该环境策略

- **WHEN** 环境所有者提交 `source_rules`
- **THEN** 云端只更新该环境的审批策略
- **AND** 当前及历史账号的策略旧列、风控档位、风控终态与其它账号配置逐位保持原值

### Requirement: 能力吊销必须按账号身份定位并验证命中

撤销某账号互动能力（读写开关）与登录态的写入，SHALL 只按账号身份（平台 + 账号）定位，MUST NOT 额外附加环境标识作为匹配条件——该标识在库中可空且并非身份的一部分，附加它会使吊销在空值下静默命中 0 行。

吊销 SHALL 检查实际更新行数。**存在能力却没改到 MUST 抛错并整笔回滚，MUST NOT 向调用方回报成功**。「目标行本就不存在」（从未配置过能力）MUST NOT 被用作吞掉全部 0 行情况的借口：系统 SHALL 区分「无能力可撤」与「有能力但没撤掉」，后者是结构性异常。

授权与吊销 SHALL 使用同一套定位口径，MUST NOT 出现「授权永远生效、吊销条件生效」的不对称。

#### Scenario: 管理员配置过、客户端从未连过的账号被解绑

- **WHEN** 运营已在后台为某视频号账号配好互动读写开关（该账号的客户端从未上报过登录状态，环境标识列为空）
- **AND** 客户随后删除该环境、触发解绑
- **THEN** 该账号的读写开关 MUST 全部被置为关闭，登录态 MUST 被置为停用
- **AND** 后台面板 MUST NOT 再把这个已终止的账号显示为「允许读取」

#### Scenario: 吊销未命中预期的行

- **WHEN** 撤销登录态的写入实际命中 0 行（调用方是在已读到该环境的登录绑定后才进入的，因此 0 行意味着状态已被破坏）
- **THEN** 整笔事务 MUST 回滚
- **AND** 系统 MUST NOT 返回成功，MUST NOT 写下「已吊销」的审计记录

### Requirement: 未绑定环境的清理墓碑必须撤销能力并声明恢复路径

当被撤销的环境尚无登录绑定时，系统 SHALL 走「未绑定 → 清理墓碑」旁路完成撤权，MUST NOT 因缺少绑定而整笔回滚——「已授予、尚未扫码」是每一次授予的常规过渡态，不是错误。

立墓碑 SHALL 在同一事务内撤销该环境对应账号的读写能力与登录态。**只记墓碑而不撤销任何能力是被禁止的**：那是用一个死锁换一个 fail-open，且把吊销失效的暴露面从「管理员配置过的账号」扩大到每一次对未登录环境的吊销。

若此时账号身份无法确定，系统 MUST NOT 伪造账号标识、MUST NOT 假称已清理；此种情况下 fail-closed 由能力投影屏障承担。

墓碑 SHALL 有明确的恢复路径：**当迟到的登录态出现、账号身份因此可确定时，系统 SHALL 把墓碑兑现为正式解绑流程并移除墓碑**。墓碑 MUST NOT 是一个没有出口的终态。

#### Scenario: 撤销一个从未登录过的已授予环境

- **WHEN** 管理员撤销某环境的归属，或停用持有该环境的客户，而该环境从未有过登录绑定
- **THEN** 撤权 MUST 成功完成，MUST NOT 返回「缺少绑定」类错误并回滚
- **AND** 系统 SHALL 记录清理墓碑，且该环境在墓碑了结前 MUST NOT 被重新分配给任何客户

#### Scenario: 立墓碑时账号身份可确定则同批撤销能力

- **WHEN** 立清理墓碑时该环境对应的账号身份可以确定
- **THEN** 该账号的读写能力与登录态 MUST 在同一事务内被撤销
- **AND** MUST NOT 出现「墓碑已记、能力仍开」的中间态

#### Scenario: 迟到的登录态把墓碑兑现成正式解绑

- **WHEN** 某环境存在未了结的清理墓碑
- **AND** 该环境随后首次上报登录态、账号身份变为可确定
- **THEN** 系统 SHALL 据此发起正式解绑并删除该墓碑
- **AND** 该账号的读写能力 MUST 保持关闭

### Requirement: 能力投影不得捏造绑定

发往边缘与后台的能力投影 SHALL 只反映库中真实存在的绑定。环境标识缺失时，系统 MUST NOT 用账号标识顶替出一个「看起来合法」的作用域——把「不确定是否绑定」洗成「作用域有效」是静默假成功。

环境标识缺失时，读取与写入能力 SHALL 一律投影为关闭（fail-closed：能力缺失必须全关，MUST NOT 沿用旧连接或别的账号的能力）。

未了结的清理墓碑 SHALL 与待处理解绑同等对待，构成能力屏障：任一存在即 SHALL 把该账号的全部互动能力投影为关闭。

#### Scenario: 控制记录尚无环境绑定

- **WHEN** 某账号的运行控制记录存在但环境标识为空（管理员已配置、边缘从未上报）
- **THEN** 投影出的评论读取、评论回复、私信读取、私信发送能力 MUST 全部为关闭
- **AND** 投影 MUST NOT 输出由账号标识顶替出来的环境标识

#### Scenario: 存在未了结的清理墓碑

- **WHEN** 某账号所属环境存在未了结的清理墓碑
- **THEN** 该账号的全部互动能力 MUST 投影为关闭，与存在待处理解绑时的结果一致

