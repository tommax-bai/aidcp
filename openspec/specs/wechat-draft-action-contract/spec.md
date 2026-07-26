# wechat-draft-action-contract Specification

## Purpose
TBD - created by archiving change wechat-draft-action-contract-alignment. Update Purpose after archive.
## Requirements
### Requirement: 客户草稿路由 MUST 遵循公开契约

Cloud SHALL 通过 `PUT /environments/:envKey/replies/:jobId/draft` 接收客户草稿保存请求，并 SHALL 从该路由定位目标互动。未带末尾 `/draft` 的内部短路由 MUST NOT 作为等价客户 API 暴露。现有客户环境作用域、资源归属和防枚举行为 MUST 保持不变。

#### Scenario: 客户保存所属环境的草稿

- **GIVEN** 当前客户拥有目标环境且目标互动属于该环境
- **WHEN** 客户以有效版本调用 `PUT /environments/:envKey/replies/:jobId/draft`
- **THEN** Cloud 将请求交给草稿编辑工作流
- **AND** MUST NOT 因路由形态返回资源不存在

#### Scenario: 未公开的短路由不被接受

- **WHEN** 客户调用 `PUT /environments/:envKey/replies/:jobId`
- **THEN** Cloud 返回资源不存在
- **AND** MUST NOT 建立第二套草稿保存契约

### Requirement: 纯 Cloud 草稿动作 MUST 与平台发送能力解耦

当目标互动属于当前客户环境，且渠道授权为 `active`、已确认平台身份、配置与状态机条件有效时，Cloud SHALL 允许生成、编辑和批准草稿，即使对应评论回复或私信发送能力尚未生效。渠道授权非活动、身份缺失、配置无效、资源不属于当前环境或 CAS 版本不匹配时，既有拒绝行为 MUST 保持不变。

#### Scenario: 发送能力未生效时仍可维护草稿

- **GIVEN** 视频号授权为 `active` 且已确认身份
- **AND** 目标互动属于当前客户环境
- **AND** 对应平台回复或发送能力为 false
- **WHEN** 客户生成、编辑或批准该互动的草稿
- **THEN** Cloud 完成相应的纯 Cloud 草稿状态变更
- **AND** MUST NOT 仅因平台发送能力为 false 返回权限拒绝

#### Scenario: 授权失效仍阻止草稿动作

- **GIVEN** 视频号授权不是 `active` 或已确认身份缺失
- **WHEN** 客户尝试生成、编辑或批准草稿
- **THEN** Cloud 按既有协议返回需要重新授权

### Requirement: 真实发送 MUST 继续 fail-closed

平台发送能力未生效时，Cloud MUST NOT 自动入队、派发或执行评论回复和私信发送。真实发送 SHALL 继续同时满足平台写能力、运行控制、熔断、暂停、风险、幂等及其它既有门禁。草稿生成、编辑或批准成功 MUST NOT 被解释为发送能力已生效。

#### Scenario: 草稿可编辑但不可发送

- **GIVEN** 活动授权允许客户维护草稿
- **AND** 对应平台回复或发送能力为 false
- **WHEN** 草稿被生成、编辑或批准
- **THEN** Cloud 可以保存草稿生命周期状态
- **BUT** MUST NOT 自动入队或调用平台发送接口

