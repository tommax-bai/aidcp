## Why

`dev` 与 `ol` Cloud 目前共享 PostgreSQL，但委托任务没有 Cloud 执行归属，任一环境的 worker 都能领取另一环境创建的任务。这会让任务使用错误环境的进程内状态、运行时连接、飞书机器人与配置；2026-07-20 已在 dev 复现为账号已配置人设却被另一 Cloud worker 误报“未配置人设”。

## What Changes

- 为每条 `DelegatedTask` 持久化服务端可信的 Cloud 执行目标（`dev` 或 `ol`），与用户输入中的业务来源、来源会话和 `sourceRef` 分离。
- 所有任务创建入口都由当前 Cloud 运行目标注入执行目标，不接受客户端或命令载荷指定、覆盖该字段。
- 委托 worker 只领取与自身 Cloud 运行目标一致的任务；恢复中断 claim、到期收敛与 ownership 查询同样不得跨目标处理。
- 将部署前已存在的委托任务幂等回填为 `dev`，这是本次由用户确认的历史数据归属。
- Cloud 缺少或配置非法执行目标时 fail-closed：任务服务/worker 不得以猜测目标继续创建或消费任务。
- 本变更不增加人设缓存的跨进程刷新；任务与写入被正确限定在同一 Cloud 后，继续使用既有本进程热更新与启动加载机制。

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `user-delegated-tasks`: 委托任务新增可信 Cloud 执行归属，任务创建、领取、恢复与到期处理必须保持同目标隔离；历史任务统一归属 dev。

## Impact

- **aidcp-cloud**：`delegated_tasks` schema / 类型 / store 查询、任务服务装配、worker 启动与相关测试。
- **aidcp control**：OpenSpec 契约、设计、任务与部署证据。
- **运行配置**：dev/ol Cloud 必须各自提供可验证的运行目标；不得从客户端请求派生。
- **数据**：启动幂等 schema 升级为旧行写入 `dev`；不删除任务、不改任务业务状态或 attempt 证据。
- **部署**：由于 dev/ol 共享数据库且旧 worker 不识别 target，运行迁移必须在明确授权后协调升级两个 Cloud 目标；只发布 dev 不能形成隔离闭环。
