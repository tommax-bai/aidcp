## MODIFIED Requirements

### Requirement: 客户端规则模式读写保持 Cloud 环境作用域权威

客户规则模式接口 SHALL 只接受当前客户 `envKey`，由 Cloud 复核环境归属并校验该环境的权威平台后，直接读取或写入**该环境**的规则模式配置。`accountId` MUST NOT 由客户端提交，也 MUST NOT 作为写入目标选择器。写请求 MUST 只接受布尔 `enabled`，客户端 MUST NOT 提交或选择 `accountId`、规则定义、运行进度、HTTP 目标或授权模式。该路由 MUST NOT 依赖环境↔账号绑定、账号是否存在、边缘活会话或环境内核是否停止。

成功回包 SHALL 返回写后环境配置真态。有唯一有效当前账号绑定时，回包 MAY 额外标注该配置当前是否有执行对象；没有有效绑定时，回包 SHALL 明确标注绑定未知且不编造执行态或进度。云端环境写入成功即为配置已保存，回包 MUST NOT 引入「已保存 / 待下发边缘」二态。

#### Scenario: 已绑定 Facebook 环境读取配置

- **WHEN** 已登录客户读取自己一个已唯一绑定账号的 Facebook 环境规则模式
- **THEN** Cloud 返回同一 `envKey` 与该环境现有规则模式配置的最小客户投影
- **AND** 响应不泄露 `accountId` 或内部更新者

#### Scenario: 已绑定 Facebook 环境写入配置

- **WHEN** 已登录客户为自己一个已唯一绑定账号的 Facebook 环境提交唯一字段 `{ enabled: boolean }`
- **THEN** Cloud 写入该环境的规则模式配置并返回写后权威投影
- **AND** Edge 不创建任何本地规则配置或运行授权

#### Scenario: 未绑定账号的环境仍可预设

- **WHEN** 已登录客户为自己一个尚未绑定账号的 Facebook 环境提交 `{ enabled: true }`
- **THEN** Cloud 写入该环境配置并返回已配置真态
- **AND** 回包标注当前没有执行对象，MUST NOT 伪造绑定、进度或生效态

#### Scenario: 停止的环境仍可更改 Cloud 配置

- **WHEN** 客户拥有的 Facebook 环境内核已停止
- **THEN** 规则模式读写仍可通过 customer-auth 完成
- **AND** 系统不要求启动浏览器、Edge 会话或存在账号绑定来证明这次 Cloud 配置写入

#### Scenario: 非法范围和平台失败关闭

- **WHEN** 环境不归属当前客户、环境平台不是 Facebook、环境注册表不可读，或请求包含 `enabled` 之外的字段
- **THEN** Cloud 返回可区分的拒绝或不可用结果
- **AND** 不修改任何环境规则配置

#### Scenario: 环境换绑不需要客户重新设置

- **WHEN** 客户已为某 Facebook 环境开启规则模式，该环境随后换绑到另一个账号
- **THEN** 客户端读到的该环境配置逐位不变
- **AND** 客户 MUST NOT 被要求为新账号重新开启一次
