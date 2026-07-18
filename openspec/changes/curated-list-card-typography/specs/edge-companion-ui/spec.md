## RENAMED Requirements

- FROM: `### Requirement: 精选正文与列表摘要使用分级跨平台字体排版`
- TO: `### Requirement: 精选正文与列表卡片使用分级跨平台字体排版`

## MODIFIED Requirements

### Requirement: 精选正文与列表卡片使用分级跨平台字体排版

桌面客户端的精选详情正文内容、灵感库列表标题、正文摘要与状态标签 SHALL 使用以下有序字体回退链：`system-ui, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji", -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif, BlinkMacSystemFont, "Helvetica Neue", Arial, "PingFang SC", "PingFang TC", "PingFang HK", "Microsoft Yahei", "Microsoft JhengHei"`。详情正文 SHALL 使用 `16px / 400`；列表标题 SHALL 使用 `16px / 700`；列表正文摘要 SHALL 使用 `14px / 400`；“可创作”等列表状态标签 SHALL 使用 `11px / 700`。列表标题 SHALL 保持单行省略，正文摘要 SHALL 保持两行截断，状态标签 SHALL 保持不收缩。该排版 MUST NOT 改变作者、话题、元信息、按钮、详情页徽标或其它内容工作区页面；详情页徽标 SHALL 继续使用 `9.5px` 字号。既有行高、换行、间距与滚动行为 SHALL 保持不变。

#### Scenario: 精选详情正文应用指定字体排版

- **WHEN** 客户打开包含文字内容的精选详情
- **THEN** 正文使用指定字体回退链、`16px` 字号与 `400` 字重显示

#### Scenario: 灵感库列表卡片形成清晰文字层级

- **WHEN** 灵感库列表卡片同时显示标题、正文摘要和“可创作”等状态标签
- **THEN** 标题使用 `16px / 700`，摘要使用 `14px / 400`，状态标签使用 `11px / 700`，且三者使用指定字体回退链

#### Scenario: 列表标题与摘要截断保持不变

- **WHEN** 灵感库列表标题或正文摘要超过可用空间
- **THEN** 标题继续单行省略，正文摘要继续按既有两行规则截断，卡片布局保持不变

#### Scenario: 详情页徽标不随列表标签放大

- **WHEN** 客户打开带状态徽标的精选详情
- **THEN** 详情页徽标继续使用既有 `9.5px` 字号，不继承列表状态标签的 `11px` 字号

#### Scenario: 字体调整不扩散到其它元素

- **WHEN** 精选详情或灵感库列表同时显示作者、话题、元信息和操作按钮
- **THEN** 本变更不改变这些元素或其它内容工作区页面的字体样式

#### Scenario: 正文滚动与换行保持不变

- **WHEN** 精选详情正文超过文字栏可视高度
- **THEN** 正文继续按既有行高和换行规则排版，文字栏继续独立滚动
