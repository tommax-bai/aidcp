## Why

Facebook 主界面在首作寻找、首作生成和普通运行期间展示整张运行价值/获得感卡，与顶部真实状态和今日进展形成重复信息。Facebook 需要收回这三类主动运行卡片，让主界面只保留真实状态与数据；人设完成引导和小红书现有体验不得受影响。

## What Changes

- 当选中环境为 Facebook 且首作状态为 `searching` 或 `generating` 时，不渲染整张主运行价值卡。
- 当选中环境为 Facebook 且满足普通 `running` 运行价值卡条件时，不渲染整张主运行价值卡。
- Facebook 的人设完成弹窗保持原样，包括全部首作说明、“开始找灵感”按钮、吉祥物、撒花和流光。
- Facebook 顶部在场感、本轮/小时间隔卡、今日完成卡、今日进展和发布卡保持现有行为。
- 小红书所有运行价值卡与人设引导保持现有行为。
- 不改变 Cloud 首作状态、自动生成、待审、发布确认或自动化运行链路。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `runtime-value-guidance`: 增加 Facebook 首作寻找、首作生成和普通运行三类主动状态整卡隐藏规则，同时明确间隔、完成、人设弹窗和小红书不受影响。

## Impact

- `aidcp-edge/src/electron/renderer/ui-logic.js`：按平台和运行价值模式收紧返回规则。
- `aidcp-edge/test/electron/ui-logic.test.ts`、`test/electron/companion-ui.test.ts`：覆盖三类 Facebook 隐藏状态、保留状态及 XHS 对照。
- `aidcp/openspec/specs/runtime-value-guidance/spec.md`：归档后更新平台状态展示合同。
- 无协议、Cloud API、持久化、浏览动作或发布链路变更；不需要部署服务或构建桌面安装包。
