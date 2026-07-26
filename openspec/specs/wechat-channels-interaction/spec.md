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

