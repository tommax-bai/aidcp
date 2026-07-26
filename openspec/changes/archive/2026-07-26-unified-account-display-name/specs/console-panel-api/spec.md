## ADDED Requirements

### Requirement: Panel 账号 DTO 暴露统一显示名和来源

Panel 账号 API SHALL 为每个账号返回 Cloud 统一解析器产生的 `displayName` 与 `displayNameSource`，同时保留 `accountId`、平台昵称、运营标签和运营别名的原始字段供诊断。Console 所有账号名展示和只持有 `accountId` 的 join SHALL 使用 `displayName`，MUST NOT 在页面或共享前端工具中重写别名优先级。

#### Scenario: 管理后台展示客户端人工别名
- **WHEN** 账号在 Cloud 已有运营别名
- **THEN** 账号列表、人设、内容、用量、联系方式及其它账号选择/展示位置均显示该别名，并保留同一 `displayNameSource`

#### Scenario: 人工别名清除后后台回落
- **WHEN** 运营别名被清空且平台昵称存在
- **THEN** 下一次 Panel 读取返回平台昵称和来源 `platform_nickname`，Console 不保留旧人工名

#### Scenario: 旧服务端兼容边界
- **WHEN** Console 在发布切换窗口收到尚无 `displayName` 的旧 DTO
- **THEN** 前端只做兼容性账号 ID 回落并明确不可判断来源，MUST NOT 重新复制完整昵称优先级
