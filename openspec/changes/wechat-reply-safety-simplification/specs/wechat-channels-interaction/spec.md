## ADDED Requirements

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

