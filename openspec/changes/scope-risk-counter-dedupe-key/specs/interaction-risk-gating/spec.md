## MODIFIED Requirements

### Requirement: 边缘确认的真实动作必须先落持久 outbox 再推进

云端 SHALL 在收到边缘对真实平台动作的确认回执后，**先把该既成事实同步提交进一张带 `execution_target` 的持久 outbox 表，再推进浏览闭环**。该路径 MUST NOT 依赖进程内事件总线上的 fire-and-forget 异步写，MUST NOT 以「异常只记日志」的方式吞掉记账失败。

具体要求：

- outbox 行 MUST 带 `execution_target`（服务端注入），worker MUST 只认领本 target 的行；MUST 带去重键。Edge 来源事实的去重键 MUST 同时绑定已认证会话中的账号 ID、Edge 环境 ID、原始回执信封时间戳、原始回执信封 ID、动作及既有事实判别字段；边缘重发同一原始回执信封 MUST 只产生一行，不同账号、不同环境或不同原始时间戳的回执 MUST NOT 因复用同一顺序信封 ID 而碰撞。
- 认领 MUST 使用认领令牌 + 租约 + 跳锁，并 MUST 在进程启动时回收租约过期的在途行——与委托任务 worker 同一范式。
- apply MUST 在单个数据库事务内同时完成「写入计数」与「标记 outbox 行已应用」，且 MUST 由数据库唯一约束保证 exactly-once，MUST NOT 用进程内集合去重。
- 内存计数 MUST 只在 apply 成功时递增，且 MUST 只有这一条递增路径（回执处理时 MUST NOT 先加一次）。
- 入队失败 MUST 视为本次记账失败：MUST 告警，并 MUST 使该账号停止继续下发自动互动命令，MUST NOT 当作无事发生继续浏览闭环。
- 重试 MUST 有界；超限 MUST 转入死信并告警，MUST NOT 静默丢弃。outbox 积压量与死信量 MUST 可被读取。

#### Scenario: 崩在回执与记账之间不丢账

- **WHEN** 边缘确认了一次真实点赞，云端提交了 outbox 行，随后进程在 apply 之前崩溃并重启
- **THEN** 重启后该行被回收并 apply，该次点赞 MUST 出现在计数里
- **AND** 该次点赞 MUST 只被计入一次

#### Scenario: 重复投递只记一次

- **WHEN** 边缘因重连重发了账号、环境、时间戳、信封 ID 和事实内容均相同的动作确认信封
- **THEN** outbox MUST 只保留一行，计数 MUST 只增加一次

#### Scenario: 不同账号或环境不被顺序 ID 误去重

- **WHEN** 两个不同账号或不同 Edge 环境提交了相同顺序信封 ID、动作和原始时间戳的确认回执
- **THEN** Cloud MUST 为两条事实生成不同去重键
- **AND** 两条事实 MUST 分别进入各自账号的计数

#### Scenario: 进程重启后复用顺序 ID 不碰撞

- **WHEN** 同一账号和环境的新 Edge 进程复用了旧顺序信封 ID，但原始信封时间戳不同
- **THEN** Cloud MUST 为新事实生成不同去重键
- **AND** 新事实 MUST 正常进入该账号的计数

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
