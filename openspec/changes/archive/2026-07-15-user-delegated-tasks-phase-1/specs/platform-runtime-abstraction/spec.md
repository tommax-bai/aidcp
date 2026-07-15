## ADDED Requirements

### Requirement: 平台注册表必须声明委托动作支持级别与限制

cloud 与 edge 平台注册表 SHALL 为 Phase 1 委托动作声明 `supported`、`beta` 或 `unsupported` 及非空限制原因。任务创建与每次执行前 MUST 以账号平台事实源查表；无声明、平台不一致或 runtime gate 不满足时 MUST fail-closed，MUST NOT 回落到小红书路径或其他平台目标。

#### Scenario: Facebook 受限动作在 UI 中可辨识
- **WHEN** 用户在 Facebook 环境打开委托入口
- **THEN** 普通发布和已配置范围评论显示 Beta/能力闸说明，今日灵感与任意 URL 评论显示不可用原因
- **AND** 客户端与 cloud 准入结论保持一致

#### Scenario: 未知平台不路由
- **WHEN** 任务绑定的平台值不在注册表或执行时账号平台已改变
- **THEN** 系统 deferred/failed 并记录平台事实不一致
- **AND** MUST NOT 尝试任何已知平台执行器

