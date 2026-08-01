## ADDED Requirements

### Requirement: Every irreversible Xiaohongshu page write SHALL open a commit window

Each Xiaohongshu page action whose platform-side effect cannot be undone or replayed SHALL be wrapped in a commit window for the duration between the last cancellable point and the terminal receipt. At minimum this covers:

- comment submission (the submit keystroke that publishes the comment),
- notification-sweep consumption of the comment category,
- notification-sweep consumption of the like/follow categories,
- publish submission.

The window MUST be requested by the runtime that actually performs the write, at the point immediately before dispatch, and MUST be released at the terminal outcome (success, failure, or budget expiry). Wrapping a whole command instead of the write is not compliant: it converts "protect the irreversible write" into "forbid preemption for the entire command" and silently disables preemption for navigation, locating and waiting.

While a window is open, the coordinator MUST refuse preemption and answer with a busy verdict plus the remaining budget, and MUST NOT inject a cancellation safe point inside the window.

If the window cannot be obtained — request denied, no window facility wired, or the facility unavailable — the write MUST NOT be dispatched and the receipt MUST report a truthful not-started outcome. The absence of in-flight cancellation for write commands MUST NOT be treated as protection: an unprotected write that happens not to be torn today is unprotected, and the coordinator's window probe reporting "no window" during a live irreversible write is itself the defect.

#### Scenario: Preemption during comment submission is refused

- **WHEN** a Xiaohongshu comment submission has opened its commit window and a higher-priority task requests the lease
- **THEN** the coordinator refuses preemption and returns a busy verdict with the remaining budget
- **AND** it does not abort the in-flight submission and does not inject a cancellation safe point inside the window

#### Scenario: Notification consumption is protected like the comment write

- **WHEN** a Xiaohongshu notification sweep is about to consume a category's unread state
- **THEN** the executing runtime opens a commit window before the consuming action and releases it at the terminal receipt
- **AND** the coordinator's window probe reports busy with remaining budget throughout that interval

#### Scenario: No window means no write

- **WHEN** an irreversible Xiaohongshu write requests a commit window and the request is denied or the facility is unavailable
- **THEN** the write is not dispatched and the receipt reports a truthful not-started outcome
- **AND** the runtime does not proceed on the grounds that the write would probably not be interrupted

#### Scenario: Window is released at the terminal outcome

- **WHEN** an irreversible Xiaohongshu write reaches success, failure, or budget expiry
- **THEN** its commit window is released
- **AND** a later preemption request is answered on the coordinator's ordinary terms rather than by a leaked permanently-busy window

## MODIFIED Requirements

### Requirement: 通知巡视按窗口保护，其不可逆消费段不可被抢占

通知巡视点开分类栏目的那一刻，平台未读即被消费，且该未读**只在从无到有翻转时上报一次**、两端都无副本、无可回退游标。因此点分类栏目到未读回传之间 SHALL 被视为一个**不可逆提交窗口**：在该窗口内协调器 MUST 拒绝抢占（回「窗口占用中 + 剩余预算」），MUST NOT 在窗口内注入安全取消点。

窗口内允许抢占 = 一整波未读永久丢失（既没写进任何账本，也无法再次上报）。这与发布/评论的提交窗口保护同构，但巡视的窗口**恰恰缺席安全取消点**：安全取消点的定义（操作到第一次真正改写页面之前皆可中止）在此不成立，因为「点分类栏目」这一下本身就是不可逆的平台副作用。

**本保护 MUST 由实际执行巡视的运行时开窗，并随执行运行时更换而迁移。** 页面动作的执行体从一个运行时搬到另一个（例如页面智能迁入已编码的页面引擎）MUST NOT 使该窗口失效：搬家后仍必须有人在消费动作的正前方开窗、在未读回传的终态关窗。协调器的窗口探针在该段内 MUST 报「忙 + 剩余预算」；探针在真实不可逆消费进行中报「无窗口」即视为违反本条，无论是哪个运行时在执行。

#### Scenario: 点开分类栏目后抢占被拒
- **WHEN** 通知巡视已点开某分类栏目、未读尚未回传，此时更高档位任务申请租约
- **THEN** 协调器 MUST 拒绝抢占并回「窗口占用中、剩余 ≤20s」，MUST NOT 在该窗口内中止巡视命令（否则已消费未上报的未读永久丢失）

#### Scenario: 执行运行时更换后窗口仍在
- **WHEN** 通知巡视的页面动作由新的执行运行时承担，一次分类消费正在进行
- **THEN** 协调器的窗口探针 MUST 报「忙 + 剩余预算」，抢占 MUST 被拒
- **AND** MUST NOT 因为「窗口参数没有传到新执行体」而退化成无窗口的可抢占段
