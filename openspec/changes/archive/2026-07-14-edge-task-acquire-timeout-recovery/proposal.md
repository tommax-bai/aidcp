## Why

自动排期评论在 edge 忙于收敛普通浏览动作时可能等不到 `edge.task.acquired`。cloud 超时后只丢弃本地等待，edge 仍可能稍后获得并持有一段无主租约，导致浏览器冻结；同时任务回执会错误地写成“已选中笔记、发布未确认”，即使评论流程尚未开始。

## What Changes

- 为 `edge.task.acquire` 增加由 cloud 下发的本地等待上限，使 edge 不会无限等待普通浏览动作后再授予过期任务。
- cloud 获取租约超时时主动撤销尚未取得的任务；若随后收到迟到的 acquired 回执，重复撤销，避免无主租约占用浏览器。
- 自动排期评论在租约未取得时返回“未开始”的诚实结果，明确没有搜索、选中笔记或发布评论。
- 增加 cloud、edge 与协议契约测试，覆盖超时撤销、迟到回执和人类可读回执。

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `edge-task-execution-coordination`: 为 acquire 等待、撤销和迟到回执定义有界且可自愈的租约收敛。
- `content-schedule`: 为自动排期评论在浏览器接管失败时定义未开始、未执行页面动作的诚实回执。

## Impact

- Cloud：edge 任务租约客户端和自动评论调度器。
- Edge：任务协调器和双端协议定义。
- 控制仓：协议文档与 OpenSpec 契约。
- 不改变已取得租约后的评论提交、风控计数或浏览器关闭策略。
