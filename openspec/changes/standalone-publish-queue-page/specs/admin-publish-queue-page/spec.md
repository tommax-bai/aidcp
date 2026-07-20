## ADDED Requirements

### Requirement: 发布队列 SHALL 是内容分组下的独立管理目的地

管理后台 SHALL 提供 `/publish-queue` 独立路由，并在“内容”一级分组中以“发布队列”标签呈现。`/content` SHALL 继续承载待审稿编辑、批准、驳回和发布历史，MUST NOT 再渲染发布队列主体或重复请求队列数据。

#### Scenario: 管理员从内容分组进入发布队列

- **WHEN** 已登录管理员选择内容分组中的“发布队列”
- **THEN** 控制台打开 `/publish-queue` 并保持“内容”分组和“发布队列”目的地为选中态

#### Scenario: 管理员进入内容页

- **WHEN** 已登录管理员打开 `/content`
- **THEN** 页面展示稿件审批与发布历史，不再在其上方展示发布队列主体

### Requirement: 独立页面 SHALL 先呈现可核实的运营摘要

发布队列页 SHALL 在队列详情之前分别呈现“活跃稿件”“等待人工”和“排队任务”数量。活跃稿件与等待人工 MUST 来自显式 lifecycle 投影，排队任务 MUST 仅统计发布动作族中 `queued`、`planning` 或 `deferred` 的任务。摘要 MUST NOT 把等待审批、执行中、已提交或终态记录计作尚未开跑的排队任务。

#### Scenario: 多份稿件处于不同状态

- **WHEN** lifecycle 含五份活跃稿件且其中一份为 `waiting_human`，委托查询含零份尚未开跑任务
- **THEN** 页面摘要显示“活跃稿件 5”“等待人工 1”“排队任务 0”

#### Scenario: 排队任务查询失败

- **WHEN** lifecycle 查询成功而排队任务查询失败
- **THEN** 活跃与等待人工摘要仍可查看，排队任务区域明确显示加载失败且不伪造为零

### Requirement: 页面 SHALL 分离活跃生命周期与尚未开跑任务

发布队列页 SHALL 允许管理员在多份活跃稿件之间切换，并为选中稿件呈现既有八阶段生命周期、账号与标题、可证实事实、阶段状态及原始字段折叠入口。尚未开跑的排队任务 SHALL 置于独立区域，MUST NOT 伪造成阶段已经开始；最近终态结果 MUST NOT 因 snapshot 仍存在而计入活跃稿件。

#### Scenario: 选中等待人工的稿件

- **WHEN** 管理员查看状态为 `waiting_human` 的活跃稿件
- **THEN** 人工审批阶段显示“等待人工”，平台下发显示“未开始”，页面不得声称已发布或已下发

#### Scenario: 没有活跃稿件但存在排队任务

- **WHEN** lifecycle 没有活跃稿件而发布委托查询返回排队任务
- **THEN** 页面明确显示暂无活跃稿件，并仍在独立排队任务区域展示任务真态

#### Scenario: 新旧 Cloud 版本切换

- **WHEN** `GET /api/content/queue` 不带 lifecycle 但仍带既有 runs 或 snapshot
- **THEN** 页面使用旧版回落视图继续展示可证实进度，且不会白屏或臆造新版生命周期状态

### Requirement: 等待人工 SHALL 回到内容页执行审批

发布队列页 MUST NOT 复制候选稿编辑、批准或驳回动作。对于等待人工的稿件，页面 SHALL 提供清晰的内容页审批入口；只有存在可靠 candidate 标识时才可构造精确记录定位，缺少该证据时 SHALL 回到待审内容列表而不得猜测记录。

#### Scenario: 生命周期没有可靠 candidate 标识

- **WHEN** 等待人工的 lifecycle item 只有稿件标题、账号和发布记录标识
- **THEN** 页面提供“去内容页审批”入口并打开待审内容列表，不根据标题或列表顺序猜测 candidate

