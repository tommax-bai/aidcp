## MODIFIED Requirements

### Requirement: 搜索默认配额与可选慢启动可配置且 never-brick

代码默认 daily 搜索配额 SHALL 为 conservative=5、normal=10、aggressive=20，独立 minute=1、hour=4，并作为 `quota_config` 缺行或非法时的 never-brick 回落。可选慢启动开启时 SHALL 同时夹逼搜索：XHS 继续使用编译期 D1-2=2、D3-4=3、D5-7=5；Facebook SHALL 使用环境开启时 pin 的已发布七日数字策略中对应 day 的 `search.dailyCap`，并按既有公式派生 minute/hour 天花板。未开启慢启动时 MUST NOT 因账号年龄自动应用该夹逼。

Facebook 环境存在慢启动起点但 policy pin 或其 search 值缺失、陈旧、非法或 schema 不兼容时，Cloud MUST 停止新的 search 和其它平台动作并返回具名 unavailable；MUST NOT 回落此处旧的 Facebook D1-D7 常量、全局当前 revision 或其它平台曲线。`quota_config` 的 never-brick 回落只适用于安全基准配额，MUST NOT 被借用来掩盖慢启动策略权威不可读。

#### Scenario: 配额配置缺 search 行时回落代码默认

- **WHEN** 某档位的 `quota_config` 缺少 `search` 或字段非法，但慢启动策略权威可用或未开启
- **THEN** `effectiveQuotas()` 对安全基准 search 回落该档位代码默认，不抛错、不放开无限搜索

#### Scenario: Facebook search 使用 active revision

- **WHEN** Facebook 环境慢启动 active revision 的当日 `search.dailyCap=4`
- **THEN** Cloud 使用 4 作为当日 search 慢启动天花板并继续与更严格的安全基准逐窗口取小
- **AND** 新全局 revision 的 search 数字不得在该生命周期中途替换它

#### Scenario: Facebook 策略不可读时不冒充 never-brick 默认

- **WHEN** Facebook 环境慢启动起点存在但 active revision 的 search 策略不可读
- **THEN** Cloud 以具名 unavailable 停止新的平台动作
- **AND** MUST NOT 使用旧 D1-D7 数字或安全基准 search 默认冒充慢启动权威

#### Scenario: restricted 账号只保留被动浏览

- **WHEN** 账号处于将主动行为清零的 restricted 或 frozen 状态
- **THEN** search 生效配额为 0，而 view 保持既有只读浏览语义
