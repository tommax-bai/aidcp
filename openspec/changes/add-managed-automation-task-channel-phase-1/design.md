## Context

旧设计 `docs/design/managed-automation-runtime/` 已于 2026-07-30 从活跃 OpenSpec 撤出；其中 111 项任务和“重叠处以本方案为准”的授权均已失效。随后 Qoder 在 `aidcp-cloud` feature branch 上实现了 contracts、四组 migration、typed stores、线性 compiler/worker、Create/Cancel/Query 和只读研究测试纵切，但生产组合根没有启动 worker，也没有真实 API→Automation→Edge 闭环。

与此同时，`split-cloud-automation-production-runtime` 已把生产 Automation 边界迁到独立 `aidcp-automation` 进程。直接合并旧 Cloud branch 会把新任务运行时重新接回单体 `server.ts`，与当前进程所有权相反。本 change 只重建一期任务通道，并把旧分支降为可选择移植的实现素材。

一期的业务关系是：手工请求产生 Task；未来排期器也产生同一 Task。两者共享 Task/ExecutionPlan/Run/Ledger 执行层。本期只接手工来源和只读研究能力，不实现未来排期器。

## Goals / Non-Goals

**Goals:**

- 在独立 Automation 进程中建立唯一的 Task/ExecutionPlan/Run 权威与默认关闭的 worker。
- 让 API 以窄端口创建、取消和查询任务，不跨 owner 写 Automation 表。
- 以账号 lane 保证一期 TaskRun 不与同账号旧编排并发驱动 Edge。
- 通过 `persona.research@1` 证明 Create→Compile→Run→Step→Intent→Attempt→Trace→Query 的只读闭环。
- 复用旧分支已验证的纯类型、SQL、store 和 engine 代码，但逐文件移植并按新进程边界复核。
- 清楚区分源码验证、进程接线、DEV 部署和真实平台证据。

**Non-Goals:**

- 不恢复旧 111 项总 change，也不取代任何 publish/comment/reply/content-schedule 线上规格。
- 不实现 ManagedPlan、ManagedCycle、Trigger Binding 或自动排期生产者。
- 不执行发布、评论、回复、点赞、关注等外部写动作。
- 不新增一级 Workflow/CapabilityRun，不允许任意脚本式 TaskDefinition。
- 不让 Edge 承担跨步骤编排，不用 hello `mode` 作为任务权威。
- 不在本 change 中下线旧编排、制作客户端 UI、发布 Edge 安装包或部署 OL。

## Decisions

### 1. 新 change 分期承接，不复活旧总 change

本 change 新建独立 capability，只吸收一期所需合同。旧设计的 §24 处置表和未来四期路线仍可作研究材料，但对生产验收零约束。

备选方案是把 `docs/design/managed-automation-runtime/` 原样移回 `openspec/changes/`。拒绝原因是它会同时恢复 111 项范围和已撤销的上位取代关系，并忽略已经落地的三进程边界。

### 2. Automation 是运行账本与 worker 的唯一 owner

Task、revision、plan、run、step、intent、attempt、trace 和 lane 均由 `aidcp-automation` 单写，表位于 Automation owner database 并带服务端注入的 `execution_target`。API 只持有请求身份、授权和客户投影，通过版本化内部端口提交命令和查询；Edge 只执行原子命令并回报证据。

跨进程 DTO 如需共享，放到 kernel/transport；业务 compiler、worker、stores 和 executor 不进入共享包。

### 3. 用账号 lane 仲裁，不用连接 mode 仲裁

lane key 为 `execution_target + account_id`。旧编排默认占用 legacy 路径；Task worker 只有在确认该账号没有在途旧编排工作后才能以 CAS/lease 获取 managed lane。持有 managed lane 时，所有旧编排入口对该账号均返回可观测的 `managed_task_lane_active` 跳过，不影响其他账号。

Task 创建本身不抢 lane；排队任务可以等待。worker 崩溃后，只有租约过期且在途 Attempt 已完成 receipt/reconciliation 判定，才允许恢复或释放。只读 attempt 结果未知不得伪装为 completed，但可在记录重驱原因后重新执行有界读取。

备选方案是让 Edge hello 声明 `task|orchestration`。拒绝原因是连接属性无法表达队列、抢占、恢复和同账号现有在途工作，且生产 Edge 当前没有创建专用 task session 的闭环。

### 4. 一期图是版本化、不可变、有界的线性图

`TaskDefinition` 由代码 registry 提供，`persona.research@1` 固定为 search→browse→assess→summarize。PlanCompiler 校验版本、节点输入输出 schema、最大步数、终态和 CapabilityScope 后，生成带稳定 hash 的不可变 ExecutionPlan。TaskRevision 或授权版本变化必须生成新 plan/run，不原地修改运行中 plan。

一期不实现自由 DAG、循环或用户脚本。未来扩图必须通过新的 Capability/TaskDefinition 版本和 OpenSpec delta。

### 5. 入口命令是 owner-safe 的窄端口

第一组端口为：

- `CreateTask(commandId, actor, accountId, taskDefinitionVersion, parameters, authorizationRevision)`
- `CancelTask(commandId, actor, taskId, expectedRevision, reason)`
- `QueryTask(requestId, actor, taskId)`

每个请求携带 contract version、Bearer、服务端确定的 execution target 和稳定幂等键。API 先做客户/账号授权；Automation 再校验 capability scope、版本、target 和当前启用状态。创建/取消使用 dedupe receipt；写后响应丢失返回 `result_unknown`，不自动重提。Query 只返回客户安全投影，不暴露秘密、原始模型输入或跨账号 trace。

### 6. 持久化复用旧资产，但重新编号和归属校验

选择性移植旧 Cloud feature 中的四组 migration 和 typed stores到 `aidcp-automation`。迁移编号以移植时 Automation owner ledger 的最新值为准，不沿用旧分支编号假设；每张表登记到当前 Automation ownership manifest。stores 保留 target filter、CAS、租约、终态保护和能力探测，禁止运行时自建表。

schema gate 缺失或 target 无效时 worker 不启动。入口是否允许创建任务由独立 readiness 判定决定，不把 SQL 缺表转成空结果。

### 7. Edge 执行只走现有原子命令和诚实 receipt

Research executor 通过 Automation 当前连接注册表按 account/edge 定向投递现有 search/browse/observe 类原子命令。每个 intent 有稳定 idempotency/correlation 标识；Attempt 分开记录 dispatch、submitted/unknown、completed、empty、failed、timeout、undeliverable 和 aborted。

“已发送”“活动日志存在”或“lane 已释放”都不是读取成功。唯一内容计数只接受带稳定平台内容引用和同目标后验的证据；不支持的平台/命令显式返回 unsupported。

### 8. 默认关闭并依赖独立 Automation root

Task API、worker 和 lane exclusion 使用分开的默认关闭开关。生产组合根只有在 `split-cloud-automation-production-runtime` 的 main/readiness/connection runtime 已闭合后才接线；在此之前可以完成纯模块与测试，但不得声称 production runtime ready。

开启顺序为 schema/ports → query → create/cancel → worker → lane exclusion。任一步失败均关闭新入口和新 claim，不影响旧编排。已经 dispatched 的 attempt 继续 receipt/reconciliation。

## Risks / Trade-offs

- [旧 Cloud 代码与新 Automation 代码漂移] → 只按文件/行为移植，不 merge 整条旧 branch；每批对照当前 owner 和依赖。
- [与三进程组合根工作并发冲突] → 新模块可并行，`automation-composition-root.ts`、`automation-service-entry.ts`、连接 registry 等热点等前置 change 收口后串行接线。
- [账号 lane 释放过早导致双驱动] → lane 与在途 Attempt/reconciliation 绑定；未知结果不直接释放为可用。
- [只读命令重驱造成重复浏览] → 记录原 attempt 与重驱原因，使用有界次数和唯一内容去重，不把重复观察计为新成功。
- [additive tables 形成长期遗留] → 默认关闭、无旧路径依赖；回滚只关入口/worker，表保留到专门清理 change，不做破坏性回滚。
- [一期被误解为未来自动编排已完成] → projection、文档和任务证据分别标记 manual source、future producer、source/runtime/deploy/platform 四层状态。

## Migration Plan

1. 等 `split-cloud-automation-production-runtime` 的 Automation root 热点收口，rebase 新 worktree；完成现状/所有权/迁移 ledger 盘点。
2. 移植并验证 contracts、migrations、typed stores；默认没有生产调用点。
3. 增加 API→Automation route/client/adapter 和 query projection，保持入口关闭。
4. 增加 compiler、worker、research executor、lane arbiter 与组合根接线，仍默认关闭。
5. 跑 focused、owner-boundary、target-isolation、acceptance、full test 和 typecheck；有 PostgreSQL 时跑 CAS/claim/lease/target integration。
6. 串行集成到各默认分支；只在全部门禁通过后提 DEV 部署，OL 另行授权。

回滚：关闭 create/worker/lane flags，停止新 claim；保留已派发 attempt 的 receipt/reconciliation；additive tables 和历史 trace 不回删。若 DEV 三进程健康或旧编排回归失败，回滚代码并保持功能关闭。

## Open Questions

- 一期客户可见入口的具体产品面（Agent command、Console 还是内部运维入口）不在本 change 实现；本期只冻结 API authorization adapter 和内部 port，后续入口另起 change。
- 写动作接入前必须单独裁决 submitted-unknown lane 上限、prepare/commit 和平台确认合同；只读一期不预判这些规则。
