## ADDED Requirements

### Requirement: Panel API 提供严格的 Facebook 数字策略生命周期

Cloud Panel SHALL 在既有内部 JWT 守卫下提供：

- `GET /api/facebook-mode-policies`：返回两个策略族的完整 API owner current、draft、schema/range metadata、audit head、服务端 publish gate 状态，以及 DEV/OL 各 execution target 的 applied current/cursor/lag/readiness、writer rollout phase/epoch、expected-instance-set coverage 与 freshness；
- `PUT /api/facebook-mode-policies/{rule-mode|slow-start}/draft`：使用严格 body 与 `expectedDraftVersion` 保存草稿；
- `POST /api/facebook-mode-policies/{rule-mode|slow-start}/preview`：重新校验并返回规范化数字、派生值、影响范围、消费者兼容性、publish gate observation 与 digest；
- `POST /api/facebook-mode-policies/{rule-mode|slow-start}/publish`：使用 `expectedDraftVersion`、`expectedPublishedRevision`、preview digest、说明和幂等键原子发布；
- `GET /api/facebook-mode-policies/{rule-mode|slow-start}/revisions?cursor=...`：以不透明游标分页返回 immutable published revision 历史，稳定包含 revision identity、schema version、发布时间、actor 与规范化数字摘要；
- `GET /api/facebook-mode-policies/{rule-mode|slow-start}/revisions/:revision`：返回一个 immutable published revision 的完整严格类型数值与发布元数据，未知 kind/revision 返回结构化未找到且不猜测 current；
- `GET /api/facebook-mode-policies/{rule-mode|slow-start}/publish-results/:idempotencyKey?payloadDigest=...`：按幂等键与完整 publish payload 的规范化 digest 查询权威发布结果；
- `GET /api/facebook-mode-policies/{rule-mode|slow-start}/audit?cursor=...`：分页返回最小审计投影。

所有响应 SHALL 使用完整的服务端 DTO 与结构化错误，不得仅返回 `{ok:true}`。规则 DTO MUST 只携带 `1..100` 的两个整数和版本/审计元数据；慢启动 DTO MUST 携带 `totalDays=7` 和恰好七行固定动作、`0..100000` 的 daily caps。任一路由 MUST NOT 接受动作列表、Prompt、模板、分钟/小时覆盖、客户/环境覆盖或任意 URL。

从历史数值恢复 SHALL 先通过 immutable revision detail GET 读取完整服务端真态，再把其严格类型数值作为一个**新的**草稿 body，经现有 draft PUT 与当前 `expectedDraftVersion` 保存。该流程 MUST NOT 原地编辑历史 revision、把全局 current 指针倒退到历史 revision，或让 Console 自行生成 revision/schema identity；后续仍须重新 preview 并发布成新的单调 revision。

#### Scenario: 有效 Panel JWT 读取完整策略真态

- **WHEN** 已认证内部管理员读取数字策略
- **THEN** Cloud 返回两个策略族 owner current、草稿版本、严格 schema/ranges、freshness、audit head 与每个 target 的 applied current/cursor/lag/readiness
- **AND** 不返回 token、密钥或无关客户数据

#### Scenario: Customer JWT 不能进入内部策略域

- **WHEN** customer token、Edge token 或未认证请求调用任一数字策略 Panel 路由
- **THEN** Cloud 拒绝请求且不泄露策略是否存在、版本或数字

#### Scenario: 未知字段整块拒绝

- **WHEN** 草稿 body 携带 action list、Prompt、额外 day/action、分钟/小时值或其它未知键
- **THEN** Cloud 返回可定位的 4xx schema 错误
- **AND** 草稿、published revision、全局当前指针和镜像 cursor 均不改变

#### Scenario: 历史 revision 游标分页且详情不可变

- **WHEN** 内部管理员按 cursor 翻阅某一策略族的 published revision 并读取其中一个详情
- **THEN** Cloud 返回稳定下一游标及该 revision 的完整严格类型数值、schema 和发布元数据
- **AND** 该 GET 不创建草稿、不移动 current 指针，也不提供修改或删除历史 revision 的能力

#### Scenario: 从历史数值建立新草稿

- **WHEN** 管理员读取一个兼容历史 revision 的完整详情并选择恢复其数值
- **THEN** Console 以这些数值和当前 `expectedDraftVersion` 调用既有 draft PUT，Cloud 保存一个新的可编辑草稿
- **AND** 历史 revision 与 current 指针保持不变，恢复值必须重新 preview 并发布为新的单调 revision

### Requirement: Panel 策略写入使用 CAS、幂等发布和写后真态

草稿与发布 SHALL 分别校验预期草稿版本和预期当前 published revision；冲突 SHALL 返回 409 与当前服务端版本，MUST NOT 静默覆盖。发布 route SHALL 先由服务端强制检查默认关闭的 gate：仅 OL API process 同时满足 `AIDCP_DEPLOY_ENV=ol`、`AIDCP_FACEBOOK_MODE_POLICY_PUBLISH_ENABLED=true` 与非空 `AIDCP_FACEBOOK_MODE_POLICY_PUBLISH_CHANGE_REF` 才继续，其它情况返回 `policy_publish_disabled`。通过 gate 后，发布 SHALL 在一个事务内创建不可变 revision、推进该策略族全局当前指针、写 outbox/mirror version 与审计；任一步失败 MUST 整体回滚。相同幂等键与**完全相同的 publish payload**（包括 kind、草稿版本、预期 current revision、preview digest、说明及其它严格字段）重放 SHALL 返回第一次请求的同一权威结果；相同键对应任何不同 payload MUST 拒绝，即使二者碰巧产生相同业务数字。

Cloud 成功回包 SHALL 返回完整写后 current/draft/audit 真态。客户端在超时或连接中断后 MUST 保留原幂等键与完整 publish payload，并且只可用该相同键和逐字段完全相同 payload 安全重放，或用同一键及该完整 payload 的规范化 digest 查询 `publish-results` 权威结果。查询确认已提交时 SHALL 返回第一次发布的 revision 与写后真态；确认未提交时 MAY 允许仍以原键和原 payload 重放；查询本身也无法确认时 SHALL 保持 `result_unknown`。客户端 MUST NOT 换新幂等键、修改 payload 后无条件重试，或在权威结果未知时宣称成功/失败。依赖存储、schema capability 或镜像健康不可确认时，读取 SHALL 返回 unknown/503，发布 SHALL 失败关闭而不是合成 legacy 默认。

#### Scenario: 草稿 CAS 冲突不覆盖

- **WHEN** 草稿写入的 `expectedDraftVersion` 落后于服务端当前版本
- **THEN** Cloud 返回 409 与当前草稿版本并保持服务端数字不变

#### Scenario: 发布事务任一步失败

- **WHEN** revision 写入、current pointer、审计或 mirror/outbox version 任一步失败
- **THEN** 整个事务回滚，不留下孤立 revision、不推进 current、不产生伪审计

#### Scenario: 服务端发布闸默认关闭

- **WHEN** 调用 publish route 的进程为 DEV，或 OL process 的 enabled/changeRef 任一缺失或非法
- **THEN** Cloud 返回 `policy_publish_disabled`，并在 read/preview/health 暴露具名 gate 状态
- **AND** draft、published revision、current pointer 与 mirror cursor 均不改变，前端是否显示按钮不影响该裁决

#### Scenario: 相同发布请求安全重放

- **WHEN** 客户端因回包丢失以原幂等键和逐字段完全相同的 publish payload 重放
- **THEN** Cloud 返回第一次发布的同一 revision 与写后真态
- **AND** 不生成第二个 revision或重复审计

#### Scenario: 相同幂等键不能承载不同发布请求

- **WHEN** 客户端复用已有幂等键但改变 publish payload 的任一字段
- **THEN** Cloud 拒绝请求并返回幂等冲突
- **AND** MUST NOT 创建新 revision、覆盖第一次结果或仅凭相同数字把两个请求视为相同

#### Scenario: 发布结果仍无法确认

- **WHEN** 发布请求超时，按原幂等键与原 payload digest 查询权威结果也失败，且原请求的完全相同重放仍无法得到权威回包
- **THEN** Console 显示结果未知并禁止无条件重试
- **AND** MUST NOT 换新幂等键、改变 publish payload，或把本地草稿标成 published/current

### Requirement: Panel 发布预览说明真实采用边界

规则策略发布预览 SHALL 分开统计当前为 0 可在下次 admission 采用的账号、部分 collecting progress、活动 batch 和无法确认状态；慢启动预览 SHALL 分开统计关闭/毕业环境、处于第 1 至第 7 天并继续 pin 旧 revision 的环境，以及 binding/platform 不可确认状态。预览 SHALL 另外逐 target 返回 owner current、applied current/cursor/lag/schema readiness，并逐 envKey 返回受影响客户端 `facebook_mode_policy_projection_v1` 的 compatible/incompatible/unknown cohort。易变统计 SHALL 标注 `asOf`，预览 MUST 明示规则只会从 target applied current 的下一安全轮次采用、在途慢启动不换版、最终风险额度继续逐动作取更严值。

发布事务 SHALL 复核规范化草稿、预期 current revision、稳定 preview digest、服务端 publish gate observation、DEV/OL runtime 兼容性、经 fresh authenticated health 投影的永久 `reject_missing` rollout attestation、权威 expected API/automation writer instance-set coverage 与受影响客户端 cohort。预览不可读、承重 digest 漂移、gate observation 变化、任何 target/实例不兼容、缺失、陈旧或仅有部分 coverage，或规则策略 cohort 中任一环境 capability missing/unsupported/stale 时，发布 MUST 返回具名冲突/不可用并保持共享 owner current revision 不变。API MUST NOT 跨库查询 automation rollout 表，也 MUST NOT 以“旧 heartbeat 为零”替代完整实例集合证明。DEV/OL 共库下不存在 DEV-only non-legacy publish；仅有 DEV 授权或 OL 尚未兼容时 writer MUST 保持关闭。易变影响计数自然变化时 SHALL 返回最新 `asOf` 统计但不单独拒绝发布。

#### Scenario: 规则预览不把部分进度算成立即生效

- **WHEN** 某账号已经按旧 revision 收集部分 view
- **THEN** 预览把它列入旧轮次收敛范围
- **AND** 不声称发布后该账号的当前分子/分母会立即改变

#### Scenario: 慢启动预览保留 active pin

- **WHEN** 环境正按旧 revision 处于第 5 天
- **THEN** 预览明确该环境本次发布后仍完成旧七日策略
- **AND** 不把它计入立即使用新 revision 的环境

#### Scenario: 兼容性在预览后失效

- **WHEN** preview 成功后某执行目标不再满足待发布 schema capability
- **THEN** publish 复核失败且 current revision 保持不变

#### Scenario: publish 回包不冒充 target 已应用

- **WHEN** owner current 已成功推进但某 target 的下一份 snapshot 尚未原子应用
- **THEN** Panel 返回并显示 owner current 与该 target 旧 applied current/cursor/lag
- **AND** 不把该 target 或其账号标成已经采用新 revision
