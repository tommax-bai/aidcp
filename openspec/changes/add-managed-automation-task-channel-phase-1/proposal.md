## Why

今天的手工委托与自动编排仍由不同入口和状态机直接驱动执行，无法把“谁产生任务”与“如何执行任务”分开。现在三进程拆分已经把 Automation 进程做成独立运行边界，一期应在该边界内建立一条默认关闭、只读可验的 Task/ExecutionPlan 主通道，而不是继续把旧 Cloud feature branch 直接并回单体组合根。

## What Changes

- 建立 Automation-owned 的 Task、TaskRevision、不可变 ExecutionPlan、TaskRun、StepRun、ExecutionIntent、ExecutionAttempt 与 DecisionTrace 契约和持久化。
- 通过 API→Automation 的鉴权、版本化、target-bound 窄端口提供 CreateTask、CancelTask 与 QueryTask；API、Agent 与 Edge 均不得直接写运行账本。
- 建立有界 worker、租约/CAS、恢复和诚实终态映射，并以 `persona.research@1` 只读研究任务完成第一条纵切。
- 以账号工作 lane 仲裁 TaskRun 与现有编排；一期任务持有 lane 时，旧编排不得向同一账号并发派工，Edge 连接本身不新增“task/orchestration”业务权威。
- 所有 worker、入口与仲裁默认关闭；只有依赖、schema、`execution_target`、契约和接线门禁通过后才能启用。
- 复用已撤出设计稿中的类型和测试资产，但重新落在现有 `aidcp-automation`/`aidcp-api` 进程边界；旧 `add-managed-automation-runtime` 的 111 项计划及其“取代线上规格”声明不恢复。
- 一期不包含 ManagedPlan/ManagedCycle/Trigger Binding、自动排期生产者、写平台动作、客户客户端入口、旧编排下线或 OL 发布。

## Capabilities

### New Capabilities

- `managed-automation-task-channel`: 定义一期 Task/ExecutionPlan/Run/Ledger/Trace 权威模型、入口命令、账号 lane 仲裁、只读研究执行与诚实恢复语义。

### Modified Capabilities

- `cloud-automation-api-direct-ports`: 增加 API→Automation 的任务入口窄端口，并保持 owner、Bearer、版本、target、幂等与结果未知边界。
- `multi-tenant-orchestration`: 增加同账号 TaskRun 与旧编排互斥的 lane 规则，同时保持不同账号和 Edge 连接的隔离。

## Impact

- `aidcp-automation`: 任务契约、Automation-owned migrations/stores、compiler/worker、只读 executor、lane arbiter 与默认关闭的生产组合根接线。
- `aidcp-api`: customer-auth/Agent-facing adapter 之前的内部任务命令客户端与查询投影；本期不新增客户 UI。
- `aidcp-kernel` / `aidcp-transport`: 仅在跨进程 DTO 或 route/client 需要时增加纯类型和窄传输合同，不放业务执行器。
- `aidcp-cloud`: 旧 Qoder feature 仅作为移植来源，不直接合并其单体 `server.ts` 接线；必要时保留迁移/边界对账证据。
- `aidcp-edge`: 复用现有定向原子命令与诚实 receipt，不新增跨步骤编排，也不以握手字段代替 Automation 的账号 lane 权威。
- 依赖 `split-cloud-automation-production-runtime` 的独立 Automation `main()` 与 readiness gate；依赖未闭合时只能声明源码/测试完成，不能声明运行时或部署完成。
