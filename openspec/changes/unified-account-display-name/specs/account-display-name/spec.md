## ADDED Requirements

### Requirement: Cloud 账号运营别名与平台昵称分离持久化

Cloud SHALL 为每个真实账号持久化可空的运营别名，且 MUST 与平台验证昵称、运营标签及账号 ID 物理分离。人工设置仅更新运营别名；平台身份采集仅更新平台昵称，MUST NOT 覆盖运营别名。trim 后空内容 SHALL 清空运营别名为 `NULL`。

#### Scenario: 平台昵称刷新不覆盖人工别名
- **WHEN** 账号已有运营别名，随后平台身份链上报新的已验证昵称
- **THEN** Cloud 更新平台昵称但保留运营别名，账号主键和任务归因不变

#### Scenario: 空内容清空人工别名
- **WHEN** 已有运营别名的账号提交空白人工内容
- **THEN** Cloud 将运营别名清为 `NULL`，保留平台昵称、运营标签和账号 ID

### Requirement: 账号显示名解析在单一 Cloud 模块收口

Cloud SHALL 通过同一个纯解析模块把账号记录解析为显示名与来源，优先级固定为运营别名 → 平台真实昵称 → 运营标签 → 账号 ID。来源 SHALL 明确标记为 `operator_alias`、`platform_nickname`、`label` 或 `account_id`。Console DTO、飞书取名和 Cloud 运行时展示 MUST 复用该模块或其账号目录封装，MUST NOT 各自重新实现优先级。

#### Scenario: 人工别名覆盖其它可读名称
- **WHEN** 同一账号同时存在运营别名、平台昵称和运营标签
- **THEN** 统一解析器返回运营别名且来源为 `operator_alias`

#### Scenario: 清除后恢复系统名称
- **WHEN** 账号运营别名被清空且平台昵称存在
- **THEN** 统一解析器立即返回平台昵称且来源为 `platform_nickname`

#### Scenario: 所有可读字段缺失
- **WHEN** 账号没有运营别名、平台昵称或非空运营标签
- **THEN** 统一解析器返回稳定账号 ID 并标记来源为 `account_id`，由人类通知层显示明确的未获取昵称提示

### Requirement: 显示名不得参与机器身份和授权

运营别名、平台昵称和解析后的显示名 SHALL 仅用于展示与人工输入匹配；路由、客户归属、风控、配额、发布、互动、回调和任务归因 MUST 继续使用稳定 `accountId/envKey/requestId`。显示名相同或发生变化 MUST NOT 创建、合并或改写账号身份。

#### Scenario: 两个账号使用相同运营别名
- **WHEN** 两个不同账号解析出相同显示名
- **THEN** 系统保留两个独立账号，机器处理仍按各自账号 ID，人工选号在歧义时拒绝猜测
