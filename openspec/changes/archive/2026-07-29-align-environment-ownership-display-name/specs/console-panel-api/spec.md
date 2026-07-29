## MODIFIED Requirements

### Requirement: Panel 账号 DTO 暴露统一显示名和来源

Panel 账号 API SHALL 为每个账号返回 Cloud 统一解析器产生的 `displayName` 与 `displayNameSource`，同时保留 `accountId`、平台昵称、运营标签和运营别名的原始字段供诊断。内部环境注册表 API SHALL 为已绑定环境返回同一解析结果产生的 `account.displayName`。Console 所有账号名展示、只持有 `accountId` 的 join，以及“环境归属”中按 `envKey` 关联到绑定账号的昵称展示 SHALL 使用服务端 `displayName`，MUST NOT 在页面或共享前端工具中重写别名优先级。没有绑定账号投影的环境 MAY 回落到环境系统名、既有环境备注和稳定 `envKey`，但 MUST NOT 把该回落用于账号身份或归属判断。

#### Scenario: 管理后台展示客户端人工别名
- **WHEN** 账号在 Cloud 已有运营别名
- **THEN** 账号列表、人设、内容、用量、联系方式及其它账号选择或展示位置均显示该别名并保留同一 `displayNameSource`，环境归属也显示同一别名

#### Scenario: 环境归属按稳定环境键关联显示名
- **WHEN** 已分配 scope 行只含 `envKey`，且全局环境注册表中该 `envKey` 已绑定带统一 `displayName` 的账号
- **THEN** Console 在环境归属的已分配与待分配位置都展示该 `displayName`，保存和归属判断仍使用原 `envKey`

#### Scenario: 未挂载环境回落环境自身名称
- **WHEN** 环境没有绑定账号投影或在滚动发布窗口暂未收到账号显示字段
- **THEN** Console 回落展示环境系统名、既有环境备注或稳定 `envKey`，且不在前端推断账号别名来源

#### Scenario: 人工别名清除后后台回落
- **WHEN** 运营别名被清空且平台昵称存在
- **THEN** 下一次 Panel 读取返回平台昵称和来源 `platform_nickname`，Console 不保留旧人工名

#### Scenario: 旧服务端兼容边界
- **WHEN** Console 在发布切换窗口收到尚无 `displayName` 的旧账号 DTO
- **THEN** 前端只做兼容性账号 ID 回落并明确不可判断来源，MUST NOT 重新复制完整昵称优先级
