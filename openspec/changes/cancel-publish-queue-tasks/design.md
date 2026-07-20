## Context

“发布队列”同时读取 Cloud 的发布生命周期和发布类委托任务。尚未进入完整发布生命周期的 `queued`、`planning`、`deferred` 任务目前只能查看。Cloud 已有受管理端 JWT 保护的 `POST /api/delegated-tasks/:taskId/cancel`，以任务 `version` 做 CAS，并对尚未开跑与已经进入规划的任务采用不同的安全收口方式。

## Goals / Non-Goals

**Goals:**

- 让管理员在对应排队任务卡片上直接、安全地发起取消。
- 保证取消请求针对页面所见版本，避免陈旧页面取消已经变化的任务。
- 区分立即终止和等待工作器安全收口，给出真实反馈。
- 操作后主动刷新任务列表与发布生命周期，避免等待下一轮轮询。

**Non-Goals:**

- 不新增 Cloud 接口、任务状态或数据库迁移。
- 不取消已经进入发布生命周期的稿件、人工审批或平台下发动作。
- 不把取消请求已记录描述成外部平台动作已停止。

## Decisions

### Reuse the delegated-task cancellation contract

Console 调用现有 `POST /api/delegated-tasks/:taskId/cancel`，请求体只传当前任务的 `version`。不增加发布队列专属接口，因为服务端已经集中处理状态转换、审计事件、部分完成语义和工作器协作；重复实现会产生两套取消规则。

### Keep cancellation scoped to the rendered queued-task region

取消入口只出现在发布队列当前筛选出的发布类 `queued`、`planning`、`deferred` 任务卡片中。生命周期稿件继续使用既有审批和下发流程，避免把“任务排队取消”和“已生成稿件处置”混成一个权限动作。

### Confirm intent and serialize mutation feedback

每张卡片提供“取消任务”按钮并使用产品既有确认浮层。确认文案包含任务标题或动作名；关闭确认浮层不发送请求。请求进行时锁住取消操作并只在对应卡片显示 loading，避免重复提交与错认目标。

### Reflect server truth instead of optimistic terminal success

服务端返回终态时，Console 提示任务已取消；返回 `cancelRequested=true` 且任务仍在 `planning` 时，Console 只提示取消请求已受理，并在刷新后显示“取消中”且不允许重复取消。未知的非终态回执只说明状态已更新，不推断已经停止。

### Refresh both task and lifecycle projections

成功后失效 `delegated-tasks` 与 `content/queue` 查询。版本冲突时也刷新排队任务，让管理员基于最新版本重新判断；其它失败保留卡片并使用说人话错误，不展示原始错误码。

## Risks / Trade-offs

- [Risk] `planning` 任务不会在接口返回瞬间变成终态，用户可能认为取消无效。 → 明确显示“取消中”，并保留轮询直到 Cloud 工作器完成安全收口。
- [Risk] 取消与后台状态推进并发，页面版本可能过期。 → 强制携带 `version`，409 时不重试写入，只刷新最新状态。
- [Risk] 取消成功后的两类查询短暂不同步。 → 同时失效任务与生命周期查询，且以各自 Cloud 响应为真，不做跨模型乐观覆盖。

## Migration Plan

1. 在 Console 类型镜像中接收可选 `cancelRequested` 证据并实现卡片交互。
2. 增加确认、CAS 请求、立即取消、取消中、版本冲突与失败保留测试。
3. 通过 Console 测试、typecheck、build 与 OpenSpec strict validation 后合入默认分支。
4. 从干净的 Console 默认 checkout 部署静态资源到 `dev`；回滚时恢复部署前的 Console 备份，无需 Cloud 或数据库回滚。

## Open Questions

None.
