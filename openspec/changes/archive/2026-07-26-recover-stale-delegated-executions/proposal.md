## Why

Cloud 在委托任务执行中重启时，数据库会把 `planning` / `executing` 与已失效的 claim 一起永久保留到任务截止时间；这些残留任务继续占用 `(accountId, sourceId)` ownership，使运营重新触发的洗稿每 30 秒反复显示“暂缓”，即使生成并发仍有空位。2026-07-20 dev 现场已有两条同源任务因此被昨日重启遗留的 `executing` 阻塞，当前实现也违反了“重启后干净接受新触发”的既有发布并发契约。

## What Changes

- Delegated worker 启动时原子回收上一进程遗留的 `planning` / `executing` claim，清除已失效的 ownership，而不等待 24 小时 deadline。
- 对未派发的 prepared attempt 证明零动作后安全退回队列；对已标记 dispatched、无法证明结果的 attempt 走现有 reconcile/`submitted_result_unknown` 终局，禁止盲重试与重复写入。
- 恢复动作写入稳定事件与日志，保留被回收状态、attempt 形状和恢复数量，便于运行态审计。
- Console 排队任务在“暂缓”之外显示可读等待原因；`waiting_ownership` 明确说明正在等待同一参照稿任务释放，不再让“下次尝试”看起来像届时必定起跑。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `user-delegated-tasks`: 增补 Cloud 重启时对遗留执行 claim 的恢复、未派发与结果未知分流，以及不得长期占用 ownership 的要求。
- `publish-generation-concurrency`: 补齐持久化委托层的重启恢复，保证进程内生成轮丢失后同源新触发不会被旧 DB `executing` 残留阻塞。
- `console-panel-api`: 暂缓任务除状态与下次尝试时间外，还须展示已有证据支持的等待原因。

## Impact

- `aidcp-cloud`: `src/delegated-task/store.ts`、`src/delegated-task/worker.ts`、`src/server.ts` 及委托 worker/store 测试。
- `aidcp-console`: 内容页排队任务原因映射及页面测试。
- PostgreSQL：不新增表或列；复用 `delegated_tasks`、`delegated_task_attempts` 与 `delegated_task_events`。
- 运行态：部署 dev 后启动恢复会诚实终结当前两条已派发结果未知的昨日僵尸 attempt，并释放同源新任务；不会宣称旧生成成功或自动发布。
