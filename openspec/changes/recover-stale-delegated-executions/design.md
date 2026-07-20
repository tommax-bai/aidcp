## Context

`DelegatedTaskWorker` 领取任务后把 DB 状态写成 `planning`，创建并派发 attempt 后再写成 `executing`。claim 带 15 分钟租约，但 worker 没有心跳续租；正常生成可能接近该时长，因此“租约到期”本身不足以证明当前进程已经死亡。

进程重启则有更强证据：新 worker 启动前不存在任何本进程在途执行，DB 中仍为 `planning` / `executing` 的 claim 必然属于已退出进程。当前 `claimNext` 只领取 `queued` / `deferred` / `waiting_approval`，所以这些行即使 claim 过期也不会进入已有 `reconcileAttempt`，直到 24 小时 deadline 才由到期扫描终结；期间它们仍被 `hasTaskOwnershipConflict` 当成活跃 owner。

Console 已收到 `currentStep` 与 `nextEligibleAt`，但排队卡只把 `deferred` 翻译为“暂缓”，没有展示 `waiting_ownership` / `waiting_safe_slot` 等已有事实。

## Goals / Non-Goals

**Goals:**

- Cloud 每次 worker 启动时，在接受新任务前回收上一进程遗留的执行 claim。
- 复用 attempt 账本区分“确定未派发”与“已派发、结果未知”，不盲重试、不伪造成功或干净失败。
- 释放僵尸 ownership，使同源重新触发能在恢复收敛后继续进入生成。
- 让 Console 用已有 `currentStep` 展示有证据的暂缓原因。

**Non-Goals:**

- 不自动恢复已丢失的进程内生成管线。
- 不改变 `(accountId, sourceId)` 单飞、全局生成帽、账号在途帽或审批规则。
- 不把任意运行时 claim 超时都当成进程死亡；本 change 不新增 claim heartbeat 或多 Cloud 实例协调。
- 不修改平台发布下发与 at-least-once 边界。

## Decisions

### D1：只在 worker 启动前做一次进程级恢复

新增 store 级 `recoverInterruptedClaims`，由 server 在 `worker.start()` 前 `await`。它原子选择 `planning` / `executing` 行，清除旧 claim，并按 pause/cancel 状态恢复到可收敛状态；普通任务回 `queued`。每行写 `interrupted_claim_recovered` 事件，记录原状态与旧租约时刻。

不在每个 poll 按 `claim_expires_at` 扫描：当前没有续租心跳，生成超过 15 分钟时仍可能真实在跑；周期扫描会制造并发重复。启动边界才提供“旧执行进程已经不存在”的确定证据。

### D2：恢复后复用现有 attempt reconcile，不新造第二套状态机

- 没有 unsettled attempt：任务按正常队列重新执行。
- `prepared`：该状态证明 `markAttemptDispatched` 尚未发生；worker 原子丢弃临时 attempt、归还 attemptCount，再排队。
- `dispatched`：进入执行器既有 `reconcileAttempt`。没有可核验证据时以 `submitted_result_unknown` 终结，释放 ownership，禁止自动重复派发。

否决“直接把所有 executing 改 failed”：它会把已派发但是否产生候选未知的事实说成干净失败。也否决“全部重新 queued 并直接开始新 attempt”：它可能重复生成、重复发审批卡，甚至对候选控制/评论形成重复写入。

### D3：恢复先于 worker 定时器和并发 pump

server 必须先等待恢复完成，再启动最多 3 槽的 pump。这样新任务不会在旧 ownership 尚未清理时先被领取，也避免多个 slot 对同一恢复批次发生对称让路。

### D4：Console 从 `currentStep` 做窄映射

不为本 change 新增 DB 列或 API 字段。排队卡对稳定步骤码显示中文原因：`waiting_ownership`、`waiting_safe_slot`、`waiting_new_target`、`paused_by_user`；未知步骤不猜测、不显示原因。时间文案改为“预计再次检查”，避免把轮询时刻承诺为一定起跑。

## Risks / Trade-offs

- **[同一数据库被多个活跃 Cloud worker 共享时，新实例启动会回收另一实例的任务]** → 当前部署契约为每 target 单 Cloud service；本 change 明确不扩展为多实例租约协议。若未来水平扩容，须先引入 worker session/heartbeat。
- **[dispatched 实际只做了生成、却被标结果未知]** → 保守终局比盲重试安全；重启后进程内 outcome 已不可回读，且现有账本没有候选 recordId 证据。新触发会在 ownership 释放后继续。
- **[恢复批次触发多张终态失败卡]** → 仅对已有 dispatched 且无法对账的真实遗留任务发卡，文案明确“重启前未收敛、结果未知”；不声称平台失败。
- **[Console 原因映射随步骤码漂移]** → 使用显式白名单，未知码静默省略，不猜测。

## Migration Plan

1. 先部署 cloud：启动恢复旧 claim，验证事件、任务终态与新任务进入生成。
2. 再部署 console 静态资源：展示暂缓原因与“预计再次检查”。
3. 核验 dev 服务、8787/8090、PostgreSQL、Feishu 与 isales 隔离；检查目标两条新任务不再因昨日同源 owner 反复暂缓。
4. 回滚时恢复 cloud/console 备份并重启 cloud；已诚实终结的旧僵尸任务不反向复活，新任务保留真实状态。

## Open Questions

无。
