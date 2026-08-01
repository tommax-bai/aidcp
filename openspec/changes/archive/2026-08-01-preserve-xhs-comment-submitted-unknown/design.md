## Context

小红书 Native 执行端在评论提交动作派发后，会用同一目标上的“评论出现”和“编辑器清空”做双证据确认。当前可能返回 `submitted_unconfirmed`、`submitted_editor_not_cleared` 或 `submitted_ack_unreadable`；三者都表示提交动作已经派发，但 Cloud 的 `edge-steps` 只识别第一种。其余原因落入 `not_dispatched`，下游不会写评论去重账，之后可能再次选择同一笔记并重复提交。

现有 Cloud 下游已经正确处理 `CommentPostResult.status='submitted_unconfirmed'`：普通搜索评论和定向评论都会写去重账并停止重试，同时不把它记为平台确认成功。因此修复应停留在 Edge 回执进入 Cloud 的归一边界。

## Goals / Non-Goals

**Goals:**

- 将三个已知的提交后不确定原因归一到现有 `submitted_unconfirmed` 状态。
- 复用现有去重且不重试的下游处理，并保持确认成功计数边界不变。
- 用闭集测试锁住提交后、提交前失败和提交前抢占三类语义。

**Non-Goals:**

- 不更改 Edge 的 DOM/CDP 操作、验证轮询或原因码。
- 不扩展协议、不新增持久化状态、不重命名现有 Cloud 结果类型。
- 不把任意 `submitted_*` 字符串自动视为已派发，也不执行真实账号验证。

## Decisions

1. 在 `aidcp-cloud/src/comment-agent/edge-steps.ts` 使用一个命名的精确原因集合做归一。精确闭集避免把未来语义不明的字符串仅凭前缀升级成“已提交”，同时让新增 Edge 原因必须显式补齐 Cloud 测试。
2. 三个原因都返回现有 `{ status: 'submitted_unconfirmed' }`。不扩展 `CommentPostResult`，因为两个任务入口已经以该状态写去重并停止重试；新增状态会扩大所有穷举分支和存储契约。
3. 平台确认成功仍只由 `action.completed.ok === true` 产生。提交后不确定只防重复，不进入确认成功计数。
4. 在 `edge-steps` 单元测试中逐项覆盖三个原因，并保留未知失败与抢占反例；下游去重行为由现有 `comment-task-runner` 测试继续证明。

## Risks / Trade-offs

- [Edge 新增另一种提交后原因但 Cloud 未同步] → 精确集合默认不升级语义；要求同一变更补充集合和测试，并通过协议/回执审计发现漂移。
- [提交前失败被错误列入集合] → 测试固定当前三个均来自提交派发后的验证阶段，未知原因继续落入 `not_dispatched`。
- [结果未知却被误报成功] → 继续复用 `submitted_unconfirmed`，不产生 `confirmed`，不改变成功计数门。

## Migration Plan

1. 先部署 Cloud 归一与测试；Edge 现有版本无需同步升级。
2. 部署后检查 Cloud 日志与健康状态，不执行真实评论。
3. 若需回滚，只回滚 Cloud 提交；协议和数据结构未变化，无数据迁移。

## Open Questions

无。
