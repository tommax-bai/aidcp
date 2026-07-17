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

interaction list/detail 与 read-controls 成功回包 SHALL 为当前 account/env 返回只读 `replyConfig` 投影，至少区分 `missing`、`draft_only`、`published` 并给出 current/draft/published version。该投影 MUST NOT 包含模板正文、规则条件、完整私信或 internal permission；查询失败 MUST 显示 unknown/fail-closed，不能伪造默认 published 配置。

#### Scenario: 无发布配置时客户端得到明确阻断
- **WHEN** 当前账号没有 config head 或只有未发布 draft
- **THEN** 客户回包分别返回 missing 或 draft_only，客户端可保持收件箱可读并禁用依赖 published 配置的生成/发送流程

#### Scenario: 已发布配置只暴露版本状态
- **WHEN** 当前账号存在 immutable published 配置
- **THEN** 客户回包返回 published 与版本号，不返回模板、规则、profile 或审计正文

### Requirement: 客户读取自助不得打通 internal 配置域

客户 JWT SHALL 继续不能访问 internal reply policy/template/rule/profile/preview/publish/audit 路径。客户侧读取开关 API MUST 使用独立 schema 与具名 renderer IPC，MUST NOT 接受任意 URL、internal token 或代理配置写入。

#### Scenario: 客户 token 调用内部配置发布仍被拒绝
- **WHEN** 客户使用有效 customer JWT 调用 internal reply-config/publish
- **THEN** 请求按认证域隔离被拒，已发布版本和 runtime write controls 均不变化

