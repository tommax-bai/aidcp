# Facebook feed 两步点赞提交根因修复：浮层项走 CDP 坐标点击 + scoped + 滚 react 控件进视口

## Why

云端点赞闸竞态修好（`56112be`，簇82）让 like 命令真被下发后，暴露出边缘 feed 两步点赞**从不生效**——每次都 `state_unchanged`（用户长期观感「读了从不点赞」，且偶发「只有第一帖成功」）。真机 A/B 实证（dev、FB 号 Tianxing Bai、只读 CDP + 真实执行器驱动活页），定位三重根因：

1. **picker-commit 全文档搜 `/^赞$/` → 点错帖**。feed 里**每张卡的中性 Like 按钮 aria-label 也恰是「赞」**（计数汇总按钮亦然），而反应选择器浮层是 portal、document 序排在**所有卡之后**。旧实现全文档搜第一个「赞」→ 目标**非首卡**时命中**上方另一张卡**的 Like 按钮：既点错了别的帖（点错卡红线），目标帖的浮层又永不提交（verify 恒 `state_unchanged`）。目标恰为首卡时才碰巧撞对——这正是之前偶发「首帖成功」的真相。

2. **浮层反应项 in-page `element.click()` 无效**。浮层里的反应项监听真实指针事件（mousedown/mouseup），`element.click()` 只派发一个 `'click'` 事件，被 FB 当 hover 态忽略、**不提交**（`clicked=true` 但反应不生效）。只有 CDP 坐标 press/release 才真提交。这是 FB **逐控件事件机制不一致**的又一例（直接 Like 按钮反而吃 `'click'`；加群、发帖 composer 各不相同——见 memory `fb-flyout-needs-coordinate-click` / `fb-join-coordinate-click-fails`）。

3. **坐标点击要求元素在可视视口内**。旧 `scrollTargetIntoView` 只把**文章顶部**滚进视口——长招工帖的 Like 按钮/浮层落在折叠线以下（真机实测浮层项 cy≈1372 > innerHeight≈1002）→ 坐标点空、依旧 `state_unchanged`。

## What Changes

1. **picker-commit 只在打开的反应浮层 dialog 内定位「赞」项**（scoped：可见 `[role=dialog]` 等、且含 ≥2 个反应项，排除反应人数查看 toolbar），绝不全文档搜索——从结构上杜绝点到别的帖。
2. **浮层「赞」项走 CDP 坐标点击**（`dispatchClick` 贝塞尔移动 + press/release，`from` 设为目标 react 控件坐标以防中途 mouseleave 收起浮层），不再 in-page `element.click()`。in-page 只回坐标、不点。
3. **`scrollTargetIntoView` 改滚帖级 react 控件进视口**（而非文章顶）+ 浮层定位加**视口内守卫**（屏外坐标不点、诚实回 `state_unchanged`，不静默空点）。
4. detail 路径（单击即翻转、不弹浮层）逐位不变——两步只在弹浮层时触发。

## Impact

- **Affected specs**: `facebook-note-scoped-targeting`（ADDED：feed 两步反应提交的作用域 + 真指针事件 + react 控件入视口三条不变量）。
- **Affected code**（edge `aidcp-edge`，已 land `b4ac517`）：`src/facebook/like-executor.ts`（`commitFeedPicker` 走 `dispatchClick`、`buildPickerLocateJs` scoped 返坐标 + 视口守卫、`buildRectJs` 滚 react 控件）。edge-only、无协议/云端改动。
- **验证**：真实 `FacebookLikeExecutor` 驱动活页**非首位帖**（articleIndex=2）→ `✓ 点赞成功`、仅目标帖翻转、别的帖不动；坐标点击 @(632,378) 落在视口内。新增 jsdom 坐标落点回归测试（scoped 到浮层、非首卡不点错帖）+ 两步桩测改坐标提交口径；edge 全量 1348 + acceptance 20 + typecheck 绿。
- **生效边界**：客户端边缘代码，生效需重打客户端包（非云端部署）；出安装包按惯例默认不做、等显式发版。
- **关联**：上游云端点赞闸竞态修复 `56112be`（change 待补建）；同簇 82 的 feed 刷屏修复 `facebook-feed-dialog-and-lazyload-refresh-fix`。
