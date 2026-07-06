## ADDED Requirements

### Requirement: 阻断告警卡片账号展示必须昵称优先

云端发送验证码 / 未知阻断弹窗 Feishu 告警卡时，卡片可见账号标识 SHALL 使用账号主数据中的 `accounts.nickname` 作为优先展示名；当昵称为空、未知或账号存储不可用时，MUST 诚实回落展示真实 `accountId`。该展示名仅用于 Feishu 文案，告警落库、风控状态迁移、edge 暂停 / 恢复和日志关联 MUST 继续使用真实 `accountId`。

#### Scenario: 未知阻断告警标题展示昵称

- **WHEN** 账号 `acc-1` 已捕获昵称 `工程师大白` 且该账号上报 `risk.captcha_detected{kind:'unknown'}`
- **THEN** Feishu P1 告警卡标题中的账号后缀 SHALL 展示 `工程师大白`
- **AND** 告警落库与风控迁移仍 SHALL 使用 `acc-1`

#### Scenario: 昵称缺失时回落账号 ID

- **WHEN** 账号 `acc-2` 尚未捕获昵称且该账号上报验证码或未知阻断
- **THEN** Feishu 告警卡 SHALL 展示 `acc-2`
- **AND** 系统 MUST NOT 编造昵称或隐藏账号标识
