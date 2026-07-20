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

### Requirement: 客户只能为自己环境上已绑定的账号开关慢启动，且不依赖边缘在线

customer-auth SHALL 提供 env-scoped `PUT /environments/:envKey/slow-start`。请求体 MUST 只接受 `enabled`，夹带任何其它键 MUST 整块拒绝且不写入。

**accountId MUST 由云端解析、MUST NOT 由客户端提交**。解析 SHALL 经**持久的环境↔账号绑定**（change `curated-envkey-account-binding` 所建、`env_key` 为 PK ⇒ 一个环境至多一个账号），MUST NOT 接受请求体或查询参数中的账号选择器，**MUST NOT 依赖边缘活会话**。

该路由 MUST NOT 要求该环境的边缘在线：`slow_start_since` 的执行体位于云端配额计算内、经运行时现读生效，边缘对这次写入**没有任何参与**。以边缘在线与否为前置 SHALL 被视为缺陷。

授权 SHALL 在同一 enabled-user 与 env ownership 权威范围内进行：客户 MUST 拥有该 `envKey`，否则 fail-closed。绑定读 SHALL 与 `accounts` 关联校验，悬空绑定 MUST fail-closed，MUST NOT 当作有效目标。

该路由 MUST NOT 修改风控档位、风控终态、账号写总闸或任何其它账号配置——`slow_start_since` 是唯一可被本路由写入的字段。

成功回包 SHALL 返回写后真态与生效后的当日上限。因慢启动的执行体位于云端配额计算内、且开关经运行时现读生效，云端写入成功即为已生效，回包 MUST NOT 引入「已保存 / 待下发边缘」二态——照抄一个不存在的状态同样是不诚实。

#### Scenario: 边缘离线时环境所有者仍能开启慢启动

- **WHEN** 某 `envKey` 的所有者在该环境**边缘未连接**（含从未启动）但存在有效账号绑定时提交 `{ enabled: true }`
- **THEN** 云端经持久绑定解析出 accountId，写入对齐运营自然日起点的 `slow_start_since`，回包带写后真态与生效后的当日上限
- **AND** customer-auth MUST NOT 因边缘不在线而拒绝

#### Scenario: 环境未绑定账号时诚实冲突

- **WHEN** 某 `envKey` 没有账号绑定行，或绑定指向的账号在 `accounts` 中不存在
- **THEN** customer-auth 返回 `409 binding_unknown`，MUST NOT 写入，MUST NOT 猜测任何账号

#### Scenario: 绑定查询失败 MUST NOT 伪装成未绑定

- **WHEN** 绑定读因数据库不可达或表缺失而失败
- **THEN** customer-auth 返回 `503`，MUST NOT 返回 `binding_unknown`，MUST NOT 把「没查成」表述为「该环境没有绑定账号」

#### Scenario: 请求体夹带账号选择器被拒绝

- **WHEN** 请求体额外携带 `accountId`、`since`、`quotaLevel` 或任何其它键
- **THEN** customer-auth 返回校验失败且不写入任何字段

#### Scenario: 非所有者请求 fail-closed

- **WHEN** 某已登录客户对不属于自己的 `envKey` 提交请求
- **THEN** customer-auth fail-closed 拒绝，MUST NOT 写入，MUST NOT 泄露该环境的账号身份

#### Scenario: 关闭慢启动只清起点不动其它

- **WHEN** 环境所有者提交 `{ enabled: false }`
- **THEN** 云端只清空该账号 `slow_start_since`，其风控档位、风控终态与其它账号配置逐位保持原值

### Requirement: 慢启动状态 SHALL 提供不依赖边缘的 env-scoped 读

customer-auth SHALL 提供 env-scoped `GET /environments/:envKey/slow-start`，在该环境边缘不在线（含从未启动）时也返回该环境的慢启动真态与生效后的当日上限。

该读 SHALL 经与写路由**同一份持久绑定**解析 accountId，SHALL 复用与 `ui.snapshot` 慢启动投影**同一个 controller 产出**（同一 anchor 解析、同一次 clock），MUST NOT 另行推算天数、绑定性或上限。

授权 SHALL 与写路由同口径：客户 MUST 拥有该 `envKey`，否则 fail-closed。回包 MUST NOT 包含 accountId 或任何其它账号身份标识。

环境未绑定账号时，该读 SHALL 返回 `eligible=false` 且 `ineligibleReason=binding_unknown` 的诚实投影；此时 MUST NOT 编造 `state`、`day`、`since` 或 `totalDays`——没有账号即不知平台，任何默认值都是伪造。绑定读失败 MUST 返回 `503`，MUST NOT 降级为 `binding_unknown`，MUST NOT 返回一个看起来正常的空投影。

#### Scenario: 从未启动的环境也能读到慢启动真态

- **WHEN** 某 `envKey` 的所有者读取一个边缘从未连接、但存在有效账号绑定的环境
- **THEN** customer-auth 返回该账号的慢启动真态与生效后的当日上限
- **AND** 回包 MUST NOT 包含 accountId

#### Scenario: 未绑定环境返回诚实的不可用投影

- **WHEN** 客户读取一个自己拥有但没有账号绑定的环境
- **THEN** customer-auth 返回 `eligible=false` 与 `ineligibleReason=binding_unknown`
- **AND** 回包 MUST NOT 包含 `state`、`day`、`since` 或 `totalDays`

#### Scenario: 读路由不得泄露他人环境

- **WHEN** 某已登录客户读取不属于自己的 `envKey`
- **THEN** customer-auth fail-closed 拒绝，MUST NOT 泄露该环境的账号身份或慢启动状态

#### Scenario: 读路由的查询失败同样不得伪装

- **WHEN** 绑定读或 controller 取用因数据库不可达而失败
- **THEN** customer-auth 返回 `503`，MUST NOT 返回 `binding_unknown`，MUST NOT 返回空投影

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

首次成功完成 Facebook 创建 intent 时，Cloud SHALL 在同一数据库事务中插入环境、写入唯一客户归属、完成 intent，并把 `client_environments.slow_start_since` 写为服务端当前时刻所属上海自然日的 00:00，同时显式标记初始化完成。慢启动起点 MUST NOT 取 Edge 时钟、账号入库时间、Cookie 时间或 `accounts.slow_start_since`。

已完成 intent 的幂等重试 MUST 只返回既成归属，不得再次写入或重置慢启动起点；若运营在首次完成后手动关闭慢启动，陈旧重试 MUST NOT 重新开启。接口不得修改风控档位、风险状态、账号旧慢启动列或其它环境配置。

#### Scenario: Facebook 创建原子写入 D1 起点

- **WHEN** 有效客户使用待完成 intent 注册一个全新 Facebook 环境并提交 `slowStartEnabled=true`
- **THEN** 环境、归属、intent 完成态与上海当日 00:00 慢启动起点在同一事务中提交

#### Scenario: 旧客户端省略字段保持兼容

- **WHEN** 有效旧客户端完成环境归属但未提交 `slowStartEnabled`
- **THEN** 请求继续按既有规则成功，环境慢启动字段保持 NULL

#### Scenario: 非 Facebook 开启意图原子拒绝

- **WHEN** 请求以小红书、视频号或未知平台提交 `slowStartEnabled=true`
- **THEN** Cloud 在注册环境前拒绝整个请求，环境、归属和 intent 均不发生部分写入

#### Scenario: 完成重试不重置或复活慢启动

- **WHEN** Facebook intent 已成功完成，随后同一 intent/环境被再次提交
- **THEN** Cloud 返回幂等成功但不更新 `slow_start_since`
- **AND** 即使该环境已被运营手动关闭，也不得重新开启

### Requirement: 客户登录后 SHALL 自动建立可信环境的浏览器无关核心

客户登录完成并取得权威环境 roster 后，客户端 SHALL 对每个归属可用且已解析可信绑定的环境自动启动或恢复浏览器无关核心，无需用户点击“启动环境”。该 bootstrap MUST 使用有界并发和独立退避，MUST NOT 调用浏览器 provider、申请浏览器槽位或要求 CDP。环境未绑定、归属冲突或绑定不可用时 SHALL fail-closed 显示具名原因，不得猜测账号或通过打开浏览器自动消除归属闸。

#### Scenario: 首次登录自动恢复全部可信环境

- **WHEN** 客户登录后 roster 返回三个已归属且可信绑定的环境
- **THEN** 客户端有界并发建立三个浏览器无关核心与其 Cloud 会话，三个环境的浏览器均保持关闭且不消费槽位

#### Scenario: 一个环境绑定冲突不牵连其他环境

- **WHEN** roster 中一个环境存在绑定冲突、另两个环境绑定可信
- **THEN** 冲突环境停在具名 fail-closed 状态，另两个环境正常建立核心，客户端不得为冲突环境自动打开浏览器

### Requirement: 客户态 Cloud 操作 MUST 逐请求解析环境归属与账号绑定

由客户鉴权直接执行的人设、内容、待审编辑、审批受理和配置操作 SHALL 只接收客户令牌上下文、`envKey` 与最小业务入参；Cloud MUST 逐请求验证客户拥有该环境并从权威绑定解析 `accountId`，MUST NOT 采信 renderer 或请求体自报账号。该类操作 MUST NOT 以 Edge 活会话、浏览器登录、CDP 或槽位为准入条件；renderer MUST NOT 获得客户令牌、权威 `accountId` 或通用 HTTP 能力。

#### Scenario: 浏览器和 Edge 页面会话均缺席时生成客户人设

- **WHEN** 客户已登录、拥有环境且其账号绑定可信，但该环境浏览器关闭且无 CDP
- **THEN** Cloud 由 customer-auth 请求解析账号归属并执行人设生成，MUST NOT 返回“请启动浏览器”或等待浏览器槽位

#### Scenario: 客户请求越权环境

- **WHEN** 客户请求中的 `envKey` 不属于当前客户，或该环境绑定无法权威解析
- **THEN** Cloud 以可区分拒因 fail-closed，MUST NOT 使用请求体账号、历史 UI 缓存或浏览器启动来绕过校验

