## Context

云端向边缘申请「页面写执行权」（任务租约）失败时，有 6 个错误码（`aidcp-cloud/src/comm/edge-task-lease-client.ts:34-41`）：`edge_offline` / `edge_unhealthy` / `browser_wake_failed` / `acquire_timeout` / `release_timeout` / `edge_disconnected`。

其中 5 个发生在**任务体尚未执行**时——租约没拿到，`withLease` 的 work 回调根本没跑（`edge-task-lease-client.ts:180`），**零命令下发**。只有 `release_timeout` 例外：它发生在 work **之后**的释放阶段，此时评论可能已经真发出去了。

排期／按需评论链有一个判定函数把这些码分成「根本没开始」与「其他」（`comment-scheduler.ts:1509`）。它的实现是一张**枚举白名单**，当前认 4 个码，漏了 `edge_unhealthy`。定向评论链（`comment-scheduler.ts:1190`）连白名单都没有，catch 里一律 `post_failed`。

`typecheck` 对此完全无感：往联合类型里加成员是**变宽**，既有的 `===` 比较仍然合法。这是它第二次从同一位置漏出来（上一次漏的是 `browser_wake_failed`，由 change `browser-slot-scheduling` 补上）。

## Goals / Non-Goals

**Goals:**

- 租约未取得 → 终态一律为「未开始」，回执如实说明零命令下发。**判定与错误码解耦**，新增码不再需要改这里。
- 定向评论链获得同等的诚实性（当前它更糟）。
- 排期链的小时格回流闸重新对这类失败生效（不再白烧名额）。
- 失败原因按**处置语义**分档呈现，使运维不会误判排查方向。
- 修正受理超时的注入点，让 `browser-slot-scheduling` 已声明的 200s 真正生效。

**Non-Goals:**

- **不新增边缘健康上报协议消息**。那要动两份 `protocol.ts` + 命令映射（热点文件、需串行），而本 change 靠诚实回执已能覆盖运维需求。YAGNI。
- **不做 console 的边缘健康视图**。需先在云端建健康投影，属另一尺度的工作。
- **不改边缘**。边缘在 `recovering`（可恢复）态下即时判死任务，是一个独立的可用性问题（一次几秒的 CDP 抖动可判死一次排期评论），但它与本 change 的诚实性缺陷正交，另行评估。
- **不动 `browser-slot-scheduling` 的 tasks.md**（有并发 session 在其上作业）。其 task 3.3 的缺口由本 change 补齐并在此记录。

## Decisions

### D1：判定改为「码的补集」，而非继续维护白名单

**决定**：把「哪些码算未开始」反转为「**哪些码不算**」——只排除 `release_timeout`，其余租约错误一律 `not_started`。

**为什么不继续加枚举项**：白名单的失败模式是**沉默的**——新增码时没有任何机械手段会提醒你回来改它（`typecheck` 变宽不报错）。它已经漏过两次。补集写法把默认值从「不认识 = 当成发布失败（撒谎）」翻转为「不认识 = 当成未开始（诚实）」，让沉默的漏失偏向安全的一侧。

**为什么必须排除 `release_timeout`**：它是**唯一**发生在 work 之后的码——那时评论**可能已经真发出去了**。把它标成 `not_started` 会是反向的谎，并且会错误地把小时格退回去 → 诱发**重复评论**。（实践上它到不了这个 catch：`withLease` 的 finally 把释放异常吞成一条 warn，`edge-task-lease-client.ts:181-188`。但判定必须自洽，不能依赖调用链的偶然性。）

**替代方案（弃）**：给 `EdgeTaskLeaseError` 加一个 `startedWork: boolean` 字段，由抛出点自己声明。更本质，但要改 6 个抛出点 + 一个对外类型，收益与「排除一个码」等价。YAGNI。

### D2：原因分档按「运维该去做什么」切，而不是按错误码切

三档，各自对应一个不同的处置动作：

| 档 | 触发码 | 回执说什么 | 运维该做什么 |
|---|---|---|---|
| 控制面故障 | `edge_unhealthy` | 边端在线，但浏览器控制面不可用 | 查 / 重启该环境的客户端；**别去查连接** |
| 待机唤不醒 | `browser_wake_failed` | 浏览器处于待机且未在唤醒死线内起来 | 可恢复，稍后自动重试 |
| 失联 | `edge_offline` / `edge_disconnected` / `acquire_timeout` / 其他 | 边端离线或未在受理窗内响应 | 查连接 |

把前两者混说是本次故障的次级伤害：卡片说「browser control is unavailable」，而边缘其实**在线且连接正常**，只是浏览器被自己收起来了。

### D3：定向链复用同一判定，但需先扩类型

定向链的终态联合（`comment-task-runner.ts:186`）里**没有 `not_started` 这个概念**，所以不是"接一下判定"就完事——必须：

1. 给 `TargetedCommentOutcome` 加 `not_started` 成员；
2. `targetedOutcomeToReceipt`（`comment-scheduler.ts:1459`）是**穷举 switch 且无 default** —— 不补分支 `typecheck` 直接失败。**这是好事**：编译器会替我们把关，保证回执文案不会漏写。

### D4：受理超时——注入点是唯一事实源

`browser-slot-scheduling` 把类默认改成 200s（`edge-task-lease-client.ts:80`）并写了详尽注释说明为什么 45s 不行，但注入点（`server.ts:1470`）硬写 `?? 45_000`，**永远覆盖默认值**。类默认成了死代码。

**决定**：注入点**删掉硬编码回落值**，改为「有 env 用 env，无 env 走类默认」。这样默认值只有一处，不可能再漂移。

**为什么不是把注入点也改成 200_000**：那会留下两个必须同步的数字——正是本 change 要根治的那类缺陷。

## Risks / Trade-offs

- **[受理超时抬到 200s，失联边缘的失败变慢]** → 可接受，且是设计意图（`edge-task-lease-client.ts:77-78` 明说超时不是发现故障的主要手段）：边缘掉线由连接层**立刻**发现（`pushToEdges` 投递 0 → 即时 `edge_offline`），控制面故障与唤醒失败都是**即时回执**。这条超时只兜「边缘完全失声」这一种罕见情形。

- **[补集写法把未来的新码默认当成 `not_started`]** → 这正是意图。风险的另一面（默认当成 `post_failed`）已经造成了本次事故。若将来出现一个「work 之后」的新码，它必须显式加进排除集——把这条写进要求，并让排除集旁的注释说明判据（**work 是否已经跑过**）。

- **[边缘 `recovering` 瞬态仍会判死任务]** → 本 change 不治（Non-Goal）。诚实性修复之后，这类失败会如实呈现为「浏览器控制面不可用」，运维至少能看懂；可用性改进另行评估。

- **[`edge_unhealthy` 是粘滞态，退回小时格会导致小时内重试再次失败]** → 可接受：重试**零成本**（零命令下发），且重试次数受 `MAX_RETRIES_PER_CELL` 限界（`content-scheduler.ts:239-249`），用尽即诚实放弃。相比「白烧一个名额且不重试」，这一侧明显更好。
