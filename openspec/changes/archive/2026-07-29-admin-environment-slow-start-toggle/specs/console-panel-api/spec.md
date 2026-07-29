## ADDED Requirements

### Requirement: 内部 Panel 提供环境慢启动配置投影与写接口

内部 Panel 环境资产响应 SHALL additive 返回直接来自 `client_environments.slow_start_since` 的环境慢启动配置，以及当前 Cloud 的全局停用真态。内部 Panel SHALL 在有效 Panel JWT 之后提供按 `envKey` 写入 `{ enabled: boolean }` 的慢启动接口；请求 MUST NOT 接受 `accountId`、起点时间、平台或其它选择器。

接口开启慢启动时 SHALL 仅在原值为 NULL 时写入服务器当前时刻所属上海自然日的 00:00，重复开启 MUST 保留原起点；关闭时 SHALL 清空环境起点。写入成功后 MUST 在回包前推进并刷新 `client_environment_slow_start` 镜像，使已缓存 RiskController 的下一次同步读可见新值。环境不存在、非 active 或非 Facebook 时 MUST 具名拒绝，MUST NOT 部分写入、重置起点或改变账号风控状态。

#### Scenario: 内部管理员首次开启环境慢启动

- **WHEN** 有效 Panel JWT 对 active Facebook 环境提交严格的 `{ "enabled": true }`
- **THEN** Cloud 写入上海当日 00:00 起点、刷新环境慢启动镜像并返回写后配置
- **AND** 未挂载账号不阻止该环境配置保存

#### Scenario: 重复开启保持原起点

- **WHEN** 已开启第 4 天的 Facebook 环境再次收到 `enabled=true`
- **THEN** 接口幂等返回开启状态，`slow_start_since` 保持原值，MUST NOT 重置为第 1 天

#### Scenario: 关闭环境慢启动

- **WHEN** 有效 Panel JWT 对已开启的 active Facebook 环境提交 `{ "enabled": false }`
- **THEN** Cloud 清空该环境的 `slow_start_since`、刷新镜像并返回关闭真态
- **AND** 账号风险状态、档位和旧账号慢启动列逐位不变

#### Scenario: 非法目标和非法请求 fail closed

- **WHEN** 环境不存在、生命周期非 active、平台不是 Facebook，或请求体包含非布尔值或额外选择器
- **THEN** 接口返回可区分的 4xx 拒绝且不修改任何环境慢启动字段

#### Scenario: 客户令牌无法调用内部写接口

- **WHEN** 持客户令牌请求内部 Panel 环境慢启动写接口
- **THEN** Panel JWT 校验拒绝请求，且不返回跨客户环境配置或写入结果

#### Scenario: 全局停用真态随资产投影返回

- **WHEN** `AIDCP_SLOW_START_DISABLED=true` 且一个环境的慢启动配置已开启
- **THEN** 资产响应同时返回该环境配置为开启与 `globallyDisabled=true`
- **AND** 接口 MUST NOT 把全局停用改写成环境配置关闭
