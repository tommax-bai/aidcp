## Why

桌面客户端的精选详情把参考图与稿件文字放在同一个纵向滚动面中；当两栏高度差较大时，较短栏到达末尾后仍被继续推离视口，留下持续扩大的空白，影响图文对照阅读。

## What Changes

- 精选详情在宽屏双栏模式下让参考图栏与文字栏联动滚动，并分别夹紧在各自的顶部和底部边界。
- 任一栏先到达底部后保持在底部，只保留固定的小段尾部留白；另一栏继续滚动直到自身到底。
- 向上滚动时采用对称规则：先到顶部的栏保持不动，另一栏继续回到顶部。
- 窄屏单栏布局继续使用普通页面滚动，不引入并列滚动行为。
- 保持键盘操作、按钮点击、图片加载及详情返回行为不变。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-companion-ui`: 增加桌面客户端精选详情双栏滚动边界与响应式回退要求。

## Impact

- `aidcp-edge/src/electron/renderer/content-workspace.js`: 精选详情滚动协调与生命周期清理。
- `aidcp-edge/src/electron/renderer/styles.css`: 双栏可滚动高度、尾部留白与窄屏回退。
- `aidcp-edge/test/electron/content-workspace.test.ts`: 双栏边界夹紧及单栏回退的回归测试。
- 不涉及协议、云端、数据库或管理后台 API 变更。
