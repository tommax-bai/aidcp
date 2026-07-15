## Context

`waiting_approval` 同时承担用户可见业务状态和 worker 可轮询状态。当前 `claimNext` 会把它改成 `planning` 并递增版本；审批仍未完成时又 release 回 `waiting_approval`、再次递增版本并调用 `onTaskUpdated`。服务端把所有 `waiting_approval` 更新都映射成新的飞书卡，因此 30 秒重试延迟叠加 5 秒 worker tick 后形成约 35 秒一次的通知循环。

审批结果仍需周期对账，因为审批可能来自飞书或 console，且 cloud 重启后必须能恢复；不能简单把 `waiting_approval` 从 worker 队列永久排除。

## Goals / Non-Goals

**Goals:**

- 等待审批的无变化对账不改变用户可见状态或版本，不发新进度卡。
- 保留跨进程 claim、lease 到期恢复和周期性审批结果对账。
- 审批通过、驳回、任务终态、真实计数及暂停/取消变化仍能正常反馈。
- 防止未来其他相同状态回写重新引入重复卡。

**Non-Goals:**

- 不改变发布审批业务、人审默认值或平台成功计数。
- 不把轮询改造成新的消息总线，也不新增数据库迁移。
- 不更新历史飞书消息，不构建 Edge 安装包，不部署 OL。

## Decisions

### 1. 等待审批使用“同状态静默 claim”

`claimNext` 命中 `waiting_approval` 时只写 claim token、lease 和内部 `reconcile_waiting_approval` step，保持业务状态与 task version 不变。普通 `queued`/`deferred` 仍按既有方式转换为 `planning` 并递增版本。

选择该方案而不是完全停止轮询，因为 console 审批和重启恢复仍依赖对账；也不只做飞书层节流，因为只节流会继续制造无意义事件、版本漂移和过期卡片按钮。

### 2. 增加专用静默 release 操作

当对账结果仍为 `waiting_approval` 时，store 通过专用方法清除 claim、设置下一次对账时间并恢复内部 step，但不递增 task version、不写业务状态事件。worker 直接返回，不调用 `onTaskUpdated`。

若对账得到批准、驳回、失败或真实成功，则继续走现有 attempt/terminal 更新路径并调用 `onTaskUpdated`。

### 3. 通知层使用语义指纹兜底

飞书通知以状态、成功/尝试/跳过/失败计数、当前步骤、终态结果、暂停/取消意图组成语义指纹，忽略 `version`、`updatedAt`、claim 和下一轮对账时间。同一进程内相同指纹只发送一次；终态和实际状态变化仍发送。

静默 claim 是根修复，语义指纹是防御性兜底。进程重启后指纹缓存可以为空，因为静默 claim 本身不会再次触发通知。

## Risks / Trade-offs

- [审批变化不能被及时发现] → 继续保留原轮询间隔和 executor 对账，只静默“结果仍未变化”的分支。
- [多 worker 重复对账] → 仍使用数据库 claim token、lease 和 `FOR UPDATE SKIP LOCKED`，不削弱 ownership。
- [暂停/取消与对账竞争] → 静默 release 使用 claim token 条件更新；若控制动作已终结任务则返回最新真态，不把终态改回等待审批。
- [通知去重误吞真实变化] → 指纹包含全部用户可见计数、状态、结果和控制意图，并由测试覆盖 waiting→completed/failed/cancelled。
- [历史任务已有高版本] → 不回写或重置旧版本；部署后只停止继续无意义增长。

## Migration Plan

1. 在 cloud worktree 实现 Pg/Memory store 的静默等待审批 claim/release。
2. 更新 worker 和通知指纹，补回归测试。
3. 依次运行相关 acceptance、full tests、typecheck；严格校验 OpenSpec。
4. 提交、推送并快进集成 cloud master/control main。
5. 运行 `scripts/deploy-target dev --check`，备份并部署 cloud；验证现有任务事件不再周期增长、服务健康及审批结果仍可对账。
6. 失败时恢复 cloud 备份并重启服务；不触碰 OL。

## Open Questions

无。现有任务 `69324efc-0d50-42a7-bf35-171258f2eca7` 可作为 dev 的非破坏性静默观察样本，但不会代替真实审批/发布验收。
