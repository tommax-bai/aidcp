## ADDED Requirements

### Requirement: 客户可为自有已绑定环境设置或清除账号运营别名

客户鉴权 API SHALL 提供仅接受环境键和运营别名的窄写接口。服务端 MUST 验证 token、该环境当前归属该客户、环境绑定无冲突且已解析到真实账号，才可更新该账号运营别名。非空值 trim 后写入；空值清除。成功回包 SHALL 返回 Cloud 解析后的显示名与来源。

#### Scenario: 自有已绑定环境设置别名
- **WHEN** 已登录客户为自己归属且已绑定账号的环境提交非空人工昵称
- **THEN** Cloud 更新绑定账号的运营别名并返回来源 `operator_alias`

#### Scenario: 自有已绑定环境清除别名
- **WHEN** 已登录客户为自己归属且已绑定账号的环境提交空内容
- **THEN** Cloud 清除运营别名并返回按平台昵称、运营标签或账号 ID 回落的显示名与来源

#### Scenario: 越权环境拒绝
- **WHEN** 客户尝试修改不归属自己的环境
- **THEN** API 以 403 拒绝且不修改任何账号记录

#### Scenario: 环境尚未绑定账号
- **WHEN** 客户拥有该环境但 Cloud 尚无可信 `envKey → accountId` 绑定
- **THEN** API 返回可判断的 `account_unbound` 冲突，不猜测账号、不报告成功
