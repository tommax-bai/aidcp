## Context

发布队列现有生命周期投影从 orchestrator run、`publish_log` 和 dispatcher 在途集合组合而成，只能观察已经开始生成或已经落成稿的记录。统一委托任务在进入 orchestrator 之前处于 `queued`、`planning` 或 `deferred`，这些状态目前只能从 `/api/delegated-tasks` 读取，内容页没有消费该列表。

现有委托列表仅支持账号与 limit 过滤。若由 console 拉取最近任务后再客户端过滤，较旧但仍排队的发布任务可能被大量终态任务挤出窗口，因此过滤必须在服务端完成。

## Goals / Non-Goals

**Goals:**

- 完整、只读地展示尚未进入可见发布生命周期的发布类排队任务。
- 让运营可区分等待执行、准备中和暂缓重试，并看到账号、动作、来源标题和任务短标识。
- 保持旧客户端与不带过滤参数的 `/api/delegated-tasks` 调用兼容。

**Non-Goals:**

- 不展示或承诺精确队列名次。
- 不从此面板暂停、恢复、取消或调整任务优先级。
- 不改变委托 worker、发布编排、审批与平台发布判定。

## Decisions

1. `GET /api/delegated-tasks` 增加可选 `actionFamily` 与逗号分隔 `statuses` 参数。服务端校验枚举后下推到 store 查询；不带参数时维持既有结果。选择加性过滤而非新增专用端点，以复用统一任务读模型，同时避免客户端窗口过滤导致漏项。
2. “排队任务”仅包含发布动作族中 `queued`、`planning`、`deferred` 三种状态。`awaiting_confirmation` 尚未真正入队；`waiting_approval` 与 `executing` 已由发布生命周期的待审/生成/下发视图承担，避免重复展示。
3. 页面以 10 秒轮询独立读取排队任务，和生命周期轮询节奏一致。查询失败只让排队列显示错误，不遮蔽现有活跃稿件与最近结果。
4. 活跃稿件摘要与排队任务组成响应式双列；八阶段条仍占满下一行，避免压缩排障信息。窄屏退化为单列。
5. 列表不显示“第 N 位”。worker 的真实选择还受优先级、deadline、`notBefore` 与 `nextEligibleAt` 影响；页面只显示当前状态和时间证据。

## Risks / Trade-offs

- [旧 Cloud 不认识过滤参数且返回未过滤列表] → Console 仍二次按动作和状态过滤；该回落可能受旧接口 limit 窗口限制，但不会误把非发布任务显示出来。
- [任务从 planning 快速进入 executing 时出现短暂消失] → 两路查询均为轮询快照，下一次生命周期刷新会呈现生成 run；不伪造连续性。
- [来源标题不是所有入口都有] → 仅在 `sourceConstraints.title` 为非空字符串时展示，否则回落动作名和任务短标识。

## Migration Plan

1. 先部署向后兼容的 Cloud 查询过滤。
2. 再发布 Console 双列视图。
3. 回滚 Console 即恢复旧页面；Cloud 的可选参数可保留且不影响旧调用。

## Open Questions

无。
