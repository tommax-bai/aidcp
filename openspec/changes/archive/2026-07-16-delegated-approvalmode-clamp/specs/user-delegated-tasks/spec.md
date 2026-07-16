## MODIFIED Requirements

### Requirement: 自然语言入口先结构化确认；结构化精确入口直接入队

只有**自然语言**委托入口（`source=feishu`）SHALL 先创建 `awaiting_confirmation` 任务并展示结构化确认摘要——账号 / 数量 / 截止 / 尝试均为从散文**推断**、可能解析错，需人过目；只有带 task id 与当前版本的明确确认才能进入 `queued`。**结构化精确入口**（console 行级动作 / Edge 快捷入口 / api / 旧 slash 命令，即 `source ≠ feishu`）参数已在调用处显式给定、无可推断歧义，SHALL 在创建时直接确认入队（`awaiting_confirmation → queued`），MUST NOT 展示结构化确认卡。

**结构化入口的客户端请求体对 `approvalMode` 不可信**：免审（`auto_approve`）只由账号级授权授予，客户端体 MUST NOT 自带、系统 MUST NOT 原样采信。系统 SHALL 在 HTTP 建草稿边界把客户端体的 `approvalMode` 收口——缺省保持未定（交由按动作的默认，如 `generate_candidates → draft_only`）、`draft_only` 放行、其余（含 `auto_approve` 与任何未来模式）夹成 `review`。**服务端自建 intent**（后台洗稿 / 候选控制已显式传 `review`、飞书 parser 已硬编码 `review`）不经此收口、不受影响。

两类入口的人审都不受影响（发布 / 评论仍在下游内容审批处保留人审），昵称重名或找不到仍 fail-closed 拒绝。重复创建（去重命中）MUST 幂等返回当前真态，MUST NOT 重复入队。任务创建时 SHALL 从账号事实源回读平台，调用方自报平台不一致 MUST 拒绝。直接入队 ≠ 已执行：worker 接管前不得有任何一次尝试或平台副作用。

#### Scenario: 客户端体自带 auto_approve 被夹成 review

- **WHEN** 结构化建草稿路由（面板 / 客户端）收到请求体带 `approvalMode:'auto_approve'`
- **THEN** 系统在创建前把该字段夹成 `review`，任务以必审入队
- **AND** MUST NOT 让内容以免审绕过下游人审直达平台，即使该账号未开启账号级免审

#### Scenario: 结构化精确入口不出确认卡但保留人审

- **WHEN** 管理后台对一条精选图文点「洗稿」（`source=console`，服务端自建 intent 传 `review`）
- **THEN** 系统直接确认入队（状态 `queued`），MUST NOT 展示确认卡
- **AND** 其 `review` 授权不经客户端收口、保持不变，下游人审仍强制

#### Scenario: 自然语言委托仍先结构化确认

- **WHEN** 飞书管理群发送自然语言业务目标
- **THEN** 系统仍先创建 `awaiting_confirmation` 任务并展示结构化确认摘要，明确确认后才 `queued`

#### Scenario: 重复创建幂等、不产生双任务

- **WHEN** 同一结构化精确动作在去重窗口内被重复触发
- **THEN** 去重命中返回同一 task id 的当前真态，MUST NOT 重复入队或重复执行
