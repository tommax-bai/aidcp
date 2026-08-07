## MODIFIED Requirements

### Requirement: 已确认搜索进入支持平台的客户端今日进展

Cloud SHALL 将已按 `actuated=true` 一次性记入账号 `search` 风险事实的搜索，投影到该账号环境级客户鉴权 HTTP 今日进展，并 MAY 同步出现在兼容 `ui.push_snapshot.dailyUsage` 中。投影 SHALL 包含 day alias 以及 session、minute、hour、day 窗口中真实可得的搜索次数、有效上限、饱和状态和恢复时间；MUST NOT 使用命令下发次数、关键词尝试账或旧 Edge 的未确认搜索补造计数。

#### Scenario: Facebook 今日搜索显示真实次数与上限

- **WHEN** Facebook 账号今日已有 2 次已确认搜索且当前有效 day 上限为 10
- **THEN** 客户 HTTP 今日进展的 totals 与 day window 均包含 `search=2`，day quota 包含 `search=10`

#### Scenario: 离线查看仍读取 Cloud 已确认搜索

- **WHEN** 账号已有已确认搜索，但对应浏览器、自动化引擎或 Edge 当前离线
- **THEN** 客户端仍可通过环境级客户鉴权 HTTP 读取最近的 Cloud 已确认 search 今日进展

#### Scenario: 未确认搜索不进入客户端用量

- **WHEN** Cloud 只下发过搜索命令，或旧 Edge 未提供可消费的 `actuated=true` 终态
- **THEN** 系统不因该下发或未知状态增加客户端 search 次数
