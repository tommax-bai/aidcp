## Context

`search` 已进入 Cloud `RiskAction`、三窗口/自然日配额、PG 计数和 Console，但客户端今日进展仍使用旧的七键 `UI_DAILY_USAGE_ACTIONS`。Cloud 的 `pickDailyUsageCounts` 因此在客户 HTTP 与兼容 `ui.snapshot` 的共同构造入口就丢弃 search；Edge 的 TypeScript/CJS 清洗白名单、静态 KPI 节点、渲染清单和完成优先级也都没有 search。当前症状不是单纯安装包版本偏旧：即使按现有 master 重打包，搜索仍不可见。

今日进展的权威读面是环境级客户鉴权 HTTP，浏览器与自动化 WebSocket 仅提供任务执行和失效提示。实现必须保持这条数据面边界，并保持旧 Cloud/Edge 对新增可选键的兼容。

## Goals / Non-Goals

**Goals:**

- 在 Facebook 与小红书客户端今日进展中显示 Cloud 已确认的搜索次数与有效上限。
- 让 search 贯穿 daily alias 以及 session/minute/hour/day 窗口的次数、配额、饱和与恢复口径。
- 保持 Cloud 平台投影决定指标是否存在，Edge 不根据本地平台标签重建第二张能力表。
- 保持 HTTP 真源、协议加性兼容与旧客户端缺键降级。
- 用跨 Cloud/Edge 的枚举与穿透测试阻止“云端发送、客户端静默丢弃”再次发生。

**Non-Goals:**

- 不改变搜索风险配额数字、搜索执行回执或既成事实记账语义。
- 不补记旧 Edge 无法证明的历史搜索，也不把命令下发数冒充平台搜索数。
- 不重做今日进展布局、不调整其他动作的 `0/0` 或完成提示语义。
- 不构建或发布桌面安装包。

## Decisions

### D1. `UI_DAILY_USAGE_ACTIONS` 是跨 Cloud/Edge 的投影全集

在两份协议的 `UI_DAILY_USAGE_ACTIONS` 中把 `search` 放在 `view` 之后。Cloud 的计数物化、配额物化、饱和计算和客户 HTTP/快照共享该集合；Edge 的 TypeScript 投影与 CJS 清洗手工镜像同一顺序，并以测试逐位对齐。

备选方案是在客户端单独读取风险动作全集。该方案会绕过平台投影、把后台内部动作泄到客户界面，并制造第二个数据源，因此拒绝。

### D2. 搜索指标由平台 registry 显式声明，未知平台保持缺席

给平台 registry 增加仅由客户端指标投影消费的 `search` 编排能力声明：小红书与 Facebook 为支持，视频号为不支持。`USAGE_METRIC_SUPPORT_SOURCE.search` 使用 `statusQuo=absent`，只有显式支持的平台才增加新格；平台未知、查表失败或未来未声明平台均维持缺席。

备选方案是硬编码 `platform === 'xhs' || platform === 'facebook'`，或把 search 当作既有 supplied 指标 fail-open。前者复制平台矩阵，后者会让未知/视频号账号凭空出现搜索格，均拒绝。

### D3. 四个窗口分别使用其真实来源

minute/hour/day 从 `risk_counters.search` 读取。session 仍使用连接运行时的单场预算统计，并在现有复数键映射中加入 `search <- searches`，使“本轮计划”不把日累计冒充单场累计。各窗口均先物化、再做平台投影，避免被摘掉的键重新补成 `0/0`。

### D4. Edge 只渲染 Cloud 明确供给的 search

Electron 增加静态“搜索”格与 renderer 字段，`USAGE_ITEMS` 和配额优先级把 search 放在 view 后。Cloud 明确供给 `search: 0` 时显示 `0/上限`；字段缺席时整格隐藏。search 不使用本机 stats 回落，因为本机日志无法替代 Cloud 对 `actuated=true` 终态的一次性消费。

### D5. HTTP 继续是权威真源

客户环境 overview 继续调用共享的 `buildTodayUsageForAccount`。自动化事件或旧 `ui.snapshot` 只可触发/加速刷新，不能覆盖 HTTP 已确认用量；浏览器停止、引擎停止或 Edge 离线时，最近一次 Cloud 已确认 search 仍可展示并带既有新鲜度语义。

## Risks / Trade-offs

- [Cloud 先升级而旧 Edge 忽略新键] → 字段是可选加性键，旧 Edge 保持既有七项，不崩溃。
- [Edge 先升级而旧 Cloud 不发 search] → 清洗与渲染按供给键工作，搜索格保持缺席，不伪造 0。
- [平台声明漏配导致静默隐藏] → registry 全覆盖类型、FB/XHS/视频号投影单测和 Electron 穿透测试共同约束。
- [session 使用错误键导致窗口始终为 0] → 明确测试 `searches -> search` 映射，并同时断言四窗口。
- [源码已交付但已安装客户端仍不显示] → 交付证据明确区分 Edge 源码与安装包；本变更不宣称客户端已升级。

## Migration Plan

1. 先合入并部署兼容 Cloud，使客户 HTTP/旧快照开始可选供给 search。
2. 合入 Edge 源码；旧安装包忽略新增键，新源码客户端在收到键后显示。
3. 在 `dev` 验证 Cloud 客户 HTTP 投影、服务健康和平台过滤；不把没有新版在线 Edge 解释为桌面真机通过。
4. 回滚时恢复 Cloud/Edge 前一默认提交；无数据库迁移、无数据回滚。

## Open Questions

无。桌面安装包发布需用户另行明确授权。
