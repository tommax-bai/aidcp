## Why

桌面客户端精选详情已经使用左右独立滚动，但 Chromium/Windows 的原生灰色滚动条在两栏内持续占据视觉和横向空间，与紧凑详情设计不一致。

## What Changes

- 宽屏精选详情隐藏图片栏和文字栏的可见滚动条轨道与滑块。
- 保留滚轮、触控板、键盘与程序化滚动能力，两栏独立滚动和边界行为不变。
- 移除滚动条预留槽，避免隐藏后仍留下窄白边。
- 吸顶标题进一步压缩为单行，只展示返回、当前标题和关闭按钮；隐藏详情类型与作者副行，且标题栏继续占据正常布局空间、不遮挡正文。
- 窄屏单栏回退行为不变。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-companion-ui`: 增加精选详情独立滚动区隐藏视觉滚动条但保留可滚动性的要求，并把详情吸顶标题收敛为单行。

## Impact

- `aidcp-edge/src/electron/renderer/styles.css`: 精选详情栏的跨浏览器滚动条隐藏样式。
- `aidcp-edge/test/electron/renderer-smoke.test.ts`: 样式契约回归测试。
- 不涉及 JavaScript、协议、云端、数据库或 API 变更。
