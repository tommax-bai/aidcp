## Why

桌面客户端的精选正文详情目前同时提供左侧返回按钮和右侧关闭按钮。两者在紧凑吸顶标题里语义重复，而右侧关闭按钮会直接关闭整个内容工作区，不符合用户从正文返回灵感库的预期。

## What Changes

- 仅在精选正文详情卡中移除左侧返回按钮，吸顶标题只保留当前标题和右侧 `×`。
- 精选正文详情中的 `×` 改为返回灵感库，并保留灵感库原有列表状态与滚动位置。
- 精选正文详情中的 `×` 使用“返回灵感库”可访问名称。
- 灵感库、创作页、稿件审核等其它页面的关闭按钮继续关闭内容工作区，行为与可访问名称不变。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-companion-ui`: 将精选正文详情的紧凑吸顶标题收敛为标题与单一退出入口，并明确该入口返回灵感库而非关闭内容工作区。

## Impact

- `aidcp-edge/src/electron/renderer/content-workspace.js`: 按当前页面切换返回按钮可见性、关闭按钮语义及点击行为。
- `aidcp-edge/src/electron/renderer/styles.css`: 移除精选正文详情标题栏为左侧返回按钮保留的网格列。
- `aidcp-edge/test/electron/content-workspace.test.ts`、`test/electron/renderer-smoke.test.ts`: 补充页面行为、可访问性和样式契约回归。
- 不涉及协议、云端、数据库或 API 变更。
