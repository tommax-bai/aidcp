## MODIFIED Requirements

### Requirement: 批量和异步委托必须遵守自动化风险额度并保留人审

**精确单次操作员命令**（`source=legacy_command` 且 `targetConstraints.manualSingle=true`，含 `/publish` 与 `/comment`）SHALL 以操作员全权执行——越过风控 status / canDo 与配额闸（发帖侧透传 `operatorOverride=true`，评论侧 `manualOverride=true`），但**发布前 / 评论前的人审 MUST 仍强制**（越权只越风控 / 配额，绝不越人审）。`targetSuccessCount>1`、跨账号、自然语言（`source=feishu`）或结构化（`source ∈ {edge,console,api}`）委托 MUST 使用自动化额度与风险闸（`governed`），MUST NOT 置 `operatorOverride` / 为每次 attempt 传 `manualOverride=true`。RiskController SHALL 继续是账号风险状态唯一写者。公开评论和发布默认 SHALL 使用 `review`，除非既有受控配置明确允许其他模式。

#### Scenario: 批量评论不能循环绕额度
- **WHEN** 用户确认一个 5 条评论的委托任务
- **THEN** 每次评论尝试按自动化路径检查风险/配额且 `manualOverride=false`
- **AND** 额度不足时任务 deferred 或诚实部分完成，不得循环伪装成五次单次人工命令

#### Scenario: 精确 /publish 在风控受限账号仍以操作员全权执行
- **WHEN** 管理群对一个风控非 normal 或当天已达发布配额的账号发送 `/publish <昵称>`（`source=legacy_command`、`manualSingle`）
- **THEN** 系统越过风控 status/canDo 与配额生成草稿并发出发布人审卡（`operatorOverride=true`）
- **AND** MUST NOT 因风控/配额把该精确命令 blocked→deferred→静默判失败
- **AND** 发布前人审 MUST 仍强制，越权 MUST NOT 越过人审

#### Scenario: 自然语言与结构化发帖不得越风控
- **WHEN** 委托发帖来自自然语言（`source=feishu`）或结构化入口（edge/console/api）
- **THEN** 系统走 `governed` 路径，风控非 normal / canDo 拒时诚实 blocked
- **AND** MUST NOT 置 `operatorOverride`，MUST NOT 让结构化发帖跳过风控闸

### Requirement: 委托层通知由底层业务结果卡承担、发帖失败兜底、无变化对账静默

委托层 MUST NOT 为任务的常规状态迁移（`queued`、`executing`、`completed`、`waiting_approval`）主动推送自有的任务进度卡。每个任务的执行结果 SHALL 由其底层动作的**正常业务结果卡**承担：评论由评论链的结果卡回报；发帖成功由发布人审卡自证（成功不重复报绿）；发帖等待人审由发布人审卡本身承担。

**终态失败兜底**（红线：绝不静默失败）——没有独立业务结果卡的终态失败，委托层 MUST 补一张诚实卡：

- **发帖类终态失败**（`failed`，或仍有缺口的 `partially_completed`）：MUST 补发失败 / 部分完成结果卡。
- **评论类「起跑前触发闸失败」**（`failed`、0 成功、终态码 `non_retryable_failure`——人设未绑 / 联系方式缺 / 平台不支持 / 未接线等在异步任务起跑前早退，评论链从未起跑、`postResultCard` 从未发过）：MUST 补发一张诚实失败卡。
- **评论类起跑后失败**（`max_attempts` / `deadline` 等，评论链已发结果卡）：MUST NOT 由委托层补发（避免与 `postResultCard` 双发）。

精确旧 slash 写命令（`source=legacy_command`）直接排队时 SHALL **静默受理**——只保留已读表情，MUST NOT 发送队列提示卡；结果由该任务自身的业务结果卡回报。自然语言委托仍先展示结构化确认卡（不受影响）；用户主动请求的控制命令（查看 / 暂停 / 取消）与卡片按钮回卡不受影响。

委托任务处于 `waiting_approval` 时保留有界的审批结果对账，但当审批、真实进度、控制意图和终态结果均未变化时，MUST NOT 发送新的用户通知或递增用于卡片控制的 task version；内部 claim/lease MAY 更新，但不得把无变化心跳呈现为新的业务进度。

#### Scenario: 发帖失败仍诚实通知
- **WHEN** 一个委托发帖任务达到最大尝试仍 0 成功 → `failed`
- **THEN** 委托层补发一张红色失败结果卡（含真实完成数 0/N），MUST NOT 静默

#### Scenario: 评论起跑前触发闸失败仍诚实通知
- **WHEN** 一个委托评论任务在异步任务起跑前因人设未绑 / 联系方式缺 / 平台不支持 / 未接线而以非重试失败终结（`failed`、0 成功、终态码 `non_retryable_failure`）
- **THEN** 委托层补发一张红色「评论任务未触发」结果卡（含起跑失败的人类可读原因），MUST NOT 静默

#### Scenario: 评论起跑后失败不重复报卡
- **WHEN** 一个委托评论任务已起跑到终态失败（评论链已按账号发出结果卡），终态码为 `max_attempts` / `deadline`
- **THEN** 委托层 MUST NOT 再叠加一张失败卡（避免与评论链 `postResultCard` 双发）

#### Scenario: 发帖成功不重复报绿
- **WHEN** 委托发帖经人审通过并发布 → `completed`
- **THEN** 委托层 MUST NOT 再发绿色成功卡（成功由发布人审卡自证）
