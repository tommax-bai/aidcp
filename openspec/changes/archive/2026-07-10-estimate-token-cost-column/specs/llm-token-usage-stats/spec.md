## MODIFIED Requirements

### Requirement: console 提供 token 用量表格 + 10 分钟曲线页

管理后台 SHALL 提供 `/usage` 页，展示 token 消耗的四维表格与每 10 分钟曲线。

- 表格 SHALL 含列：日期、账号、角色、provider/model、输入 token、输出 token、**总 token（醒目主列）**、估算成本、调用次数。
- Console MUST NOT 从硬编码公开模型价目表估算 token 成本，也 MUST NOT 在前端用 provider 公开 list price 本地换算成本。
- Cloud MAY 用 billing-derived 内部价格快照乘以该行 token 量生成估算成本；价格快照 MUST 至少按 provider、model、usage day 建键。
- 成本估算 MUST 如实暴露来源/日期，避免运营把它误认为实时 provider 价目表。
- 没有匹配 billing-derived 价格快照的行 MUST 保持估算成本列可见，并显示诚实的待定/空态，不得使用 fallback 价格。
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

#### Scenario: 无 billing-derived 数据时成本待定

- **WHEN** 某用量行没有匹配的 billing-derived 价格快照
- **THEN** `/usage` 仍显示估算成本列
- **AND** 该行显示诚实的待定/空成本状态
- **AND** console 不显示硬编码或公开 list price 估算

#### Scenario: 显示 billing-backed 估算成本

- **WHEN** cloud 有匹配该行 provider、model 与日期的 billing-derived 价格快照
- **THEN** `/api/llm-usage` 返回该行估算成本
- **AND** `/usage` 在估算成本列显示金额
- **AND** UI 暴露估算来源/日期
