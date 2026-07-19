## Context

Electron 客户端运行于 Chromium。主文档使用浏览器根滚动容器，“今天做了这些”使用 `.stream-wrap { overflow-y: auto; }`，开发者日志使用 `.dev pre { overflow-y: auto; }`。开发者日志还可能因长技术行产生横向滚动条。

## Goals / Non-Goals

**Goals:**

- 隐藏三类目标区域的纵向滚动条轨道与滑块。
- 保持所有原生纵向滚动输入和既有 `scrollTop` 行为。
- 保持横向滚动条的可见性、尺寸与行为不变。

**Non-Goals:**

- 不隐藏其它独立列表、抽屉或工作区的滚动条。
- 不制作自定义滚动条，不增加 JavaScript 滚动模拟。
- 不改变容器尺寸、内容换行或溢出策略。

## Decisions

### 只选择 Chromium 纵向滚动条伪元素

使用 `::-webkit-scrollbar:vertical` 并只设置 `width: 0`。选择器限定在 `html`、`body`、`.stream-wrap` 和 `.dev pre`，其中 `html` 与 `body` 共同覆盖 Electron 不同文档滚动根表现。

不使用 `scrollbar-width: none`，因为该标准属性会同时隐藏横向与纵向滚动条；不使用无轴向限定的 `::-webkit-scrollbar`，避免影响开发者日志的横向滚动条；不使用 `overflow: hidden`，避免禁用真实滚动。

### 保持滚动容器和布局不变

`.stream-wrap` 与 `.dev pre` 继续保留 `overflow-y: auto` 和原有高度约束。根文档不新增固定高度或新的内部滚动容器，因此 sticky 标题栏、环境栏和现有滚动位置逻辑不变。

## Risks / Trade-offs

- [隐藏纵向滚动条降低“还有更多内容”的视觉提示] → 内容裁切、滚轮与触控板交互仍提供线索；这是用户明确选择。
- [Chromium 私有伪元素存在实现依赖] → 桌面客户端固定运行在 Electron/Chromium，且同一渲染层已使用 WebKit 滚动条伪元素。
- [误伤横向滚动条] → 使用 `:vertical` 轴向伪类，并以回归测试禁止规则出现 `height`、无轴向选择器或双轴隐藏属性。

## Migration Plan

纯 CSS 变更，无数据迁移；回滚对应样式即可。

## Open Questions

无。
