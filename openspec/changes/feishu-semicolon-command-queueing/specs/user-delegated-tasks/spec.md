## ADDED Requirements

### Requirement: 同环境并发就绪命令必须由单写者队列确定执行顺序

多个委托子命令 MAY 并发准备，但同一 Edge 环境在任一时刻 MUST 只有一个浏览器写任务持有 active lease。当多个请求同时就绪时，系统 SHALL 先按既有任务优先级选择；同优先级请求 SHALL 按 Edge 实际接收申请的单调顺序 FIFO 执行，MUST NOT 并发操作页面，也 MUST NOT 让同优先级任务彼此抢占。

#### Scenario: 两个人工命令几乎同时到达 Edge

- **WHEN** 同一账号的人工发布与人工评论租约请求几乎同时到达 Edge，且两者优先级均为 `human`
- **THEN** Edge SHALL 把先收到的请求授予为唯一 active lease
- **AND** 后收到的请求 SHALL 留在队列中等待前者释放
- **AND** 两个任务 MUST NOT 同时发送页面命令

#### Scenario: 同毫秒时间不依赖文本顺序裁决

- **WHEN** 两个同优先级请求具有相同或不可区分的墙钟时间
- **THEN** 系统 SHALL 使用 Edge 单调收包序号作为确定性 tiebreaker
- **AND** MUST NOT 依赖原始分号命令的书写顺序伪造“同时”裁决

### Requirement: 资源等待发生在动作起跑前时不得消耗尝试或失败预算

当执行器能够证明一次延后发生在任何浏览器或平台命令下发之前，系统 SHALL 将其保留为可恢复的排队/延后状态，并 MUST NOT 增加 `attempt_count`、`failure_count` 或 `skipped_count`。资源释放后任务 SHALL 在截止时间内重新竞争执行权；它 MUST NOT 仅因反复等待同一浏览器资源而进入 `max_attempts`。

只有明确标记为“动作未开始”的机器可读结果可以回收临时 attempt。已经发送浏览器命令、进入提交窗口、被抢占或提交结果不明的执行 MUST 保留 attempt 账本并走既有对账/防重复语义。

#### Scenario: 发布占用浏览器时评论排队

- **WHEN** 人工发布持有该账号 Edge lease，而同批人工评论申请执行权
- **THEN** 评论 SHALL 等待或以机器可读的 pre-start defer 重新排队
- **AND** 在零浏览器命令下发的等待期间 `attempt_count`、`failure_count` 与 `skipped_count` SHALL 均保持不变
- **AND** 发布释放后评论 SHALL 在截止时间内自动再次竞争执行权

#### Scenario: 两次 acquire 超时不再产生 max_attempts

- **WHEN** 精确 `/comment` 的两次 Edge acquire 都因另一个合法任务占用而在起跑前超时
- **THEN** 该评论任务 MUST NOT 因默认 `maxAttempts=2` 进入 `max_attempts` 失败
- **AND** 任务 SHALL 保持可恢复延后，直到资源可用、用户取消或任务截止

#### Scenario: 已有副作用可能性的 defer 保留 attempt

- **WHEN** 一个任务已发送浏览器命令后被抢占，或提交结果无法确认
- **THEN** 系统 MUST 保留对应 attempt 账本
- **AND** MUST NOT 把它回收成“从未开始”后自动重试而制造重复发布或重复评论

#### Scenario: 结构性不可执行仍诚实终止

- **WHEN** 子命令因昵称不存在、平台不支持、人设未绑定或缺少必需联系方式而结构上不可执行
- **THEN** 系统 SHALL 独立回报不可执行原因并按既有语义终止
- **AND** MUST NOT 以无限排队掩盖结构性失败
