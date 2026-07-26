## Why

AdsPower 环境在启动阶段被其他设备或窗口占用时，本机引擎已经退出且不会重试，但 Electron 将该环境投影为 `automationState=error` 后只显示“启动”和“浏览器”，没有“关闭自动化”入口。操作者无法明确结束本机启动意图、清除终态异常，也容易把“外部仍占用”误解为“本机任务仍在运行且关不掉”。

## What Changes

- 自动化处于终态错误、且本机仍保留启动意图时，客户端同时提供“重试启动”和“关闭自动化”动作。
- “关闭自动化”只关闭本机自动化意图、取消本机重试/排队并清除本轮失败；不得把外部 AdsPower 占用冒充为本机浏览器仍可关闭，也不得向占用端发送 stop、强杀或调试附着。
- 对启动前即被拒绝、从未取得本机浏览器句柄的占用终态，关闭后直接收敛为本机自动化已关闭；文案明确外部会话不受影响，不执行无依据的浏览器关闭确认。
- 其他可能遗留本机浏览器的异常终态继续沿用既有诚实确认：只有确认已关闭才显示关闭完成，无法确认时仍保留可操作失败。
- 增加渲染器与主进程生命周期回归测试；不修改 Cloud/协议，不制作 Edge 安装包。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-companion-ui`: 终态启动失败仍须提供关闭本机自动化的入口，并将重试与关闭表达为不同动作。
- `edge-node-supervised-recycle`: 不可重起的外部占用终态在用户关闭本机自动化时必须安全收敛，且不得误停或假称关闭外部会话。

## Impact

- Edge Electron：`src/electron/renderer/renderer.js` 的生命周期按钮映射、`src/electron/renderer/ui-logic.js` 的关闭态诚实在场文案，以及 `src/electron/main.cjs` 的无子进程关闭收敛。
- Edge 测试：渲染器生命周期交互与主进程源码契约测试。
- Control：上述两个能力的 OpenSpec delta 与任务证据。
- 无 Cloud、数据库或协议变更；无部署顺序要求；不构建或发布桌面安装包。
