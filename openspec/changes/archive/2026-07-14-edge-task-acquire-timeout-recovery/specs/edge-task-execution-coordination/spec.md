## MODIFIED Requirements

### Requirement: cloud 必须等待 edge acquired/quiesced 再发首条业务命令

protocol v2 SHALL 提供 `edge.task.acquire`、`edge.task.acquired`、`edge.task.release`、`edge.task.released`。cloud 发出 acquire 后 MUST 等 edge 回 `acquired`；该回执同时表示当前浏览原子动作已到安全边界、未开始的普通浏览命令已取消且租约已经生效。未收到 acquired 时 MUST NOT 下发该任务第一条业务命令。每个 acquire MUST 携可选的本地等待时长；edge MUST 从收到申请起在该时长内完成 quiesce 并授予租约，逾期仍未授予时 MUST 取消该排队申请，MUST NOT 在 cloud 已超时后再授予无主租约。

#### Scenario: 在途 navigation.back 先收尾
- **WHEN** `navigation.back` 已在 edge 执行中，cloud 申请发布租约
- **THEN** edge 等该原子动作收敛到安全边界后才回 `edge.task.acquired`，cloud 随后才发 `navigate_entry`

#### Scenario: acquire 超时不越权发布
- **WHEN** 目标 edge 离线、协议过旧或在超时内未回 acquired
- **THEN** 发布/评论任务诚实失败或保持可重试状态，且零条业务写命令被下发，MUST NOT 回退到无租约执行

#### Scenario: edge 等待期届满不授予陈旧任务
- **WHEN** 普通浏览原子动作持续到 acquire 的本地等待上限之后
- **THEN** edge 移除该未获授任务、回到可继续协调的状态，MUST NOT 在上限之后发送 `acquired` 或持有该任务租约

### Requirement: 释放、断线与超时有界且幂等

租约 SHALL 有 idle/absolute 有界期限，匹配任务命令 MAY 刷新 idle 期限。cloud 的任务体 MUST 在 `finally` 发送 release；edge 对重复 acquire/release MUST 按 `taskId` 幂等。同 edge 重连、cloud 断线、租约到期或执行异常 MUST 使旧租约最终失效并收敛到下一任务或安全浏览状态，MUST NOT 永久冻结。cloud acquire 超时前尚未收到 `acquired` 时，MUST 主动发送该 `taskId` 的 release；若随后收到相同 edge 的迟到 `acquired`，MUST 再次发送 release，直到 edge 收敛或取消记录到期。

#### Scenario: 任务抛错仍释放
- **WHEN** 发布或评论任务体中途抛异常
- **THEN** cloud finally 发送 release，edge 回 released 并授予下一等待任务或恢复浏览

#### Scenario: release 回执丢失可自愈
- **WHEN** cloud 已发送 release 但回执丢失
- **THEN** 重复 release 不产生副作用，且 edge 不会因一次丢包永久持有租约

#### Scenario: acquire 已超时但 acquired 迟到
- **WHEN** cloud 已因 acquire timeout 终止等待，edge 随后才回相同 taskId 的 `acquired`
- **THEN** cloud 不下发业务命令并再次发送 release，edge 释放该租约；任务不会一直占用浏览器直到自然 lease expiry

#### Scenario: 同 edge 重连不继承旧所有权
- **WHEN** 持有租约的 edge 连接断开并以同 edgeId 重连
- **THEN** 旧连接租约失效，cloud 在途任务诚实失败/重试；新连接从无租约安全状态开始，MUST NOT 静默续跑旧命令
