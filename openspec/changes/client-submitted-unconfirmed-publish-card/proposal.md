## Why

小红书已经接受提交、但系统尚未取得公开 `postId/postUrl` 时，客户端当前会折回并继续展示更早的“上次发布”，使最新发布动作看起来像完全没有发生。客户端需要显式承接 `submitted` / `submitted_unconfirmed`，同时继续区分“平台已接受提交”和“平台公开结果已确认”。

## What Changes

- 发布卡增加“已提交，平台确认中”展示态，显示本次稿件标题、编号和相对时间。
- `submitted` 状态优先于旧的 `lastPublish` 历史态展示，不再让旧标题盖住最新动作。
- 该状态保持诚实：不显示“已发布”，不把四阶段全部标为平台确认完成，并保留旧的真实已发布记录作为回退数据。
- 后续收到 `published` 时仍按既有逻辑转为“上次发布”；重启或连接快照只有旧历史时维持原行为。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `edge-companion-ui`: 发布卡新增提交已受理但公开结果未确认的可见状态及其优先级、诚实文案与终态转换要求。

## Impact

- `aidcp-edge` Electron 发布卡纯函数、渲染投影及相应单元测试。
- `edge-companion-ui` OpenSpec 行为契约。
- 不改变 cloud/edge 协议枚举、发布状态落库或平台写入行为；不需要构建或发布桌面安装包。
