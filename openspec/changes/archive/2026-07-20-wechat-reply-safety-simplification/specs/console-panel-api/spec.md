## ADDED Requirements

### Requirement: 视频号账号限速必须以预设优先并保留高级真值

Console SHALL 默认以“保守 / 标准 / 自定义”表达视频号账号限速。保守与标准预设 MUST 确定性映射完整 rateLimits；历史值只有逐位匹配预设时才能显示为该预设，否则 SHALL 显示自定义。六个原始字段 SHALL 收进可展开的高级设置并始终展示服务端真值；打开页面、识别预设或切换到自定义 MUST NOT 自动保存或扩大权限。

#### Scenario: 新安全草稿显示保守预设
- **WHEN** Cloud 返回新初始化 policy 的保守限速值
- **THEN** Console 选择“保守”并显示摘要
- **AND** 详细数字默认收折但可展开查看

#### Scenario: 历史零值不被静默改写
- **WHEN** Cloud 返回不匹配任何预设的历史 rateLimits
- **THEN** Console 显示“自定义”及真实数字
- **AND** 未经管理员主动选择预设并保存时不发送修改请求

### Requirement: 限速预设不得模糊系统硬门禁和平台事实

Console SHALL 将限速预设描述为 Cloud 本地回复节流，MUST NOT 声称其为视频号官方安全额度。选择预设 MUST NOT 修改 runtime controls、published version、平台 capability、RiskController 风险状态或熔断状态；保存仍只更新 policy draft，发布仍遵循既有原子边界。

#### Scenario: 选择标准预设只修改草稿限速
- **WHEN** 管理员选择标准预设并保存
- **THEN** 请求只携带现有 policy DTO 中更新后的 rateLimits
- **AND** 即时运行开关、平台能力和已发布版本保持不变

