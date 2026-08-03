## Why

Facebook Feed 与 Reels 当前在正常档位下共用约 7 秒的翻页停留中心，实际节奏偏快且现有抖动范围较窄。两条路径已经共用 `page.scroll` 停留链路，因此应以一个变更统一放慢，避免形成两套难以校准的节奏规则。

## What Changes

- 将 Facebook Feed 与 Reels 的正常翻页停留中心统一提高到 11 秒；风险档位仍由现有 `tempo` 单调放大。
- 仅对 Facebook `page.scroll` 使用更宽但有界的 lognormal 抖动：`sigma=0.30`、相对中心 `0.55x..1.90x` 反射边界、绝对上限 60 秒。
- 延续现有按已用时间抵扣、只补正差额的语义；不新增 Feed/Reels 分支状态或协议字段。
- 保持页面识别、输入预留、命令执行、空闲唤醒与会话结束等既有超时不变。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `command-pacing`: 明确 Facebook Feed/Reels 共享的 11 秒正常翻页中心、Facebook 专属有界抖动，以及既有超时不随此次节奏调整联动变化。

## Impact

- Cloud：Facebook 平台翻页停留下限及相关测试。
- Edge：`page.scroll` 的 Facebook 专属随机采样、等待诊断及相关测试。
- Protocol/Native Rust：不改变消息形状或 Rust 命令执行超时。
- Delivery：Cloud 运行时变更可部署到 DEV；Edge 源码变更需要后续显式打包并安装后才会进入已安装客户端，本变更不自行产出安装包。
