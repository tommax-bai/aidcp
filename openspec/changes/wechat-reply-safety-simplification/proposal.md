## Why

视频号回复目前把通用 `RiskController` 三窗口配额、账号回复三窗口限速、新登录冷却和多层运行开关同时叠在每次发送上，导致私信默认配额为零、人工审核发送仍被自动化冷却阻断，以及“配置已发布但仍无法发送”的不可理解状态。后台为保证诚实发送保留的状态机和硬门禁又被直接暴露为多次保存、批准和发送操作，使普通管理员重复表达同一个意图。

## What Changes

- 视频号评论/私信回复只使用 interaction 域的账号分钟、小时、每日和会话冷却作为数量准入；`RiskController` 继续单写风险状态、阻断 `restricted`/`frozen` 等风险态并记录平台已确认动作，但其通用 `comment`/`dm_reply` 数量配额不再成为视频号发送的第二套数量闸。
- 新建回复配置使用可实际发送的保守限速默认值，不再创建“三窗口全为零、可以发布却必然拒绝人工发送”的草稿。
- 新登录冷却只约束无人值守自动发送；已经人工审核的发送仍须满足身份、capability、运行控制、熔断、专用限速、CAS、幂等和结果核验，但不再额外等待登录冷却。
- 纯 Cloud 的草稿生成、编辑和批准以客户环境/资源归属、配置和状态机为准，不再要求平台登录态当前为 active；真实发送前仍重新验证登录、身份和写 capability。
- Electron 客户工作区将“批准回复”与“发送回复”收敛为一次“审核并发送”主动作；Cloud 内部仍分别记录 `approved` 和 `queued`，失败时不得把批准冒充为已发送。
- Console 将六个限速数字收进“保守 / 标准 / 自定义”预设与高级设置，普通路径只需选择安全档位；运行控制、策略发布和不可关闭硬门禁继续保持真实边界。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `wechat-channels-interaction`: 调整草稿准入、人工/自动发送冷却、视频号回复数量门禁和组合审核发送行为。
- `interaction-risk-gating`: 将视频号入站回复的风险状态控制与数量限额解耦，保留已确认动作记账。
- `edge-companion-ui`: 客户端以一次“审核并发送”表达人工发送意图，同时保持批准、排队和平台确认状态诚实分离。
- `console-panel-api`: 新配置提供可用的保守限速默认值，并以预设优先、详细数字高级化的方式呈现账号限速。

## Impact

- `aidcp-cloud`: reply workflow、send orchestrator、默认 policy、配置校验与 interaction focused/acceptance tests。
- `aidcp-edge`: Electron interaction workspace 动作编排与 UI 回归测试；不修改 WS v2 协议、不构建安装包。
- `aidcp-console`: 视频号回复安全设置、预设映射和组件测试。
- 控制仓：OpenSpec delta、任务证据和严格校验。
- 不修改数据库 schema，不放宽账号归属、身份/capability、CAS、幂等、单飞、ambiguous 回查或平台确认成功边界；不在本 change 重做账号级熔断数据模型。
