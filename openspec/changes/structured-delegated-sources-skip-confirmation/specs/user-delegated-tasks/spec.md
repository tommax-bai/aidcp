## RENAMED Requirements

- FROM: `### Requirement: 公共写操作必须先结构化确认`
- TO: `### Requirement: 自然语言入口先结构化确认；结构化精确入口直接入队`

## MODIFIED Requirements

### Requirement: 自然语言入口先结构化确认；结构化精确入口直接入队

只有**自然语言**委托入口（`source=feishu`）SHALL 先创建 `awaiting_confirmation` 任务并展示结构化确认摘要——账号 / 数量 / 截止 / 尝试均为从散文**推断**、可能解析错，需人过目；只有带 task id 与当前版本的明确确认才能进入 `queued`。**结构化精确入口**（console 行级动作 / Edge 快捷入口 / api / 旧 slash 命令，即 `source ≠ feishu`）参数已在调用处显式给定、无可推断歧义，SHALL 在创建时直接确认入队（`awaiting_confirmation → queued`），MUST NOT 展示结构化确认卡。

两类入口的人审都不受影响（发布 / 评论仍在下游内容审批处保留人审），昵称重名或找不到仍 fail-closed 拒绝。重复创建（去重命中）MUST 幂等返回当前真态，MUST NOT 重复入队。任务创建时 SHALL 从账号事实源回读平台，调用方自报平台不一致 MUST 拒绝。直接入队 ≠ 已执行：worker 接管前不得有任何一次尝试或平台副作用。

#### Scenario: console 行级动作直接入队、不出确认卡

- **WHEN** 管理后台对一条精选图文点「洗稿」或对候选稿点「批准 / 驳回 / 修改」（`source=console`）
- **THEN** 系统在创建时直接确认入队（状态 `queued`），MUST NOT 展示「请确认用户委托任务」卡
- **AND** 入队时 `attemptCount=0`、无边端接管 / 生成 / 发布；结果由下游业务结果卡回报

#### Scenario: 自然语言委托仍先结构化确认

- **WHEN** 飞书管理群发送自然语言业务目标（如「让 <昵称> 发布一篇稿件」）
- **THEN** 系统仍先创建 `awaiting_confirmation` 任务并展示结构化确认摘要，明确确认后才 `queued`

#### Scenario: 重复创建幂等、不产生双任务

- **WHEN** 同一结构化精确动作在去重窗口内被重复触发
- **THEN** 去重命中返回同一 task id 的当前真态，MUST NOT 重复入队或重复执行

#### Scenario: 平台事实不一致时拒绝

- **WHEN** 入口把 Facebook 账号声明为小红书以请求小红书定向评论
- **THEN** 系统以 accounts 平台事实源拒绝该草稿或入队
- **AND** MUST NOT 将任务路由到另一平台执行器
