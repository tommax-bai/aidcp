## Why

视频号已经进入账号级互动配置链路，但 Console 的客户环境管理仍只提供小红书和 Facebook 平台选项；同时回复配置审计页丢弃 Cloud 已返回的分页游标，只展示首屏记录。运营因此无法正常登记视频号环境，也会把截断的审计列表误当成完整台账。

## What Changes

- 在客户环境登记、编辑和展示入口中把 `wechat_channels` 作为受支持的平台值，显示中文“视频号”，同时保留未知未来值的灰底原值兜底。
- 让账号级回复配置审计页消费既有 opaque `nextCursor`，按需追加后续页，并明确区分加载中、已到底、权限拒绝和加载失败。
- 审计追加请求继续绑定当前账号；切换账号或关闭抽屉时中止旧请求，旧页不得串入新账号台账。
- 对未知 audit action/entity 枚举诚实显示原值，不因 Cloud 先扩枚举而白屏或隐藏事件。
- 不修改 Cloud 审计 API、数据库、权限或回复配置行为；不扩大视频号 delegated-task 能力。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `console-panel-api`: Console 的客户环境平台选项补齐 `wechat_channels`，并完整消费既有回复配置审计分页契约，保持账号隔离和枚举漂移兜底。

## Impact

- `aidcp-console`: `ClientUsersPage` 平台元数据/选项、回复配置 audit API 与组件状态、组件测试。
- `aidcp`: `console-panel-api` OpenSpec delta 与任务证据。
- `aidcp-cloud`: 无代码或数据库变更；继续复用现有 `GET /api/accounts/:accountId/reply-config/audit?limit&cursor`。
- 部署：Console 行为变更完成并集成后发布到 `dev`；不构建或发布 Edge 安装包，不执行视频号真实写操作。
