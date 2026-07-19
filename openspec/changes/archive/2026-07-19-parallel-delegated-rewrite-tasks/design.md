## Context

当前有两层准入：

1. `PublishScheduler` 已按 `rewrite:<accountId>:<sourceId>` / `auto:<accountId>` 建立原子 claim，并受全局默认 3 与账号在途默认 20 约束。
2. `DelegatedTaskWorker` 在调用 scheduler 前先执行 `hasActiveOwnership(accountId, actionFamily)`；该查询把同账号所有 `planning / executing / waiting_approval` 发布任务视为冲突。同时 worker 用单个 `ticking` 布尔覆盖完整执行器等待期。

因此第二层把第一层允许的跨来源并行全部抹平，并让一个待审批任务继续阻塞其他来源生成。

## Goals / Non-Goals

**Goals:**

- 同账号不同稳定 `sourceId` 的参照洗稿从委托入口最多并行三轮，并继续受 scheduler 容量帽保护。
- 同源同刻仍至多一轮生成；前一轮生成收敛后即使草稿待审，也允许再次重洗形成候选版本。
- 普通自主发布继续账号单飞，既有评论/候选控制单飞不放宽。
- 并发准入不产生同 lane 双发、对称互相让路或 attempt 重复记账。

**Non-Goals:**

- 不提高发布 scheduler 全局帽或账号 pending 帽。
- 不改变审批、发布下发串行、风险/配额或平台成功判定。
- 不解决 `publish-claim-reject-defer-not-fail` 已登记的 scheduler claim 拒绝形状问题。

## Decisions

### D1：ownership 以任务输入身份判冲突

为任务推导生成 lane：

- 参照洗稿：`rewrite:<accountId>:<sourceId>`，其中 `sourceId` 只读 `sourceConstraints.sourceId` 的非空稳定值。
- 自主发布：`auto:<accountId>`。
- 评论与候选控制：保持 `(accountId, actionFamily)` 粗粒度。

两个参照洗稿任务只有同账号、同 `sourceId` 且另一条仍在 `planning / executing` 时冲突；`waiting_approval` 表示生成已经收敛，不再占参照洗稿 lane。自主发布之间继续冲突，并保留待审批 ownership。参照洗稿与自主发布互不以 delegated ownership 阻塞，实际资源由 PublishScheduler 的全局帽统一裁决。

### D2：并发执行，但准入串行

worker 增加 `maxConcurrent`（服务端 env `AIDCP_DELEGATED_TASK_MAX_CONCURRENT`，默认 3）与 admission mutex。

每次 tick 在 admission mutex 内完成：到期清理 → `claimNext` → 回读真态 → ownership / external busy → attempt 准备与派发 → 标记 `executing`。只有在执行器即将开始前才释放 admission mutex，让下一次 tick 领取其他 lane。执行器可并行等待；总在途数达到 `maxConcurrent` 时新 tick 快速返回。

这保留 DB 的 `FOR UPDATE SKIP LOCKED LIMIT 1` 和现有 attempt 账本，同时避免两个同 lane 任务同时处于 `planning` 后互相观察、双双 defer 的对称竞态。

### D3：待审批对账不参与生成 ownership

`reconcile_waiting_approval` 是短时持久态对账，不是新生成。它跳过 delegated generation ownership 检查，但仍受 worker 有界并发和 token 条件写保护。对账不应因为另一条生成在跑而停止，也不应占满生成 lane。

## Risks / Trade-offs

- **[三轮生成同时进行提高模型/生图峰值]** → 继续由现有 `AIDCP_PUBLISH_MAX_CONCURRENT_RUNS=3` 与图片子并发控制；worker 默认同为 3，不突破底层帽。
- **[通用 worker 并发使不同账号评论也可能同时执行]** → 评论仍有 delegated ownership、CommentScheduler 状态和 Edge lease 三层保护；worker 总并发有界。测试覆盖同账号评论单飞不回归。
- **[与 `show-queued-publish-tasks` 同改 store]** → 独立 worktree；对方先落地后本 change rebase，冲突只在接口/list 邻近处手工合并并重跑全量。
- **[进程重启时内存中的 worker 在途计数丢失]** → 与现有 PublishScheduler claim 一致；DB claim/attempt 恢复仍按既有先对账、禁止盲重试语义处理。

## Migration Plan

1. 新增纯函数与 worker/store 回归，先验证三条跨来源并行、同源单飞、普通稿单飞。
2. 跑 acceptance、全量、typecheck；串行集成到最新 `master`。
3. 部署 dev，核验服务、端口、PG、飞书和启动配置；以桩/受控任务状态证明 delegated worker 可出现最多三条不同 rewrite lane 同时 `executing`，不触发真实发布授权。

## Open Questions

无。
