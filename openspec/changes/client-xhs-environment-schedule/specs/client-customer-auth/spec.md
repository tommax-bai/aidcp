## ADDED Requirements

### Requirement: customer-auth SHALL 提供当前环境的小红书生效排期只读投影

customer-auth SHALL 提供 env-scoped `GET /environments/:envKey/schedule`。每次请求 MUST 在客户验签、撤销与 enabled 检查后重新解析路径环境的 ownership、持久账号绑定和账号权威平台；仅小红书可返回。Cloud SHALL 从账号生效活跃/内容周历生成客户可读七日区间、启用动作摘要、当前/下一窗口、实际时区与 `meta.asOf`。

响应 MUST 使用显式客户 DTO，且 MUST NOT 返回 `accountId`、168 位原始掩码、global/override 来源、`updatedBy`、内部调度键或后台 catalog 原对象。内容区间 MUST 取生效内容掩码与生效活跃掩码交集；活跃缺失按运行时 fail-open 语义投影全天，内容缺失或非法按 fail-closed 语义投影为空。

#### Scenario: 离线读取小红书排期
- **WHEN** 已登录客户读取其授权且已绑定小红书账号的环境排期，而浏览器、Edge 自动化或 WebSocket 均未运行
- **THEN** customer-auth 仍返回该账号的生效七日排期，MUST NOT 要求先启动浏览器

#### Scenario: 非小红书平台拒绝
- **WHEN** 授权环境绑定账号的权威平台不是小红书或平台未知
- **THEN** customer-auth 返回 `409 unsupported_platform`，MUST NOT 返回其它平台的排期投影

#### Scenario: 环境绑定不可确认
- **WHEN** 环境不归当前客户、绑定未知、绑定冲突或绑定存储不可用
- **THEN** customer-auth 复用现有对应 403/409/503 失败语义，MUST NOT 返回空成功或泄露账号身份

#### Scenario: 内容掩码非法
- **WHEN** 账号生效内容掩码缺失或非法
- **THEN** 返回的每日内容区间为空，账号活动区间仍按其独立生效语义投影

### Requirement: 客户排期接口 SHALL 保持只读

本变更 SHALL NOT 新增 customer-auth 排期 PUT、PATCH、POST 或 DELETE 路由。客户请求 MUST NOT 能修改账号周历、总开关、动作模式、审批模式或日上限。

#### Scenario: 客户尝试写排期
- **WHEN** 客户对环境排期路径提交非 GET 请求
- **THEN** 请求不得修改任何排期配置，且 MUST NOT 通过透传后台写端点绕过此限制
