## MODIFIED Requirements

### Requirement: console 提供 token 用量表格 + 10 分钟曲线页

管理后台 SHALL 提供 `/usage` 页，展示 token 消耗的四维表格与每 10 分钟曲线，并在明细表中显示仅由 billing-derived 数据支持的估算成本。

- 表格 SHALL 含列：日期、账号、角色、provider/model、输入 token、输出 token、**总 token（醒目主列）**、估算成本、调用次数。
- Console MUST NOT 从硬编码公开模型价目表估算 token 成本，也 MUST NOT 在前端用 provider 公开 list price 本地换算成本。
- Cloud MAY 用 billing-derived 内部价格快照乘以该行 token 量生成估算成本；价格快照 MUST 至少按 provider、model、usage day 建键。
- 当没有同日价格时，Cloud SHALL 使用同一 provider/model 的最新可用 billing-derived 历史价格。
- 面板 SHALL 提供一个手动动作，通过查询最近已用模型的 T-1 / T-2 provider billing samples 刷新 provider/model 价格。
- 手动刷新 MUST NOT 实现为 scheduled task、cron job 或 background worker。
- 成本估算 MUST 如实暴露来源/日期，避免运营把它误认为实时 provider 价目表。
- 对没有任何历史 billing-derived 价格的 provider/model 行，估算成本列 MUST 保持可见并显示诚实的待定/空态。
- 曲线 SHALL 为单条总量线（每 10 分钟一点），受页面筛选器（账号 / 角色 / 模型）约束，时间轴 SHALL 显式按 `Asia/Shanghai` 渲染（不依赖浏览器本地时区）。
- 页面 SHALL 提供日期范围选择与账号/角色/模型筛选。
- 角色列 SHALL 把原始内部 tag（如 `browse:content_evaluator` / `publish:TitleCreator` / `system:model_probe` / `untagged`）映射为人类可读中文标签展示（PG 仍存原 tag 做稳定键）；未知 tag SHALL 回落去前缀的可读形，MUST NOT 直露内部 tag 串。
- 账号维度今天为单值 `default`：console SHALL 显式标注其为单租户（如「默认账号（单租户）」+ 提示「多账号上线后按真实账号拆分」），MUST NOT 让运营误判统计损坏。

#### Scenario: 查看用量表与曲线

- **WHEN** 运营打开 `/usage`
- **THEN** 默认展示近 24 小时的总量曲线（每 10 分钟）与按四维聚合的表格，总 token 列醒目

#### Scenario: 角色显示中文标签

- **WHEN** 表格渲染某行角色为 `browse:content_evaluator`
- **THEN** 显示「内容评估」式中文标签，而非原始 `browse:content_evaluator` 串

#### Scenario: 筛选驱动曲线

- **WHEN** 运营在筛选器选定某角色
- **THEN** 曲线变为该角色的总量线，表格相应收窄

#### Scenario: 空区间显式空态

- **WHEN** 所选区间无任何用量
- **THEN** 表格与图各显示「暂无数据」，而非空白或报错

#### Scenario: 手动价格刷新更新估算成本

- **GIVEN** T-1 or T-2 billing details contain a provider/model token charge
- **WHEN** an operator triggers the manual provider model pricing refresh
- **THEN** cloud derives an effective token price from billed amount and billed tokens
- **AND** stores the result as a billing-derived price snapshot
- **AND** subsequent `/api/llm-usage` responses may use that price for matching provider/model rows.

#### Scenario: 缺少近期 billing sample 时复用历史价格

- **GIVEN** a provider/model already has a billing-derived price snapshot from an earlier refresh
- **AND** T-1 and T-2 billing details contain no new sample for that provider/model
- **WHEN** `/api/llm-usage` returns rows for that provider/model
- **THEN** cloud estimates cost using the latest available historical billing-derived price
- **AND** the row does not show pending solely because recent billing data is absent.

#### Scenario: 无历史 billing 价格时保持待定

- **GIVEN** a provider/model has no billing-derived price snapshot
- **WHEN** `/api/llm-usage` returns rows for that provider/model
- **THEN** `/usage` still shows the estimated-cost column
- **AND** that row shows an honest pending/empty cost state.
