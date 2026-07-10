## Context

同一边缘进程只有一个真实浏览器/CDP 写通道，但当前存在多条互不知情的异步执行链：

- `BrowseSession.commandQueue` 只串行浏览/互动命令；
- `publish.command` 在 `main.ts` 直接进入发布原子执行器；
- `CommentScheduler` 通过停止/恢复云端 `RoleDispatcher` 宣称独占，但停止云端不会等待 edge 已收命令执行完；
- 发布与评论各自有 `finally resume`，彼此没有共同占用计数。

因此“云端不再生成浏览命令”不等于“边缘 CDP 已静止”。已下发的 `navigation.back` 可以晚于发布 `navigate_entry` 完成并改写页面，单条 FIFO 也无法保护由多条原子命令组成的发布事务。

约束包括：edge 继续保持原子执行、云端负责调度；不能取消已经产生不可逆副作用的动作；协议双端必须同步；缺确认必须诚实失败；评论的人审可能持续数分钟，不能长期占用浏览器。

## Goals / Non-Goals

**Goals:**

- 让同一 `edgeId/CDP` 任一时刻只有一个页面写任务拥有执行权。
- 以任务而非单条命令为互斥单位，保证发布完整序列、评论 prepare/commit 各自不可交错。
- 抢占浏览时等待当前原子动作到安全边界，取消尚未开始的陈旧浏览动作。
- 只有 edge 回报 `task.acquired`（即 quiesced）后，cloud 才发送该任务第一条业务命令。
- 人工批准的同优先级任务 FIFO；系统恢复可优先；自动任务不抢人工任务。
- 断线、超时、错误均有界收敛，并保持真实失败语义。

**Non-Goals:**

- 不把云端 LLM、图片生成或飞书人审放进边缘执行队列。
- 不尝试中断已经点击提交、上传中或已产生平台副作用的原子动作。
- 不在本次变更中增加发布最小时间间隔；既有同账号发布 `accountTail` 仍保留。
- 不建立跨 edge 的全局互斥；边界是一个真实 `edgeId/CDP`，同账号不同 edge 仍由既有账号风控/去重治理。

## Decisions

### 1. protocol v2 使用显式任务租约握手

新增四类消息：

- `edge.task.acquire`：cloud→edge，携 `taskId`、`kind`、`priority`、`leaseMs`；
- `edge.task.acquired`：edge→cloud，携 `taskId`、`kind`、`cancelledBrowseCommands`；
- `edge.task.release`：cloud→edge，携 `taskId`、`outcome`；
- `edge.task.released`：edge→cloud，携 `taskId`、`reason`。

所有独占任务业务命令携同一个 `taskId`。edge 只有在它等于当前租约所有者时才执行；无租约、错租约或过期租约必须拒绝。发布有专用结果可直接返回 `task_lease_mismatch`；浏览协议型命令则丢弃并记录结构化告警，cloud 的有界等待最终诚实失败。

选择显式握手而不是依赖 `session.end`，因为 `session.end` 只表达浏览会话生命周期，既不确认当前 CDP 动作完成，也无法跨发布与评论表达所有权。

### 2. edge 协调器是执行权事实源

新增 `EdgeTaskCoordinator`，状态为 `browsing | quiescing | leased`，维护：

- 当前租约；
- 按优先级、同优先级 FIFO 的申请队列；
- 每个租约的有界失效定时器；
- `BrowseSession` 的冻结/恢复适配口。

优先级顺序为 `system_recovery > human > automatic`。发布、人工评论为 `human`；排期评论/发布为 `automatic`；验证码/身份恢复为 `system_recovery`。通知巡视属于可抢占的维护任务，低于人工任务；加群按触发来源映射人工或自动优先级。

租约申请到达后，协调器先调用 `BrowseSession.quiesceForTask()`：禁止新的无 `taskId` 浏览命令入队，删除尚未开始的普通浏览命令，并等待当前 `executeCommand`/启动导航收敛到命令边界。此 Promise 完成后才回 `edge.task.acquired`。

### 3. 浏览循环冻结而非销毁

`BrowseSession` 新增三个窄能力：

- `quiesceForTask()`：冻结普通命令准入、清陈旧队列、等待活动命令结束；
- `onTaskCommand(env, taskId)`：租约有效时仍复用现有命令执行器处理评论 prepare/commit；
- `resumeAfterTask()`：仅在协调器确认无当前/待接管任务后解除冻结，回到 explore 并重新上报真实页面快照。

选择冻结而不是 `stop()/start()`，因为评论仍需使用 `BrowseSession` 内成熟的搜索、开帖、滚评论和发评论执行器；销毁循环会引入队列无人消费和上下文重建问题。

抢占不“排空浏览队列”：只有当前原子动作得到收尾，所有未开始的普通浏览命令作废。它们来自旧页面判断，任务结束后必须通过新快照重新决策。

### 4. cloud 只在 acquired 后运行任务体

新增 `EdgeTaskLeaseClient`，按 `taskId` 关联四类回执，负责推送、超时和释放。调用形态为：

```ts
await leases.withLease({ edgeId, kind, priority, leaseMs }, async (lease) => {
  // 只有这里才允许发送带 lease.taskId 的业务命令
});
```

边缘离线、acquire 超时或 release 异常均抛出可识别错误，由发布/评论现有失败路径如实落状态。cloud 本地不把“发出 acquire”当成已经静止。

edge 收到重复 acquire/release 按 `taskId` 幂等处理；同 `edgeId` 重连时旧租约失效，cloud 在途等待失败，不跨连接静默继承页面所有权。

### 5. 发布持有一份完整租约

`PublishDispatcher` 在账号 `accountTail` 轮到该记录、解析出在线 edge 后申请租约；随后把 `taskId` 传给 `CommandSequencer`，每条 `publish.command` 都携它。发布从 `navigate_entry` 至 `capture_post` 完成或失败全程不释放。

保留 `accountTail` 是因为它同时表达同账号业务顺序和熔断语义；edge 租约解决的是同浏览器跨任务冲突，两者职责不同。

### 6. 小红书评论拆为 prepare 与 commit

当前 `runCommentTask` 把边缘 I/O、LLM、人审和提交揉在一个 runner 中。此次将编排拆开：

1. prepare 租约：生成搜索词可在租约外完成；租约内搜索候选、筛选、打开目标并读取正文/评论，得到带稳定 `noteId` 的快照；释放；
2. cloud-only：甄选、撰写、去 AI 味、飞书人审，期间没有边缘租约；
3. commit 租约：按稳定 `noteId` 重新搜索/打开目标，复检目标身份和去重状态，再发送 `interaction.comment`；释放。

定向当前笔记路径也遵循相同原则：prepare 可读取当前现场，但 commit 不信任旧页面，必须重开/复检。被拒、超时不进入 commit。

Facebook 专用自动评论执行器不复用 xhs `BrowseSession`，本次不改变其人审/校验策略；若它共享同一 CDP 写通道，则通过同一租约客户端包住其边缘 I/O 阶段。

### 7. 浏览恢复由 edge 租约队列收敛决定

删除发布/评论各自“任务一结束立即恢复浏览”的所有权假设。云端仍可停止/重启 `RoleDispatcher` 以阻止产生新决策，但真正的页面恢复由 edge 协调器在当前租约释放且没有更高/同级待接任务时执行。

这避免发布与评论同时排队时发布先结束就恢复浏览，并让连续发布可以直接把执行权交给下一任务而不在中间闪回 feed。

### 8. 系统恢复与只读探针的边界

只读 DOM 探针不申请租约，但不得发导航、点击、输入或滚动。任何探针发现需要恢复页面时，恢复动作必须升级为 `system_recovery` 任务。验证码人工点击沿既有硬暂停通道，优先级最高且可以穿透传输层暂停；普通发布/评论申请在硬暂停时送达 0 并诚实失败/等待重试。

## Risks / Trade-offs

- [协议双端版本短暂不一致] → cloud 对 acquire 设置短超时且不回退无租约执行；按 edge→cloud→docs 同一发布批次交付。
- [租约持有者崩溃导致永久冻结] → edge `leaseMs` 有界到期自动释放并重新评估队列；cloud `finally` 总是 release。
- [发布耗时超过租约] → 每个匹配业务命令刷新 idle deadline，另设绝对上限；默认覆盖现有最慢发布时长并允许 env 配置。
- [评论人审后目标已删除/变化] → commit 必须重开稳定 `noteId` 并复检；失败如实回报，不使用旧 DOM 或位置兜底。
- [冻结时丢弃浏览命令导致少做一次动作] → 这是刻意的安全取舍；释放后以新页面快照重算，不重放旧意图。
- [连续独占任务让浏览饥饿] → 同级 FIFO、自动任务低优先级；后续可增加最大连续任务数，但本次不在人为批准的任务间强插浏览。
- [release 回执丢失] → release 幂等；cloud 可把超时记录为告警，edge 仍由 lease deadline 自愈。

## Migration Plan

1. 先提交 protocol、协调器和测试，保持业务调用未启用。
2. 部署 cloud 与 edge 同一 dev 批次，先以测试 edge 验证 acquire/quiesced/release 往返。
3. 接入发布完整租约并复现“在途 navigation.back + 发布”场景，确认发布首命令只在 quiesced 后发送。
4. 接入评论 prepare/commit，验证人审等待期间浏览可恢复、批准后 commit 重新抢占并重开目标。
5. 接入通知/加群/系统恢复的任务分类，跑协议验收、全量测试与 typecheck。
6. 若 dev 异常，cloud 回滚到旧版本时必须同步回滚 edge；不得保留只改单边的协议组合。

## Open Questions

无阻塞问题。默认租约 idle/absolute 超时与优先级使用代码常量并允许 env 覆盖，dev 实测后再决定是否进入后台配置。
