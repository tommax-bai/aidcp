## MODIFIED Requirements

### Requirement: 客户端开关不得改变规则模式仲裁

客户端规则模式开关 SHALL 只修改既有 Cloud 配置的 `enabled` 字段。Cloud 仍 MUST 在会话装配时应用既有平台、绑定人设、活跃时段、慢启动、风险和单飞仲裁；慢启动为 active 时规则模式 MUST 保持暂停且不累计进度。Edge MUST NOT 根据本地 checkbox 自行选择模式、累计任何级别的规则节奏计数，或触发点赞、加群和评论。两级节奏的阈值与周期一律由 Cloud 的权威规则定义决定，Edge MUST NOT 内置或推断任何节奏数字。

#### Scenario: 慢启动继续优先

- **WHEN** 规则模式配置已开启且同一环境慢启动为 active
- **THEN** Cloud 继续选择慢启动而不是规则模式
- **AND** 客户端开关不绕过或覆盖该仲裁

#### Scenario: 客户端不内置节奏数字

- **WHEN** Cloud 的权威规则定义发生节奏变更
- **THEN** 客户端无需发版即可继续正确工作
- **AND** 客户端 MUST NOT 依据本地写死的浏览条数或点赞轮次自行触发任何动作
