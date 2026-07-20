## ADDED Requirements

### Requirement: 委托任务必须绑定可信 Cloud 执行目标

每条委托任务 SHALL 持久化 `executionTarget ∈ {dev,ol}`，表示创建和执行该任务的 Cloud 部署目标。该字段 MUST 由服务端当前运行目标注入，MUST NOT 从客户端请求体、自然语言、命令参数、`envKey`、`sourceRef` 或其他用户可控字段派生或覆盖。

业务来源 `source`、来源引用 `sourceRef`、来源会话 `originChatId` 与 Cloud 执行目标是不同概念，系统 MUST NOT 复用其中任一字段替代 `executionTarget`。

#### Scenario: dev 客户端创建精选创作任务
- **WHEN** dev Cloud 收到已鉴权客户对某环境发起的精选创作请求
- **THEN** 新任务 SHALL 持久化 `executionTarget=dev`
- **AND** 请求体即使携带伪造 target 字段也 MUST NOT 改变该值

#### Scenario: Cloud target 缺失时拒绝装配委托能力
- **WHEN** Cloud 启动时部署目标缺失或不属于 `dev | ol`
- **THEN** 委托任务创建服务和 worker SHALL fail-closed 不可用并留下明确运行日志
- **AND** MUST NOT 猜测或默认该进程为 dev

### Requirement: 委托任务的生命周期必须按 Cloud 执行目标隔离

任务创建去重、读取、列表、精选内容“已创作/未创作”投影、确认、暂停、恢复、取消、ownership 判断、worker 领取、启动中断恢复和到期收敛 SHALL 只处理与当前 Cloud `executionTarget` 一致的任务。一个 Cloud worker MUST NOT 领取、恢复、改变或终结另一个 target 的任务，即使两者共享 PostgreSQL、账号 id、动作、截止时间或去重键。任何依赖委托任务数据的旁路投影在 target 缺失时 SHALL fail-closed，不得执行跨目标查询或猜测为 dev。

同一 target 内的活跃任务去重语义 SHALL 保持不变；不同 target 的相同业务请求 MUST NOT 因共享唯一索引互相去重。

#### Scenario: ol worker 观察到 dev 排队任务
- **WHEN** 共享数据库中存在 `executionTarget=dev` 的 queued 任务，而 ol worker 轮询队列
- **THEN** ol worker SHALL 跳过该任务且不得写入 claim
- **AND** dev worker SHALL 仍可按既有优先级领取该任务

#### Scenario: ol 启动不恢复 dev 的执行中任务
- **WHEN** ol Cloud 重启，而共享数据库中有 `executionTarget=dev` 的 planning 或 executing 任务
- **THEN** ol 的启动恢复 SHALL 不修改这些任务的状态、claim、attempt 或事件

#### Scenario: 两个 target 的相同请求分别幂等
- **WHEN** dev 与 ol 对同一账号创建业务字段及业务去重键相同的任务
- **THEN** 两个 target SHALL 各自保留一条任务
- **AND** 每个 target 内重复创建仍 SHALL 返回本 target 的同一活跃任务

#### Scenario: dev 控制请求不能改变 ol 任务
- **WHEN** dev 的任务查询或控制入口收到一个只存在于 `executionTarget=ol` 的 task id
- **THEN** 系统 SHALL 按本 target 不存在处理
- **AND** MUST NOT 暴露或修改 ol 任务真态

### Requirement: 历史委托任务必须安全回填为 dev

部署本变更前已存在且没有 Cloud 执行目标的所有委托任务 SHALL 幂等回填为 `dev`。回填 MUST 保留任务 id、账号、业务来源、状态、版本、进度、claim、终态、时间戳、attempt 与事件，不得把历史任务重新排队、重新执行或改写业务结论。

回填完成后 `executionTarget` MUST 非空且只允许 `dev | ol`；新任务写入 MUST 显式提供服务端 target，数据库不得依靠永久默认值把未知来源静默归入 dev。

#### Scenario: 旧任务启动迁移
- **WHEN** schema 升级发现没有执行目标的历史委托任务
- **THEN** 系统 SHALL 将这些行的执行目标设为 dev
- **AND** 迁移前后任务总数、各业务状态计数和 attempt 数量 SHALL 保持一致

#### Scenario: 重复启动迁移幂等
- **WHEN** 已完成回填的 Cloud 再次启动并执行同一 schema 自愈
- **THEN** 已有 dev/ol target SHALL 保持不变
- **AND** MUST NOT 再次改变任务状态、版本、claim 或时间戳
