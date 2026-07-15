## ADDED Requirements

### Requirement: Edge 委托入口必须绑定当前选中环境并二次确认

Edge 客户端 SHALL 在当前选中环境的主区域提供 Phase 1 快捷委托入口。创建任务时 MUST 使用该环境真实 account id、可读名称与平台；没有当前环境或身份未确立时入口 MUST 禁用。第一次操作只创建确认草稿，用户在同一环境卡片确认后才可排队。

#### Scenario: 切换环境后委托绑定随之切换
- **WHEN** 用户从小红书环境 A 切换到 Facebook 环境 B 后打开委托入口
- **THEN** 确认卡绑定环境 B 的账号与 Facebook 平台
- **AND** MUST NOT 沿用环境 A 的账号或目标约束

### Requirement: Edge 任务卡必须投影真实委托进度且不冒充浏览进度

客户端 SHALL 独立展示委托任务的状态、成功/目标、尝试、跳过、失败原因和可用控制；MUST NOT 复用探索进度百分比或静态成功话术冒充任务结果。源码已实现但安装包未发布时，对外状态 MUST 明确“安装端尚未发布”。

#### Scenario: 三比五部分完成显示真实计数
- **WHEN** 委托任务以 3/5 `partially_completed` 收敛
- **THEN** Edge 卡片显示 3 个验证成功、实际尝试与跳过/失败原因
- **AND** MUST NOT 显示“任务已全部完成”

