## ADDED Requirements

### Requirement: 今日进展折叠控件直接表达展开状态

今日进展的窗口详情 disclosure 控件 SHALL 同时显示动作文字与方向箭头：收起态显示“展开”及向下箭头，展开态显示“收起”及向上箭头。该控件 MUST 使用次要 ghost 样式，视觉权重 MUST 低于启动、暂停、恢复或关闭等生命周期主操作，并 MUST 同步 `aria-expanded` 与可访问名称。

#### Scenario: 今日节奏详情默认收起

- **WHEN** 客户端已收到可展开的配额窗口且详情尚未展开
- **THEN** disclosure 控件显示“展开”及向下箭头
- **AND** 控件的 `aria-expanded` 为 `false`，可访问名称明确表达展开今日节奏

#### Scenario: 今日节奏详情已经展开

- **WHEN** 用户通过今日进展卡或 disclosure 控件展开窗口详情
- **THEN** disclosure 控件显示“收起”及向上箭头
- **AND** 控件的 `aria-expanded` 为 `true`，可访问名称明确表达收起今日节奏
