## Why

桌面客户端的精选详情把参考图与稿件文字放在同一个纵向滚动面中；当两栏高度差较大时，较短栏到达末尾后仍被继续推离视口，留下持续扩大的空白，影响图文对照阅读。

## What Changes

- 精选详情在宽屏双栏模式下把参考图栏与文字栏改为两个独立滚动区；指针位于哪一栏，滚轮只控制哪一栏。
- 任一栏到达底部或顶部后保持在自身边界，只保留固定的小段尾部留白，不带动另一栏改变位置。
- 灵感详情标题区改为紧凑吸顶态，持续显示详情类型、标题、作者、返回与关闭入口；关闭按钮不得因压缩而隐藏。
- 窄屏单栏布局继续使用普通页面滚动，不引入并列滚动行为。
- 保持键盘操作、按钮点击、图片加载及详情返回行为不变。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-companion-ui`: 增加桌面客户端精选详情双栏滚动边界与响应式回退要求。

## Impact

- `aidcp-edge/src/electron/renderer/content-workspace.js`: 精选详情模式生命周期清理。
- `aidcp-edge/src/electron/renderer/styles.css`: 双栏可滚动高度、尾部留白与窄屏回退。
- `aidcp-edge/test/electron/content-workspace.test.ts`: 双栏滚动位置隔离、紧凑吸顶标题及单栏回退的回归测试。
- 不涉及协议、云端、数据库或管理后台 API 变更。
