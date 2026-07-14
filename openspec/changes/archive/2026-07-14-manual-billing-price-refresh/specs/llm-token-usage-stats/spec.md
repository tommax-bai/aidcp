## MODIFIED Requirements

### Requirement: Token Usage Cost Estimates

系统 SHALL 在 token 用量视图里给出**估算成本**，且该估算 MUST 由**厂商账单反算**而来，MUST NOT 依赖任何硬编码的公开模型价目表。账单派生价格由**运营手动触发的一次性刷新动作**采集，MUST NOT 做成定时任务。

- 云端 MAY 用「账单派生的内部价格快照 × 该行 token 数」估算某一行的成本。
- 账单派生的价格快照 SHALL 至少按 **provider、model、用量日**三键索引。
- console MUST NOT 用硬编码的公开模型价目表估算成本，MUST NOT 在前端按厂商公开报价本地计算成本。
- 成本估算 SHALL 诚实暴露其来源 / 日期，使运营 MUST NOT 把它误当成厂商的实时官方报价。
- **当某 provider/model 当日无价格快照时，云端 SHALL 回落到该 provider/model 的「最新可用历史账单派生价」**，MUST NOT 仅因当日缺样本就把该行判为 pending。
- 面板 SHALL 提供一个**手动**刷新动作：按近期实际用到的模型，去查询厂商 **T-1 / T-2** 的账单明细样本，反算出单价并写成快照。
- 该刷新动作 MUST NOT 被实现为定时任务 / cron / 后台 worker——它只由运营在面板上显式触发。
- 某 provider/model **从无任何历史账单派生价**时，其行 MUST 保留「估算成本」列（不隐藏该列）并显示诚实的 pending / 空态，MUST NOT 用任何兜底价 / 猜测价填充。

#### Scenario: 无账单派生数据时诚实 pending

- **WHEN** 某 provider/model 从无任何账单派生价格快照
- **THEN** `/usage` 仍显示「估算成本」列
- **AND** 该行显示诚实的 pending / 空态
- **AND** console MUST NOT 显示任何硬编码 / 公开价目表推算出的金额

#### Scenario: 有账单派生快照时显示金额并暴露来源

- **WHEN** 云端存在与某用量行的 provider、model、用量日相匹配的账单派生价格快照
- **THEN** 用量查询接口为该行返回估算成本
- **AND** `/usage` 在「估算成本」列显示该金额
- **AND** 界面暴露该估算的来源 / 日期

#### Scenario: 手动刷新反算出单价并写入快照

- **GIVEN** 厂商 T-1 或 T-2 的账单明细里含某 provider/model 的 token 计费行
- **WHEN** 运营触发面板上的「更新厂商模型定价」动作
- **THEN** 云端用「账单金额 ÷ 账单 token 数」反算出有效单价
- **AND** 将结果写为账单派生价格快照
- **AND** 后续用量查询 MAY 用该价格为匹配的 provider/model 行出成本

#### Scenario: 当日无新账单样本时复用最新历史价

- **GIVEN** 某 provider/model 已有一次早前刷新留下的账单派生价格快照
- **AND** T-1 与 T-2 的账单明细里没有该 provider/model 的新样本
- **WHEN** 用量查询返回该 provider/model 的行
- **THEN** 云端用其**最新可用历史**账单派生价估算成本
- **AND** 该行 MUST NOT 仅因「近期账单缺样本」而显示 pending
