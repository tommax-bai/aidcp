## ADDED Requirements

### Requirement: XHS client SHALL expose a compact publish summary and full queue

客户端 SHALL 只在当前环境平台明确为小红书时，将运行首页现有单记录发布区域升级为“发布进度”摘要，并允许客户在同一主窗口内容工作区打开完整发布队列。摘要 SHALL 展示可证实的活跃总数、待客户处理数量和最需要处理的一条内容；全页 SHALL 分离需要客户处理、系统处理中和尚未开跑的任务与最近终态。视频号、Facebook 或平台未知环境 MUST NOT 展示或请求该队列。

#### Scenario: 小红书环境存在多条并行内容

- **WHEN** 当前小红书环境同时有一条待确认稿、两条系统处理中内容和一条尚未开跑任务
- **THEN** 首页摘要显示四条进行中与一条待确认，点击后全页分别展示对应内容且不隐藏同环境其它任务

#### Scenario: 首页逐条查看进行中内容

- **WHEN** 当前小红书环境有两条 active 与一条 queued task
- **THEN** 展开态首页卡可通过左右按钮循环查看三条内容，并始终显示当前项的标题、客户状态和可证实阶段；该切换只改变本地展示，不改变 Cloud 队列或任务顺序

#### Scenario: 首页待确认卡复用完整队列的视觉层级

- **WHEN** 当前轮播项是 waiting approval 稿件
- **THEN** 首页以发布摘要、当前任务卡、四阶段状态和主次操作的层级展示，不出现无真实内容的图片占位；当前项提供主操作“审核稿件”，完整队列入口保持次级

#### Scenario: 首页先展示今日进展再展示发布内容

- **WHEN** 当前环境的今日进展与发布摘要同时可见
- **THEN** 客户端在页面和辅助技术阅读顺序中均先呈现完整“今日进展”卡，再呈现内容发布卡，且两张卡的状态与操作保持原有语义

#### Scenario: 切换到非小红书环境

- **WHEN** 客户在发布队列页切换到视频号、Facebook 或平台未知环境
- **THEN** 客户端立即关闭发布队列回到新环境运行首页，清除旧环境内容且不为新环境请求队列

### Requirement: Queue SHALL separate queued tasks, active lifecycle, and recent terminal truth

发布队列 SHALL 将 `queued / planning / deferred` 发布委托展示为尚未进入或尚未完成进入发布生命周期的任务，将生成中、等待审批和下发中的内容展示为 active，将已发布、已提交待确认、失败、驳回、草稿或跳过等最近结果展示为 recent。客户端 MUST NOT 把列表顺序描述为精确队列名次，MUST NOT 因存在旧 snapshot 将终态重新算作 active，并 MUST NOT 将 `submitted` 描述为已发布。

#### Scenario: 已提交平台但链接未确认

- **WHEN** Cloud 返回一条状态为 `submitted` 的最近内容
- **THEN** 客户端显示“平台确认中”并说明无需重复操作，不显示“已发布”或完成全部发布结果

#### Scenario: 尚未开跑任务与活跃生命周期并存

- **WHEN** 同一环境既有 `queued` 委派任务也有生成中的 lifecycle journey
- **THEN** 客户端把前者显示为“排队中”、后者显示为“创作中”，不得把 queued 任务伪造成已经进入正文或配图阶段

### Requirement: Customer progress SHALL use truthful four-stage semantics

客户端 SHALL 以“开始创作、正文与配图、发布确认、发布结果”四阶段展示客户进度，但每一阶段状态 MUST 只由 Cloud 显式生命周期投影映射。当前阶段有可证实数量时 SHALL 展示，例如配图 `2/4`；“发布确认”处于 `waiting_human` 时 SHALL 显示“待你确认”，完成时 SHALL 显示“已确认”；“发布结果”尚未开始时 SHALL 显示“等待发布”。缺少状态证据时 SHALL 显示未知或未开始，不得根据等待时长、字段存在或页面顺序推断完成。

#### Scenario: 等待人工确认

- **WHEN** lifecycle 明确显示审批阶段为 `waiting_human` 且下发阶段为 `pending`
- **THEN** 客户端显示“发布确认”为当前阶段及“待你确认”，显示“发布结果”为“等待发布”，并提供现有稿件审核入口

### Requirement: Queued publish tasks SHALL be individually cancellable

客户端 SHALL 为当前环境中状态为 `queued / planning / deferred` 且未设置 `cancelRequested` 的每条发布任务提供独立“取消任务”入口。客户确认时 SHALL 只提交该任务的 id 与页面所见 version；关闭确认 SHALL 不发送请求。生命周期稿件和平台下发记录 MUST NOT 通过该入口取消。

#### Scenario: 客户取消尚未开跑任务

- **WHEN** 客户确认取消一条 `queued` 任务且 Cloud 返回终态 `cancelled`
- **THEN** 客户端提示任务已取消、刷新完整队列，并只在 Cloud 刷新真态后将该任务移出可取消区域

#### Scenario: 客户取消规划中任务

- **WHEN** 客户确认取消一条 `planning` 任务且 Cloud 返回 `cancelRequested=true` 的非终态
- **THEN** 客户端显示“取消中”和“将在安全边界停止”，禁用重复取消且不得宣称任务已经停止

#### Scenario: 任务版本已经变化

- **WHEN** Cloud 因 version 冲突拒绝取消
- **THEN** 客户端说明任务状态已经变化并刷新当前队列，不自动使用新版本重试写入

### Requirement: Queue reads SHALL survive browser and engine inactivity

发布队列读取与取消 SHALL 通过客户鉴权 HTTP 完成，与浏览器、自动化引擎和 WebSocket 生命周期解耦。客户端 SHALL 在环境切换、打开页面、窗口聚焦和有界轮询时按当前环境刷新；自动化事件 MAY 触发失效重读，但 MUST NOT 直接覆盖 Cloud HTTP 已确认数据。迟到的旧环境响应 MUST 被丢弃。

#### Scenario: 浏览器未启动时查看队列

- **WHEN** 客户已登录客户端并选择已授权小红书环境，但该环境浏览器与自动化引擎未启动
- **THEN** 客户端仍通过客户 HTTP 读取并展示该环境队列，不要求先启动浏览器

#### Scenario: 读取失败不伪装为空队列

- **WHEN** 当前环境首次队列读取失败或 Cloud 尚未确认绑定
- **THEN** 客户端显示明确不可用或绑定待确认状态，不显示“暂无任务”或零计数
