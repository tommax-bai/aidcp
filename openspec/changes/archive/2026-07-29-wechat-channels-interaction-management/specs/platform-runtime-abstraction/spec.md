## ADDED Requirements

### Requirement: 平台运行时必须支持 wechat_channels 的非浏览器常驻 connector

平台运行时 SHALL 把 `wechat_channels` 加入 Edge/Cloud/环境配置的 `PlatformId`，并 SHALL 允许该平台同时装配 browser auth sidecar 与独立 `InteractionConnector`。浏览器 driver 负责身份/挑战/sidecar 生命周期，connector 负责 API probe、增量同步、发送和回查；浏览器关闭 MUST NOT 被解释为平台 runtime 停止。缺少 connector 或有效 capability 时 MUST 诚实 unsupported，MUST NOT 回落 XHS/Facebook 浏览逻辑。

#### Scenario: api-only runtime 不依赖打开页面
- **WHEN** 视频号账号已登录、身份验证通过且浏览器关闭
- **THEN** runtime 保持 online 并由 InteractionConnector 工作，MUST NOT 创建虚假的 browse session

#### Scenario: connector 缺失时 fail-fast
- **WHEN** 构建识别 `wechat_channels` 但没有 InteractionConnector
- **THEN** 该平台互动能力诚实不可用，MUST NOT 装配 XHS/Facebook driver 代替

### Requirement: 平台能力 registry 必须区分编排能力与入站互动能力

Edge 与 Cloud registry SHALL 为 `wechat_channels` 声明 `identity/overlay/auth.browser_sidecar` 与 comment/DM read/write interaction capabilities，并对 browse/like/collect/follow/publish/patrol 显式 unsupported。Cloud 现有 note-scoped registry MUST NOT 被迫为视频号编造站点指标、surface 或调度入口；如果扩展 registry shape，旧 XHS/Facebook entries 和消费者 MUST 保持逐位兼容。

#### Scenario: 视频号不显示不存在的浏览能力
- **WHEN** Cloud/Edge 查询 `wechat_channels` registry
- **THEN** 只得到真实 interaction/auth 能力，MUST NOT 因满足旧 Record 类型而声明 collect/follow/publish

#### Scenario: 现有平台零回归
- **WHEN** registry 支持 InteractionConnector 后运行 XHS/Facebook contract tests
- **THEN** 两个平台的既有能力、surface、comment profile 与调度行为不变

### Requirement: 视频号平台归属必须随环境原子传递

环境创建、加入、列表、选择、settings 与核心启动注入 SHALL 支持 `wechat_channels` 并保持 `envKey/accountId/platform` 原子一致。已标注视频号环境 MUST NOT 被旧的二值 normalize 逻辑回落为 xiaohongshu；Cloud MUST 校验 edge hello platform 与 `accounts.platform`，不一致时拒绝同步和发送。

#### Scenario: 二值 normalize 不吞掉 wechat_channels
- **WHEN** Electron/Edge 从环境 remark/settings 读取 `wechat_channels`
- **THEN** 值原样注入 `AIDCP_PLATFORM=wechat_channels`，MUST NOT 归一化成 xiaohongshu

#### Scenario: 平台与账号不一致时拒绝派活
- **WHEN** hello 报 `wechat_channels` 但目标 account 的 `accounts.platform` 不是 `wechat_channels`
- **THEN** Cloud 拒绝注册 interaction route 并返回稳定配置错误
