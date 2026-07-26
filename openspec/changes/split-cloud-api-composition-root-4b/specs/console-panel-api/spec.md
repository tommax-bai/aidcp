## MODIFIED Requirements

### Requirement: 总览接口暴露数据新鲜度，后台据此区分「无新活动」与「界面冻结」

总览只读接口 `GET /api/dashboard/summary` SHALL 在响应中附带一个**服务端生成的数据新鲜度时间戳**
（`asOf`，每次请求落地为该次查询的服务器当前时刻），并 SHALL 继续如实回报在线边缘事实：
Edge presence 镜像 fresh 时返回 `edgesOnline` 数值以及 `edgePresenceState=fresh`、owner
`edgePresenceAsOf`；镜像 uninitialized/stale/invalid 时返回 `edgesOnline=null` 与可区分的
`edgePresenceState=unknown|stale|invalid`，MUST NOT 把最后好值或空集合冒充当前在线数。
管理后台总览页 SHALL 用响应时刻与 presence 数据时刻把「系统当前没有新活动」「presence 暂不可用」
与「界面冻结 / 看板坏了」可视化区分：

- SHALL 呈现「数据截至 `asOf` / 自动刷新中」一类的新鲜度标识，使运营一眼看出页面轮询仍在更新；
- 只有 `edgePresenceState=fresh` 且 `edgesOnline=0` 时 SHALL 呈现「系统当前未在浏览」；
- presence unknown/stale/invalid 时 SHALL 呈现「在线状态暂不可用」及其数据时刻，
  MUST NOT 归因为零个 Edge 或虚构正在浏览。

该呈现 MUST 诚实：MUST NOT 把「无新活动」粉饰为有数据流入，也 MUST NOT 在无可靠 presence
证据时显示虚构的在线/离线结论。本要求只触及前端可读性与新鲜度暴露：MUST NOT 改变互动计数的
采集口径，MUST NOT 在总览接口引入会阻塞事件循环的全表扫描或重聚合。

#### Scenario: 总览响应带服务端新鲜度时间戳

- **WHEN** 请求 `GET /api/dashboard/summary` 且 Edge presence mirror fresh
- **THEN** 响应含本次请求 `asOf`、owner `edgePresenceAsOf`、`edgePresenceState=fresh` 与如实的 `edgesOnline`
- **AND** 不执行阻塞事件循环的全表扫描

#### Scenario: 自动刷新时新鲜度标识推进，证明界面未冻结

- **WHEN** 后台总览页按轮询完成一次刷新且后端返回了更晚的响应 `asOf`
- **THEN** 页面上的「数据截至 …」标识推进到新的响应时刻
- **AND** Edge presence 数据时刻独立呈现，MUST NOT 用响应时刻伪造 source freshness

#### Scenario: 无边缘在线时如实提示无新数据来源

- **WHEN** `edgePresenceState=fresh` 且 `edgesOnline=0`
- **THEN** 后台总览页显示「系统当前未在浏览，故无新数据」一类提示
- **AND** 把无新计数归因为 owner 已确认的零在线，而非界面故障

#### Scenario: Edge presence 暂不可用

- **WHEN** `edgePresenceState` 为 unknown、stale 或 invalid
- **THEN** 后台显示「在线状态暂不可用」并保留 owner 数据时刻
- **AND** MUST NOT 显示零个在线 Edge、无边缘在浏览或其它肯定离线结论

#### Scenario: 诚实呈现，不粉饰无活动

- **WHEN** 当前无新互动产生且计数较上次无变化
- **THEN** 后台如实呈现「数据已更新但无新活动」，MUST NOT 伪造活跃感
- **AND** MUST NOT 改变互动计数采集口径或把 `view` 加进互动 allow-list

### Requirement: 发布队列快照按阶段摘要呈现并保留原始明细

Cloud 的 `GET /api/content/queue` SHALL 在保留既有 `status`、`snapshot` 与 `runs` 字段的同时，
返回面向管理后台的发布生命周期投影。该投影 SHALL 将每份稿件拆为触发与选题、正文生成、文本质检、
视觉策划、出图复核、成稿封装、人工审批、平台下发八个阶段，并为每个阶段返回明确状态和可证实摘要。
阶段状态 MUST 至少能区分未开始、进行中、重试中、等待人工、已完成、部分完成、失败、跳过与
`evidence_unavailable`。

生命周期投影 SHALL 组合当前 orchestrator runs、`publish_log` 持久化状态、API-owned durable approval
dispatch projection 和 automation dispatcher in-flight 镜像，并返回 `inFlightEvidence.state/asOf`。
durable dispatch projection 已证明状态时 SHALL 以其为准；只有缺少 durable 证明且
`inFlightEvidence.state=fresh` 时，才可用 record id 是否在集合中补足等待人工/正在下发分类。
in-flight evidence unknown/stale/invalid 时，受影响稿件的下发阶段 SHALL 标记
`evidence_unavailable`，MUST NOT 由空集合推断“未下发”或“等待人工”。

管理后台 SHALL 优先使用该投影，将有可靠证据的生成中、等待人工或正在下发稿件展示在“活跃稿件”，
将 published、submitted、failed、needs_review、draft、skipped 等终态展示在“最近结果”或发布历史；
最近终态快照 MUST NOT 因存在 snapshot 而继续冒充活跃稿件。

该呈现 MUST 保持诚实：阶段完成 SHALL 由明确终点或持久化状态证明，不得因任意中间字段出现而声称
整段完成；文本质检和视觉策划等真实并行分支 MAY 同时显示进行中；没有逐命令证据时不得臆造平台下发
子步骤。原始 snapshot 字段 MUST 继续通过二级展开入口可见，供排障和未知未来字段检查。新字段
MUST 向后兼容，不得改变发布编排行为、审批授权或平台成功判定。

#### Scenario: 生成中的稿件显示八阶段投影

- **WHEN** 管理后台读取到一个 running orchestrator run，正文已经产出而文本质检与视觉策划尚未收敛
- **THEN** 活跃稿件 SHALL 显示该账号和稿件摘要，正文生成标记已完成
- **AND** 文本质检与视觉策划 MAY 同时标记进行中，其余阶段按依赖保持未开始

#### Scenario: 待审稿件明确等待人工

- **WHEN** `publish_log` 为 `pending_approval`，durable projection 未证明已开始下发，
  且 fresh in-flight 集合明确不含该 record id
- **THEN** 该稿件 SHALL 位于活跃稿件，人工审批阶段标记等待人工，平台下发阶段标记未开始

#### Scenario: 已批准稿件显示平台下发中

- **WHEN** durable dispatch projection 证明 dispatching，或 fresh in-flight 集合明确包含该 record id
- **THEN** 人工审批阶段 SHALL 标记已完成，平台下发阶段 SHALL 标记进行中
- **AND** 后台不得继续显示为单纯待审

#### Scenario: in-flight 证据不可用

- **WHEN** 稿件缺少 durable dispatch 证明且 `inFlightEvidence.state` 为 unknown、stale 或 invalid
- **THEN** 平台下发阶段 SHALL 标记 `evidence_unavailable` 并显示“下发状态暂不可用”
- **AND** MUST NOT 因本地集合为空将其标为等待人工、未下发或正在下发

#### Scenario: 下发失败离开活跃稿件

- **WHEN** 一份稿件的持久化状态从 `pending_approval` 变为 `failed`
- **THEN** 该稿件 MUST 从活跃稿件移入最近结果或发布历史
- **AND** 平台下发阶段标记失败并明确不得声称已经发布

#### Scenario: 已提交但链接未确认显示部分完成

- **WHEN** 一份稿件的持久化状态为 `submitted` 且没有可验证的平台帖子链接
- **THEN** 平台下发阶段 SHALL 标记部分完成并显示“已提交，待链接确认”
- **AND** 不得标成失败或已发布

#### Scenario: 原始字段仍可展开排障

- **WHEN** 生命周期关联的生成 snapshot 中存在未被阶段摘要识别的顶层字段
- **THEN** 页面 SHALL 提供原始字段展开入口并显示该字段的序列化值
- **AND** 运营排障不需要翻服务器日志确认字段是否存在

#### Scenario: 空闲状态不伪造进度

- **WHEN** lifecycle 没有可靠 running、waiting_human 或 dispatching 稿件
- **THEN** 发布队列 SHALL 显示无可确认的活跃稿件
- **AND** MUST NOT 因最近终态 snapshot 或 unavailable in-flight evidence 渲染虚假进行中阶段

## ADDED Requirements

### Requirement: 配置镜像健康按消费服务分域并暴露 delivery 新鲜度

`GET /api/config-mirrors` SHALL 分别返回 api 本地 health 与 automation health 投影，每段带
`sourceService`、source `asOf` 和 `deliveryState=fresh|stale|unknown|invalid`。automation health
delivery 不 fresh 时，整段 entries MUST 视为 unavailable；响应 MUST NOT 沿用旧 entry 的 `fresh`
值拼成全局健康结论。管理后台 SHALL 分域展示，不合并成单个“全部正常”状态。

#### Scenario: 两个消费服务状态不同

- **WHEN** api 本地 mirror fresh，而 automation 某 gate mirror stale
- **THEN** API 与管理后台分别显示两个 source service 的状态
- **AND** MUST NOT 聚合为全局 fresh

#### Scenario: automation health delivery 陈旧

- **WHEN** automation health snapshot 的 deliveryState 为 stale
- **THEN** API 将 automation 段标为 unavailable 并保留 source/delivery 时刻
- **AND** 管理后台 MUST NOT 展示旧 entries 为当前 fresh
