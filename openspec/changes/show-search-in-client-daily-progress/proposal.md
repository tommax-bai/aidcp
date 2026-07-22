## Why

Facebook 与小红书搜索已经是独立的账号级风险动作，但客户端「今日进展」的 Cloud 投影、协议清洗和渲染清单仍停留在搜索入账之前，导致搜索真实发生并占用配额后，客户仍看不到次数与上限。该缺口会让客户端与 Console、风控预闸和账号实际节奏互相矛盾。

## What Changes

- 将 `search` 加入 Cloud/Edge 客户端今日用量契约，覆盖当日别名以及 session/minute/hour/day 窗口的次数、上限与饱和状态。
- 由 Cloud 按账号平台投影搜索指标：Facebook 与小红书显示，视频号和未知平台不凭猜测增加新格子。
- 在 Electron「今日进展」中增加“搜索”格，排序在“浏览”之后，并让搜索参与节奏详情、配额休息与已完成提示。
- 保持环境级客户鉴权 HTTP 为今日进展的权威真源；自动化事件只触发刷新或本地短暂乐观更新，不建立第二套统计事实。
- 保持协议加性兼容；旧 Cloud/Edge 缺少 `search` 字段时继续按既有指标显示，不伪造搜索为 0 次已确认事实。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `platform-search-activity`: 将已确认搜索的账号用量与有效配额投影到支持平台的客户端今日进展和各窗口，未知/不支持平台保持缺席。
- `edge-companion-ui`: 将 Cloud 明确供给的 `search` 渲染为“搜索”进度项，并纳入节奏窗口与完成状态计算。

## Impact

- Control：更新 `platform-search-activity` 与 `edge-companion-ui` 规范。
- Cloud：更新 UI daily-usage 协议枚举、平台能力声明、账号 HTTP/快照用量投影、session 搜索预算映射及测试。
- Edge：同步协议枚举，更新 daily-usage 清洗、Electron 静态结构、渲染与完成状态优先级及测试。
- 部署：Cloud 需部署到 `dev`；Edge 源码需合入并推送。桌面安装包不在本次默认授权范围内。
