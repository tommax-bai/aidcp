## MODIFIED Requirements

### Requirement: 批量和异步委托必须遵守自动化风险额度并保留人审

**精确单次操作员命令**（`source=legacy_command` 且 `targetConstraints.manualSingle=true`，含 `/publish` 与 `/comment`）SHALL 以操作员全权执行——越过风控 status / canDo 与配额闸（发帖侧透传 `operatorOverride=true`，评论侧 `manualOverride=true`）。发布前人审 MUST 仍强制；评论前人审默认强制，但账号显式 `auto_approve_all` 时 MUST 改为通知成功后授权，飞书 `/comment` 不得再要求第二次按钮审批。该账号策略只改变评论授权等待，MUST NOT 改变 `manualOverride` 的风控/配额语义。`targetSuccessCount>1`、跨账号、自然语言（`source=feishu`）或结构化（`source ∈ {edge,console,api}`）委托 MUST 使用自动化额度与风险闸（`governed`），MUST NOT 置 `operatorOverride` / 为每次 attempt 传 `manualOverride=true`。RiskController SHALL 继续是账号风险状态唯一写者。公开评论和发布默认 SHALL 使用 `review`，除非既有受控来源配置或账号全局评论策略明确允许免审。

#### Scenario: 批量评论不能循环绕额度
- **WHEN** 用户确认一个 5 条评论的委托任务
- **THEN** 每次评论尝试按自动化路径检查风险/配额且 `manualOverride=false`
- **AND** 额度不足时任务 deferred 或诚实部分完成，不得循环伪装成五次单次人工命令

#### Scenario: 精确 /publish 在风控受限账号仍以操作员全权执行
- **WHEN** 管理群对一个风控非 normal 或当天已达发布配额的账号发送 `/publish <昵称>`（`source=legacy_command`、`manualSingle`）
- **THEN** 系统越过风控 status/canDo 与配额生成草稿并发出发布人审卡（`operatorOverride=true`）
- **AND** MUST NOT 因风控/配额把该精确命令 blocked→deferred→静默判失败
- **AND** 发布前人审 MUST 仍强制，越权 MUST NOT 越过人审

#### Scenario: 精确 /comment 服从账号全局免审
- **WHEN** 管理群对一个 `auto_approve_all` 账号发送精确 `/comment <昵称>`
- **THEN** 评论沿用 `manualOverride=true` 越过既有手工风险/配额闸，并在免审通知成功后继续
- **AND** MUST NOT 再发送同意/不发按钮卡或等待第二次人审

#### Scenario: 自然语言与结构化发帖不得越风控
- **WHEN** 委托发帖来自自然语言（`source=feishu`）或结构化入口（edge/console/api）
- **THEN** 系统走 `governed` 路径，风控非 normal / canDo 拒时诚实 blocked
- **AND** MUST NOT 置 `operatorOverride`，MUST NOT 让结构化发帖跳过风控闸

### Requirement: 自然语言入口先结构化确认；结构化精确入口直接入队

只有**自然语言**委托入口（`source=feishu`）SHALL 先创建 `awaiting_confirmation` 任务并展示结构化确认摘要——账号 / 数量 / 截止 / 尝试均为从散文**推断**、可能解析错，需人过目；只有带 task id 与当前版本的明确确认才能进入 `queued`。**结构化精确入口**（console 行级动作 / Edge 快捷入口 / api / 旧 slash 命令，即 `source ≠ feishu`）参数已在调用处显式给定、无可推断歧义，SHALL 在创建时直接确认入队（`awaiting_confirmation → queued`），MUST NOT 展示结构化确认卡。

**结构化入口的客户端请求体对 `approvalMode` 不可信**：免审（`auto_approve`）只由 Cloud 受控配置授予，客户端体 MUST NOT 自带、系统 MUST NOT 原样采信。系统 SHALL 在 HTTP 建草稿边界把客户端体的 `approvalMode` 收口——缺省保持未定（交由按动作的默认，如 `generate_candidates → draft_only`）、`draft_only` 放行、其余（含 `auto_approve` 与任何未来模式）夹成 `review`。**服务端自建 intent**（后台洗稿 / 候选控制已显式传 `review`、飞书 parser 已硬编码 `review`）不经此收口。评论执行到授权边界时仍 SHALL 读取 Cloud 持久化的账号全局评论策略；显式 `auto_approve_all` 可把有效评论模式覆盖为免审，这不等于采信客户端请求体。

两类入口的下游授权都不受确认卡差异影响：发布仍保留人审，评论默认保留人审但服从账号全局评论覆盖；昵称重名或找不到仍 fail-closed 拒绝。重复创建（去重命中）MUST 幂等返回当前真态，MUST NOT 重复入队。任务创建时 SHALL 从账号事实源回读平台，调用方自报平台不一致 MUST 拒绝。直接入队 ≠ 已执行：worker 接管前不得有任何一次尝试或平台副作用。

#### Scenario: 客户端体自带 auto_approve 被夹成 review
- **WHEN** 结构化建草稿路由（面板 / 客户端）收到请求体带 `approvalMode:'auto_approve'`
- **THEN** 系统在创建前把该字段夹成 `review`，任务以必审来源模式入队
- **AND** MUST NOT 因客户端自报而让内容免审直达平台

#### Scenario: 账号策略可在评论授权边界覆盖 review
- **WHEN** 结构化评论任务的客户端体已被夹成 `review`，但执行时账号权威策略为 `auto_approve_all`
- **THEN** Cloud 在授权边界解析有效评论模式为免审并先发通知，MUST NOT 把客户端体当作账号策略事实源

#### Scenario: 结构化精确入口不出确认卡但保留下游授权
- **WHEN** 管理后台对一条精选图文点「洗稿」（`source=console`，服务端自建 intent 传 `review`）
- **THEN** 系统直接确认入队（状态 `queued`），MUST NOT 展示确认卡
- **AND** 其发布 `review` 授权保持不变，下游人审仍强制

#### Scenario: 自然语言委托仍先结构化确认
- **WHEN** 飞书管理群发送自然语言业务目标
- **THEN** 系统仍先创建 `awaiting_confirmation` 任务并展示结构化确认摘要，明确确认后才 `queued`

#### Scenario: 重复创建幂等、不产生双任务
- **WHEN** 同一结构化精确动作在去重窗口内被重复触发
- **THEN** 去重命中返回同一 task id 的当前真态，MUST NOT 重复入队或重复执行
