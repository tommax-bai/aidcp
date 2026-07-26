## Context

内部管理后台账号来自 `AIDCP_PANEL_USERS`，视频号互动 grants 来自 `AIDCP_INTERACTION_PANEL_GRANTS`。两者只在 Cloud 启动时解析，Console 目前没有安全的只读出口。

## Decisions

### Fixed permission catalog

Cloud 维护固定六项权限目录：

- `interaction.config.view`
- `interaction.config.edit`
- `interaction.config.publish`
- `interaction.config.preview`
- `interaction.dm.view_full`
- `interaction.audit.view`

每项包含稳定 key、中文名称、中文说明和已授权用户名列表。列表只保留同时存在于已解析 panel users 与已解析 grants 的用户名，并按用户名稳定排序。

### Read-only authenticated API

新增 `GET /api/config/interaction-permissions`。端点位于内部 panel JWT 校验之后，只返回权限目录与用户名，不返回密码、JWT、环境变量原文或 grant 配置中的失效 actor。依赖未注入时诚实返回 503。

### No mutation surface

本变更不增加 POST、PUT、PATCH 或 DELETE 端点。Console 卡片没有编辑控件，并明确标记“只读”。权限继续由现有环境变量与 Cloud 启动期解析决定。

### Independent settings loading

权限卡片独立处理 loading/error/empty 状态，避免权限概览暂时不可用时遮蔽现有模型和凭据设置。

## Testing

- Cloud 单元测试覆盖六项固定目录、用户名交集、稳定排序、空 grants 与失效 actor 不泄漏。
- Cloud panel API 测试覆盖 JWT 后只读响应及未注入 503。
- Console 设置页测试覆盖六项说明、已授权用户、空用户与无编辑入口。
