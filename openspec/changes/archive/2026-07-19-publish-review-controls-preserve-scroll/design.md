## Context

`appendPublishPlanControls` 当前在 radio `change` 时调用 `renderPublishPreviewContent`。该函数会对 `#publish-preview-content` 执行 `replaceChildren()`，浏览器因此丢失当前焦点与审核容器的滚动锚点。`datetime-local` 还是 Electron/Chromium 原生控件，其弹出器聚焦阶段也可能在当前帧之后调整滚动位置。

## Goals / Non-Goals

**Goals:**

- 切换立即/定时发布时不重建完整稿件详情。
- 点击或修改日期时间控件后保持审核容器原滚动位置。
- 保持现有时间默认值、范围校验、按钮禁用和提交载荷不变。

**Non-Goals:**

- 不改变审批协议、Cloud 计划校验或定时发布范围。
- 不重新设计稿件审核布局，不改变列表/详情导航。
- 不构建或分发客户端安装包。

## Decisions

### 1. 发布计划区域就地更新

小红书详情首次渲染时同时创建发布模式 radio 与日期时间行。模式变化仅切换日期时间行可见性、更新内存状态并调用既有 `syncPublishPreviewActions`；不再调用完整详情 renderer。这样标题、正文、配图、焦点与滚动锚点均保持原节点。

### 2. 同步和下一帧双重恢复滚动位置

控件交互前读取 `#publish-preview-panel.scrollTop`，状态更新后立即恢复，并在 `requestAnimationFrame` 再恢复一次，以覆盖 Chromium 原生日期时间弹出器在事件返回后的聚焦滚动。恢复只作用于当前仍打开的同一审核容器，不修改页面或列表的其它滚动状态。

### 3. 用 DOM 身份和 scrollTop 守护回归

jsdom 测试将审核容器置于非零滚动位置，切换 scheduled 并操作 `datetime-local`，断言详情根节点身份未变化且 `scrollTop` 保持。该断言会在重新引入整页重建时直接失败。

## Risks / Trade-offs

- [下一帧恢复覆盖用户同帧主动滚动] → 仅在直接控件交互触发的一帧内恢复，范围限定为审核容器；用户后续滚动不受影响。
- [隐藏的时间控件保留旧值] → 这是预期行为，切回定时发布应保留客户刚选择的时间，现有提交校验仍以当前模式为准。

## Migration Plan

仅 Edge renderer 代码变更。合入默认分支后随下一次显式客户端构建生效；无需 Cloud 部署、数据迁移或协议升级。
