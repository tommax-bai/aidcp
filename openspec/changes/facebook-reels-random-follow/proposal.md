## Why

Facebook Reels 已有绑定当前视频并验证后置状态的关注执行器，但浏览编排不会自动选择关注，而且 Cloud 仍把 Facebook 的 `follow` 用量整键从客户端“今日进展”中摘掉。需要在不扩大普通主页关注能力的前提下，增加受配额约束的低频自动关注，并让真实关注在客户端可见。

## What Changes

- 对每个会话内首次出现的、唯一且规范的当前 Facebook Reel 做一次独立关注决策；作者可读且随机值严格小于 `0.10` 时选择现有 note-scoped 关注意图。
- 概率命中仍须通过本轮关注预算、RiskController 分时/每日配额、互动冷却、同账号去重和命令抑制；只有 Edge 验证同一 Reel 从 Follow 变成 Following 的真实新关注才计数。
- 在 Cloud 平台注册表中新增独立的 `reel_follow` 能力，保持 Facebook 普通主页 `follow`/`profile_visit` 不支持；客户端关注指标由普通关注或 Reel 关注任一真实能力决定。
- Facebook 客户端在确认新关注后即时显示一条“关注”活动并提供本地兜底增量，同时继续以 Cloud `dailyUsage.follow` 作为今日权威总量；`already_followed`、shadow 和失败结果不增加活动或计数。
- 不新增协议消息或字段，不改变小红书、视频号、Facebook 普通 Feed/主页关注行为。

## Capabilities

### New Capabilities

- `facebook-reels-follow-policy`: 定义每个可信 Reel 的 10% 独立关注决策、配额/风控/冷却/去重门禁，以及平台确认后才计数的终态语义。

### Modified Capabilities

- `platform-runtime-abstraction`: 将 Facebook Reels-only 关注能力与普通主页关注能力分开声明，避免为展示指标而误开启主页关注编排。
- `edge-companion-ui`: 在 Facebook “今日进展”显示 Cloud 权威关注数据，并为确认的新 Reel 关注显示结构化活动与本地兜底增量。

## Impact

- Cloud：`RoleDispatcher` 的 Reel 呈现决策、平台能力注册表、用量指标投影及相关集成/平台测试。
- Edge：Facebook companion UI 事件、Reel 关注成功投影、活动图标与客户端测试；复用现有 `interaction.follow` 和 Reel 执行器。
- Control：新增 OpenSpec 变更与交付证据。
- 无数据库迁移、无新协议类型、无 Console 变更。Cloud 运行时变更需部署到 `dev`；本变更不构建 Edge 安装包，已安装客户端获得新结构化活动需后续单独发版，但 Cloud 下发关注指标可由现有通用指标渲染器直接呈现。
