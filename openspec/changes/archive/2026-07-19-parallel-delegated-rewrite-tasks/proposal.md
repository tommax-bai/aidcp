## Why

底层发布调度器已经按 `(accountId, sourceId)` 支持同账号三篇不同来源的洗稿并行，但 Edge/console 的结构化洗稿现在先进入统一 `DelegatedTask` worker。该层仍以 `(accountId, actionFamily=publish)` 做粗粒度 ownership，并且单个 worker 在一条生成完整收敛前不领取下一条任务，导致底层“洗稿并行 3”在真实委托入口被重新串行化。

2026-07-19 dev 现场证据：账号“工程师大白”三条不同 `sourceId` 的洗稿任务先后入队，后两条反复以 `delegated_ownership_busy` 延后；实际执行始终只有一轮。第一条失败后第二条才开始，第二条从待审转终态后第三条才开始。运行时 `AIDCP_PUBLISH_MAX_CONCURRENT_RUNS` 未覆盖、真实默认仍为 3，因此不是容量配置问题，而是委托层准入粒度与执行模型不一致。

## What Changes

- 委托发布 ownership 改为与发布生成契约一致的输入身份：带稳定 `sourceId` 的参照洗稿按 `(accountId, sourceId)` 单飞；无参照稿的自主发布继续按账号单飞。
- 参照洗稿生成收敛并进入 `waiting_approval` 后不再占用生成 ownership；同源后续重洗允许串行再生成，不同来源可并行。
- `DelegatedTaskWorker` 增加有界并发准入，默认并发 3；领取、ownership 检查和转为 `executing` 仍串行完成，执行器开始后才释放下一条准入，避免同键双任务对称让路或双发。
- 评论、候选控制和无参照自主发布保持既有粗粒度单飞；暂停、取消、attempt 账本、截止时间、人审和平台验证语义不变。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `publish-generation-concurrency`: 补充统一委托入口必须保留 `(accountId, sourceId)` 洗稿并行，不得在上层重新串行化。
- `user-delegated-tasks`: ownership 从单一动作族细化为动作语义相容的生成 lane，并定义有界并发 worker 的准入原子性。

## Impact

- `aidcp-cloud`
  - `src/delegated-task/worker.ts`: 有界并发与串行准入闸。
  - `src/delegated-task/store.ts`: task-aware ownership 检查。
  - 新增 ownership 纯函数及 worker/store 回归测试。
  - `src/server.ts`: `AIDCP_DELEGATED_TASK_MAX_CONCURRENT`，默认 3。
- 不修改 `publish-scheduler.ts`，避免与活跃的 `publish-trigger-and-apply` / `publish-claim-reject-defer-not-fail` 争写发布 scheduler 热点。
- `show-queued-publish-tasks` 正在修改 `store.ts` 的只读 list 路径；本 change 在独立 worktree 开发，集成时串行 rebase。
