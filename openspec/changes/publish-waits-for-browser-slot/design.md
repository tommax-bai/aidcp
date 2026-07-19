## Context

发布下发先由 Cloud 请求 `edge.task.acquire`。目标浏览器未启动且本机槽位已满时，Electron 已把环境保留在严格 FIFO 的 `slotWaiters` 中；本次调用方到达唤醒死线后，Edge 回 `browser_wake_failed`，但环境仍会在后续槽位释放时启动。Cloud 当前在发布序列尚未开始的统一 catch 中作废授权，因此浏览器后来启动也没有原任务可继续。

现有系统已经具备三个所需部件：`publish_log.status='pending_approval'` 持久保存草稿、授权信号文件持久保存 `approved + contentVersion`、`scanAndDispatchApproved()` 每 60 秒补偿扫描已批准草稿。客户端 hello 快照也会从草稿和授权信号重建 `approved`（已批准、待发送）状态。重新实现一套队列或发布状态机会制造双重权威。

Edge 侧已有最新 `browserStandby` 提示和完整的安全关闭闸，但 task coordinator 在租约释放后只恢复普通浏览，没有通知 Electron 立即重新应用提示；因此即使账号明确处于长期等待，也可能多占一个快照周期的槽位。

## Goals / Non-Goals

**Goals:**

- 让明确的浏览器槽位等待在零发布副作用阶段保留授权，并经现有扫描器最终重试。
- 保持故障分类和发布副作用边界诚实：只有 `browser_wake_failed` 获得该待遇。
- 让操作员收到一次“等待槽位、自动重试”的通知，而不是离线或重批指引。
- 任务完全收敛后立即复用现有待机提示和安全闸归还可释放的浏览器槽位。
- 保持严格 FIFO、同账号串行、无抢占和 AC-PUB 版本闸。

**Non-Goals:**

- 不改变本地配额、慢启动、浏览器并发或启动排队上限。
- 不新增数据库表、发布业务状态枚举、Redis/消息队列、槽位预约或发布优先级车道。
- 不保证精确分钟发布；有槽位争用时发布可以在既有调度窗口之后执行。
- 不自动重试 `edge_offline`、`edge_unhealthy`、`acquire_timeout`、`yield_timeout` 或任何已经开始发布序列的失败。
- 不强制关闭仍有近期工作或不满足既有冷待机安全闸的浏览器。

## Decisions

### 1. 以授权信号和补偿扫描作为唯一持久队列

`PublishDispatcher` 收到 `EdgeTaskLeaseError.code === 'browser_wake_failed'` 且发布序列未开始时，不调用 `voidApprovalSignal()`、不改变 `publish_log`、不计序列失败。授权文件与待审草稿共同构成重启可恢复的“已批准待发送”事实；现有扫描器下一轮重新调用 `dispatch(recordId)`，本地浏览器若已由 FIFO 队列启动即可正常取得租约。

备选方案是新增 `waiting_browser_slot` 发布状态和重试表。未采用，因为它会与授权文件、`pending_approval` 和既有 scanner 形成三套恢复权威，还要求迁移所有候选/审批/客户端投影。

### 2. 只对白名单失败码保留授权

`browser_wake_failed` 明确表示 Edge 控制面在线且未授予租约，业务回调尚未进入；它是可恢复的浏览器缺席结果。真实离线、CDP 不健康和 acquire 无响应继续作废授权并要求重批；发布序列一旦进入，继续按现有 submitted/failed/unknown 规则收敛，绝不自动重发。

`browser_wake_failed` 目前也覆盖本地启动队列满和浏览器启动失败。第一版不扩协议携带子原因：本地已有 1/2/5 分钟退避并会继续尝试，Cloud 的重复 acquire 又受 60 秒 scanner 和单稿 `inFlight` 去重约束。若真机证据显示结构性启动失败造成长期空转，再单独增加机器可读子原因，不在本 change 预先扩协议。

### 3. 通知去重保持进程内、有界

dispatcher 用按 `recordId` 的集合记录已通知的槽位等待。第一次进入等待发 `browser_slot_waiting`；同一进程内 scanner 重试不重复通知。取得租约、草稿离开待审或授权失效时清除。Cloud 重启后可能再发一次恢复上下文通知，这是可接受的有界重复，换取不新增持久通知账本。

### 4. Edge 只发送私有“安全空闲”提示

`EdgeTaskCoordinator.resumeBrowseIfIdle()` 在确认无 active/queued/quiescing task、发布写者已收敛且 `resumeAfterTask()` 完成后，调用可选 `onIdle`。核心把它转成父子进程私有 IPC `lifecycle.task_idle`；Electron 收到后读取该环境最新的 standby hint，并调用现有 `applyBrowserStandbyHint()`。

该提示不命令关闭浏览器。是否关闭仍由现有本地设置、最短持有时长、验证码/认证/暂停状态、任务租约与 in-flight 操作安全闸决定。无最新提示时 no-op；新任务竞态到达时核心的 `hasActiveLease()` 闸仍会拒绝待机。

备选方案是发布完成后直接 `closeBrowser()`。未采用，因为它会打断仍有浏览/点赞工作的账号，并制造高频关开和登录态风险。

## Risks / Trade-offs

- [本地浏览器最终启动，但 Cloud 最多晚一个 scanner 周期才重投] → 接受约 60 秒延迟，避免新增 browser-ready 协议和事件订阅。
- [结构性浏览器启动故障也落入 `browser_wake_failed`] → 本地已有有界退避和诚实状态；本 change 保留现有码，不扩大到离线/CDP/未知超时。真机按码分布后再决定是否细分。
- [Cloud 重启后等待通知可能重复一次] → 接受有界重复，避免数据库通知账本；同一进程内周期扫描严格去重。
- [旧待机提示在 task idle 时已过时] → `applyBrowserStandbyHint()` 重新执行 `wakeAt`、门槛、最短持有与全套安全检查；过时或不合格提示只会 skip，不直接关闭。
- [严格 FIFO 可能使刚到点的发布晚于普通排队环境] → 保持既有公平性和无饿死原则；精确时点/预约槽位另行评估，不在本次加入抢占。

## Migration Plan

1. 先部署 Cloud：新客户端与旧客户端都能返回既有 `browser_wake_failed`；Cloud 开始保留授权并经 scanner 重试。
2. Edge 源码随后落地 task-idle 重判；未升级客户端仍能正确自动重试，只是槽位可能晚一个快照周期释放。
3. dev 以 6 环境 / 5 槽位验证：第六个已批稿等待、任一安全待机后自动取得槽位且只发一次。
4. 回滚 Cloud 即恢复“作废授权、要求重批”的旧行为；回滚 Edge 只损失即时重判，不影响槽位和发布安全。

## Open Questions

None. 本 change 不承诺精确分钟发布；若后续业务要求严格截止时间，应以独立 OpenSpec 定义调度窗口和过期语义。
