## ADDED Requirements

### Requirement: 管理后台必须只读展示视频号互动权限与有效授权用户

internal panel API SHALL 在有效 panel JWT 之后提供固定六项视频号互动权限的只读概览。每项 MUST 包含稳定 permission key、中文名称、中文说明和当前有效授权用户名；有效授权用户名 MUST 同时存在于后台登录用户与该 permission 的 grants 中。响应 MUST NOT 包含密码、JWT、环境变量原文或已经失效的 actor。Console 设置页 SHALL 展示该概览并明确标记只读，MUST NOT 提供权限新增、删除或编辑动作。

#### Scenario: 设置页展示六项权限与授权用户
- **WHEN** 已认证后台用户打开设置页
- **THEN** Console 展示 `interaction.config.view`、`interaction.config.edit`、`interaction.config.publish`、`interaction.config.preview`、`interaction.dm.view_full` 与 `interaction.audit.view` 的名称和说明
- **AND** 每项展示当前有效授权用户名或明确的空状态

#### Scenario: 失效 actor 与凭据不泄漏
- **WHEN** grants 配置包含一个不在后台登录用户清单中的 actor
- **THEN** 权限概览不返回该 actor
- **AND** 响应不包含任何后台密码、JWT 或环境变量原文

#### Scenario: 权限概览只读
- **WHEN** 后台用户查看视频号权限设置
- **THEN** 页面不显示新增、删除、保存或编辑权限的控件
- **AND** Cloud 不为该能力提供权限变更写端点

#### Scenario: 权限概览故障不遮蔽其他设置
- **WHEN** 权限概览接口不可用或返回错误
- **THEN** Console 在权限卡片内诚实显示失败和重试入口
- **AND** 已加载的模型与凭据设置仍可查看和使用
