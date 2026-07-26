## ADDED Requirements

### Requirement: 批准后跨进程 trigger SHALL 只返回短应答

API 在批准决策落库后 SHALL 通过版本化内部 HTTP 端口向 automation 发送发布触发，请求 MUST 携带 `requestId`、授权 `revision`、`executionTarget` 与 `kind`；`kind` 只能是首写授权的 `decision_recorded` 或已决授权上的人工重批 `human_reconfirm`。automation SHALL 在完成版本、target、请求字段校验并受理唤醒或识别重复后立即返回 `accepted` 或 `duplicate`，MUST NOT 等待 dispatcher、Edge 指令、平台提交或平台发布完成。

`accepted` 与 `duplicate` 只表示本次内部 trigger 已受理或已去重，MUST NOT 被映射或展示为 `dispatching`、`submitted`、`published` 或任何发布成功状态；网络超时或非成功响应同样 MUST NOT 被改写成发布失败或发布成功。

#### Scenario: 首次 trigger 快速受理
- **WHEN** API 为本环境一条新落库的批准决策发送 `decision_recorded`，automation 完成请求校验并登记一次唤醒
- **THEN** automation 返回 `accepted`，响应不等待该草稿真正下发，草稿的 dispatch、submit 与 publish 状态保持由各自持久生命周期决定

#### Scenario: 重复 trigger 不冒充下发
- **WHEN** API 因 HTTP 结果未知而重发同一 `requestId + revision + decision_recorded`
- **THEN** automation 返回 `accepted` 或 `duplicate` 且只保留一次等价唤醒，调用方 MUST NOT 因任一短应答把草稿标为已下发、已提交或已发布

#### Scenario: target 不匹配时拒绝受理
- **WHEN** trigger 的 `executionTarget` 与 automation 本地目标不一致或本地目标缺失无效
- **THEN** automation 拒绝受理且不唤醒 dispatcher，MUST NOT 返回 `accepted` 或 `duplicate`

### Requirement: 直接 trigger SHALL 只是持久授权补偿链的低延迟加速器

`publish_approval_decision`、与批准决策同事务写入的 `PublishApproved` outbox，以及按本地 `executionTarget` 过滤的 pending-approval scan SHALL 继续承担不丢任务与重启恢复。直接 HTTP trigger 只能缩短正常路径延迟，MUST NOT 成为授权事实、唯一投递通道或删除持久补偿扫描的理由。

直接 trigger 失败或结果未知时，API MUST 保留已经提交的授权决策与 outbox；automation MUST 能通过 outbox 消费或 pending scan 重新发现仍可下发的授权。补偿路径在真正驱动发布前 MUST 重新校验授权 revision、内容版本与本地 target，MUST NOT 因曾经收到 trigger 而绕过这些闸门。

#### Scenario: trigger 丢失后由持久链补投
- **WHEN** 批准决策与 `PublishApproved` outbox 已在同一事务提交，但 API 到 automation 的直接 trigger 在送达前断链
- **THEN** 授权不回滚且不被标为发布失败，automation 随后通过 outbox 或 target-filtered pending scan 发现该授权，并在重校验后推进一次等价下发

#### Scenario: automation 重启不丢已批草稿
- **WHEN** automation 在直接 trigger 受理后、真正下发前重启
- **THEN** 进程内唤醒丢失不影响持久授权，重启后的 pending scan 仍能恢复该草稿，且短应答本身不被当作已消费证据

### Requirement: 首写授权与人工重批 trigger SHALL 保持不同语义

API SHALL 对首次写入授权的路径发送 `decision_recorded`，对人工操作者再次批准一条已经 first-writer-wins 决定的授权发送 `human_reconfirm`。automation MUST NOT 仅以 `requestId + revision` 的首写去重吞掉 `human_reconfirm`；每次有效人工重批 SHALL 执行幂等的账号熔断清除并唤醒一次 pending scan，即使同一 revision 的 `decision_recorded` 已经处理。

自动批准只能产生 `decision_recorded`，MUST NOT 伪造 `human_reconfirm`，也 MUST NOT 清除账号下发熔断。HTTP 重试可以重复执行幂等唤醒，但 MUST NOT 重复消费授权或启动并行发布序列。

#### Scenario: 已决授权上的人工重批清除熔断
- **WHEN** 账号处于下发熔断中，运营再次批准一条已经存在同 revision 授权的草稿
- **THEN** API 发送 `human_reconfirm`，automation 不被既有 `decision_recorded` 去重挡住，幂等清除该账号熔断并触发 pending scan，同时仍由持久授权与版本校验决定哪些草稿可以下发

#### Scenario: 自动批准不得清除熔断
- **WHEN** 自动批准为熔断中账号写入新授权并发送 `decision_recorded`
- **THEN** automation 可以记录唤醒但保持该账号熔断，授权信号继续持久挂起且不被消费，直到后续有效人工重批明确清除熔断

#### Scenario: 人工重批重试不产生并行发布
- **WHEN** 同一次人工重批因 HTTP 结果未知被重复投递
- **THEN** 熔断清除与 scan 唤醒保持幂等，既有在途去重与账号链仍保证同一授权不会启动并行发布序列

### Requirement: publish approval authority SHALL 通过内部 HTTP 暴露 revision CAS

API 作为 publish approval authority 的所有者 SHALL 通过版本化、内部鉴权且 target 隔离的 HTTP 端口提供 `getApproval`、`listPendingDispatch`、`voidApproval`、`markDispatching`、`markConsumed`、`releaseToPending` 与 `setBlockedReason`；automation MUST 通过该端口读取和推进授权，MUST NOT 直接连接或写入 API 的授权表。

每个状态推进请求 MUST 携带 `requestId`、期望 `revision` 与 `executionTarget`，API 只能在当前有效授权的 revision 和 target 同时匹配时执行条件更新。revision 冲突、记录不存在、target 不匹配、authority 不可达与 transport 结果未知 MUST 保持可区分，MUST NOT 被折叠为空列表、默认授权、成功推进或发布终态。

#### Scenario: 当前 revision 推进成功
- **WHEN** automation 对本地 target 的有效授权以匹配 revision 调用 `markDispatching`
- **THEN** API 原子推进该 revision 并返回更新后真态，automation 才能继续相应下发阶段

#### Scenario: 旧 revision CAS 不修改新授权
- **WHEN** automation 使用过期 revision 调用 `voidApproval`、`markConsumed`、`releaseToPending` 或 `setBlockedReason`
- **THEN** API 返回可识别的 revision conflict，当前新 revision 保持不变，automation MUST 重新读取授权而不是把冲突当成功

#### Scenario: authority 不可读时不可逆发布 fail closed
- **WHEN** automation 在驱动不可逆平台动作前无法从 approval authority 读取有效授权，或读取结果为 transport unknown
- **THEN** automation 不下发平台发布命令、不伪造授权或终态，并保留可补偿状态与可观测错误供后续重试或人工处理

#### Scenario: 另一 target 的旧全局唯一键冲突不得串用授权
- **WHEN** approval 首写被现存全局 `requestId` 唯一键拒绝，且按本地 `executionTarget` 查不到活跃授权
- **THEN** API 以稳定错误 fail closed，不得返回另一 target 的 `alreadyDecided` 或 revision，也不得据此发送 `human_reconfirm`
- **AND** 解除该跨 target liveness gap 的物理键替换必须作为独立 contract migration 交付，MUST NOT 混入本 change 的 expand migration
