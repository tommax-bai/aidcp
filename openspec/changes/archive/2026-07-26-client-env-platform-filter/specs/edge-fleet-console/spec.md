## ADDED Requirements

### Requirement: 左侧环境栏按平台筛选并约束批量启动范围

桌面主界面左侧环境栏 SHALL 提供“全部 / 小红书 / Facebook / 视频号”平台分类筛选，客户端每次启动时 MUST 默认选择“全部”。筛选 SHALL 使用环境花名册的平台字段及既有平台归一化规则；选择具体平台后，环境行、状态分组和汇总计数 SHALL 只呈现匹配环境，同时保持匹配环境原有的紧迫度排序与状态分组语义。

“全部启动”MUST 只请求启动当前筛选结果中的环境，MUST NOT 因按钮沿用“全部启动”文案而启动被筛选隐藏的其他平台环境；选择“全部”时 SHALL 保持启动全部花名册环境的既有行为。主进程 MUST 将 renderer 提交的环境 ID 与当前现存花名册求交集，MUST NOT 启动请求范围外、已移出或不存在的环境。筛选结果为空时界面 SHALL 呈现该分类暂无环境的空态并禁用“全部启动”，MUST NOT 发出无目标的批量启动请求。

#### Scenario: 默认展示并启动全部平台环境

- **WHEN** 客户端打开且花名册同时包含小红书、Facebook 和视频号环境
- **THEN** 平台筛选 MUST 默认选择“全部”，左栏展示全部环境
- **AND** 用户点击“全部启动”时请求范围 SHALL 包含全部花名册环境

#### Scenario: 选择 Facebook 后只展示并启动 Facebook 环境

- **WHEN** 用户选择“Facebook”分类
- **THEN** 左栏环境行、状态分组和汇总计数 SHALL 只包含归一化平台为 `facebook` 的环境
- **AND** 用户点击“全部启动”时请求范围 MUST 只包含这些 Facebook 环境，MUST NOT 包含小红书或视频号环境

#### Scenario: force 确认保持原筛选范围

- **WHEN** 某一平台分类下的批量启动触发资源确认，用户随后选择“仍要启动”
- **THEN** force 请求 MUST 复用首次请求的平台环境 ID 范围，MUST NOT 扩大到完整花名册

#### Scenario: 所选分类无环境时不发起批量启动

- **WHEN** 用户选择一个当前没有任何环境的平台分类
- **THEN** 左栏 SHALL 显示该分类暂无环境且“全部启动”不可用
- **AND** 客户端 MUST NOT 发出 `fleet:startAll` 请求

#### Scenario: 主进程拒绝越界环境 ID

- **WHEN** renderer 提交的批量启动范围包含不存在、已移出或范围外的环境 ID
- **THEN** 主进程 SHALL 只启动当前花名册中与请求 ID 相交的环境，MUST NOT 启动其他环境
