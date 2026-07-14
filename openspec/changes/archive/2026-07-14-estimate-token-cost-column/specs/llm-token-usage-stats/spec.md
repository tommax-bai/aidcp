## ADDED Requirements

### Requirement: Token Usage Cost Estimates

系统 SHALL 在 token 用量视图里给出**估算成本**，且该估算 MUST 由**厂商账单反算**而来，MUST NOT 依赖任何硬编码的公开模型价目表。

- 云端 MAY 用「账单派生的内部价格快照 × 该行 token 数」估算某一行的成本。
- 账单派生的价格快照 SHALL 至少按 **provider、model、用量日**三键索引。
- console MUST NOT 用硬编码的公开模型价目表估算成本，MUST NOT 在前端按厂商公开报价本地计算成本。
- 成本估算 SHALL 诚实暴露其来源 / 日期，使运营 MUST NOT 把它误当成厂商的实时官方报价。
- 无匹配账单派生价格快照的行 MUST 保留「估算成本」列（不隐藏该列），并显示诚实的 pending / 空态，MUST NOT 用任何兜底价 / 猜测价填充。

#### Scenario: 无账单派生数据时诚实 pending

- **WHEN** 某用量行没有可用的账单派生价格
- **THEN** `/usage` 仍显示「估算成本」列
- **AND** 该行显示诚实的 pending / 空态
- **AND** console MUST NOT 显示任何硬编码 / 公开价目表推算出的金额

#### Scenario: 有账单派生快照时显示金额并暴露来源

- **WHEN** 云端存在与某用量行的 provider、model、用量日相匹配的账单派生价格快照
- **THEN** 用量查询接口为该行返回估算成本
- **AND** `/usage` 在「估算成本」列显示该金额
- **AND** 界面暴露该估算的来源 / 日期

## MODIFIED Requirements

### Requirement: console 提供 token 用量表格 + 10 分钟曲线页

管理后台 SHALL 新增「用量」页（路由 `/usage`），展示 token 消耗的四维表格与每 10 分钟曲线。

- 表格 SHALL 含列：日期、账号、角色、模型、输入 token、输出 token、**总 token（醒目主列）**、**估算成本**、调用次数；空区间 SHALL 显式空态提示（非空白）。
- 「估算成本」列的取数与诚实态 SHALL 遵循 `Token Usage Cost Estimates`（账单派生、无快照即 pending、绝不用公开价目表）。
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

#### Scenario: 新增成本列不挤破既有能力

- **WHEN** 「估算成本」列加入表格后运营照常使用日期范围 / 账号 / 角色 / 模型筛选与 10 分钟曲线
- **THEN** 上述能力照旧生效，MUST NOT 因新增列而丢失筛选、曲线、中文角色标签或空态提示
