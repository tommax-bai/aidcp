## Why

**「资源暂时被占」被判成了失败，而且是 2 秒内烧光预算的那种失败。**

这是 change `delegated-terminal-failure-reason` 排查用户投诉「发帖失败卡不说原因」时挖出的**第一放大器**：那个 change 让卡把原因说出来了，但没修**为什么会走到这张卡**。

链路（全部已在代码里坐实）：

1. 同账号已有一轮发帖编排在跑 / 该账号在途待审草稿到上限 / 全局生成并发已满 → `tryClaim` 拒绝（`publish-scheduler.ts:504-514`），被包成 `{ result:'triggered', status:'skipped', failureReason:'已有一轮发帖编排在运行中，本次未触发（already_running）' }`。
2. `executors.ts:133` 有一条判断**想**把这三类归为「稍后重试」——`if (outcome.result === 'blocked' && /risk_|publish_capacity|publish_busy|already_running/.test(outcome.reason))`。但这三者**从来不是 `blocked`**（`blocked` 只由人设未绑 / 风控产出，见 `publish-scheduler.ts:282/299/349/353/390/397/398`）。**该正则的后三个分支永不可达**，作者本意显然是 defer。
3. 于是落到 `executors.ts:153` → `{ kind:'failed', retryable:true }` → `worker.ts:258-260` 以 `nextEligibleAt = now + 1_000` **热重试**。
4. 自然语言发帖默认 `maxAttempts = max(target, target*2) = 2`（`parser.ts:60-63`）→ **约 2 秒烧光预算** → `failed / max_attempts / 真实完成 0/1`。

这直接违反已归档的项目共识「**资源暂时被占绝不判失败；失败判据只能是结构上做不到**」（memory `failure-must-be-structural`：排队是机器行为，不是失败）。撞车本该退避重试、把帖子发出去；今天它变成一次用户可见的失败。

## What Changes

- **按真实形状判定 claim 拒绝**：`already_running` / `publish_capacity` / `publish_busy` / `duplicate_source` / 生成并发已满这几类 → `deferred`（退避重试），MUST NOT 判 `failed`。判据 MUST NOT 依赖 `result === 'blocked'`（这三类从不是 blocked，是死条件）。
- **优先改由 scheduler 给出结构化形状**，而不是让委托层对人类可读文案做正则猜测——今天 `executors.ts:133` 对 `outcome.reason` 做子串匹配，而该字段在 `triggered` 分支里是**中文句**（`已有一轮发帖编排在运行中，本次未触发（already_running）`），靠文案匹配天然易碎。倾向让 `tryClaim` 拒绝走 `{ result:'skipped' }`（union 里已有此变体、目前无人产出）或带上机器可读的 `claimReject` 码。
- **退避间隔按「等的是什么」取**：撞车等的是另一轮编排跑完（分钟级），`now + 1_000` 的热重试只是空转烧预算。
- 顺带清掉 `executors.ts:133` 的死条件，避免下一个人照着它推理。

**注意**：`externalBusy`（`executors.ts:385-389` → `publishes.isBusy(accountId)`）已经挡掉一部分撞车，但它**不是全覆盖**——按 key 的单飞（`rewrite:<account>:<sourceId>` / `auto:<account>`）、账号在途帽（DB 待审计数）、全局并发帽都在 `tryClaim` 里，`isBusy` 看不到。所以这条路真实可达。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `user-delegated-tasks`: 「所有任务必须有有界尝试、截止时间与诚实部分完成」增补——资源暂时被占 MUST 判为可恢复的延后，MUST NOT 消耗失败预算；且延后间隔 MUST 与「在等什么」相称，MUST NOT 以秒级热重试空转烧尽预算。

## Impact

- **`aidcp-cloud`**
  - `src/publish-agent/publish-scheduler.ts`：让 claim 拒绝带上机器可读形状（**热点文件**，见下）。
  - `src/delegated-task/executors.ts`：`publishResult` 按新形状判 deferred + 退避间隔；删死条件。
  - 测试：`test/delegated-task/executors.test.ts` + scheduler 侧。
- **串行门槛（这是它被从 `delegated-terminal-failure-reason` 切出来的原因）**：`publish-scheduler.ts` 曾被 `delegated-executor-operator-authority-parity`（已于 `cd185df` 归档）与 `publish-trigger-and-apply`（活跃、29/37）双占。**动工前先 `openspec list` 复核 `publish-trigger-and-apply` 是否仍在飞**；若在，按 CLAUDE.md §7「热点文件单写者」串行等待。
- **验收关联**：真机项与 `delegated-terminal-failure-reason` 同簇（`docs/real-machine-acceptance-backlog.md` 簇 86）——那批要验「撞车时卡上说不说得清原因」，本 change 要验「撞车时**根本不该出这张卡**，帖子应当发出去」。
