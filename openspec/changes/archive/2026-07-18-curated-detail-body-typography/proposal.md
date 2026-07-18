## Why

桌面客户端精选详情的正文当前字号偏小，并沿用全局字体，长文本阅读体验与产品指定的跨平台正文排版不一致。

## What Changes

- 调整精选详情正文内容与灵感库列表正文摘要的字体族、字号与字重。
- 正文使用指定的跨平台系统字体与中英文回退字体栈，字号为 `16px`，字重为 `400`。
- 列表正文摘要使用同一字体栈，字号适度放大为 `14px`，字重为 `400`。
- 标题、作者、话题、元信息、按钮及其它页面的字体保持不变。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-companion-ui`: 增加精选详情正文与灵感库列表正文摘要的明确字体契约。

## Impact

- `aidcp-edge/src/electron/renderer/styles.css`: 更新 `.curated-detail-body` 正文与 `.curated-card-body` 列表摘要排版。
- `aidcp-edge/test/electron/renderer-smoke.test.ts`: 增加字体族、字号、字重与作用域回归断言。
- 不涉及 JavaScript、协议、云端、数据库或 API 变更。
