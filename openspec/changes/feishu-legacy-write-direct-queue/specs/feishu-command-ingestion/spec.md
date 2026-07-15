## RENAMED Requirements

- FROM: `### Requirement: 旧 slash command 语法保持兼容且写操作同样先确认`
- TO: `### Requirement: 旧 slash command 语法保持兼容；写命令直接排队、自然语言仍先确认`

## MODIFIED Requirements

### Requirement: 旧 slash command 语法保持兼容；写命令直接排队、自然语言仍先确认

现有 `/publish`、`/comment`、`/status`、`/pause`、`/resume` 等命令 SHALL 保持语法兼容；只读命令可原路执行。`/publish` 与 `/comment` 等写命令 MUST 仍创建目标数为 1 的单次 DelegatedTask；因为账号昵称与目标已在命令中**显式给定、无可推断歧义**，系统 SHALL 直接确认并入队（`awaiting_confirmation → queued`），MUST NOT 再向用户展示结构化确认卡。自然语言委托（`source=feishu`）因账号 / 数量 / 截止 / 尝试均为**推断**，MUST 仍先展示结构化确认卡、明确确认后才入队。

直接排队 MUST NOT 削弱下游人审：`/publish`、`/comment` 单次任务保留 `review` 审批模式，逐篇内容 / 评论人审在任何平台写动作前仍然触发。昵称重名或找不到 MUST fail-closed 拒绝，MUST NOT 直接排队到任意账号或静默改选。确认后的单次任务 MAY 保留既有人工额度语义，但该语义 MUST NOT 被批量 / 异步任务继承。

#### Scenario: 旧 slash 写命令直接排队、不出确认卡

- **WHEN** 用户发送 `/publish <昵称>` 或 `/comment <昵称>`，且昵称唯一可解析
- **THEN** 路由器创建目标数为 1 的单次 DelegatedTask 并直接确认入队（状态 `queued`），MUST NOT 展示结构化确认卡
- **AND** 回执为该任务的进度卡（已直接排队），该兼容语法 MUST NOT 被解释为 N 条批量任务
- **AND** 逐篇内容 / 评论人审在平台写动作前仍然触发（`review` 审批模式不变）

#### Scenario: 昵称歧义仍 fail-closed

- **WHEN** `/publish <昵称>` 或 `/comment <昵称>` 的昵称重名或找不到
- **THEN** 系统诚实拒绝并要求澄清，MUST NOT 直接排队到任意账号

#### Scenario: 自然语言委托仍先确认

- **WHEN** 用户发送自然语言业务目标（如「让 <昵称> 发布一篇稿件」「今晚前完成 3 条评论」）
- **THEN** 系统 MUST 仍先展示结构化确认卡，明确确认后才入队
