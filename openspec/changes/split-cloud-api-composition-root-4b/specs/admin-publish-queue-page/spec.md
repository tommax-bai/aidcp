## MODIFIED Requirements

### Requirement: 页面 SHALL 分离活跃生命周期与尚未开跑任务

发布队列页 SHALL 先按账号归组有可靠证据的活跃稿件，并在横向账号选择区中只显示账号名称；
账号超出可视宽度时该区域 MUST 支持横向滚动或触摸滑动。选择账号后，下方内容区域 SHALL 直接排列
该账号的全部活跃稿件，并为每份稿件呈现既有八阶段生命周期、标题、可证实事实和阶段状态，
MUST NOT 再以第二层任务下拉隐藏同账号的其它活跃稿件。页面 MUST NOT 展示原始 snapshot 字段折叠入口。
尚未开跑的排队任务 SHALL 置于独立且只出现一次的区域，MUST NOT 伪造成阶段已经开始；
最近终态结果 MUST NOT 因 snapshot 仍存在而计入活跃稿件。

Cloud 明确返回 `inFlightEvidence.state=unknown|stale|invalid` 时，页面 SHALL 显示“下发状态暂不可用”；
对缺少 durable dispatch 证明的受影响稿件，MUST NOT 根据空 in-flight 集合把它归为等待人工、未下发或
正在下发，也 MUST NOT 把证据不可用计作零条活跃稿件。

#### Scenario: 多账号横向切换并展示账号全部任务

- **WHEN** lifecycle 同时包含账号甲的三份可靠活跃稿件和账号乙的一份可靠活跃稿件
- **THEN** 页面账号选择区只显示账号甲、账号乙
- **AND** 选择账号甲后直接展示其三份稿件且不展示账号乙稿件

#### Scenario: 账号超出页面宽度

- **WHEN** 活跃账号数量使账号选择项总宽度超过可视区域
- **THEN** 账号选择区保持单行并可横向滚动或触摸滑动
- **AND** 页面主体不得被选择项撑出视口

#### Scenario: 原始字段不再展示

- **WHEN** lifecycle journey 或旧版聚合快照包含额外 raw 字段
- **THEN** 页面只消费其可证实生命周期摘要
- **AND** 不呈现“原始字段”入口或 raw 字段正文

#### Scenario: 选中等待人工的稿件

- **WHEN** durable/fresh lifecycle 证据证明稿件为 `waiting_human`
- **THEN** 人工审批阶段显示“等待人工”，平台下发显示“未开始”
- **AND** 页面不得声称已发布或已下发

#### Scenario: 下发证据不可用

- **WHEN** lifecycle item 缺少 durable dispatch 证明且 `inFlightEvidence.state` 不 fresh
- **THEN** 页面显示“下发状态暂不可用”而不是等待人工、未下发或正在下发
- **AND** 摘要 MUST NOT 把该不确定项计成零或确定状态

#### Scenario: 没有活跃稿件但存在排队任务

- **WHEN** lifecycle 确认没有活跃稿件而发布委托查询返回排队任务
- **THEN** 页面明确显示暂无活跃稿件
- **AND** 仍在独立排队任务区域展示任务真态

#### Scenario: 新旧 Cloud 版本切换

- **WHEN** `GET /api/content/queue` 不带 lifecycle 但仍带既有 runs 或 snapshot
- **THEN** 页面使用旧版回落视图继续展示可证实进度
- **AND** 不会白屏或臆造新版 lifecycle/in-flight evidence
