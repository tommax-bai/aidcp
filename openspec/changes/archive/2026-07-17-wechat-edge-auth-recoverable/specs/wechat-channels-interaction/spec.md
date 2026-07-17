# wechat-channels-interaction

## ADDED Requirements

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
