## Context

精选详情的图片栏与文字栏使用 `overflow-y: auto` 实现独立滚动，并通过 `scrollbar-gutter: stable` 为原生滚动条预留空间。Windows Chromium 会持续显示较粗的灰色轨道和滑块。

## Goals / Non-Goals

**Goals:**

- 隐藏两栏的视觉滚动条与预留槽。
- 保持原生滚动容器、独立位置、边界、滚轮、触控板和键盘行为。
- 不增加 JavaScript 滚动模拟。
- 把吸顶标题压缩为仅含返回、标题与关闭按钮的单行，并确保其正常占位、不覆盖正文。

**Non-Goals:**

- 不改变标题吸顶、栏宽、内容布局或窄屏单栏回退。
- 不制作自定义滚动条。

## Decisions

### 使用 CSS 隐藏而不禁用滚动

列容器继续保留 `overflow-y: auto`，使用标准 `scrollbar-width: none` 与 Chromium 的 `::-webkit-scrollbar` 隐藏视觉轨道和滑块，并把 `scrollbar-gutter` 恢复为 `auto`。不使用 `overflow: hidden`，因为它会破坏客户滚动内容的能力。

### 仅限定精选详情两栏

伪元素选择器只作用于 `.curated-detail-media` 和 `.curated-detail-copy`，不影响客户端其它列表、抽屉或日志区的滚动提示。

### 吸顶标题使用单行正常流布局

详情模式隐藏 kicker 与作者副行，按钮缩至 26px，标题保留单行省略；标题栏设为不可收缩的 flex 项并继续处于正常文档流。`position: sticky` 只负责吸顶，不使用 absolute/fixed 覆盖正文，因此滚动区从标题栏下方开始。

## Risks / Trade-offs

- [隐藏滚动条降低“还有更多内容”的视觉提示] → 图片裁切、正文延续及滚轮交互仍提供内容线索；本变更按用户明确选择执行。
- [浏览器实现差异] → 同时覆盖标准属性和 Chromium WebKit 伪元素。
- [标题过长挤压按钮] → 中间标题列保持 `minmax(0, 1fr)` 与单行省略，两侧按钮使用固定列宽。

## Migration Plan

纯 CSS 变更，无数据迁移；回滚对应样式即可。

## Open Questions

无。
