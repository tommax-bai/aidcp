## Why

Facebook 环境现在只能读回“已经配置了哪条代理”，运行页无法证明当前指纹浏览器的真实出口，也无法看到该浏览器本次会话实际接收了多少数据。把配置态误当成生效态会掩盖直连或代理失效风险，因此需要把配置证据、运行时出口证据和浏览器可观测接收流量分开呈现。

## What Changes

- Facebook 指纹浏览器每一代启动或冷待机唤醒后，经该环境自己的 CDP 会话发起一次无 Cookie、无账号标识、禁止缓存的出口探测，得到当前浏览器观察到的公网出口；不得用 Electron/Node 代发来冒充浏览器证明。
- Cloud 提供一个无状态、无鉴权的只读出口回显端点，仅返回请求来源 IP、服务端时间和安全请求标识，并允许浏览器跨域探测；不写账号、环境或代理台账。
- Edge 同时从不经过指纹浏览器的 Node 直连链路探测本机出口，通过“浏览器出口 vs 本机出口”生成 `未配置 / 待验证 / 已验证 / 疑似直连 / 无法确认 / 已失效` 的诚实状态；探测未知不得假报成功。
- Edge 对当前 Facebook page 及其受管网络目标启用 CDP Network 统计，只累计 `Network.loadingFinished.encodedDataLength` 接收字节；运行页只展示“本次会话接收流量”，不展示上传、请求数或代理商计费流量。
- 运行页顶栏账号身份区增加紧凑代理状态入口，详情展示非密代理摘要、浏览器实际出口、本机出口、验证时间与本次会话接收流量；密码永不回显，主列表不铺完整 IP。
- 首版保持现有无代理和探测异常的运行许可，不新增自动投产硬闸；明确异常以高优先级状态呈现，后续如需强制代理保护另立行为变更。

## Capabilities

### New Capabilities
- `proxy-runtime-observability`: 定义同一指纹浏览器会话的出口证明、接收流量统计、证据生命周期、无状态 Cloud 回显端点与诚实降级边界。

### Modified Capabilities
- `adspower-desktop-env-picker`: 将“创建成功不做运行时自检”的边界收窄为创建阶段不自检；Facebook 环境真正启动后允许按当前浏览器会话生成出口证据。
- `edge-fleet-console`: 在选中 Facebook 环境的顶栏账号身份区和详情浮层展示代理运行状态及本次会话接收流量，并在异常时保持可见。

## Impact

- `aidcp-edge`: CDP Network 观测器、出口探测、核心结构化 UI 事件、Electron fleet 状态投影、运行页 HTML/CSS/renderer 与测试。
- `aidcp-cloud`: 新增无状态出口回显 HTTP route、可信代理头解析/CORS/no-store 与聚焦测试；不新增数据库迁移。
- `aidcp`: 新增行为契约并修订既有 AdsPower 与 fleet UI 规范。
- 安全/隐私：不采集 URL、Cookie、请求正文或代理密码；只传递 IP、时间、状态和聚合字节数，浏览器探测请求不携带账号/环境标识。
