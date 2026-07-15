## Why

真实账号首次确认人设时，Electron 主进程会在返回 `persona.persist` IPC 结果前先推送 `personaBound:true`。渲染层把这条权威绑定态当作“系统误弹已结束”，提前关闭自动打开的人设浮层；随后虽然收到 `firstPostOnboarding:true` 并建立首作卡状态，但展示函数不会重新打开已关闭的浮层，导致 Cloud 已触发、用户却看不到卡片。

## What Changes

- Edge 在某账号的 `persona.persist` IPC 正在收敛时，暂缓该账号自动人设浮层的绑定态收起逻辑。
- 首作卡已经激活后，后续 `personaBound:true` 心跳不得关闭用户正在阅读的引导。
- 没有首次首作信号的普通绑定或更新仍按既有规则收起系统自动浮层；手动打开的浮层行为不变。
- 增加真实顺序回归测试：`personaBound:true` 状态推送先到，`persona.persist.result` 后到。

## Capabilities

### Modified Capabilities

- `first-post-onboarding`: 补充首作完成引导在状态推送与 IPC 回执竞态下的可见性保证。

## Impact

- `aidcp-edge/src/electron/renderer/renderer.js`
- `aidcp-edge/test/electron/fleet-console.test.ts`
- 不改变 Cloud 状态、协议、浏览或发布逻辑。
