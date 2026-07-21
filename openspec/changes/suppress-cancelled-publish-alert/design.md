## Context

发布候选的 `needs_review` 状态是复用终态：人工在审批卡、客户端或面板中明确驳回会进入该状态，定时发布对账耗尽、调度数据异常和部分发布准备失败也可能进入同一状态。委托任务等待审批时目前只读取状态枚举，因此无法区分预期取消与真实异常，并把两者都转成 `candidate_terminal_needs_review` 失败。

委托任务与发布日志位于同一 Cloud 服务，但审批与对账异步且可能跨进程重启，判定依据必须持久化，不能依赖内存或临时审批信号文件。

## Goals / Non-Goals

**Goals:**

- 让明确的人工驳回在异步对账中收敛为用户取消，而不是失败。
- 不为用户取消发送委托层失败或部分完成报警。
- 对无法证明为用户取消的 `needs_review` 继续失败并报警。
- 保留真实尝试次数、成功数和未下发证据。

**Non-Goals:**

- 不改变审批卡、客户端取消按钮或平台下发流程。
- 不重新定义所有 `needs_review` 来源，也不迁移历史记录。
- 不新增协议字段、数据库表或数据库列。
- 不改变用户主动取消整条委托任务的既有接口。

## Decisions

### 1. 在发布日志 JSONB 中持久化明确驳回证据

`PublishLogStore.rejectPendingApproval` 在完成 `pending_approval -> needs_review` 的同一条条件更新中写入 `publish_metadata.approvalDecision.kind = user_rejected` 和决定时间。该方法只承载人工驳回入口，因此标记与状态变更原子落库，进程重启后仍可对账。

备选方案是仅根据 `needs_review` 推断取消，但该状态还覆盖真实异常，会吞掉报警；读取 `/tmp` 审批信号则不能跨主机或清理/重启边界，均不采用。

### 2. 委托候选快照只暴露归一化证据

Cloud 从发布元数据解析出 `userRejected` 布尔事实交给委托执行器。执行器仅在 `status === needs_review && userRejected` 时返回新的 `cancelled` 执行结果；缺失标记或其他 `needs_review` 继续返回既有非重试失败。

这样委托模块不依赖发布元数据的内部 JSON 结构，也对历史行采取失败闭合。

### 3. Worker 以取消语义结算尝试和任务

`cancelled` 执行结果把当前尝试记为 `skipped + not_dispatched`，再以 `honestTerminalStatus(progress, 'cancelled')` 收敛任务：零成功为 `cancelled`，已有真实成功则保留 `partially_completed` 与实际计数。终态码固定为 `candidate_cancelled_by_user`，证据指向原发布记录。

### 4. 通知层按明确取消终态码静默

委托失败回执对 `candidate_cancelled_by_user` 返回 `null`。这同时覆盖零成功的 `cancelled` 和有历史成功的 `partially_completed`，避免后者被误发“部分完成”报警。发布审批卡/客户端已有取消结果展示，委托层无需重复通知。

## Risks / Trade-offs

- [历史人工驳回记录没有新标记] → 不回填、不猜测；历史或证据缺失的 `needs_review` 继续按失败处理。
- [发布元数据可能为空] → SQL 用空 JSON 对象作为合并起点，且只在条件状态更新成功时写入。
- [未来新增非人工调用误用 `rejectPendingApproval`] → 方法名、类型与测试固定其“人工驳回”语义；其他异常路径继续使用各自状态更新方法。
- [部分完成任务静默后运营看不到汇总卡] → 这是用户明确取消后的预期静默；真实计数和终态仍保存在任务与面板中。

## Migration Plan

无数据库迁移。代码上线后新发生的人工驳回会带持久化标记；回滚时新增 JSONB 字段被旧代码忽略。当前任务仅开发验证，不执行合并或部署。

## Open Questions

无。
