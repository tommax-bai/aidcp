## Why

Facebook 环境的慢启动开关要等待云端写入完成后，状态徽章才变化；网络较慢时，客户端只有一个不明显的禁用复选框，用户会误以为点击没有生效或客户端卡住。

## What Changes

- 点击慢启动开关后，客户端立即把整行切换为明确的“正在开启”或“正在关闭”临时样式，同时禁用重复操作。
- 临时样式只表达“请求正在提交”，不得冒充云端已经生效，也不得本地推算慢启动天数或配额。
- 云端成功后用写后真态确认展示；失败、异常或超时后恢复点击前的权威状态，并就地显示失败原因。
- 写入期间收到旧的 `ui.snapshot` 时，客户端保留本次临时态，避免界面来回跳变。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-companion-ui`: 为账号级慢启动开关补充即时提交反馈、权威确认和失败回滚要求。

## Impact

- 代码：`aidcp-edge/src/electron/renderer/renderer.js`、`styles.css` 与对应 jsdom 测试。
- API / 协议：不变；仍使用现有 `slow-start:set` IPC 和 env-scoped 云端 PUT。
- 依赖：本 change 依赖 `account-level-slow-start` 已提供的开关、权威回执与失败语义；不修改 cloud、protocol、风险计算或配额事实源。
