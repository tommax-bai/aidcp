## MODIFIED Requirements

### Requirement: console 提供 token 用量表格 + 10 分钟曲线页

管理后台 SHALL 新增「用量」页（路由 `/usage`），展示 token 消耗的四维表格与每 10 分钟曲线。

- 表格 SHALL 含列：日期、账号、角色、模型、输入 token、输出 token、**总 token（醒目主列）**、**预估成本**、调用次数；空区间 SHALL 显式空态提示（非空白）。
- 预估成本 SHALL 位于「总 token」之后，按该行输入 token / 输出 token 分别乘以内置公开刊例单价后求和，并以人民币元展示近似值。
- 预估成本 SHALL 是运营量级估算而非财务账单：MUST NOT 扣减免费额度、资源包、Batch 折扣、缓存命中、合同折扣或区域价差；未知模型或缺单价时 SHALL 显示空值，MUST NOT 用总 token 伪造平均价。
- 曲线 SHALL 为单条总量线（每 10 分钟一点），受页面筛选器（账号 / 角色 / 模型）约束，时间轴 SHALL 显式按 `Asia/Shanghai` 渲染（不依赖浏览器本地时区）。
- 页面 SHALL 提供日期范围选择与账号 / 角色 / 模型筛选。
- 角色列 SHALL 把原始内部 tag（如 `browse:content_evaluator` / `publish:TitleCreator` / `system:model_probe` / `untagged`）映射为人类可读中文标签展示（PG 仍存原 tag 做稳定键）；未知 tag SHALL 回落去前缀的可读形，MUST NOT 直露内部 tag 串。
- 账号维度今天为单值 `default`：console SHALL 显式标注其为单租户（如「默认账号（单租户）」提示「多账号上线后按真实账号拆分」），MUST NOT 让运营误判统计损坏。

#### Scenario: 查看用量表与曲线

- **WHEN** 运营打开 `/usage`
- **THEN** 默认展示近 24 小时的总量曲线（每 10 分钟）与按四维聚合的表格，总 token 列醒目
- **AND** 每个已知模型行在总 token 之后显示按输入 / 输出 token 粗算的预估成本

#### Scenario: 未知模型不伪造成本

- **WHEN** 表格行的模型名没有内置公开单价
- **THEN** 预估成本列显示空值
- **AND** console MUST NOT 用总 token 或任意平均价推导一个看似精确的成本

#### Scenario: 角色显示中文标签

- **WHEN** 表格渲染某行角色为 `browse:content_evaluator`
- **THEN** 显示「内容评估」式中文标签，而非原始 `browse:content_evaluator` 串

#### Scenario: 筛选驱动曲线

- **WHEN** 运营在筛选器选定某角色
- **THEN** 曲线变为该角色的总量线，表格相应收窄

#### Scenario: 空区间显式空态

- **WHEN** 所选区间无任何用量
- **THEN** 表格与图各显示「暂无数据」，而非空白或报错
