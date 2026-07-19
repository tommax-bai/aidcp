## Why

Windows 桌面客户端的主窗口、“今天做了这些”和“开发者详情”当前持续显示较粗的纵向原生滚动条，挤占紧凑界面的视觉空间。用户希望这些纵向滚动条隐藏，同时保留滚动能力，并明确要求横向滚动条不变。

## What Changes

- 隐藏客户端主文档的纵向滚动条，但保留滚轮、触控板、键盘与程序化滚动。
- 隐藏“今天做了这些”列表和“开发者详情”日志区的纵向滚动条，但不改变其高度、溢出或滚动位置行为。
- 仅对纵向 Chromium 滚动条生效；横向滚动条继续使用既有原生样式与行为。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-companion-ui`: 增加客户端主体、活动流和开发者日志隐藏纵向滚动条但保留滚动能力与横向滚动条的要求。

## Impact

- `aidcp-edge/src/electron/renderer/styles.css`: 三类纵向滚动容器的轴向滚动条样式。
- `aidcp-edge/test/electron/renderer-smoke.test.ts`: 样式契约回归测试。
- 不涉及 JavaScript、协议、云端、数据库、API 或安装包构建。
