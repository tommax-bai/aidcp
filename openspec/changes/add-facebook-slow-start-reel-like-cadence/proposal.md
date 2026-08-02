## Why

冷启动模式目前只能全局配置“每浏览 N 个 Reel 关注一次”，无法配置同一模式下的 Reel 点赞节奏，导致冷启动的点赞行为缺少后台可调的 Cloud 权威策略。需要在不改变现有 7 天逐日上限、风险门禁和 Edge 动作能力的前提下，补齐冷启动 Reel 点赞频率。

## What Changes

- 在 Facebook 全局 operation policy 中为冷启动 Reel 增加 `viewsPerLike` 整数配置，范围 `1..100`，兼容默认值为 `15`。
- Cloud 按冷启动模式会话内已确认呈现的唯一规范 Reel 计数，在每第 N 个 Reel 产生一次既有点赞意图；计数、身份去重、风险/配额/冷却和平台确认语义沿用现有 Reel 节奏机制。
- 管理后台在“冷启动全局上限”中并列展示、校验和保存 Reel 点赞与关注频率，并继续保留总天数及每日上限编辑行为。
- 不新增账号、客户或环境级覆盖，不改变 Feed/Feed 视频点赞策略，不修改 Edge 协议或动作实现。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `facebook-reel-mode-cadence`: 将全局 Reel 节奏策略从五个整数扩展为六个整数，并授权冷启动模式按独立可配置频率产生 Reel 点赞意图。

## Impact

- Control：更新 `facebook-reel-mode-cadence` delta spec、设计、任务与交付证据。
- Cloud：新增兼容数据库迁移，扩展全局策略存储/API DTO/校验，并在 `RoleDispatcher` 中接入冷启动 Reel 点赞节奏。
- Console：扩展全局策略类型、编辑器字段、校验和回归测试。
- Edge、协议 v2、账号/环境配置、OL 与已安装客户端不在本次变更范围内。
