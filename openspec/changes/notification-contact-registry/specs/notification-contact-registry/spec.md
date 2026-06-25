## ADDED Requirements

### Requirement: 通知发送者在到达处诚实捕获（含主页ID稳定身份）

系统 SHALL 在每连接通知项到达处（`notification.items.arrived`）捕获每一个**给本账号发过通知的人**，按连接真实账号归属，记录其昵称、主页ID（若可得）、加入原因（通知类型）、内容（评论类）、首次扫到时间。

- **身份标识**：捕获 SHALL 优先用边缘抽取的主页ID（`fromUserId`）作「人」的稳定身份；缺主页ID 时退回昵称；再缺退回事件去重键。
- **边轻云重（红线）**：边缘 MUST 只做结构化只读抽取与上报，MUST NOT 做任何决策、过滤判定或持久化；归属、去重、落库、聚合全在云端。
- **诚实缺失（红线）**：昵称 / 主页ID 缺失时 SHALL 如实留空，MUST NOT 伪造昵称、MUST NOT 用占位顶替；结构异常（昵称与内容皆空且无稳定锚点）的行 SHALL 丢弃而非记成空联系人。
- **记账不拖垮巡视（红线）**：记录 SHALL 被 try/catch 包住，其慢 / 失败 / 异常 MUST NOT 阻塞、抛进或拖垮通知巡视；失败 SHALL 只吞并打**准确**日志，MUST NOT 冒充飞书发送失败、MUST NOT 阻断清零。
- **零回归**：协议新增的可选字段（`NotificationItem.fromUserId?`、扩展的 `kind`）MUST NOT 改变既有调用方在评论/@ 路径上的现有行为。

#### Scenario: 评论/@ 发送者按账号记录（零边缘行为回归）

- **WHEN** 边缘巡视「评论和@」抽到评论/@ 项并经 `notification.items` 上报
- **THEN** 云端按连接真实账号记下发送者昵称、主页ID（若有）、原因（comment/mention）、内容、首次扫到时间；既有评论/@ 上报与清零行为不变

#### Scenario: 缺主页ID退回昵称、缺昵称如实留空

- **WHEN** 某通知项抽不到主页ID
- **THEN** 身份退回昵称；若昵称也为空，则身份退回事件去重键、昵称字段如实留空，MUST NOT 伪造昵称

#### Scenario: 记账失败不拖垮巡视、不冒充飞书失败

- **WHEN** 记录联系人时存储写入抛错
- **THEN** 异常被吞并打准确日志（标明是联系人记录失败、巡视照常），巡视清零与飞书通知路径不受影响，MUST NOT 记成飞书发送失败

### Requirement: 点赞 / 收藏 / 关注发送者由边缘从通知页抽取上报（保清零）

边缘 SHALL 在巡视「赞和收藏」「新增关注」分类时，除「看一眼清未读」外，**抽取发送者并经 `notification.items` 上报**，使点赞 / 收藏 / 关注者也能进入联系人名册。

- 抽取 SHALL 复用既有 code-point 安全截断；缺字段诚实留空，MUST NOT 回退整行 textContent。
- 抽取 MUST NOT 改变 notification-clear-to-zero 的清零结果 —— 抽取是清零过程中的旁路只读输出，分类未读最终仍须清至 0。
- 协议 `NotificationItem.kind` SHALL 扩为 `comment|mention|like|collect|follow`；点赞/收藏带目标笔记标题（若可得），关注无笔记。
- 两栏的真实行 DOM 结构与主页ID解析 SHALL 经真机校准后再信任（校准前宁可少抽不可瞎猜）。

#### Scenario: 点赞者进入名册

- **WHEN** 边缘巡视「赞和收藏」分类
- **THEN** 在清未读的同时抽取每条点赞/收藏的发送者（昵称 + 主页ID + 目标笔记标题若有）并上报，云端记为原因 like/collect 的联系人

#### Scenario: 关注者进入名册

- **WHEN** 边缘巡视「新增关注」分类
- **THEN** 在清未读的同时抽取每个新增关注者（昵称 + 主页ID）并上报，云端记为原因 follow 的联系人

#### Scenario: 抽取不破坏清零

- **WHEN** 巡视抽取点赞/关注发送者后
- **THEN** 该分类未读仍被清至 0，notification-clear-to-zero 的「三栏未读全 0」结果不变

### Requirement: 通知发送者按账号事件流水幂等落库（同人不同评论不丢 + 留存上限）

系统 SHALL 把每条通知发送者事件追加到一张按账号的只追加流水表，主键 `(account_id, dedup_key)`，`ON CONFLICT DO NOTHING` 保证幂等。

- **去重键按 kind 计算且与飞书去重水位解耦**：评论/@ 的键 SHALL 含内容判别（防同人同篇不同评论撞键），点赞/收藏的键含目标笔记锚点，关注的键按人。**MUST NOT 把同一人不同评论撞成一条而丢失真实事件**。
- **幂等跨重启**：同一事件被重扫 / 进程重启后重报 SHALL 折叠为一行（靠主键，不靠内存水位）。
- **第三方 PII 留存上限**：流水存别人昵称 + 评论原文，SHALL 设每账号留存上限（对齐既有第三方评论 PII 留存口径），超额删最旧；迁移表头 SHALL 注明 PII 留存理由。
- 迁移号 SHALL 为 `0016`（与已锁定 0009–0015 不冲突），DDL 幂等（`CREATE TABLE IF NOT EXISTS`）并与 store 内嵌 DDL 同源。

#### Scenario: 同一人点赞 50 篇 = 1 个联系人、次数 50

- **WHEN** 同一发送者点赞了 50 篇不同笔记
- **THEN** 流水落 50 行不同锚点，联系人列表聚为 1 个联系人、互动次数 50

#### Scenario: 同人同篇两条评论不丢（红线）

- **WHEN** 同一人在同一篇笔记下发了两条不同评论
- **THEN** 因去重键含内容判别，落两行事件（互动次数 +2），MUST NOT 因撞键丢失第二条

#### Scenario: 重扫与重启幂等

- **WHEN** 同一条通知在后续巡视轮被再次扫到，或进程重启后重报
- **THEN** `ON CONFLICT DO NOTHING` 使其折叠为同一行，不重复计数

#### Scenario: 超留存上限删最旧

- **WHEN** 某账号事件行数超过留存上限
- **THEN** 删该账号最旧行；文档/UI 注明此后该联系人「添加时间/次数」为「最早保留」口径

### Requirement: 人工字段独立侧表（巡视不覆盖、人工不碰流水）

系统 SHALL 把人工字段（微信、标签、备注）存到独立侧表，主键 `(account_id, sender_key)`，与机器写的事件流水物理隔离。

- 标签 SHALL 存为 `TEXT[]` 列（避免与事件流水二次一对多连接导致计数被放大）。
- 巡视/记录写入 MUST NOT 写本侧表；人工编辑 MUST NOT 写事件流水。
- `sender_key` SHALL 与联系人投影的分组键同口径，使人工字段正确挂到对应联系人。
- 微信为**预留**字段，可空、仅人工后补，系统 MUST NOT 自动写入。

#### Scenario: 巡视写入不覆盖人工标签

- **WHEN** 已给某联系人人工加了标签后，巡视又记录到该人的新通知
- **THEN** 新事件只进流水，人工标签/微信不受影响、不被覆盖

#### Scenario: 微信仅人工可写

- **WHEN** 任何自动记录路径运行
- **THEN** 微信字段保持为人工所填值或空，MUST NOT 被自动写入

### Requirement: 联系人按人读时聚合（计数实算、不被标签放大）

面板查询 SHALL 把事件流水按「人」（`COALESCE(主页ID, 昵称, 去重键)`）读时聚合为联系人列表，互动次数以 `COUNT(*)` 实算，不存计数列。

- 投影 SHALL 只左连人工侧表（1:1），MUST NOT 在主聚合内再左连任何一对多表（防笛卡尔放大使次数翻倍）。
- 加入原因 SHALL 取该人最早一条事件的原因；添加时间 = 最早事件时间；最近时间 = 最晚事件时间。
- 不物化投影（当前规模读时聚合即可）。

#### Scenario: 加标签后互动次数不变

- **WHEN** 某联系人有 3 条事件、被人工加了 2 个标签
- **THEN** 互动次数仍为 3（非 6），标签随行返回

#### Scenario: 加入原因取最早

- **WHEN** 某人先点赞后评论
- **THEN** 加入原因显示「点赞」（最早），原因集合含点赞与评论

### Requirement: 面板暴露按账号联系人只读查询 + 人工编辑（JWT 闸）

面板 API SHALL 提供 JWT 鉴权的按账号只读查询与人工编辑端点。

- `GET /api/notification/contacts` SHALL 要求 `accountId`，缺失则 400，MUST NOT 默认 `default`；SHALL NOT 提供全账号合并视图（防把运营各账号粉丝交叉关联的 PII 泄露）。
- 表缺失（迁移未应用）SHALL 回落空结果，MUST NOT 500；未带 JWT SHALL 401。
- `PUT /api/notification/contacts/:accountId/:senderKey` SHALL 只改 微信 / 备注 / 标签，严格校验（标签为去空的字符串数组、有界；非法值 400 不静默截断）；`accountId`/`senderKey` 取自 URL path **不取自 JWT**（token 不可越权指定账号）；`updatedBy` = JWT sub；依赖未注入 SHALL 503。
- 写端点 MUST NOT 触碰事件流水。

#### Scenario: 缺 accountId 拒绝

- **WHEN** 已鉴权请求 `GET /api/notification/contacts` 不带 accountId
- **THEN** 返回 400，MUST NOT 默认 default、MUST NOT 返回任何账号数据

#### Scenario: 按账号返回联系人

- **WHEN** 已鉴权请求带 accountId
- **THEN** 返回该账号的联系人列表（昵称/原因/标签/微信/次数/添加时间/最近时间），仅该账号数据

#### Scenario: 人工编辑只改侧表

- **WHEN** 已鉴权 `PUT` 提交合法 微信/标签/备注
- **THEN** 仅 upsert 人工侧表并返回写后联系人（诚实状态），事件流水不变；非法标签返回 400 且不落库

#### Scenario: 未鉴权与缺表

- **WHEN** 未带 JWT 请求，或迁移 0016 未应用
- **THEN** 未鉴权返回 401；缺表时读端点回落空结果而非 500

### Requirement: console 提供按账号通知联系人页

管理后台 SHALL 新增「通知联系人」页（路由 `/notification-contacts`），按账号展示并人工运营联系人。

- 页面 SHALL 要求先选账号、不提供全账号合并视图；账号列表用既有账号选择器获取。
- 表格 SHALL 含列：昵称（缺失显式标记「昵称缺失」，非留白）、加入原因（中文标签：评论/@提及/点赞/收藏/关注）、标签、微信、互动次数（可排序）、添加时间、最近时间、操作。
- 编辑入口 SHALL 仅允许改 标签（多选自由输入）/ 微信 / 备注，往返保存（非乐观）后刷新；昵称/原因/时间/次数只读。
- 页面 SHALL 顶部明示口径 Alert：只记录通知里可直接取到的人；无历史回填；添加时间为云端首次扫到时间（上线首轮会把存量未读集中记到上线时间附近）。空区间 SHALL 显式空态。

#### Scenario: 按账号查看联系人

- **WHEN** 运营打开 `/notification-contacts` 并选定账号
- **THEN** 展示该账号联系人表格，缺昵称行显式「昵称缺失」，顶部 Alert 明示口径

#### Scenario: 人工编辑标签与微信

- **WHEN** 运营在编辑弹窗填标签/微信并保存
- **THEN** 往返成功后表格刷新出新标签/微信，机器字段（昵称/原因/次数/时间）不可改

#### Scenario: 空账号显式空态

- **WHEN** 所选账号尚无任何通知联系人
- **THEN** 表格显示「暂无通知联系人」而非空白或报错
