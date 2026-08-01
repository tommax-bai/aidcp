## Why

Facebook Reel 的普通点赞与关注目前使用 Cloud 固定概率，而且慢启动仍会复用普通人设的 Reel 决策。运营无法调整频率，也无法保证普通人设、慢启动、规则和消费四种模式各自执行自己的规则。

## What Changes

- 将普通人设模式的 Reel 点赞改为严格的“本会话每 N 个唯一 Reel 尝试 1 次”，默认 N=4；该规则只在普通人设模式、只对 Reel 生效。
- 将普通人设模式的 Reel 关注改为独立的“本会话每 N 个唯一 Reel 尝试 1 次”，默认 N=10。
- 为慢启动、规则、消费模式分别增加只属于该模式的 Reel 关注频率，默认均为每 15 个唯一 Reel 尝试 1 次。
- 所有上述数字仅在管理后台的 Facebook 全局运行数值中配置，与现有规则、消费、慢启动配置平级；不增加客户、账号或环境级覆盖。
- 保留现有 Edge 能力、RiskController、会话预算、冷却、作者去重、Native CDP 动作和同 Reel 后置确认；达到 N 只代表尝试，不代表平台成功。
- 普通 Feed、Feed 视频、详情页不计入这些 Reel 计数；现有 Feed 视频普通点赞策略不在本变更范围内。

## Capabilities

### New Capabilities

- `facebook-reel-mode-cadence`: 定义四种 Facebook 浏览模式各自的全局 Reel 点赞/关注频率、计数边界和管理后台配置。

### Modified Capabilities

- `facebook-reels-like-policy`: 普通 Reel 点赞从固定 25% 抽样改为普通人设专属的可配置 N 次访问节奏。
- `facebook-reels-follow-policy`: Reel 关注从所有非自动模式共用固定 10% 抽样改为按当前模式读取各自全局 N 次访问节奏。

## Impact

- `aidcp-cloud`: 追加 API-owner migration，扩展全局 operation policy、Panel GET/PUT、模式投影和 RoleDispatcher Reel 计数/动作选择。
- `aidcp-console`: 在现有 Facebook 全局运行数值编辑器中增加普通人设 Reel 点赞/关注，以及慢启动、规则、消费 Reel 关注字段。
- `aidcp-edge`: 无协议、IPC、Native 定位器或安装包源码变更；仍使用既有 Reel follow 能力与后置确认。
- Control/OpenSpec: 收窄此前过大的通用数字策略提案，不建立 DSL、不可变版本平台、客户端 capability 发布门禁或环境覆盖。
