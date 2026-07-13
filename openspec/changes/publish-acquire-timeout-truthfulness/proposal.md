## Why

发布时的 edge task acquire timeout 表示客户端连接仍在线、但浏览器未能在时限内收敛到可接管的安全边界；当前发布通知却把它说成“边缘离线”。一次异常缓慢的 `note.open` 还会长时间占用浏览原子动作，直接触发这一超时并让运营无法判断应恢复连接还是检查 CDP。

## What Changes

- 将发布前的真实无在线 edge 与在线 edge 的 task acquire timeout 分为不同的重排/通知结果；两者都保留草稿、作废本次授权并要求重新批准。
- 为 `note.open` 的接管前浏览动作增加整体墙钟上限和可观测的分阶段耗时，超时后以真实失败收敛，不再无限占住任务协调器。
- 保持正在执行的浏览动作不被发布中途强杀；超时边界只在 `note.open` 自身的安全失败出口收敛，随后让等待的租约继续取得或被 cloud 正常取消。
- 增加 cloud/edge 测试，覆盖通知分类、草稿回待审和 `note.open` 超时释放接管队列。

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `publish-dispatch-resilience`: 区分实际边缘离线与浏览器接管超时的待审重排通知。
- `edge-task-execution-coordination`: 要求接管前的在途浏览原子动作有界结束并留下可诊断耗时，避免无限阻塞任务租约。

## Impact

- Cloud：`PublishDispatcher` 的失败分类、运维通知与发布回归测试。
- Edge：`note.open` 的执行时限/观测与浏览接管协调测试。
- 控制仓：对应 OpenSpec 契约与任务记录。
- 不改变发布授权门、已开始发布序列的失败语义或浏览/发布的任务优先级。
