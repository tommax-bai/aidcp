## Why

Facebook 新账号的首页可能合法地只显示“没有更多帖子 / 添加好友查看更多”的空态，也可能先浏览若干普通帖子后真实到达列表底部。当前 Edge 把“首页没有 feed 卡片”当成页面未就绪并反复导航，而 Cloud 对已经确认到底的非空 Facebook Feed 只会刷新同一列表；两种状态都无法继续获取内容。需要一个加载感知、fail-closed 的确认，并在 Cloud 授权后切到仍有内容的 Reels 列表继续浏览。

## What Changes

- 将“已在 Facebook 首页”与“首页已有可读卡片”拆开，按 URL、登录/阻断态、主区域、document generation、最短水合时间和连续显式空态证据确认真实空 Feed。
- 仅在 Cloud 收到 Edge 的明确首页空态报告，或收到已浏览过真实卡片后的 `feed_exhausted` 回执时，授权本会话从首页列表切到 Reels；加载中、未知布局、登录页、checkpoint/consent/captcha 等状态均不得触发降级。
- 为 Facebook Reels 增加独立的活动视频定位、文字摘要读取、单击点赞及选中态验证、下一条卡片导航与身份变化验证。
- 复用现有 `page.cards`、`note.open`、`interaction.like`、`page.scroll` 和风险控制链；只在 `page.cards` 增加向后兼容的可选列表来源/空态观察，不新增消息类型、不改变点赞授权与记账规则。

## Capabilities

### New Capabilities

- `facebook-reels-browse`: 定义 Facebook Reels 列表的活动视频识别、摘要读取、点赞和下一条导航的诚实验证行为。

### Modified Capabilities

- `facebook-feed-continuity`: 将首页在页判定与卡片存在性解耦，并把 0 卡结果细分为明确空态、仍在加载和未知状态。
- `facebook-feed-browse`: 首页明确空态或非空 Feed 确认到底时由 Cloud 授权切换 Reels，其他 0 卡/阻断状态保持 fail-closed。
- `platform-browse-surface`: 现有消息携带可选列表来源/空态观察，同时保持 `feed/detail` 语义、消息类型集和旧端默认行为不变。

## Impact

- `aidcp-edge`: Facebook feed readiness/empty-state probe、session list-mode routing、Reels reader/like/next executors and focused tests.
- `aidcp-cloud`: protocol mirror、edge event translation、RoleDispatcher fallback authorization and integration tests; existing RiskController remains the single writer.
- `aidcp`: protocol documentation, OpenSpec deltas, validation evidence.
- No Edge installer or desktop release is required; runtime deployment is limited to the Cloud `dev` service after validation.
