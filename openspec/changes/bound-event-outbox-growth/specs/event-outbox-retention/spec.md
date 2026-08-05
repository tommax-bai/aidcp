## ADDED Requirements

### Requirement: 每条 outbox 主题必须有显式保留裁定，遗漏由机械闸拦下

`event_outbox` 是队列不是账本。系统 SHALL 维护一份**穷举**的 outbox 主题登记表，
保留策略表 MUST 逐条覆盖该登记表。某主题确实不需要剪裁时，MUST 在登记表内**显式写明理由**
（例如恒为空、或由别处剪），MUST NOT 靠「不出现在保留策略表里」来表达。

新增主题却没有对应保留裁定 SHALL 当场使编译或验收检查失败，
MUST NOT 只在运行期表现为该主题在共用生产库上无界增长。

#### Scenario: 新增主题未登记保留裁定

- **WHEN** 代码新增一个会写入 `event_outbox` 的主题，但保留策略表未覆盖它
- **THEN** 穷举检查 MUST 失败并点名该主题
- **AND** MUST NOT 因为「运行起来看不出异常」而放行

#### Scenario: 主题确实不需要剪裁

- **WHEN** 某主题经裁定不需要剪裁
- **THEN** 登记表 MUST 记录该裁定与理由
- **AND** 检查 SHALL 通过，而不是要求为它编一条无意义的保留期

#### Scenario: 保留策略表与登记表漂移

- **WHEN** 保留策略表里出现登记表中不存在的主题名
- **THEN** 穷举检查 MUST 失败
- **AND** MUST NOT 静默忽略该条（它意味着有一方的主题名写错了，那条主题实际无人剪裁）

### Requirement: 剪裁上界必须是消费者游标，承重主题禁止强删

有消费者的主题 SHALL 只剪「全部必需消费者都已越过」的 id（各消费者进度的最小值）作为上界，
并在该上界之内按保留期剪裁。任一必需消费者尚无消费进度行时，本轮 MUST NOT 剪任何行。

**承重主题 MUST NOT 配置无视消费进度的强删兜底**：
`config_mirror.bump`（配置失效信号，删掉未投递的等于一处配置永远不 reload）与
`sync_read.changed`（同步读变更通知）SHALL 一律按游标下界剪，MUST NOT 设强删上限。

#### Scenario: 消费者已追平，存量到龄

- **WHEN** 某主题的必需消费者游标已推进，且游标以内存在超过保留期的行
- **THEN** 剪裁 SHALL 按有界批量删除这些行
- **AND** MUST NOT 删除游标之后、尚未投递的行

#### Scenario: 消费者尚无进度行

- **WHEN** 某主题声明了必需消费者，但该消费者在本 target 上还没有任何消费进度行
- **THEN** 本轮 MUST NOT 剪该主题任何行
- **AND** 确有到龄行堆积时 SHALL 具名报出是哪些消费者挡住了剪裁

#### Scenario: 存量远大于单轮批量上限

- **WHEN** 某主题存量行数远超单轮删除上限
- **THEN** 剪裁 SHALL 按轮次分批推进、保持有界，MUST NOT 用一条语句锁住整张表
- **AND** 「一轮没清空」MUST NOT 被判为剪裁失败

### Requirement: 变更通知主题必须登记为按游标剪裁

两条变更通知主题 SHALL 出现在保留策略表中，按各自消费者的游标下界剪裁，
且均 MUST NOT 设强删兜底：`sync_read.changed`（消费者 `api-sync-read-changed-relay`）与
`config_mirror.bump`（消费者 `config-mirror-bump`）。

#### Scenario: 同步读变更通知的存量回收

- **WHEN** `sync_read.changed` 的中继消费者游标已推进且存在超过保留期的行
- **THEN** 剪裁 SHALL 回收这些行
- **AND** 表的行数 SHALL 随轮次下降而不是继续单调增长

#### Scenario: 配置失效信号未投递

- **WHEN** `config_mirror.bump` 有行尚未被中继投递
- **THEN** 这些行 MUST NOT 被任何保留期规则删除
- **AND** 系统 MUST NOT 因「行数少、影响小」而对该主题放宽游标下界
