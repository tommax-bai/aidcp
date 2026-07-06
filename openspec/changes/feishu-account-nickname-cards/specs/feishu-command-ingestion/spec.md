## ADDED Requirements

### Requirement: 命令结果卡片账号展示必须昵称优先

Feishu 命令结果卡片包含相关账号时，可见账号行 SHALL 使用账号主数据中的 `accounts.nickname` 作为优先展示名；当昵称为空、未知或账号存储不可用时，MUST 诚实回落展示真实 `accountId`。该展示名仅用于结果卡文案，命令解析、调度、发布 / 评论归属、审计和日志 MUST 继续使用真实 `accountId`。

#### Scenario: 参照创作失败结果卡展示昵称

- **WHEN** 精选内容池对账号 `acc-1` 触发参照创作，且账号 `acc-1` 的昵称为 `工程师大白`
- **AND** 参照创作编排失败并发送异步 Feishu 结果卡
- **THEN** 结果卡的账号行 SHALL 展示 `工程师大白`
- **AND** 结果卡标题、红黄绿 honest-status 判级和失败原因 MUST 保持真实终态语义

#### Scenario: 昵称缺失时回落账号 ID

- **WHEN** 任何命令或异步任务结果卡关联账号 `acc-2`，但该账号没有可用昵称
- **THEN** 结果卡的账号行 SHALL 展示 `acc-2`
- **AND** 系统 MUST NOT 编造昵称或把缺失昵称显示成成功状态
