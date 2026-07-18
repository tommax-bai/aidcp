## Why

灵感库列表正文摘要放大到 `14px` 后，卡片标题仍为 `13px`，“可创作”等状态标签仍为 `9.5px`，标题反而弱于正文，标签也偏小，卡片信息层级失衡。

## What Changes

- 灵感库列表卡片标题调整为 `16px / 700`，继续保持单行省略。
- “可创作”等列表卡片状态标签调整为 `11px / 700`。
- 标题和状态标签使用与正文一致的跨平台字体栈。
- 列表摘要保持 `14px / 400`；详情页徽标及其它页面标签保持不变。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-companion-ui`: 完善精选列表卡片的标题、摘要与状态标签字体层级。

## Impact

- `aidcp-edge/src/electron/renderer/styles.css`: 调整 `.curated-card-top strong` 和列表卡片内状态标签的排版，并拆分详情徽标字号。
- `aidcp-edge/test/electron/renderer-smoke.test.ts`: 增加标题、列表标签与详情徽标隔离回归。
- 不涉及 JavaScript、协议、云端、数据库或 API 变更。
