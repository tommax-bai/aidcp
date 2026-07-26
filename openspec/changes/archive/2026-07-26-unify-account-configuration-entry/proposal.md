## Why

管理后台账号表当前把 Facebook 配置入口附着在“平台”列，却为视频号单独增加“运行控制”列，导致同类账号级配置入口分散且表头语义只覆盖单个平台。需要统一为清晰的“配置”列，让运营按账号和平台快速找到可用配置。

## What Changes

- 将账号表的“运行控制”表头改为“配置”。
- 将视频号账号的运行控制入口保留在统一“配置”列。
- 将 Facebook 账号的既有配置入口从“平台”单元格移动到统一“配置”列。
- 平台列只展示平台事实标签；没有账号级配置入口的平台在配置列显示明确空态。
- 保持视频号运行控制和 Facebook 配置的现有接口、弹窗内容与保存语义不变。

## Capabilities

### New Capabilities

- `account-configuration-entry`: 管理后台账号表按平台在统一“配置”列呈现账号级配置入口，并保持平台列只表达平台事实。

### Modified Capabilities

<!-- No existing capability requirements change. -->

## Impact

- `aidcp-console`: `AccountsPage`、`AccountsTable` 及相关 UI 测试。
- API 与 Cloud 数据契约不变；不涉及 Edge、Cloud、协议、风险状态或发布行为。
- 管理后台静态资源需在合并后按 dev 部署流程更新。
