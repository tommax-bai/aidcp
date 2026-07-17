# wechat-channels-interaction（delta）

## ADDED Requirements

### Requirement: 暂时不可投递 MUST NOT 被判为任务终态失败

云端发送编排 SHALL 只在**结构上做不到**时把回复 job 判为终态 `failed`。「资源暂时被占」「边缘暂时收不到命令」「连接恰好在事务期间关闭」等暂时性成因 MUST NOT 导致 job 进入终态，也 MUST NOT 烧掉已通过人工审批的授权。

同一函数中「边缘完全离线」与「投递数为 0」两条分支的成因同为暂时性，SHALL 收敛到同一条自愈语义：不建终态、job 留在可恢复状态、交由恢复循环重投。

#### Scenario: 边缘处于验证码硬暂停期

- **WHEN** 账号绑定的边缘处于验证码硬暂停态（回复命令不在下发豁免名单，投递必为 0）
- **THEN** 编排 SHALL 在建立 attempt **之前**识别该状态，不建 attempt、不改 job 状态、不作废审批授权
- **AND** job SHALL 保持 `queued`
- **AND** 编排 SHALL 抛出标记为可重试的上游不可用错误，使恢复循环记为 deferred 而非失败

#### Scenario: 投递数为 0

- **WHEN** 命令下发的投递数返回 0（连接在事务期间关闭或进入 CLOSING）
- **THEN** job MUST NOT 被置为 `failed`
- **AND** 已建立的 attempt SHALL 被作废到不占用活跃唯一槽的状态
- **AND** job SHALL 回到 `queued` 并可被恢复循环再次捞出

#### Scenario: 恢复循环 MUST NOT 成为烧毁器

- **WHEN** 恢复循环在暂停窗口内扫到整批排队积压
- **THEN** 该批 job MUST NOT 被批量置为终态
- **AND** 每轮 SHALL 只记 deferred 计量并保留 job 于 `queued`

#### Scenario: 无法证明命令未离开进程时保持不确定

- **WHEN** 下发抛出异常，或投递数大于 1
- **THEN** attempt 与 job SHALL 保持 `ambiguous` 语义不变
- **AND** MUST NOT 因本要求被自动放开重投——重复评论的代价高于人工核查

### Requirement: 每个不可发状态必须有明确的恢复路径

任何把回复 job 或 attempt 推入不可发状态的转换，SHALL 显式规定「什么把它拨回来」。没有恢复路径的降级 MUST NOT 被引入。

#### Scenario: 暂停态的恢复路径

- **WHEN** 边缘的验证码硬暂停解除
- **THEN** 留在 `queued` 的 job SHALL 在既有 30s 恢复循环的下一轮被重新下发，无需人工介入
- **AND** 原审批授权 SHALL 仍然有效——暂停是瞬态，MUST NOT 作废授权

#### Scenario: 回到 queued 的 job 必须真的可被恢复循环捞到

- **WHEN** 编排把 job 回置为 `queued` 并作废其 attempt
- **THEN** 该 attempt 的目标状态 MUST NOT 落在恢复循环的活跃排除集内（`created` / `dispatched` / `ambiguous`）
- **AND** 该 job SHALL 在下一轮待发队列中被捞出

### Requirement: 幂等键 SHALL 仅在活跃状态下唯一

发送尝试的幂等键 SHALL 由「仅活跃状态」的部分唯一索引约束，而非无条件全局唯一。同表已存在的「job+attempt 序号」唯一约束、attempt 序号递增逻辑与可重试标记，三处设计共同预设一个 job 可以有第 2、3 次 attempt；全局唯一使其在文案不变时结构上不可能，与既有设计自相矛盾。

#### Scenario: 失败后重试同一份确定性文案

- **WHEN** 一个 job 的前一次 attempt 已进入终态（`failed` / `confirmed`），该 job 被重新生成且模板渲染逐字相同（未开 AI 润色时必然如此）
- **THEN** 新 attempt SHALL 能被成功建立
- **AND** MUST NOT 因键冲突被阻断

#### Scenario: 私信渠道的结构性阻断解除

- **WHEN** 私信渠道在 AI 润色默认关闭下重试
- **THEN** 重试 SHALL 结构上可能，MUST NOT 出现 409 死循环空转

### Requirement: 键冲突 MUST NOT 冒充「已有发送尝试在进行中」

错误映射 SHALL 区分「真的有活跃 attempt」与「唯一约束冲突」两种成因。把后者报成前者是**静默假成功的近亲**——它向客户端陈述一件代码可证明为假的事实，并把 job 留在会被恢复循环反复重撞的状态。

#### Scenario: 存在活跃 attempt

- **WHEN** 建立 attempt 时唯一约束冲突，且该 job 确有处于 `created` / `dispatched` / `ambiguous` 的 attempt
- **THEN** 编排 SHALL 回「已有发送尝试在进行中」并保持 409 语义

#### Scenario: 不存在任何活跃 attempt

- **WHEN** 建立 attempt 时唯一约束冲突，但该 job 没有任何活跃 attempt
- **THEN** 编排 SHALL 如实报告键冲突，MUST NOT 声称有尝试在进行中
- **AND** 该冲突 MUST NOT 被静默吞掉后向客户端回报「已排队」

### Requirement: 无消费者的可重试标记 SHALL 被接线或删除

任何被写入但无任何消费者的可重试标记 SHALL 被接线成真实判据或删除，MUST NOT 作为无效果的标记长期留存——它会让读者误以为重试语义已实现。

若选择接线，则各处赋值口径 MUST 统一；若选择删除，则列的写入与列本身 SHALL 同批处理。

#### Scenario: 可重试标记的处置

- **WHEN** 可重试标记被写入 attempt 记录
- **THEN** 它 SHALL 被恢复循环或结果处理作为真实判据消费
- **OR** 该标记 SHALL 被移除

### Requirement: 同步上报的线程时间戳必须来自平台，取不到就让字段缺失

Edge 上报的线程更新时间 SHALL 只能来自平台响应解析出的时间值（会话列表给出的会话更新时间、或消息 / 评论自身的平台创建时间）。Edge MUST NOT 用本地时钟、云端下发请求的时刻（`requestedAt`）、或任何其它非平台来源的值充当该字段——无论是直接赋值还是经 `Math.max` 之类的运算混入。

定向（scoped）同步与全量同步在这一点上没有例外：定向路径为了发起翻页而合成的帖子 / 会话占位对象，其平台更新时间 SHALL 表达为「未知」，MUST NOT 就地编一个。

当某线程在本批次内**拿不到任何平台时间值**时，Edge SHALL 不在该批次发出这一行，让云端侧字段保持缺失；MUST NOT 为了凑齐字段而填占位值。此路径 SHALL 只在该批次同时不含属于该线程的消息时可达，以免产生引用批次外线程的孤儿消息。

**恢复路径**：省略线程行不是不可逆状态——该线程的平台更新时间会在下一次全量同步（平台会话列表带出真值）或下一次该线程有新消息时被正常补上，无需人工干预、不写任何持久化的降级标记。

#### Scenario: 定向重新同步评论不得把点击时刻写成平台时间

- **WHEN** 云端对某个帖子下发带 `scopeExternalId` 的评论同步请求，Edge 为发起翻页合成帖子占位对象
- **THEN** 该占位对象的平台更新时间 SHALL 为「未知」，上报批次中每个线程的更新时间 SHALL 等于该线程根评论的平台创建时间
- **AND** 上报的线程更新时间 MUST NOT 等于请求下发时刻，也 MUST NOT 因与请求时刻取最大值而被抬高

#### Scenario: 定向重新同步私信按本页消息的平台时间上报

- **WHEN** 云端对某个私信会话下发带 `scopeExternalId` 的同步请求，且本页返回了消息
- **THEN** 上报的线程更新时间 SHALL 等于本页消息平台创建时间的最大值
- **AND** MUST NOT 等于请求下发时刻或 Edge 本地时钟

#### Scenario: 无平台时间可取时省略线程行而非填假值

- **WHEN** 定向私信同步的某一页既无平台会话更新时间、也无任何消息
- **THEN** 该批次 SHALL 不含该线程行、也不含任何消息
- **AND** 翻页游标与 checkpoint SHALL 照常推进，同步 MUST NOT 因此中断或报失败

#### Scenario: 平台响应缺时间字段时如实报错而非兜底

- **WHEN** 平台响应里应有的时间字段缺失或无法解析
- **THEN** Edge SHALL 报接口结构已变更并点名具体端点与字段
- **AND** MUST NOT 用本地时钟兜底后当作成功上报
