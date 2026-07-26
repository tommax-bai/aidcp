## MODIFIED Requirements

### Requirement: 边缘确认的真实动作必须先落持久 outbox 再推进

云端 SHALL 在收到边缘对真实平台动作的确认回执后，**先把该既成事实同步提交进一张带 `execution_target` 的持久 outbox 表，再推进浏览闭环**。该路径 MUST NOT 依赖进程内事件总线上的 fire-and-forget 异步写，MUST NOT 以「异常只记日志」的方式吞掉记账失败。

具体要求：

- outbox 行 MUST 带 `execution_target`（服务端注入），worker MUST 只认领本 target 的行；MUST 带去重键，边缘重发同一回执信封 MUST 只产生一行。
- 认领 MUST 使用认领令牌 + 租约 + 跳锁，并 MUST 在进程启动时回收租约过期的在途行——与委托任务 worker 同一范式。
- apply MUST 在单个数据库事务内同时完成「写入计数」与「标记 outbox 行已应用」，且 MUST 由数据库唯一约束保证 exactly-once，MUST NOT 用进程内集合去重。
- 当 exactly-once 约束使用部分唯一索引时，apply 的 conflict target MUST 带可由 PostgreSQL 推断该索引的匹配谓词；MUST NOT 让已确认事实因 conflict target 与部署索引不匹配而持续失败或进入死信。
- 该 conflict target 与部署索引的契合性 MUST 由真实 PostgreSQL 合约测试验证；只模拟 query 结果、不执行 PostgreSQL 索引推断的内存桩 MUST NOT 作为充分验证。
- 内存计数 MUST 只在 apply 成功时递增，且 MUST 只有这一条递增路径（回执处理时 MUST NOT 先加一次）。
- 入队失败 MUST 视为本次记账失败：MUST 告警，并 MUST 使该账号停止继续下发自动互动命令，MUST NOT 当作无事发生继续浏览闭环。
- 重试 MUST 有界；超限 MUST 转入死信并告警，MUST NOT 静默丢弃。outbox 积压量与死信量 MUST 可被读取。

#### Scenario: 崩在回执与记账之间不丢账

- **WHEN** 边缘确认了一次真实点赞，云端提交了 outbox 行，随后进程在 apply 之前崩溃并重启
- **THEN** 重启后该行被回收并 apply，该次点赞 MUST 出现在计数里
- **AND** 该次点赞 MUST 只被计入一次

#### Scenario: 重复投递只记一次

- **WHEN** 边缘因重连重发了同一条动作确认信封
- **THEN** outbox MUST 只保留一行，计数 MUST 只增加一次

#### Scenario: 部分唯一索引可被 apply 推断

- **WHEN** `risk_counters.outbox_id` 由 `WHERE outbox_id IS NOT NULL` 的部分唯一索引约束，worker apply 一条已认领事实
- **THEN** PostgreSQL MUST 接受该 conflict target 并提交计数及 outbox 状态
- **AND** 对同一 `outbox_id` 的重复写入 MUST 仍只保留一条计数

#### Scenario: 入队失败不静默继续

- **WHEN** 一次真实动作已被边缘确认，但 outbox 入队因数据库不可写而失败
- **THEN** 系统 MUST 告警并停止对该账号继续下发自动互动命令
- **AND** MUST NOT 把这次已发生的动作当作不存在而继续浏览闭环

#### Scenario: 超限进死信且可见

- **WHEN** 某条 outbox 行的 apply 连续失败达到重试上限
- **THEN** 该行 MUST 转入死信状态并产生告警
- **AND** 死信数量 MUST 可被读取，MUST NOT 被静默删除

#### Scenario: 记账不改变判定语义

- **WHEN** 一次动作的回执抵达时该账号配额已耗尽
- **THEN** 该动作 MUST 照常入队并最终计入（既成事实照记，与既有「绝不因策略事后重判而丢弃」一致）
- **AND** 节奏饱和告警所依据的判定 MUST 仍取自写入前的判定值，MUST NOT 改为读取含这一笔的新状态
