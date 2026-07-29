## ADDED Requirements

### Requirement: 管理后台可配置 Facebook 环境慢启动

管理后台环境资产页 SHALL 展示每个环境的慢启动配置真态，并仅为 `lifecycle.state=active` 的 Facebook 环境提供开启/关闭开关。开关 SHALL 写环境级配置并随 `envKey` 保留，MUST NOT 写入账号字段、选择或提交 `accountId`，也 MUST NOT 把未挂载账号当成不能预配置的理由。

页面 MUST 区分配置已开启、请求提交中、Cloud 全局停用和实际生效；请求在途不得冒充写入成功，`AIDCP_SLOW_START_DISABLED=true` 时不得把已勾选描述为正在限制账号。非 Facebook、平台未知与非 active 环境 MUST 显示不可操作状态，MUST NOT 提供可提交的开关。

#### Scenario: 管理员为未挂载 Facebook 环境开启慢启动

- **WHEN** 一个 active Facebook 环境尚未挂载账号，管理员在环境页开启慢启动
- **THEN** 页面提交该环境的 `envKey` 与 `enabled=true`，写入成功后显示环境配置已开启
- **AND** 页面 MUST NOT 要求或构造 `accountId`，也 MUST NOT 声称已有账号配额被收紧

#### Scenario: 提交中与失败回滚

- **WHEN** 管理员拨动开关而 Cloud 写请求尚未完成
- **THEN** 页面明确显示正在开启或关闭并禁止重复提交，MUST NOT 先把目标值标成权威成功
- **AND** 请求失败时恢复原权威配置并显示失败，不得保留伪造的目标状态

#### Scenario: 全局停用时保留配置但不冒充生效

- **WHEN** 环境配置为开启且 Cloud 投影 `globallyDisabled=true`
- **THEN** 页面保持展示该环境已保存的开启配置，同时明确标注全局停用、当前不生效

#### Scenario: 不支持的平台没有写入口

- **WHEN** 环境平台为小红书、视频号、未知，或生命周期不是 active
- **THEN** 页面显示不适用或不可操作，且不渲染可提交的慢启动开关
