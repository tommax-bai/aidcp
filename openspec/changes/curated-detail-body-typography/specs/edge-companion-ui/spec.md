## ADDED Requirements

### Requirement: 精选正文与列表摘要使用分级跨平台字体排版

桌面客户端的精选详情正文内容与灵感库列表正文摘要 SHALL 使用以下有序字体回退链：`system-ui, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji", -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif, BlinkMacSystemFont, "Helvetica Neue", Arial, "PingFang SC", "PingFang TC", "PingFang HK", "Microsoft Yahei", "Microsoft JhengHei"`。详情正文 SHALL 使用 `16px` 字号与 `400` 字重；列表正文摘要 SHALL 使用较小的 `14px` 字号与 `400` 字重。该排版 MUST 只作用于这两个正文层级，MUST NOT 改变详情或列表标题、作者、话题、元信息、按钮或其它内容工作区页面的字体样式。既有行高、截断、换行、间距与滚动行为 SHALL 保持不变。

#### Scenario: 精选详情正文应用指定字体排版

- **WHEN** 客户打开包含文字内容的精选详情
- **THEN** 正文使用指定字体回退链、`16px` 字号与 `400` 字重显示

#### Scenario: 灵感库列表摘要适度放大

- **WHEN** 灵感库列表卡片显示正文摘要
- **THEN** 摘要使用同一字体回退链、`14px` 字号与 `400` 字重显示，并保持小于详情正文的字号层级

#### Scenario: 正文排版不扩散到其它元素

- **WHEN** 精选详情或灵感库列表同时显示标题、作者、话题、元信息和操作按钮
- **THEN** 本变更的字体族、字号与字重声明只作用于详情正文和列表正文摘要，其它元素继续使用既有样式

#### Scenario: 正文滚动与换行保持不变

- **WHEN** 精选详情正文超过文字栏可视高度
- **THEN** 正文继续按既有行高和换行规则排版，文字栏继续独立滚动

#### Scenario: 列表摘要截断保持不变

- **WHEN** 灵感库列表正文摘要超过两行
- **THEN** 摘要继续按既有两行规则截断，卡片布局保持不变
