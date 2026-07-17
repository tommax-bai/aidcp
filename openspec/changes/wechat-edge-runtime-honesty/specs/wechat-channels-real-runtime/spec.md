## ADDED Requirements

### Requirement: 浏览器关闭必须凭实证，未确认不得报成功

视频号 browser sidecar SHALL 只在底层 provider 确认浏览器真死之后才丢弃浏览器句柄与会话引用。关闭未被确认时，sidecar MUST NOT 把该次关闭报成成功，SHALL 保持在不可用态并向调用方抛出未确认信号。处于不可用态时再次调用关闭，SHALL 重新发起一次真实的关闭尝试（而不是因为句柄已被丢弃就空转返回成功）。

「浏览器仍被占用 / 调试端口仍应答」SHALL 被视为**未确认**，MUST NOT 被判为「已关闭」，也 MUST NOT 被判为结构性失败而放弃后续尝试。

#### Scenario: 关闭未获确认

- **WHEN** 底层 provider 经软停止、重发停止、OS 级强杀后调试端口仍应答，如实返回「未确认已死」
- **THEN** sidecar SHALL 保留浏览器句柄、置不可用态、向上抛出未确认信号
- **AND** SHALL NOT 向任何上层报告「浏览器已关闭」

#### Scenario: 未确认后的第二次关闭

- **WHEN** 上一次关闭未获确认、状态停在不可用态，云端在下一个 offboarding 周期重发同一 offboardId 触发第二次关闭
- **THEN** sidecar SHALL 真的再发起一次关闭并重新确认
- **AND** 若这次确认真死，SHALL 报成功；若仍未确认，SHALL 再次抛出未确认信号
- **AND** MUST NOT 因为句柄已在上一次被丢弃而直接返回成功

#### Scenario: 确认真死

- **WHEN** provider 确认调试端口连续不应答
- **THEN** sidecar SHALL 丢弃句柄、置已关闭态并报成功

### Requirement: 运行时 SHALL 接住关闭失败并回落到暂停而非静默退出

视频号运行时的 shutdown / terminate SHALL 遵循与其他平台核心一致的通用生命周期契约：sidecar 关闭未获确认时，运行时 MUST NOT 吞掉该信号、MUST NOT 无条件结束进程。关闭 SHALL 使用两阶段顺序：先停止/排空 connector、保持 Cloud client 连接，再确认 sidecar 真死；只有确认成功后才允许关闭 Cloud client 与退出进程。运行时 SHALL 如实向外壳上报关闭未确认，并回落到「暂停但不退出」——保持进程与云端连接存活，使浏览器仍占用的事实可被观测、可被下一次关闭指令重试。

回拨路径 SHALL 显式规定：关闭 attempt 结束后必须释放本次串行闩，暂停态由「下一次关闭指令确认浏览器真死」拨回可退出，或由运营 / 外壳显式终止进程解除；MUST NOT 因永久 `shuttingDown` 布尔闩或一次性 signal listener 形成只进不出的暂停态。

#### Scenario: 关闭未确认时收到终止信号

- **WHEN** 运行时收到 SIGTERM / SIGINT / `lifecycle.close`，而 sidecar 关闭抛出未确认信号
- **THEN** 运行时 SHALL 向外壳上报「关闭失败 / 浏览器仍在运行」
- **AND** SHALL NOT 调用 `process.exit(0)`
- **AND** SHALL 保持进程存活于暂停态，等待下一次关闭指令重试
- **AND** SHALL NOT 在浏览器确认前调用 Cloud client close

#### Scenario: 关闭确认成功时正常退出

- **WHEN** 运行时收到终止信号且 sidecar 确认浏览器真死
- **THEN** 运行时 SHALL 正常结束进程

#### Scenario: 外壳的关闭失败分支被真正接线

- **WHEN** 视频号运行时上报关闭未确认
- **THEN** 外壳既有的「关闭失败」处理分支 SHALL 被触发（不再是对视频号而言的死代码）
- **AND** 该环境的浏览器槽位 SHALL NOT 被记为已空出

#### Scenario: 关闭失败后第二次指令成功

- **WHEN** 第一次关闭未确认、运行时已经上报 `lifecycle.close_failed`，随后收到第二次 IPC close 或 SIGINT/SIGTERM
- **THEN** 运行时 SHALL 再次调用 sidecar close，而不是因旧 promise / boolean / once listener 直接返回
- **AND** 若第二次确认浏览器真死，才 SHALL 关闭 Cloud client 并正常退出

### Requirement: 解绑状态 SHALL 同时挡住连接器与浏览器授权

已解绑（持久化的解绑标记为真）的环境，其浏览器授权 SHALL 与连接器受同一组前提约束。运行时在启动授权前 SHALL 复查解绑标记；标记为真时 MUST NOT 拉起浏览器、MUST NOT 弹二维码、MUST NOT 从存活的浏览器 profile 读回候选凭据并落盘。

#### Scenario: 已解绑环境随外壳重启

- **WHEN** 环境已被解绑（凭据已清、云端已记 cleared），外壳因 profile 物理删除失败而再次拉起该环境的核心
- **THEN** 连接器 SHALL 不启动
- **AND** 授权初始化 SHALL 被同一道解绑闸挡住，不拉起浏览器、不弹二维码
- **AND** SHALL NOT 有任何凭据被写回磁盘

#### Scenario: profile 站点 cookie 仍然存活

- **WHEN** 已解绑环境的浏览器 profile 未被清理、其中的站点 cookie 仍可读出有效候选
- **THEN** 运行时 SHALL NOT 读取或落盘该候选
- **AND** 云端按 cleared 记账的墓碑游标 SHALL 能正常推进到 purged，不被边缘重开的浏览器持续阻塞

### Requirement: 解绑 SHALL 作废在途授权循环

解绑 SHALL 不仅停止连接器，还 SHALL 作废任何正在进行的授权尝试。运行时 SHALL 维护解绑代次标记；所有可能跨越解绑的 await 返回后、凭据写盘前和候选 session 发布为 active 前 SHALL 复查代次，若代次已因解绑而推进，该次写盘与内存发布 SHALL 被丢弃。该要求同时覆盖浏览器 candidate 保存与 stored legacy binding migration 保存，MUST NOT 只保护授权循环末尾的一处 `store.save(...)`。

#### Scenario: 解绑命中扫码后的网络等待

- **WHEN** 授权循环正处于扫码后的网络等待中（可持续数十秒），此时解绑命令到达并完成、上报 cleared
- **THEN** 授权循环 SHALL 被作废
- **AND** 循环从等待中恢复后，其凭据写盘 SHALL 因代次复查失败而被丢弃
- **AND** 刚被删除的加密凭据 MUST NOT 被写回磁盘

#### Scenario: 未被解绑的正常授权

- **WHEN** 授权循环期间没有解绑发生、代次未变
- **THEN** 凭据 SHALL 正常落盘，授权照常完成

#### Scenario: 解绑命中 legacy binding migration

- **WHEN** stored legacy binding 已完成身份/probe、尚未执行迁移写盘时解绑推进代次
- **THEN** migration save 与 active-session 发布 SHALL 被丢弃
- **AND** encrypted store SHALL 保持 clear 后的空状态

### Requirement: 回复发送的确定判决 SHALL 落投递箱

对某个 attempt 做出的**确定判决**（连接器未启动、命令校验不通过——即边缘明确知道该回复压根没发生任何平台调用）SHALL 被持久化进 result outbox 并触发投递，使云端能收到诚实回执。这类结果 MUST NOT 被静默丢弃，MUST NOT 只依赖需要既有 claim 的持久化路径而在无 claim 时被空 catch 吞掉。connector / reply sender SHALL 通过内部可判别结果显式携带「已持久化或重放 / 无 claim 需持久化 / 拒绝持久化」决策；runtime MUST NOT 仅凭相同的 `invalid_command` payload 或异常字符串猜测来源。

`invalid_scope`（外来 scope）与幂等命名空间冲突（幂等键已绑定到另一 attempt）两类 SHALL 保持故意的 fail-closed 拒写——外来 scope 不该写进本账号的幂等命名空间。该拒写 SHALL 与上述确定判决分开处理，MUST NOT 共用同一个静默 catch；拒写时 SHALL 留下可检索的日志。

无 claim outbox 写入 SHALL 同时校验 exact runtime scope、attemptId 与 idempotencyKey 未绑定到其他值；相同结果 MAY 幂等重放，任何 namespace 冲突 SHALL 拒写。

#### Scenario: 重连窗口内收到回复命令

- **WHEN** 云端已能解析到该边缘并派发回复命令，但连接器尚未启动（重连时的启动前窗口）
- **THEN** 边缘 SHALL 构造确定的失败结果并持久化进 result outbox
- **AND** SHALL 在投递箱可投递时把该结果送达云端
- **AND** 云端 SHALL NOT 只收到沉默；该 attempt SHALL NOT 永久停留在 dispatched

#### Scenario: 命令校验不通过

- **WHEN** 回复命令未通过校验
- **THEN** 边缘 SHALL 持久化 `invalid_command` 失败结果并投递
- **AND** 该结果 SHALL 如实标注为「未发生平台调用」，SHALL NOT 被后续对账写成 ambiguous

#### Scenario: 外来 scope 的回复命令

- **WHEN** 回复命令的 scope 与本运行时绑定不匹配
- **THEN** 边缘 SHALL 拒绝写入本账号幂等命名空间、不落投递箱
- **AND** SHALL 记录一条可检索的拒写日志，说明这是 fail-closed 拒写而非执行失败

### Requirement: 解绑墓碑 SHALL 有明确回拨路径且不得误报原因

边缘的解绑墓碑 MUST NOT 单方面永久钉死该环境，也 MUST NOT 仅凭 capability、`offboardPending=false` 或普通 runtime-controls version 自行清除。Cloud SHALL 在 welcome 的 `interactionRecovery` 中以可选 `rebindProof { accountId, envKey, purgedOffboardId }` 提供权威回拨证据；只有 active ownership 已重新建立、exact logical account/env binding 可由 Cloud 证明、且相同 scope 的对应 offboard 已 `purged` 时才能下发。

Edge SHALL 仅在 proof 的 accountId、envKey、purgedOffboardId 与当前 runtime scope 及本地 completed `cleared` / `already_cleared` 墓碑逐字段匹配时 durable 清除墓碑。缺 proof、旧 peer、畸形/错 scope proof、Cloud 查询失败、offboard 仅 tombstoned 或尚未重新归属时均 SHALL 保持 fail closed。

墓碑生效期间，边缘 SHALL 如实报告不可用原因为「本机解绑墓碑」，MUST NOT 报成「云端没协商能力」等与真实原因无关的措辞。

#### Scenario: 墓碑期内启动

- **WHEN** 本机解绑标记为真、云端亦仍视该环境为已解绑
- **THEN** 连接器 SHALL 不启动
- **AND** 日志 SHALL 指明原因是本机解绑墓碑（含 offboardId），SHALL NOT 声称云端未协商能力

#### Scenario: 云端重新绑定同一环境

- **WHEN** 对应 offboard 已 purged、Cloud 已重新建立同一环境的 active ownership，并在 welcome 下发 exact-scope rebindProof
- **THEN** 边缘 SHALL NOT 因本机遗留的解绑墓碑而拒绝启动连接器
- **AND** 本机墓碑 SHALL 随该次重新绑定被清理，环境恢复正常运行

#### Scenario: 仅收到 offboardPending false

- **WHEN** 本地仍有墓碑，而 welcome 仅有 `offboardPending=false` / interaction capability / runtime-controls snapshot，没有 exact rebindProof
- **THEN** Edge SHALL 保持墓碑，不启动 connector 或授权
- **AND** MUST NOT 把普通握手或旧 Cloud 误判成 purge 后的新绑定

#### Scenario: Rebind proof 不匹配本地墓碑

- **WHEN** proof 的 accountId、envKey 或 purgedOffboardId 任一项与当前 scope / 本地墓碑不匹配
- **THEN** Edge SHALL 拒绝清墓碑并记录不含敏感值的具名 reason
- **AND** SHALL NOT 启动 connector、授权或任何平台写

#### Scenario: 未协商能力与墓碑同时存在

- **WHEN** 云端确实未协商 interaction 能力，且本机无解绑墓碑
- **THEN** 日志 SHALL 如实报告为云端未协商，两类原因 SHALL 可被区分
