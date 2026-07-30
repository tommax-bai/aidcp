# wechat-channels-interaction Specification

## Purpose
TBD - created by archiving change wechat-edge-auth-recoverable. Update Purpose after archive.
## Requirements
### Requirement: 临时性接口失败 MUST NOT 成为终局降级

「资源暂时被占」「稍后再试」类的失败 MUST NOT 被实现成永久能力剥夺。Edge 因 `rate_limited`、`transient_network`、`permission_denied`、`schema_changed` 进入 `degraded` 时，MUST 同时安排一个**有限退避的恢复尝试**，并在恢复尝试成功后自动回到正常运行态；MUST NOT 要求客户重新登录或重扫二维码作为唯一恢复手段。

恢复尝试 SHALL 由「调用身份接口 + 重跑已启用只读探针」构成，MUST NOT 自动打开浏览器。退避 SHALL 从每类各自的初始间隔按指数增长到该类上限，到达上限后 SHALL 按上限持续重试；退避间隔 MUST NOT 增长到无穷、恢复通道 MUST NOT 归零。平台在限流响应里给出重试时机时，首次恢复尝试 SHALL 遵循该时机。

同一时刻 SHALL 最多有一个恢复尝试在飞行中。

#### Scenario: 一次限流不再让客户重扫二维码

- **WHEN** 定时同步期间平台返回限流，且本地加密会话完好、身份未变
- **THEN** 授权态进入 `degraded`、原因码为 `WECHAT_RATE_LIMITED`，并按平台给出的重试时机（缺省 30s、上限 5min）安排恢复尝试
- **AND** 恢复尝试 MUST NOT 打开浏览器
- **AND** 恢复尝试成功后授权态自动回到 API-only 正常运行、能力恢复、退避重置，全程无需客户操作

#### Scenario: 网络抖动后自愈且退避有上限

- **WHEN** 上游连续返回 5xx / 连接超时，且底层客户端已重试仍失败
- **THEN** 授权态进入 `degraded`、原因码为 `INTERACTION_UPSTREAM_UNAVAILABLE`，恢复尝试从 5s 起按指数退避、上限 2min
- **AND** 连续失败时恢复尝试 SHALL 继续按上限间隔重试，MUST NOT 停止
- **AND** 首次恢复尝试成功即回到正常运行态

#### Scenario: 恢复尝试遇到结构性失败则移交既有终局路径

- **WHEN** 恢复尝试的结果由临时性失败升级为登录失效、需要人机验证或身份不匹配
- **THEN** 恢复计时器 SHALL 被取消，并转入既有的浏览器重认证 / `reauth_required` / `challenge_required` 路径
- **AND** MUST NOT 在这些路径之外再叠加一条并行的自动重试

### Requirement: 不可恢复态的准入判据与回拨路径

只有**结构上做不到**的失败才 MAY 进入没有自动恢复的状态。Edge SHALL 仅把两类视为无自动恢复：身份不匹配（本地会话属于另一个账号，重试同一会话在结构上不可能成功）与运营显式停用；两者 MUST 各自有明确的人工恢复入口——前者是客户重新登录，后者是运营重新启用。除此之外的任何降级原因 MUST 带自动恢复通道。

任何取消恢复计时器的生命周期动作（清除会话、停用、重新登录、认证成功）SHALL 同时重置退避状态；停用之后 MUST NOT 再发起恢复尝试。

#### Scenario: 权限拒绝与接口改版慢探但不放弃

- **WHEN** 授权态因权限拒绝或接口改版进入 `degraded`
- **THEN** 恢复尝试 SHALL 按长间隔安排（权限拒绝 5min 起、上限 30min；接口改版 10min 起、上限 60min）
- **AND** 平台侧授权恢复或端点恢复正常后，Edge SHALL 在无人干预下自动回到正常运行态

#### Scenario: 身份不匹配保持终局且入口明确

- **WHEN** 本地会话经校验属于另一个账号
- **THEN** 授权态 SHALL 为 `reauth_required`、原因码 `WECHAT_IDENTITY_MISMATCH`，且 MUST NOT 安排自动重试
- **AND** 恢复入口 SHALL 是客户重新登录

#### Scenario: 停用后不再有恢复尝试

- **WHEN** 运营停用该账号的互动能力
- **THEN** 在飞行中的恢复计时器 SHALL 被取消
- **AND** 后续 MUST NOT 再发起任何恢复尝试，直到运营重新启用

### Requirement: 探针失败原因必须诚实分类

只读探针的结果 SHALL 携带结构化的失败原因，而非压成单一 boolean。Edge 对外呈现的授权原因码 SHALL 是探针算出的真实类别（限流、上游不可用、权限拒绝、登录失效、需要人机验证、身份不匹配、接口改版各归各位），MUST NOT 把非接口改版的原因统一报成接口改版。无法归类的未知错误 SHALL 报为上游不可用，MUST NOT 回落到接口改版。

原因码 SHALL 只取协议既有的授权原因码枚举值，本能力 MUST NOT 为此新增协议枚举。

#### Scenario: 限流导致的探针失败不得报成接口改版

- **WHEN** 只读探针因平台限流失败
- **THEN** 授权快照的原因码 SHALL 为 `WECHAT_RATE_LIMITED`
- **AND** MUST NOT 为 `WECHAT_SCHEMA_CHANGED`

#### Scenario: 未知错误报上游不可用

- **WHEN** 只读探针遇到无法归入既有类别的错误
- **THEN** 授权快照的原因码 SHALL 为 `INTERACTION_UPSTREAM_UNAVAILABLE`

### Requirement: 零可探范围 MUST NOT 判为接口改版

账号尚无可供探测的内容（如一篇帖子都没发过）属于「目标暂不存在」，不是平台改版、也不是失败。Edge MUST NOT 因此进入 `degraded`、MUST NOT 报 `WECHAT_SCHEMA_CHANGED`；授权态 SHALL 保持正常运行。受影响的能力因未取得探针证据 SHALL 按 fail-closed 保持关闭，并在证据记录中如实标注为「因无可探范围而被 gate」，待周期性重探取得证据后自动放行。

#### Scenario: 零发帖新号接入不被误判

- **WHEN** 帖子列表接口调用成功但返回空列表，因而没有可探测的评论目标
- **THEN** 授权态 SHALL 保持 API-only 正常运行，MUST NOT 降级、MUST NOT 报接口改版
- **AND** 评论读取能力 SHALL 保持关闭，证据记录标注 gated 与「无可探范围」
- **AND** 该账号发出第一篇帖子后，重探成功 SHALL 使评论读取能力自动放行

### Requirement: 端点熔断必须可复位

端点熔断 SHALL 是时限性的，MUST NOT 持续到进程结束。熔断 SHALL 带默认 10 分钟的存活时限，到期自动失效——这是不依赖任何外部接线的兜底恢复通道；对该端点的探针成功 SHALL 立即复位其熔断。对外的熔断快照 SHALL 只包含当前仍在生效的端点，MUST NOT 把已过期的熔断当成仍在生效上报。

#### Scenario: 熔断到期自动失效

- **WHEN** 某端点因接口改版被熔断，且此后存活时限内无新证据
- **THEN** 时限一到，该端点相关能力的熔断判定 SHALL 自动回到可用
- **AND** 后续请求 SHALL 被允许发出以获取新证据

#### Scenario: 探针成功即刻复位

- **WHEN** 某端点处于熔断中，而针对该链路的只读探针在存活时限内探测成功
- **THEN** 该端点的熔断 SHALL 立即复位
- **AND** 熔断快照中 SHALL 不再包含该端点

### Requirement: 非 schema 原因 MUST NOT 触发端点熔断

只有真正的结构不符（字段缺失、类型不符）才 SHALL 被判为接口改版并触发熔断。返回体不是 JSON（如 WAF 拦截页、平台故障页）与响应体超出大小限制 SHALL 被判为可重试的临时上游故障，MUST NOT 触发端点熔断。

#### Scenario: WAF 拦截页不熔断能力

- **WHEN** 某端点返回 HTTP 200 但响应体是 HTML
- **THEN** 该请求 SHALL 抛出可重试的临时上游故障
- **AND** 端点熔断器 MUST NOT 因此被打开

#### Scenario: 响应超限不熔断能力

- **WHEN** 某端点的响应体超出大小限制
- **THEN** 该请求 SHALL 抛出可重试的临时上游故障，MUST NOT 判为接口改版

#### Scenario: 真实结构不符仍然熔断

- **WHEN** 某端点返回合法 JSON 但必需字段缺失或类型不符
- **THEN** 该端点 SHALL 被判为接口改版并打开熔断
- **AND** 该熔断仍 SHALL 受存活时限与探针复位约束

### Requirement: Interaction schema rollout MUST degrade by capability instead of disabling safe reads

Cloud MUST distinguish the base interaction schema from the migration `0046` outbound retry schema. When the base schema is complete and the database is in the exact pre-`0046` shape, Cloud MUST start the interaction domain in a compatibility read-only mode rather than omitting the customer interaction API. In that mode Cloud MUST preserve interaction reads, sync, auth-state reads, and comment/DM read controls, while all comment-reply and DM-send paths MUST fail closed before a send attempt is created.

Cloud MUST treat the exact completed `0046` shape as full mode. A partially applied or otherwise inconsistent `0046` shape MUST NOT enter either compatibility or full mode and MUST keep the interaction domain disabled with an explicit startup error. Startup MUST NOT execute schema DDL.

#### Scenario: Exact pre-0046 schema restores safe reads

- **GIVEN** the base interaction schema is complete
- **AND** the active-attempt partial unique index from migration `0046` is absent
- **AND** the legacy `retryable` column is present
- **WHEN** Cloud starts the interaction domain
- **THEN** Cloud registers the customer interaction API in compatibility read-only mode
- **AND** interaction lists, sync, auth-state reads, and comment/DM read controls remain available

#### Scenario: Compatibility mode closes outbound capabilities at both gates

- **GIVEN** Cloud is running the interaction domain in compatibility read-only mode
- **WHEN** runtime controls are projected or an outbound comment reply / DM send is requested
- **THEN** comment-reply and DM-send controls are false
- **AND** the send orchestrator rejects the outbound request before creating a send attempt
- **AND** comment and DM read controls retain their independently configured values

#### Scenario: Completed migration preserves full behavior

- **GIVEN** the base interaction schema is complete
- **AND** the active-attempt partial unique index from migration `0046` is present
- **AND** the legacy `retryable` column is absent
- **WHEN** Cloud starts the interaction domain
- **THEN** Cloud uses full mode
- **AND** the existing global write configuration continues to govern outbound capabilities

#### Scenario: Partial migration fails closed

- **GIVEN** only one of the two migration `0046` schema markers has reached its final state
- **WHEN** Cloud starts the interaction domain
- **THEN** Cloud rejects the inconsistent schema state
- **AND** Cloud does not register the interaction customer API
- **AND** Cloud does not execute corrective DDL automatically

### Requirement: 鉴权浏览器启动失败必须退出进行中状态并保留恢复入口

视频号鉴权流程在本地浏览器 sidecar 打开失败时 SHALL 立即退出 `authenticating`，MUST NOT 无限停留在 `browser_opening`。若已有失效的绑定会话，授权态 SHALL 回到 `reauth_required`；若尚未建立会话，授权态 SHALL 回到 `login_required`。两条路径均 SHALL 使用既有 `WECHAT_AUTH_REQUIRED` 原因码、保持所有写能力关闭，并保留客户重新鉴权入口。

浏览器状态 SHALL 独立报告为 `unavailable`，MUST NOT 因 Cloud 控制面仍在线而冒充浏览器已打开或鉴权通过。

#### Scenario: 旧会话过期且浏览器打不开时提示重新鉴权

- **WHEN** Edge 发现已保存的视频号会话过期，尝试打开绑定 AdsPower profile 时失败
- **THEN** 授权态 SHALL 为 `reauth_required`、原因码 SHALL 为 `WECHAT_AUTH_REQUIRED`、浏览器状态 SHALL 为 `unavailable`
- **AND** workspace SHALL 提供现有重新鉴权入口，MUST NOT 继续显示“鉴权中”

#### Scenario: 首次登录浏览器打不开时仍可重新检查登录

- **WHEN** 环境尚无已保存会话且鉴权浏览器启动失败
- **THEN** 授权态 SHALL 为 `login_required`、原因码 SHALL 为 `WECHAT_AUTH_REQUIRED`、浏览器状态 SHALL 为 `unavailable`
- **AND** 客户后续 SHALL 能通过既有登录检查入口重试

### Requirement: 本地鉴权浏览器失败诊断不得泄露凭据

Edge SHALL 为鉴权浏览器打开失败记录结构化、脱敏的本地诊断，并把运行时错误码归入既有授权错误 `WECHAT_AUTH_REQUIRED`，MUST NOT 把该已知失败压成 `INTERACTION_INTERNAL_ERROR`。诊断 MAY 包含白名单化的 provider、operation、失败类别、HTTP 状态或 AdsPower 错误码；MUST NOT 包含 API key、Authorization header、cookie、会话材料、原始响应正文或带 query 的 URL。

#### Scenario: AdsPower 拒绝启动时记录可操作且脱敏的诊断

- **WHEN** AdsPower `browser-profile/start` 返回非成功状态
- **THEN** Edge 日志 SHALL 标明 provider、operation 与安全错误类别，并在可安全解析时包含 HTTP 状态或 AdsPower code
- **AND** 运行时 SHALL 回报 `WECHAT_AUTH_REQUIRED`，MUST NOT 回报 `INTERACTION_INTERNAL_ERROR`
- **AND** 日志 MUST NOT 包含任何本地 API 凭据或视频号会话材料

### Requirement: 视频号回复数量准入必须只有一套 interaction 限速

Cloud SHALL 使用 published reply policy 的账号分钟、小时、每日限额和同会话冷却作为视频号评论/私信回复的唯一数量准入，并 SHALL 在创建 send attempt 的账号级事务内原子复核。`RiskController` 的风险状态拒因 MUST 继续阻断发送，但其通用 `quota:*` 拒因 MUST NOT 再作为视频号回复的第二套数量限额。缺少 controller 或遇到未知非 quota 拒因 MUST fail closed。

#### Scenario: 通用私信 quota 为零但专用限速有余量
- **WHEN** 视频号私信 job 已满足全部发送门禁、interaction 专用限速有余量，而 `RiskController.explain(dm_reply)` 仅返回 `quota:*`
- **THEN** Cloud 继续按 interaction 专用限速创建发送尝试
- **AND** MUST NOT 要求运营再写一份共享 `quota_config`

#### Scenario: 风险状态仍然阻断发送
- **WHEN** `RiskController.explain(comment|dm_reply)` 返回 `state:restricted`、`state:frozen` 或其它非 quota 拒因
- **THEN** Cloud 在创建 send attempt 前拒绝发送

### Requirement: 人工审核发送不得等待自动发送登录冷却

新登录冷却 SHALL 只约束无人值守自动发送。带非空人工批准主体的 job MUST NOT 因新登录冷却单独被拒；它仍 MUST 满足 active auth、identity、写 capability、运行控制、熔断、专用限速、CAS、幂等、单飞和结果核验。无人值守自动 job MUST 在生成准入和派发复核时都满足新登录冷却。

#### Scenario: 新登录后人工审核可立即发送
- **WHEN** 平台身份与 capability 已确认、job 已由人工批准且其它门禁均满足，但登录时间未超过配置冷却
- **THEN** Cloud 允许该人工 job 进入发送流程

#### Scenario: 新登录后自动发送继续降级
- **WHEN** 无人工批准主体的 auto-safe job 命中新登录冷却
- **THEN** Cloud 不自动入队或派发，并将其保留为需要人工处理的安全状态

### Requirement: 纯 Cloud 草稿生命周期必须与平台在线鉴权解耦

已鉴权客户在其所属环境内生成、编辑或批准回复草稿时，Cloud SHALL 校验资源归属、配置、文本门禁、状态机和 CAS，但 MUST NOT 要求平台 auth 当前为 active 或写 capability 当前为 true。真实发送前 SHALL 重新验证全部平台与运行时门禁；草稿动作成功 MUST NOT 被呈现为发送能力已确认。

#### Scenario: 登录过期期间继续准备草稿
- **WHEN** 客户仍拥有环境访问权、互动数据已持久化，但视频号登录当前需要重新鉴权
- **THEN** 客户可以生成、编辑和批准草稿
- **AND** 实际发送保持关闭直到登录、身份与 capability 恢复

### Requirement: 新建回复策略必须包含可用的保守限速

新初始化的视频号 reply policy SHALL 保持生成、发送、渠道和自动化默认关闭，同时 SHALL 写入正数的保守 interaction 限速，而非三窗口全零。初始化 MUST NOT 发布配置或修改 runtime controls，且历史配置 MUST NOT 因读取或部署被静默改写。

#### Scenario: 初始化不扩权但避免零额度陷阱
- **WHEN** 管理员初始化一个从未配置的视频号账号
- **THEN** draft 中发送与自动化仍为关闭
- **AND** 分钟、小时、每日限额均为正数的保守预设
- **AND** 管理员后续主动选择人工审核并启用发送时不需要额外修复零额度

### Requirement: 启动鉴权与浏览器授权原因必须可诊断

视频号 Edge 在启动鉴权时 SHALL 记录安全、可检索的阶段日志，使客户能够判断本地加密会话是否命中、是否校验通过，以及浏览器为何被启动。有效会话通过身份校验和已启用只读探针后，日志 SHALL 明确说明浏览器未启动且运行时已进入 API-only 模式。

任何鉴权驱动的浏览器启动 SHALL 在调用浏览器提供商之前记录稳定原因标签，至少区分：启动时无本地会话、本地会话不可读或失效、平台要求验证、客户主动重新授权、运行中会话失效。临时网络、限流、权限拒绝或结构探测故障继续沿用既有无浏览器恢复语义时，日志 SHALL 明确说明浏览器保持关闭并等待接口恢复，MUST NOT 宣称需要重新登录。

上述日志 MUST NOT 包含 Cookie、请求头或请求上下文原文、密钥、密文、账号身份原文及其它授权凭据。

#### Scenario: 有效本地会话跳过浏览器

- **WHEN** 启动时找到本地加密会话，且身份校验与已启用只读探针均通过
- **THEN** Edge 进入 API-only 运行且不调用浏览器提供商
- **AND** 日志明确记录本地会话有效、浏览器未启动

#### Scenario: 无可复用会话时说明启动原因

- **WHEN** 启动时不存在可复用本地会话，或已有会话确认失效
- **THEN** Edge 在调用浏览器提供商之前记录对应稳定原因标签
- **AND** 日志说明浏览器用于登录或重新授权，不含任何凭据材料

#### Scenario: 临时故障不冒充登录失效

- **WHEN** 已有会话的启动校验遇到限流、临时网络、权限拒绝或结构探测故障
- **THEN** Edge 进入既有退避恢复路径且不启动浏览器
- **AND** 日志说明浏览器保持关闭并等待接口恢复，MUST NOT 记录为需要重新登录

### Requirement: 视频号启动鉴权必须优先复用已保存 API 会话

视频号 Edge 启动时 SHALL 先读取本地加密会话，并在浏览器关闭状态下校验平台身份与所有已启用只读探针。只有这些硬门禁全部通过，授权态才 SHALL 进入 API-only 正常运行；该路径 MUST NOT 启动浏览器。加密记录存在但身份或探针未通过时，MUST NOT 仅凭记录存在宣称鉴权成功。

#### Scenario: 有效记录无需浏览器即可鉴权通过

- **WHEN** 本地加密会话可读、平台身份与绑定一致，且所有已启用只读探针通过
- **THEN** Edge SHALL 上报 `status=active`、`browserState=closed`、`reasonCode=null`
- **AND** MUST NOT 调用浏览器 provider

#### Scenario: 失效记录不得冒充成功

- **WHEN** 本地加密会话存在但平台返回登录失效，或身份/已启用只读探针未通过
- **THEN** Edge MUST NOT 上报鉴权通过
- **AND** 只有需要补授权的结构性结果才 SHALL 进入既有浏览器重认证路径

### Requirement: 补授权浏览器被占用必须进入明确可重试真态

视频号因会话失效而需要浏览器补授权时，若 provider 明确返回 profile 被占用，授权协调器 SHALL 结束本次 `authenticating`，进入 `reauth_required`，上报 `browserState=unavailable` 与 `reasonCode=INTERACTION_BROWSER_PROFILE_IN_USE`。该状态下历史内容 SHALL 保持可查看，所有平台写能力 MUST 保持关闭；系统 MUST NOT 自动强制抢占、MUST NOT 宣称仍在鉴权或鉴权成功。

Cloud SHALL 接受、持久化并通过客户 API 原样投影该原因码。客户工作区 SHALL 显示“浏览器环境被占用”、说明解除占用后重试，并提供显式重新鉴权入口；客户 API 与 UI MUST NOT 暴露原始占用邮箱。动作 accepted 只表示重试请求已受理，只有后续 auth status 回到 `active` 才表示恢复完成。

#### Scenario: 启动补授权时 profile 被占用

- **WHEN** 已保存会话校验为登录失效，且 `browser-profile/start` 明确拒绝原因为 profile 被占用
- **THEN** Edge SHALL 上报 `status=reauth_required`、`browserState=unavailable`、`reasonCode=INTERACTION_BROWSER_PROFILE_IN_USE`
- **AND** Cloud SHALL 原样持久化和投影该状态
- **AND** 客户工作区 SHALL 显示占用提示、历史可读与写操作暂停，并显示“重试打开浏览器”入口
- **AND** Edge、Cloud、客户 API 与 UI MUST NOT 暴露原始占用邮箱

#### Scenario: 解除占用后显式重试恢复

- **GIVEN** 当前授权原因码为 `INTERACTION_BROWSER_PROFILE_IN_USE`
- **WHEN** 客户解除外部占用并触发既有重新鉴权动作，provider 成功打开 profile，身份与已启用只读探针通过
- **THEN** Edge SHALL 保存新会话并回到 `status=active`
- **AND** UI 只有读回新的 active 状态后才 SHALL 显示鉴权通过

#### Scenario: 占用状态不做高频自动抢占

- **WHEN** profile 占用持续存在且客户尚未触发重试
- **THEN** Edge MUST NOT 高频重复调用 start、stop 或执行强制抢占
- **AND** 授权状态 SHALL 保持 fail-closed，等待显式重试或新的真实状态证据

### Requirement: 授权请求上下文漂移 MUST 精确恢复

Edge SHALL 区分浏览器页面登录态与加密 API 会话真态。平台明确返回已知的授权请求上下文失效业务码时，Edge MUST 把现有 API 快照视为失效，进入既有浏览器重新授权路径，重新采集 Cookie 与请求上下文，并在身份和已启用只读探针均通过后才保存新快照、恢复 `active`。浏览器页面可见或 profile 仍在运行 MUST NOT 单独作为鉴权成功证据。

只有经过证据确认的授权请求上下文失效码 MAY 触发该路径；其他未知平台拒绝 MUST 保持原分类，MUST NOT 因共享通用错误文案而自动打开浏览器。

#### Scenario: 业务码 300334 触发会话重新采集

- **GIVEN** Edge 正以已保存的加密会话运行，浏览器页面仍可显示登录状态
- **WHEN** 身份或已启用读取接口返回 HTTP 200、平台业务码 `300334`
- **THEN** Edge 将当前 API 会话判为失效并上报 `WECHAT_AUTH_REQUIRED`
- **AND** Edge 通过既有 sidecar 打开或接管原 profile、刷新页面并重新采集授权材料
- **AND** 只有身份和已启用只读探针通过后才重新进入 `active`

#### Scenario: 未知平台拒绝不冒充授权失效

- **WHEN** 平台返回并非 `300334` 的未知非零业务码，且没有登录失效、验证挑战或权限拒绝证据
- **THEN** Edge 保持该结果为一般平台拒绝
- **AND** MUST NOT 仅因通用 `request failed` 文案自动打开浏览器

### Requirement: 客户工作区鉴权真态 MUST 持续收敛

视频号工作区在可见且环境在线时 SHALL 持续低频读取 Cloud 真态。当前鉴权状态不是 `active`、读取开关关闭或读取能力尚未生效 MUST NOT 永久停止该刷新通道。重新授权请求被接受后，界面 MUST 等待 Edge 实际状态回报，MUST NOT 合成鉴权成功。

明确收到 `browserState=closed` 时，界面 MUST 将其视为已回报：`active` 时显示后台模式，其他状态显示浏览器已关闭；只有缺失 browserState 回报时才显示未回报。

#### Scenario: 首次旧状态随后收敛为 active

- **GIVEN** 工作区首次读取到 `login_required + browserState=closed`
- **AND** Cloud 随后持久化 `active + browserState=closed`
- **WHEN** 工作区保持可见且环境在线
- **THEN** 后续低频刷新取得新快照并显示鉴权通过与后台模式
- **AND** MUST NOT 永久停留在等待登录或未回报

#### Scenario: 读取关闭不切断鉴权刷新

- **WHEN** 评论和私信读取开关均关闭，但工作区可见且环境在线
- **THEN** 工作区仍安排后续真态刷新
- **AND** 读取与写入操作继续由现有能力门禁关闭

### Requirement: 平台拒绝诊断 MUST 安全且可定位

Edge 对平台 API 失败的运行日志 SHALL 至少包含稳定 endpoint 与协议错误码；当响应提供 HTTP 状态或平台业务码时 SHALL 记录对应标量。日志 MUST NOT 包含 Cookie、请求头、请求正文、响应正文、平台 message、身份原文或其它授权材料。

#### Scenario: 定时同步输出安全诊断字段

- **WHEN** 定时同步收到 HTTP 200、平台业务码 `300334`
- **THEN** 日志包含同步渠道、稳定 endpoint、HTTP 状态 `200`、平台码 `300334` 和协议错误码
- **AND** 日志不包含 Cookie、请求或响应正文

### Requirement: 视频号产品写能力不得依赖本机隐藏授权

Edge SHALL derive comment and DM text-write capabilities from the scoped Cloud runtime controls, active matching identity, successful corresponding read-path evidence, and current endpoint circuit state. It MUST NOT require a local account grant, local channel enable, local write kill switch state, operator-recorded write-probe approval environment variable, or unpackaged-client bypass token as an additional product authorization.

The first and every subsequent real write MUST still pass Cloud policy, runtime controls, risk, interaction rate limits, CAS, idempotency and single-flight, and Edge exact-target/post-action validation. Missing read evidence, identity mismatch, open circuit, or disabled Cloud control MUST keep the capability closed.

#### Scenario: Packaged client gains configured comment write capability
- **WHEN** a packaged client has active matching identity, successful comment read evidence, healthy endpoints, and scoped Cloud controls enable comment reading and replying
- **THEN** Edge reports comment reply capability without requiring `AIDCP_WECHAT_COMMENT_WRITE_PROBE_VERIFIED` or another local grant

#### Scenario: Cloud channel off remains authoritative
- **WHEN** stale local environment values imply writes are enabled but scoped Cloud controls disable DM text send
- **THEN** Edge reports DM text send unavailable and MUST NOT execute a DM write

#### Scenario: Read evidence or circuit failure remains fail closed
- **WHEN** the corresponding read probe has not succeeded or a required write endpoint circuit is open
- **THEN** Edge keeps the write capability closed regardless of the Cloud channel toggle

### Requirement: 视频号平台标识与能力必须诚实声明

系统 SHALL 使用精确 `PlatformId='wechat_channels'`，并 SHALL 继续把每个视频号账号绑定为一个 `envKey + accountId` 环境。平台能力 SHALL 分别声明 `identity`、`overlay`、`auth.browser_sidecar`、`interaction.comment.read`、`interaction.comment.reply`、`interaction.dm.read`、`interaction.dm.send_text`、`interaction.dm.send_image`；browse/like/collect/follow/publish/patrol MUST 显式 unsupported。账号状态上报的 capability 布尔值 MUST 表达 build support、feature flag、active auth、identity match 与 endpoint probe 同时成立后的有效能力，MUST NOT 把“代码可能支持”冒充“当前可用”。

#### Scenario: 视频号环境按精确平台启动
- **WHEN** 一个环境被标注为 `wechat_channels` 并启动
- **THEN** Edge 与 Cloud 均以 `wechat_channels` 路由该账号，MUST NOT 回落 `xiaohongshu` 或 `facebook`

#### Scenario: 未通过发送探针时不声明写能力
- **WHEN** 当前账号评论读取正常但评论发送 probe/feature flag 未通过
- **THEN** `commentsRead` MAY 为 true，但 `commentsReply` MUST 为 false，系统 MUST NOT 下发发送命令

#### Scenario: 图片私信在 v1 诚实禁用
- **WHEN** 任意 v1 视频号账号上报能力
- **THEN** `dmSendImage` MUST 为 false，任何图片 send 请求 MUST 返回 unsupported 而非转成文本或伪成功

### Requirement: 浏览器仅作为鉴权 sidecar

Edge SHALL 维护 `uninitialized → browser_login_required → browser_opening → qr_waiting → identity_verifying → session_active → browser_closing → api_only_running` 的本地鉴权主链；`api_only_running` MAY 进入 `reauth_required`、`challenge_required` 或 `degraded`。只有登录确认、身份匹配、本地密文保存和至少一个已启用只读 probe 成功后，浏览器才 MAY 关闭。关闭浏览器 MUST NOT 停止 Edge 核心、Cloud WebSocket、connector timer 或本地会话。

#### Scenario: 浏览器关闭后继续同步
- **WHEN** 账号进入 `api_only_running` 且浏览器正常关闭
- **THEN** Edge 核心与 WS 保持在线，已启用的评论/DM connector 继续工作，UI 将 browser closed 表达为正常副状态

#### Scenario: 普通网络错误不频繁拉起浏览器
- **WHEN** connector 遇到短暂网络超时但没有 auth/challenge/identity 信号
- **THEN** 鉴权状态进入或保持 `degraded` 并有限退避，MUST NOT 自动反复打开浏览器

#### Scenario: auth reopen 只在原环境执行
- **WHEN** Cloud 下发 `interaction.auth.reopen` 给某 `envKey + accountId`
- **THEN** Edge 只在该环境绑定的 browser profile 拉起 sidecar，并通过后续 `interaction.auth.status` 如实上报阶段

### Requirement: 会话凭证必须留在所属 Edge 并防串号

Cookie/session/二维码/浏览器调试地址 MUST NOT 出现在 Cloud DB、WS payload、普通日志、crash report、metrics、renderer 或 fixtures。Edge 本地密文 SHALL 绑定 `envKey + accountId + finderIdentity + browserProfileId`；每个环境 MUST 使用独立 cookie jar、timer 与 in-flight namespace。每次恢复会话和发送前 MUST 校验稳定身份；身份不符时 MUST 停止同步和发送并上报 `WECHAT_IDENTITY_MISMATCH`。

#### Scenario: 登录到错误账号时 fail closed
- **WHEN** 会话恢复后的身份 probe 与环境绑定 identity 不一致
- **THEN** Edge 禁止读写、清除当前 effective capabilities、上报 identity mismatch，MUST NOT 把观察到的账号内容写入目标环境

#### Scenario: 清除登录信息立即停写
- **WHEN** 用户对当前环境执行清除登录信息
- **THEN** Edge 停止新发送、删除本地密文并进入 login required，Cloud 只保留业务队列而不把任务标记成功

### Requirement: 已验证的视频号昵称必须回填通用账号展示名

Cloud 在完成连接账号、平台与环境 scope 校验后收到 `interaction.auth.status` 时，只有 payload 同时满足 `status='active'`、identity 非空且 `identity.displayName` 去除首尾空白后非空，才 SHALL 将该展示名写入通用 `accounts.nickname`。该写入只补充展示元数据，MUST NOT 改变 `accountId`、平台、环境归属、身份路由或授权状态；昵称补充失败 MUST NOT 把已经持久化的 auth status 冒充为失败。Console 账号列表 SHALL 继续使用通用 `nickname → label → accountId` 诚实回落链，MUST NOT 增加视频号专用假名分支。

#### Scenario: active 身份状态自动回填后台昵称
- **WHEN** 已绑定视频号环境上报 scope 匹配的 active auth status，identity displayName 为 `示例视频号`
- **THEN** Cloud 持久化 auth status 并把对应 `accounts.nickname` 更新为 `示例视频号`，Console 后续读取账号列表时显示该昵称而非 envKey/accountId

#### Scenario: 未验证或空白身份不得覆盖昵称
- **WHEN** auth status 不是 active、identity 为空，或 displayName 去除首尾空白后为空
- **THEN** Cloud MAY 持久化真实 auth status，但 MUST NOT 新建、清空或覆盖 `accounts.nickname`

### Requirement: 私有接口必须由安全 adapter 隔离

所有创作者助手私有端点调用 SHALL 收口在 Edge `WechatChannelsApiClient`，默认启用 TLS 验证、超时、响应大小上限、有限重试和逐端点 schema 校验。未知字段 MAY 容忍，关键字段缺失 MUST 分类为 `schema_changed` 并关闭对应 capability。第三方响应/错误 MUST 经稳定 error category/code 脱敏，MUST NOT 作为官方 API 或原文直接透传。

#### Scenario: schema 漂移关闭单一能力
- **WHEN** DM history 的关键字段缺失而 comment schema 仍正常
- **THEN** Edge 关闭 `dmRead/dmSend*` 并上报 `WECHAT_SCHEMA_CHANGED`，评论能力 MAY 保持，MUST NOT 崩溃或吞掉错误当成功

#### Scenario: 读能力不自动开放写能力
- **WHEN** 评论列表 probe 成功但评论发送未做受控验证
- **THEN** 读取 MAY 开启，评论写 MUST 继续关闭

### Requirement: WS v2 互动扩展必须完整协商并原子接线

系统 SHALL 在 WS v2 完整接线基础 inbox 七个类型，以及 `interaction.reply.result.ack`、`interaction.reply.reconcile`、`interaction.reply.reconcile.result`、`interaction.offboard.command`、`interaction.offboard.result`、`interaction.offboard.ack` 六个恢复/offboard 类型，使目标 `MessageType` 总数为 91；该数字为人工维护、可能滞后，权威口径以 Cloud 与 Edge 两端 `protocol.ts` 的联合类型穷举为准。两份 protocol 定义、Cloud handler/mapping、Edge active-command routing、`docs/protocol.md` 与共享 schema/fixtures MUST 同步。基础能力用 `interaction_inbox_v1`，结果恢复用 `interaction_reply_recovery_v1`，offboard 用 `interaction_offboarding_v1`；Cloud 只回显双方支持的能力，扩展能力依赖基础能力。回显 offboard 能力时 welcome MUST 带 account-bound `interactionRecovery.offboardPending`，Edge 只有明确 false 才可恢复 connector。

#### Scenario: 新 Cloud 不向旧 Edge 派 interaction 命令
- **WHEN** Edge hello 不含 `interaction_inbox_v1`
- **THEN** Cloud 不下发 sync/send/reopen，旧 Edge 连接与既有功能保持可用

#### Scenario: 新 Edge 遇旧 Cloud 不重试风暴
- **WHEN** welcome 未回显 `interaction_inbox_v1`
- **THEN** 新 Edge 不启动新 batch/status 上报，呈现 integration unavailable/degraded，MUST NOT 循环发送未知 type

#### Scenario: active-command routing 漏项使验收失败
- **WHEN** protocol 枚举包含 `interaction.reply.send` 但 Edge 主动命令入口未放行
- **THEN** 契约/acceptance MUST 失败，MUST NOT 以 typecheck 通过视为接线完成

#### Scenario: 未协商恢复能力不清 durable result
- **WHEN** 新 Edge 对接只支持基础 inbox 的旧 Cloud
- **THEN** Edge MAY 发送基础 reply.result，但 MUST 保留 result outbox，直到后续连接协商 recovery 并收到 exact ack

#### Scenario: 未协商 offboard 能力保持撤权待清理
- **WHEN** Cloud 已撤权但连接的旧 Edge 没有 `interaction_offboarding_v1`
- **THEN** Cloud 不发送未知 type、不恢复同步/写，offboard 保持 pending 且不得提前 tombstone

#### Scenario: pending 查询失败不短暂恢复 connector
- **WHEN** Cloud 回显 offboard capability 但 pending 状态读取失败或 welcome 缺少 recovery barrier
- **THEN** Edge 将其视为 offboardPending=true，保持 connector 停止，MUST NOT 在 command 到达前短暂同步或写

### Requirement: Edge 同步 checkpoint 必须等 Cloud 显式 ack

一个 `interaction.sync.batch` SHALL 只覆盖一个 account/env/channel/scope。Cloud MUST 以相同 envelope `id` 回 `interaction.sync.ack`；Edge 只有在 ack status 为 `accepted|duplicate` 且 `cursorAfter` 逐字匹配时才提交 checkpoint。`rejected`、断连、超时或 cursor 不匹配 MUST 保持旧 checkpoint。

#### Scenario: 重复 batch 不重复副作用
- **WHEN** Edge 因 ack 丢失重发同一 `batchId`
- **THEN** Cloud 返回 `duplicate` 与原 cursor 真态，MUST NOT 重复创建 message/job，Edge MAY 安全提交 checkpoint

#### Scenario: 部分持久化失败不推进 cursor
- **WHEN** batch 中任一 thread/message 校验或事务写失败
- **THEN** Cloud 回 `rejected` 或连接错误且整批回滚，Edge 保持 `cursorBefore`

### Requirement: Edge 发送必须幂等并诚实处理歧义

Edge SHALL 持久保存 `idempotencyKey` 与已执行结果；重复 `interaction.reply.send` MUST 返回既有结果而不再次调用平台。只有平台 ack 或历史/评论回查确认才可返回 `confirmed`；网络超时、连接中断和响应解析失败 MUST 返回 `ambiguous` 并先回查，MUST NOT 盲目重发。

#### Scenario: 重复发送命令只调用一次平台
- **WHEN** 同一 `attemptId + idempotencyKey` 因 WS 重连重复到达
- **THEN** Edge 复用持久结果并回 `interaction.reply.result`，平台写接口最多调用一次

#### Scenario: 超时不冒充失败或成功
- **WHEN** 平台提交请求已发出但响应超时且回查尚无结论
- **THEN** Edge 返回 `status='ambiguous'`、`verification='not_verified'`，MUST NOT 返回 confirmed 或触发自动重试

### Requirement: Edge 发送结果必须 durable 并由 Cloud exact ack

Edge SHALL 在发送 `interaction.reply.result` 前将完整结果写入 durable outbox，并在启动/重连后补发。Cloud SHALL 在事务持久化 scope-matching attempt/job 后返回同 envelope id 的 ack。Edge MUST 只在 ack status=`accepted|duplicate` 且 jobId/attemptId/idempotencyKey/envKey/accountId/platform 全部逐字匹配时清除 outbox。

#### Scenario: Cloud 持久化后在 ack 前崩溃
- **WHEN** Edge 未收到 ack 并在重连后重发同一 result
- **THEN** Cloud 返回 duplicate，job/attempt/RiskController 副作用至多一次，Edge 收 exact ack 后清 outbox

#### Scenario: 错绑或 rejected ack 不清 outbox
- **WHEN** ack 的 accountId、attemptId 或 idempotencyKey 不匹配，或 status=rejected
- **THEN** Edge 保留 durable result 并停止本轮 flush，MUST NOT 把结果视为已确认

### Requirement: Attempt reconciliation 禁止 blind resend

Cloud SHALL 在启动和 Edge 重连时针对 `created|dispatched|ambiguous` 原 attempt/idempotency identity 发 `interaction.reply.reconcile`。Edge SHALL 只检查 durable execution/result 或平台历史，不得调用 reply platform write。`created+not_found` MAY 明确 failed；`dispatched|ambiguous+not_found` MUST 保持 ambiguous；`result_replayed` MUST 通过正常 durable result 回传推进。

#### Scenario: Edge 本地没有 dispatched attempt
- **WHEN** reconcile 请求一个 Cloud 已 dispatched、Edge 状态中不存在的 attempt
- **THEN** Edge 回 not_found 且平台写调用数为 0，Cloud 保持 ambiguous 并禁止同 job 新 attempt

### Requirement: Edge offboard 必须 durable、scope-bound 且与普通生命周期分离

Edge SHALL durable claim scope-bound `interaction.offboard.command`，先停止新同步/写并 drain 在途任务，再清除 `envKey+accountId+identity+profile` 加密 session、关闭 sidecar、durable 保存 result，并在 exact Cloud ack 前跨重启补发。普通 pause/close/standby/logout MUST NOT 执行 session clear。

#### Scenario: Edge 离线后重连补清理
- **WHEN** Cloud 已撤权并持久化 offboard，而 Edge 当时离线
- **THEN** 新 Edge 重连协商 capability 后收到同一 offboardId，按顺序清理并补发结果，期间不得恢复 connector 同步/写

#### Scenario: 清理失败可重试且不误报成功
- **WHEN** session clear 或 sidecar close 失败
- **THEN** Edge durable 回 failed，Cloud 保持 pending；重试同 offboardId 可继续清理，MUST NOT tombstone 或显示已完成

### Requirement: 可见客户昵称不得因缺失非展示 ID 而丢弃

Edge SHALL 保留私有接口已返回的非空客户昵称和头像。评论响应的稳定 username 为空但 `commentNickname` 非空时，Edge SHALL 生成仅用于 participant scope 的确定性 opaque surrogate，MUST NOT 用昵称、头像 URL 或消息正文作为明文 ID。DM history 只提供会话与双方 username 时，Edge SHALL 以同批 session IDs 调用已验证的 `get-session-info` 只读端点，并用其 `username/nickname/headImgUrl` 富化 thread participant；昵称富化 MUST NOT 改变 message/thread 去重键、发送方向或 checkpoint ack 规则。

#### Scenario: 评论 username 为空仍展示平台昵称
- **WHEN** comment item 的 username 为空但 commentNickname 非空
- **THEN** 同步 batch 的 thread participant 使用确定性 opaque externalId 并保留 nickname/avatar，MUST NOT 把整个 participant 降为 null

#### Scenario: 私信历史通过 session info 富化客户昵称
- **WHEN** DM history 返回非空 sessionId/fromUsername/toUsername 且 session-info 返回同 sessionId 的 username/nickname/headImgUrl
- **THEN** Edge 在发布 batch 前把对应 participant 填为真实 nickname/avatar，且不在日志、fixture 或证据中记录真实值

### Requirement: Unverified WeChat writes are restricted to the named development runtime

The Electron companion SHALL inject the unverified WeChat write-test token only for an unpackaged development process whose selected Cloud environment is exactly `dev` and whose platform is exactly `wechat_channels`. Packaged clients and `ol` or custom Cloud selections MUST NOT receive this token. Without the exact token, candidate write descriptors and unverified capability bypasses MUST remain unavailable.

#### Scenario: Unpackaged dev WeChat environment receives the test token

- **WHEN** an unpackaged Electron client starts a `wechat_channels` environment connected to the named `dev` Cloud selection
- **THEN** the child Edge process receives the exact unverified-write test token

#### Scenario: Packaged or non-dev environment remains closed

- **WHEN** the client is packaged or its Cloud selection is `ol` or custom
- **THEN** the child Edge process does not receive the unverified-write test token
- **AND** unverified comment and DM descriptors remain blocked before fetch

### Requirement: Dev write testing bypasses only per-channel write grants and prior-probe evidence

When the exact dev token is active, Edge MAY treat the comment-reply and DM-text Cloud per-channel write booleans and prior-write-probe evidence gates as satisfied. Edge MUST still require a valid scoped/versioned Cloud runtime-control snapshot, active authentication, matching identity, healthy and Cloud-enabled channel reads, enabled global/local writes, closed kill switches, and a closed channel circuit. Cloud approval, policy, risk-state, account/thread rate-limit, CAS, idempotency, and dispatch gates MUST remain unchanged except for the documented reviewed-dev login/quota-only compatibility rule.

#### Scenario: Healthy dev account reports both text writes available

- **WHEN** the exact dev token is active and every non-probe comment and DM gate is satisfied
- **THEN** Edge reports `commentsReply=true` and `dmSendText=true`
- **AND** it records diagnostics identifying the unverified dev override

#### Scenario: Auth, read control, or control-snapshot validity still closes writes

- **WHEN** the exact dev token is active but authentication is inactive, identity mismatches, the channel read control is false, or the scoped Cloud-control snapshot is missing or invalid
- **THEN** the affected effective write capability remains false

#### Scenario: Dev token overrides false per-channel write booleans

- **WHEN** the exact dev token is active, the scoped Cloud-control snapshot is valid, the affected channel read is healthy and enabled, and only its per-channel write boolean is false
- **THEN** Edge reports the corresponding text-write capability as true
- **AND** diagnostics identify that the dev write-control override is active

### Requirement: Candidate write dispatch and confirmation remain honest

The dev override SHALL permit only the candidate comment-create and DM-text descriptors identified from the current first-party bundle. Both descriptors MUST remain non-retry-safe and MUST retain an evidence label distinct from capture-backed production descriptors. Edge MUST confirm a comment only from a platform-returned comment identifier and MUST confirm a DM only from a successful platform base response plus a server message identifier. Missing acknowledgements, changed schemas, platform rejection, and lost responses MUST remain failed or ambiguous according to dispatch evidence and MUST NOT be reported as sent.

#### Scenario: Platform server identifier confirms a test write

- **WHEN** the candidate request is dispatched and the platform returns the channel-specific successful response with a server identifier
- **THEN** Edge reports the attempt as confirmed with `verification=platform_ack`

#### Scenario: Candidate response cannot prove acceptance

- **WHEN** a candidate request leaves the process but its response lacks the required successful shape or server identifier
- **THEN** Edge does not report the attempt as confirmed
- **AND** schema drift opens only the affected endpoint circuit

#### Scenario: Candidate write is never retried blindly

- **WHEN** the candidate write times out or its response is lost after dispatch
- **THEN** Edge preserves the attempt as ambiguous
- **AND** recovery performs history verification without resending the platform write

### Requirement: Legacy-schema write testing is restricted to the named dev Cloud deployment

Cloud MUST keep the pre-0046 interaction schema read-only outside dev. Cloud MAY enable reviewed text writes on that exact schema only when `AIDCP_DEPLOY_ENV` is exactly `dev` and the existing global interaction-write switch is enabled. No additional Cloud write-test token is required. Missing base schema and partially migrated or inconsistent 0046 shapes MUST remain disabled. The override MUST NOT execute or emulate migration 0046 and MUST preserve the legacy database's unconditional idempotency uniqueness and `retryable=false` default.

#### Scenario: Existing dev write switch admits the pre-0046 schema

- **WHEN** Cloud is deployed as `dev`, the global write switch is enabled, and startup classifies the database as the exact pre-0046 shape
- **THEN** Cloud projects the stored comment-reply and DM-text controls without forcing them false
- **AND** normal approval, policy, risk, quota, CAS, attempt, dispatch, and result gates still apply

#### Scenario: Non-dev or invalid schema remains read-only

- **WHEN** the deployment is not exactly `dev`, the global write switch is off, or schema classification is missing or inconsistent
- **THEN** outbound interaction writes remain disabled before an attempt is created

#### Scenario: Compatibility mode does not add retry semantics

- **WHEN** a dev compatibility write has already consumed the legacy schema's deterministic idempotency key
- **THEN** Cloud does not weaken or replace the legacy uniqueness constraint
- **AND** no automatic resend is introduced by this override

#### Scenario: Reviewed dev send bypasses only local login and zero-default quota gates

- **WHEN** the named dev deployment has global interaction writes enabled and an already approved send is blocked only by post-login cooldown or a RiskController `quota:*` reason
- **THEN** Cloud continues admission without writing shared `quota_config`
- **AND** restricted or frozen risk state, interaction account/thread limits, auth, capability, approval, CAS, idempotency, dispatch, and result gates still apply

#### Scenario: Client distinguishes local admission from platform throttling

- **WHEN** Cloud returns `INTERACTION_RATE_LIMITED`
- **THEN** the client describes a Cloud-local send restriction and does not claim the platform rate-limited the request
- **AND** only `WECHAT_RATE_LIMITED` is described as platform throttling

### Requirement: 暂时不可投递 MUST NOT 被判为任务终态失败

云端发送编排 SHALL 只在**结构上做不到**时把回复 job 判为终态 `failed`。「资源暂时被占」「边缘暂时收不到命令」「连接恰好在事务期间关闭」等暂时性成因 MUST NOT 导致 job 进入终态，也 MUST NOT 烧掉已通过人工审批的授权。

同一函数中「边缘完全离线」与「投递数为 0」两条分支的成因同为暂时性，SHALL 收敛到同一条自愈语义：不建终态、job 留在可恢复状态、交由恢复循环重投。

#### Scenario: 边缘处于验证码硬暂停期

- **WHEN** 账号绑定的边缘处于验证码硬暂停态（回复命令不在下发豁免名单，投递必为 0）
- **THEN** 编排 SHALL 在建立 attempt **之前**识别该状态，不建 attempt、不改 job 状态、不作废审批授权
- **AND** job SHALL 保持 `queued`
- **AND** 编排 SHALL 抛出标记为可重试的上游不可用错误，使恢复循环记为 deferred 而非失败

#### Scenario: 投递数为 0

- **WHEN** 命令下发的投递数返回 0（连接在事务期间关闭或进入 CLOSING）
- **THEN** job MUST NOT 被置为 `failed`
- **AND** 已建立的 attempt SHALL 被作废到不占用活跃唯一槽的状态
- **AND** job SHALL 回到 `queued` 并可被恢复循环再次捞出

#### Scenario: 恢复循环 MUST NOT 成为烧毁器

- **WHEN** 恢复循环在暂停窗口内扫到整批排队积压
- **THEN** 该批 job MUST NOT 被批量置为终态
- **AND** 每轮 SHALL 只记 deferred 计量并保留 job 于 `queued`

#### Scenario: 无法证明命令未离开进程时保持不确定

- **WHEN** 下发抛出异常，或投递数大于 1
- **THEN** attempt 与 job SHALL 保持 `ambiguous` 语义不变
- **AND** MUST NOT 因本要求被自动放开重投——重复评论的代价高于人工核查

### Requirement: 每个不可发状态必须有明确的恢复路径

任何把回复 job 或 attempt 推入不可发状态的转换，SHALL 显式规定「什么把它拨回来」。没有恢复路径的降级 MUST NOT 被引入。

#### Scenario: 暂停态的恢复路径

- **WHEN** 边缘的验证码硬暂停解除
- **THEN** 留在 `queued` 的 job SHALL 在既有 30s 恢复循环的下一轮被重新下发，无需人工介入
- **AND** 原审批授权 SHALL 仍然有效——暂停是瞬态，MUST NOT 作废授权

#### Scenario: 回到 queued 的 job 必须真的可被恢复循环捞到

- **WHEN** 编排把 job 回置为 `queued` 并作废其 attempt
- **THEN** 该 attempt 的目标状态 MUST NOT 落在恢复循环的活跃排除集内（`created` / `dispatched` / `ambiguous`）
- **AND** 该 job SHALL 在下一轮待发队列中被捞出

### Requirement: 幂等键 SHALL 仅在活跃状态下唯一

发送尝试的幂等键 SHALL 由「仅活跃状态」的部分唯一索引约束，而非无条件全局唯一。同表已存在的「job+attempt 序号」唯一约束、attempt 序号递增逻辑与可重试标记，三处设计共同预设一个 job 可以有第 2、3 次 attempt；全局唯一使其在文案不变时结构上不可能，与既有设计自相矛盾。

#### Scenario: 失败后重试同一份确定性文案

- **WHEN** 一个 job 的前一次 attempt 已进入终态（`failed` / `confirmed`），该 job 被重新生成且模板渲染逐字相同（未开 AI 润色时必然如此）
- **THEN** 新 attempt SHALL 能被成功建立
- **AND** MUST NOT 因键冲突被阻断

#### Scenario: 私信渠道的结构性阻断解除

- **WHEN** 私信渠道在 AI 润色默认关闭下重试
- **THEN** 重试 SHALL 结构上可能，MUST NOT 出现 409 死循环空转

### Requirement: 键冲突 MUST NOT 冒充「已有发送尝试在进行中」

错误映射 SHALL 区分「真的有活跃 attempt」与「唯一约束冲突」两种成因。把后者报成前者是**静默假成功的近亲**——它向客户端陈述一件代码可证明为假的事实，并把 job 留在会被恢复循环反复重撞的状态。

#### Scenario: 存在活跃 attempt

- **WHEN** 建立 attempt 时唯一约束冲突，且该 job 确有处于 `created` / `dispatched` / `ambiguous` 的 attempt
- **THEN** 编排 SHALL 回「已有发送尝试在进行中」并保持 409 语义

#### Scenario: 不存在任何活跃 attempt

- **WHEN** 建立 attempt 时唯一约束冲突，但该 job 没有任何活跃 attempt
- **THEN** 编排 SHALL 如实报告键冲突，MUST NOT 声称有尝试在进行中
- **AND** 该冲突 MUST NOT 被静默吞掉后向客户端回报「已排队」

### Requirement: 无消费者的可重试标记 SHALL 被接线或删除

任何被写入但无任何消费者的可重试标记 SHALL 被接线成真实判据或删除，MUST NOT 作为无效果的标记长期留存——它会让读者误以为重试语义已实现。

若选择接线，则各处赋值口径 MUST 统一；若选择删除，则列的写入与列本身 SHALL 同批处理。

#### Scenario: 可重试标记的处置

- **WHEN** 可重试标记被写入 attempt 记录
- **THEN** 它 SHALL 被恢复循环或结果处理作为真实判据消费
- **OR** 该标记 SHALL 被移除

### Requirement: 同步上报的线程时间戳必须来自平台，取不到就让字段缺失

Edge 上报的线程更新时间 SHALL 只能来自平台响应解析出的时间值（会话列表给出的会话更新时间、或消息 / 评论自身的平台创建时间）。Edge MUST NOT 用本地时钟、云端下发请求的时刻（`requestedAt`）、或任何其它非平台来源的值充当该字段——无论是直接赋值还是经 `Math.max` 之类的运算混入。

定向（scoped）同步与全量同步在这一点上没有例外：定向路径为了发起翻页而合成的帖子 / 会话占位对象，其平台更新时间 SHALL 表达为「未知」，MUST NOT 就地编一个。

当某线程在本批次内**拿不到任何平台时间值**时，Edge SHALL 不在该批次发出这一行，让云端侧字段保持缺失；MUST NOT 为了凑齐字段而填占位值。此路径 SHALL 只在该批次同时不含属于该线程的消息时可达，以免产生引用批次外线程的孤儿消息。

**恢复路径**：省略线程行不是不可逆状态——该线程的平台更新时间会在下一次全量同步（平台会话列表带出真值）或下一次该线程有新消息时被正常补上，无需人工干预、不写任何持久化的降级标记。

#### Scenario: 定向重新同步评论不得把点击时刻写成平台时间

- **WHEN** 云端对某个帖子下发带 `scopeExternalId` 的评论同步请求，Edge 为发起翻页合成帖子占位对象
- **THEN** 该占位对象的平台更新时间 SHALL 为「未知」，上报批次中每个线程的更新时间 SHALL 等于该线程根评论的平台创建时间
- **AND** 上报的线程更新时间 MUST NOT 等于请求下发时刻，也 MUST NOT 因与请求时刻取最大值而被抬高

#### Scenario: 定向重新同步私信按本页消息的平台时间上报

- **WHEN** 云端对某个私信会话下发带 `scopeExternalId` 的同步请求，且本页返回了消息
- **THEN** 上报的线程更新时间 SHALL 等于本页消息平台创建时间的最大值
- **AND** MUST NOT 等于请求下发时刻或 Edge 本地时钟

#### Scenario: 无平台时间可取时省略线程行而非填假值

- **WHEN** 定向私信同步的某一页既无平台会话更新时间、也无任何消息
- **THEN** 该批次 SHALL 不含该线程行、也不含任何消息
- **AND** 翻页游标与 checkpoint SHALL 照常推进，同步 MUST NOT 因此中断或报失败

#### Scenario: 平台响应缺时间字段时如实报错而非兜底

- **WHEN** 平台响应里应有的时间字段缺失或无法解析
- **THEN** Edge SHALL 报接口结构已变更并点名具体端点与字段
- **AND** MUST NOT 用本地时钟兜底后当作成功上报

