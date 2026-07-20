## Context

dev 与 ol Cloud 目前同时读写同一个 PostgreSQL 数据库。`delegated_tasks` 只记录业务来源（如 `operator_action`）、来源引用和账号，没有部署环境归属；`claimNext`、启动恢复和任务列表都在全表工作。与此同时，人设、账号连接、飞书凭据、风险控制器与调度器是 Cloud 进程/目标局部状态，因此“共享任务表 + 无目标领取”会把 dev 创建的业务交给 ol 进程执行，反之亦然。

现有运行配置已经使用 `AIDCP_DEPLOY_ENV` 区分 `dev` 与 `ol`。本变更复用该事实源，不新增第二套环境命名。用户确认所有迁移前历史委托任务均属于 dev。

## Goals / Non-Goals

**Goals:**

- 每条委托任务持久化不可由客户端伪造的 `execution_target ∈ {dev,ol}`。
- 创建、读取、控制、去重、ownership、领取、启动恢复和到期收敛均限定在当前 Cloud target。
- 旧任务幂等回填为 dev，保留状态、attempt、版本和终态证据。
- target 缺失或非法时委托写入口与 worker fail-closed，不猜测为 dev。
- 保持现有 dev/ol 单进程部署下的人设缓存模型不变。

**Non-Goals:**

- 不实现 PostgreSQL `LISTEN/NOTIFY`、定时轮询或其他跨进程人设缓存刷新。
- 不拆分 dev/ol PostgreSQL。
- 不把客户端 `envKey` 等同于 Cloud target，也不允许请求体选择 `dev`/`ol`。
- 不改变业务 `source`、`sourceRef`、`originChatId`、人审、风险、配额或任务状态机语义。
- 不把实现授权自动扩张为 ol 发布授权；协调升级 ol 必须在发布门前单独获得明确授权。

## Decisions

### D1. 复用并严格解析 `AIDCP_DEPLOY_ENV`

Cloud 启动时把 `AIDCP_DEPLOY_ENV` 严格解析为 `dev | ol`，并将结果注入唯一 `PgDelegatedTaskStore`。缺失、空白或其他值时，不装配委托任务 service/worker，并输出明确告警；其他无关 Cloud 能力保持既有启动边界。

选择现有 env 而不是新增 `AIDCP_DELEGATED_TASK_TARGET`，避免两个环境事实源漂移。选择 fail-closed 而不是缺省 dev，避免 ol 漏配置后再次消费 dev 数据。

### D2. target 由 store 注入，而不是任务调用方传入

`PgDelegatedTaskStore` 在构造时持有 target，`createDraft` 插入时自行写入。`DelegatedTaskIntent`、客户 API DTO、飞书 parser 和客户端请求体不新增 target 字段。任务读取结果包含 target 供审计和测试，但调用方不能在创建参数中覆盖它。

这样可信边界集中在服务端装配点；若让每个创建入口传 target，漏传、误传或客户端字段穿透都会重新打开跨环境通道。

### D3. store 是环境隔离边界

所有任务级 PostgreSQL 查询都带 `execution_target=currentTarget`：

- `createDraft` 的去重冲突回读；
- `get` / `list` / 确认 / 暂停 / 恢复 / 取消；
- `claimNext` 与进程启动的 interrupted-claim recovery；
- active ownership / ownership conflict；
- 精选内容列表基于委托任务判断“已创作/未创作”的旁路投影；
- 持有 claim token 的执行写回继续以 token 作为主防线，并在任务行更新处附加 target。

worker 不再单独接收可漂移的 target；它只使用已绑定 target 的 store。`expireDueTasks` 通过 target-scoped `list` 自然只收敛本环境任务。

### D4. 去重唯一性按 target 分区

活跃任务唯一索引从 `dedupe_key` 改为 `(execution_target, dedupe_key)`。同一业务请求在同一 target 内仍幂等，dev 与 ol 的相同账号/动作不会互相吞掉任务。

### D5. 启动 schema 自愈与显式迁移保持一致

新增 `execution_target TEXT` 后，先把所有 `NULL` 历史行更新为 `dev`，再设 `NOT NULL` 与 `CHECK (execution_target IN ('dev','ol'))`，最后重建 target-aware 活跃去重索引并增加 target-first claim/ownership 索引。`migrations/0052_delegated_task_execution_target.sql` 与启动 schema SQL 保持同源。

不保留列默认值：回填完成后每次新建任务必须显式写 target，避免未来绕过可信装配点时静默落 dev。

### D6. 本次不刷新人设缓存

同一个 Cloud 进程通过客户 API/面板/边缘写人设时，现有 `PersonaStore.set` 已在写库成功后同步刷新本进程缓存；进程重启会重新加载数据库。任务 target 隔离后，dev 写入的人设与 dev 任务由 dev worker 使用，当前单进程/target 模型闭合。

若未来同一 target 扩成多副本、允许跨实例 failover 或直接写数据库，再单独设计缓存失效机制。

## Risks / Trade-offs

- [ol 未配置 `AIDCP_DEPLOY_ENV=ol` 时委托能力不可用] → 上线前做配置只读检查与启动日志验证；禁止回退为默认 dev。
- [两个 Cloud 同时首次执行 schema 自愈] → 使用幂等 DDL/DML与 PostgreSQL 表锁；迁移只新增列、回填空值和重建索引，不删除业务数据。
- [旧任务全部归 dev 的决定不可从数据自行证明] → 按用户明确授权执行；部署前记录旧行总数和各状态，迁移后断言全部为 dev、业务计数不变。
- [只隔离领取但控制 API 仍跨 target] → 把 store 全部任务读写入口一起 target-scope，并用 SQL 形状测试覆盖。
- [已有活跃任务在部署瞬间被重启恢复] → 沿既有备份与串行部署流程；迁移不改状态/claim，dev worker只恢复回填为 dev 的历史任务，符合用户确认归属。
- [只发布 dev 时旧 ol worker 仍会忽略 target 并领取 dev 任务] → 禁止 dev-only 运行迁移；发布前必须获得 ol 授权并协调停止旧 worker、升级两个目标。
- [第一个新进程收紧 `NOT NULL` 后，尚未升级的旧进程无法创建任务] → 两个旧 worker 都停止后再迁移和升级，不把新旧版本并行运行当作支持的滚动发布路径。

## Migration Plan

1. 在发布前分别执行 dev/ol 目标检查，确认 `.env` 中 `AIDCP_DEPLOY_ENV=dev|ol`，并只读统计共享库的任务总数、状态分布、活跃 claim 与 `execution_target` 列状态。
2. 获得明确 ol 发布授权；未获授权时停在代码交付门，不执行数据库迁移或 dev-only 发布。
3. 备份两端 Cloud/env 与共享数据库中的委托任务相关表，记录可验证的回滚点。
4. 协调停止两个目标的旧 `aidcp-cloud.service`，避免旧 worker 在迁移后继续跨目标领取或写入缺少 target 的任务。
5. 执行幂等 schema 迁移，将全部历史任务回填为 dev；断言行数、状态/attempt/event 计数不变且无 NULL/非法 target。
6. 用户已确认 ol 没有历史委托任务；从各自合规分支先升级/启动 ol，再升级/启动 dev，并分别验证服务、监听、健康、PostgreSQL、Feishu，以及 `AIDCP_DEPLOY_ENV` 装配日志。
7. 用 SQL/日志及新建任务证明 dev/ol 分别只写入和领取自身 target；确认 ol worker 不读取历史 dev 任务。

回滚代码前必须先评估：旧代码忽略新列后仍会恢复跨环境领取，因此不能把“代码回滚但继续双 worker”当安全状态。紧急回滚应先停止非目标 worker 的委托消费或恢复单环境消费，再回退代码；新增列与数据可保留，避免破坏审计。

## Open Questions

运行迁移前仍需用户明确授权 ol 协调发布。历史任务归属已由用户明确指定为 dev；同 target 多副本不在当前部署模型内。
