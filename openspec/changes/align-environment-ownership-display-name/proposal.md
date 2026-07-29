## Why

管理后台“环境归属”抽屉当前把环境 `label` 当作昵称展示，未消费 Cloud 已按统一规则解析的绑定账号 `displayName`，因此客户端人工修改昵称后，后台同一环境仍可能显示旧备注名。需要让该位置与客户端共享同一个 Cloud 显示结果，避免运营人员按过期名称分配环境。

## What Changes

- “环境归属”的待分配和已分配列表优先展示环境绑定账号的 Cloud `account.displayName`，使客户端人工运营别名立即成为可见昵称。
- 未挂载账号或滚动发布期间缺少账号投影时，依次回落到环境系统名、已有归属备注和稳定环境 ID，不在 Console 重建账号别名优先级。
- 对齐 Console 的环境注册表类型与 Cloud 已有 additive DTO，并补测试锁定人工别名优先及未挂载回落。
- 不修改 `envKey/accountId`、客户归属、路由、平台昵称、Cloud 数据库或 Edge 写入流程。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `account-display-name`: 明确管理后台“环境归属”中的环境昵称也必须消费绑定账号的统一 `displayName`，并规定未挂载环境的非账号回落边界。

## Impact

- 代码：`aidcp-console` 的环境注册表 DTO、环境归属展示辅助函数和页面测试。
- 契约：补充 `account-display-name` 对环境归属位置的具体场景。
- API/运行时：复用 Cloud `/api/client-environments` 已有 `account.displayName`，无需 Cloud、Edge、协议或数据库变更；Console 运行时行为变化需发布到 `dev`。
