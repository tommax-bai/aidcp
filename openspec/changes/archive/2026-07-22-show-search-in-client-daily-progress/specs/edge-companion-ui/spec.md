## ADDED Requirements

### Requirement: 客户端今日进展将搜索作为独立进度项

Electron SHALL 在 Cloud 为当前账号明确供给 `search` 今日用量时，以“搜索”独立进度项呈现真实次数与当前有效上限，并将其排序在“浏览”之后、点赞等互动之前。search SHALL 参与节奏详情窗口、配额饱和、休息与计划完成判断；MUST NOT 合并进浏览、评论或其他动作。

#### Scenario: Facebook 显示搜索零次和有效计划

- **WHEN** 客户端收到 Facebook 账号 `totals.search=0` 且 `quotas.search=10`
- **THEN** 今日进展在浏览之后显示“搜索 0/10”，而不是隐藏、并入浏览或显示为未知动作

#### Scenario: 搜索达到上限参与完成提示

- **WHEN** Cloud 投影某一有效窗口 `search` 已达到正数上限并标为 saturated
- **THEN** 客户端把搜索纳入该窗口完成状态，并使用“搜索”标签生成既有完成/休息语义

#### Scenario: 搜索窗口详情保持逐窗真实值

- **WHEN** session、minute、hour、day 的 search 次数或上限不同
- **THEN** 展开今日节奏后每个窗口分别显示 Cloud 提供的 search 值，不用 day alias 覆盖其他窗口

### Requirement: 搜索格对旧端和缺席字段保持加性兼容

Electron SHALL 仅渲染 Cloud 明确供给的 `search` 键。旧 Cloud 未供给 search、平台投影摘除 search 或客户 HTTP 首次读取尚未成功时，客户端 MUST 保持搜索格缺席，不得凭本机平台标签、搜索日志或缺字段补成 `0/0`；已取得的 HTTP 确认真态 SHALL 沿用既有缓存与新鲜度语义，不依赖浏览器或引擎在线。

#### Scenario: 旧 Cloud 缺少搜索键时保持既有布局

- **WHEN** Electron 收到不含 search 的旧版 dailyUsage
- **THEN** 既有指标继续显示且搜索格保持缺席，界面不报错

#### Scenario: Cloud 明确供给零次时仍显示

- **WHEN** dailyUsage 明确包含 `search=0` 和正数有效上限
- **THEN** 客户端显示搜索格，因为供给的零是真实观测而不是字段缺失

#### Scenario: 自动化停止不清空 HTTP 搜索真态

- **WHEN** 客户端已通过环境级客户鉴权 HTTP 取得 search 用量，随后浏览器或自动化停止
- **THEN** 今日进展保留该 Cloud 确认值并按既有规则标记新鲜或陈旧，不回退成本机猜测
