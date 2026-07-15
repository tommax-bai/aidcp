# Tasks — facebook-feed-like-picker-commit-fix

## 1. aidcp-edge — 两步点赞提交修复（like-executor）

- [x] 1.1 `commitFeedPicker` 改走 CDP 坐标点击：新 `buildPickerLocateJs` 只在打开的反应浮层 dialog 内（`[role=dialog]` 等、≥2 反应项）定位「赞」项**坐标**（不 in-page click），caller 用 `dispatchClick`（`from`=目标 react 控件、`overshoot:false`）派发真指针 press/release。<!-- aidcp-edge b4ac517 -->
- [x] 1.2 浮层定位加**视口内守卫**：屏外坐标（cx/cy 越界）回 `found:false`，由 caller 诚实走 `state_unchanged`，绝不静默空点。<!-- aidcp-edge b4ac517 -->
- [x] 1.3 `buildRectJs` 改滚**帖级 react 控件**进视口（fallback 文章 rect），使 Like 按钮/浮层落在可视区、坐标点击命中（治长帖浮层在折叠线下）。<!-- aidcp-edge b4ac517 -->
- [x] 1.4 回归测试：新增 jsdom 坐标落点断言（scoped 到浮层、非首卡不点到别卡「赞」）；两步桩测（`like-executor-two-step.test.ts`）改 picker-locate + `onPress` 坐标提交口径；detail directToggle / 只补一次 / shadow 不变。<!-- aidcp-edge b4ac517 -->
- [x] 1.5 edge 全量 1348 + acceptance 20 + typecheck 绿。<!-- aidcp-edge b4ac517 -->

## 2. 真机验证（dev）

- [x] 2.1 真实 `FacebookLikeExecutor` 驱动活页**非首位帖**（articleIndex=2）→ `✓ 点赞成功`、仅目标帖翻转、别的帖不动、坐标 @(632,378) 在视口内。<!-- 2026-07-15 dev, FB 号 Tianxing Bai ads-k1ei3dbi, 只读 CDP + tsx 驱动 -->
- [ ] 2.2 运营机重打客户端包后肉眼复验 feed 逐帖真点赞（出包默认不做、等显式发版）。→ backlog 簇 82.4

## 3. 归档

- [ ] 3.1 `openspec validate facebook-feed-like-picker-commit-fix --strict` → archive。
