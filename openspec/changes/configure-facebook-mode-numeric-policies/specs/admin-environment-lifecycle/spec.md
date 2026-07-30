## MODIFIED Requirements

### Requirement: 管理后台可配置 Facebook 环境慢启动

管理后台环境资产页 SHALL 展示每个环境的慢启动配置真态，并仅为 `lifecycle.state=active` 的 Facebook 环境提供开启/关闭开关。开关 SHALL 只以目标 `envKey` 和 `{ enabled: boolean }` 调用 Cloud 的共享环境慢启动原子服务；MUST NOT 写入账号字段、选择或提交 `accountId`、policy revision、每日数字、动作或 Prompt，也 MUST NOT 把未挂载账号当成不能预配置的理由。Cloud MUST 在服务端复核环境生命周期与权威平台；伪造请求指向非 Facebook、平台未知或非 active 环境时 MUST 整块拒绝且不产生部分写入。

首次开启 SHALL 在同一事务写入服务端当前时刻所属上海自然日的起点与当时全局 current published slow-start revision 的 active pin。全局 current revision 缺失、未发布、不可读、结构无效或 schema 不兼容时，整次开启 MUST 失败且起点与 pin 均不改变；current 为 non-legacy revision 时，还 MUST 要求该环境存在 30 天内服务端观察到的 positive `facebook_mode_policy_projection_v1`，missing/unsupported/stale 时整次失败。对已开启环境重复提交 `{ enabled: true }` SHALL 幂等返回原起点与原 active pin，MUST NOT 重置 day、借重复开启换版或重新要求 capability。关闭 SHALL 在同一事务清空起点与 active pin；共享服务任一步失败 MUST 回滚整次写入。

页面 MUST 区分配置已开启、请求提交中、Cloud 全局停用和实际生效；请求在途不得冒充写入成功，只有包含同一环境完整写后真态的成功回包才能收敛开关、起点与 active/next revision。失败时 SHALL 恢复最近一次权威真态并保留可读原因。`AIDCP_SLOW_START_DISABLED=true` 时不得把已勾选描述为正在限制账号，但全局停用 MUST NOT 删除或改写环境已保存的起点与 active pin。非 Facebook、平台未知与非 active 环境 MUST 显示不可操作状态，MUST NOT 提供可提交的开关。

#### Scenario: 管理员为未挂载 Facebook 环境开启慢启动

- **WHEN** 一个 active Facebook 环境尚未挂载账号，管理员在环境页开启慢启动
- **THEN** 页面提交该环境的 `envKey` 与唯一字段 `{ enabled: true }`，Cloud 原子写入上海当日起点与当时全局 current revision 的 active pin
- **AND** 写后页面显示环境配置已开启及完整 active revision，MUST NOT 要求或构造 `accountId`，也 MUST NOT 声称已有账号配额被收紧

#### Scenario: 重复开启保持既有生命周期

- **WHEN** 环境已按 revision 4 开启后全局 current revision 变为 5，管理员再次提交 `{ enabled: true }`
- **THEN** Cloud 幂等返回原起点与 revision 4 active pin
- **AND** 页面 MUST NOT 把 day 重置为第一天或把该生命周期显示为已采用 revision 5

#### Scenario: 提交中与失败回滚

- **WHEN** 管理员拨动开关而 Cloud 写请求尚未完成
- **THEN** 页面明确显示正在开启或关闭并禁止重复提交，MUST NOT 先把目标值、起点或 revision 标成权威成功
- **AND** 请求失败时恢复原权威配置与 active/next revision 并显示失败，不得保留伪造的目标状态

#### Scenario: 全局当前策略不可用时首次开启整块失败

- **WHEN** 管理员首次开启环境慢启动，但全局 current slow-start revision 缺失、未发布、不可读、结构无效或 schema 不兼容
- **THEN** Cloud 返回具名不可用结果，环境起点与 active pin 均保持原值
- **AND** 页面恢复原开关真态，MUST NOT 用编译期七日表或其它 revision 冒充开启成功

#### Scenario: 后台不能替旧客户端绕过 non-legacy 能力门禁

- **WHEN** 管理员为一个没有 30 天内 positive `facebook_mode_policy_projection_v1` 观察的环境首次开启 non-legacy 慢启动策略
- **THEN** Cloud 返回具名 capability missing/unsupported/stale，起点与 active pin 均不写入
- **AND** 页面显示具体 blocker，不提供口头确认或隐藏 override

#### Scenario: 关闭慢启动原子清除生命周期

- **WHEN** 管理员为已开启环境提交 `{ enabled: false }`
- **THEN** Cloud 在同一事务清空该环境的上海日起点与 active pin，并返回完整写后关闭真态
- **AND** MUST NOT 修改全局 current revision、账号字段、风险状态或历史 immutable revision

#### Scenario: 全局停用时保留配置但不冒充生效

- **WHEN** 环境配置为开启且 Cloud 投影 `globallyDisabled=true`
- **THEN** 页面保持展示该环境已保存的开启配置、起点与 active pin，同时明确标注全局停用、当前不生效

#### Scenario: 不支持的平台没有写入口

- **WHEN** 环境平台为小红书、视频号、未知，或生命周期不是 active
- **THEN** 页面显示不适用或不可操作，且不渲染可提交的慢启动开关
- **AND** 绕过页面直接提交的 admin PUT 也被 Cloud 整块拒绝

## ADDED Requirements

### Requirement: 环境页只读呈现模式数字策略版本

管理后台环境资产页 SHALL 在既有规则模式与慢启动开关附近只读呈现 Cloud 权威的数字策略版本。规则模式 SHALL 区分 API owner current revision、execution-target applied current/cursor/传播等待、当前绑定账号的 adopted revision 与“下一轮采用”状态；慢启动 SHALL 区分全局 current revision、环境 active pin 与“下次开启采用”状态。环境页 MUST NOT 提供数字、版本、动作、Prompt 或客户覆盖编辑入口。

版本投影 SHALL 与环境开关、账号 binding 和运行态分别呈现。未绑定账号时可以显示规则模式 owner current 与目标已 applied current；只有 applied current 可描述为目标下次 admission 的候选，MUST NOT 编造 adopted revision、进度或动作状态。慢启动已开启但未绑定账号时 SHALL 显示环境 active pin、since/day 与 `binding_unknown`，MUST NOT 冒充当前账号已被 clamp。缺失、陈旧、不兼容或不可读版本 MUST 显示具名 unknown/unavailable，MUST NOT 回填 `5/2` 或本地七日表。

#### Scenario: 规则传播与账号采用分别可见

- **WHEN** owner current 已更新、target applied current 仍旧，或环境当前账号有按更旧 revision 收集中的 progress/batch
- **THEN** 环境页同时显示 owner current、target applied current/cursor/lag 与 adopted revision，并分别标注传播等待或下一轮采用
- **AND** 不把当前进度按新阈值重新换算

#### Scenario: 在途慢启动保留 active pin

- **WHEN** 全局慢启动 current revision 已更新，而环境正按旧 revision 处于第 4 天
- **THEN** 环境页显示旧 active revision 为当前七日策略、新 current revision 为下次开启采用
- **AND** 不提供立即换版按钮或数字编辑器

#### Scenario: 未绑定环境不编造账号运行态

- **WHEN** Facebook 环境没有唯一有效当前账号绑定
- **THEN** 页面仍显示环境开关以及可证的 current/active revision
- **AND** adopted revision、账号 clamp 和规则进度显示未绑定/未知

#### Scenario: 策略不可读不伪装成默认

- **WHEN** Cloud 无法解析某环境关联的 current、active 或 adopted revision
- **THEN** 页面显示具名 unavailable 与 freshness
- **AND** MUST NOT 展示编译期阈值、周期或七日额度
