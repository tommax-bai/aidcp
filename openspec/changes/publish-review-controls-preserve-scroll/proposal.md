## Why

客户端稿件审核详情通常较长，发布计划控件位于页面下方。当前选择“定时发布”会重建整份审核正文，日期时间控件的原生点击也没有保护审核滚动容器，导致视口跳回顶部，客户必须再次滚动到底部才能继续批准。

## What Changes

- 发布模式切换只更新发布计划控件和批准状态，不重建整份稿件详情。
- 对发布模式和日期时间交互保存并恢复审核容器的滚动位置，覆盖 Electron 原生控件可能产生的延迟滚动。
- 增加 renderer 回归测试，证明点击定时发布与日期时间选择后仍停留在原阅读位置。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `edge-companion-ui`: 稿件审核中的发布计划控件不得因模式或时间选择把详情视口跳回顶部。

## Impact

- `aidcp-edge`: Electron renderer 发布计划控件与 companion UI 测试。
- `aidcp`: OpenSpec delta。
- 不改变 Cloud、协议、审批参数、时间校验或发布语义；不构建 Electron 安装包。
