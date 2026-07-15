## MODIFIED Requirements

### Requirement: 发布队列快照按阶段摘要呈现并保留原始明细

Cloud 的 `GET /api/content/queue` SHALL 在保留既有 `status`、`snapshot` 与 `runs` 字段的同时，返回面向管理后台的发布生命周期投影。该投影 SHALL 将每份稿件拆为触发与选题、正文生成、文本质检、视觉策划、出图复核、成稿封装、人工审批、平台下发八个阶段，并为每个阶段返回明确状态和可证实摘要。阶段状态 MUST 至少能区分未开始、进行中、重试中、等待人工、已完成、部分完成、失败与跳过。

生命周期投影 SHALL 组合当前 orchestrator runs、`publish_log` 持久化状态和 dispatcher 下发在途状态。管理后台 SHALL 优先使用该投影，将仍在生成、等待人工或正在下发的稿件展示在“活跃稿件”，将 published、submitted、failed、needs_review、draft、skipped 等终态展示在“最近结果”或发布历史；最近终态快照 MUST NOT 因存在 snapshot 而继续冒充活跃稿件。

该呈现 MUST 保持诚实：阶段完成 SHALL 由明确终点或持久化状态证明，不得因任意中间字段出现而声称整段完成；文本质检和视觉策划等真实并行分支 MAY 同时显示进行中；没有逐命令证据时不得臆造平台下发子步骤。原始 snapshot 字段 MUST 继续通过二级展开入口可见，供排障和未知未来字段检查。新字段 MUST 向后兼容，不得改变发布编排行为、审批授权或平台成功判定。

#### Scenario: 生成中的稿件显示八阶段投影

- **WHEN** 管理后台读取到一个 running orchestrator run，正文已经产出而文本质检与视觉策划尚未收敛
- **THEN** 活跃稿件 SHALL 显示该账号和稿件摘要，正文生成标记已完成，文本质检与视觉策划 MAY 同时标记进行中，其余阶段按依赖保持未开始

#### Scenario: 待审稿件明确等待人工

- **WHEN** `publish_log` 中一份稿件状态为 `pending_approval` 且其 record id 不在 dispatcher in-flight 集合
- **THEN** 该稿件 SHALL 位于活跃稿件，人工审批阶段标记等待人工，平台下发阶段标记未开始

#### Scenario: 已批准稿件显示平台下发中

- **WHEN** `publish_log` 中一份 `pending_approval` 稿件的 record id 位于 dispatcher in-flight 集合
- **THEN** 人工审批阶段 SHALL 标记已完成，平台下发阶段 SHALL 标记进行中，后台不得继续显示为单纯待审

#### Scenario: 下发失败离开活跃稿件

- **WHEN** 一份稿件的持久化状态从 `pending_approval` 变为 `failed`
- **THEN** 该稿件 MUST 从活跃稿件移入最近结果或发布历史，平台下发阶段标记失败，并明确不得声称已经发布

#### Scenario: 已提交但链接未确认显示部分完成

- **WHEN** 一份稿件的持久化状态为 `submitted` 且没有可验证的平台帖子链接
- **THEN** 平台下发阶段 SHALL 标记部分完成并显示“已提交，待链接确认”语义，不得标成失败或已发布

#### Scenario: 原始字段仍可展开排障

- **WHEN** 生命周期关联的生成 snapshot 中存在未被阶段摘要识别的顶层字段
- **THEN** 页面 SHALL 提供原始字段展开入口并显示该字段的序列化值，运营排障不需要翻服务器日志确认字段是否存在

#### Scenario: 空闲状态不伪造进度

- **WHEN** 生命周期投影没有 running、waiting_human 或 dispatching 稿件
- **THEN** 发布队列 SHALL 显示无活跃稿件，MUST NOT 因最近终态 snapshot 存在而渲染虚假的进行中阶段；最近终态 MAY 在独立的最近结果区域展示
