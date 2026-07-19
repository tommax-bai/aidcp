## ADDED Requirements

### Requirement: 发布队列展示尚未开跑的发布委托

管理后台内容页的发布队列 SHALL 在活跃稿件摘要旁提供“排队任务”只读列。该列 MUST 展示发布动作族中状态为 `queued`、`planning` 或 `deferred` 的任务，并至少包含账号、动作、状态和任务标识；来源标题有证据时 SHALL 展示。`awaiting_confirmation`、`waiting_approval`、`executing` 与终态任务 MUST NOT 混入该列。页面 MUST NOT 把列表顺序描述为精确队列名次。

`GET /api/delegated-tasks` SHALL 加性支持按动作族和一个或多个状态过滤，并在服务端过滤后应用 limit，确保仍在排队的任务不会被较新的无关终态记录挤出结果窗口。不带新过滤参数的既有请求 SHALL 保持兼容。

#### Scenario: 排队发布任务显示在独立列

- **WHEN** 一个发布类委托处于 `queued` 且尚未产生 orchestrator run
- **THEN** 内容页在“排队任务”列显示其账号、发布动作、排队状态和任务短标识，活跃稿件区不伪造生成阶段

#### Scenario: 暂缓任务与来源标题诚实可见

- **WHEN** 一个发布类委托处于 `deferred` 且 `sourceConstraints.title` 为非空标题
- **THEN** 排队任务列显示“暂缓”状态与该来源标题，不把它描述为执行中或已发布

#### Scenario: 已进入生命周期的任务不重复

- **WHEN** 发布类委托进入 `executing` 或 `waiting_approval`
- **THEN** 该委托不再出现在排队任务列，并由既有发布生命周期投影承担生成中或等待审批的展示

#### Scenario: 服务端过滤先于窗口限制

- **WHEN** 请求按 `actionFamily=publish` 和排队状态过滤，且较新的无关终态任务数量超过 limit
- **THEN** 服务端先筛选匹配任务再应用 limit，仍在排队的发布任务不会被无关记录挤出

#### Scenario: 排队任务查询失败不遮蔽活跃稿件

- **WHEN** 排队任务请求失败而发布生命周期请求成功
- **THEN** 排队任务列明确显示加载失败，活跃稿件、阶段和最近结果仍可查看
