# browser-cold-standby Specification

## Purpose
TBD - created by archiving change browser-cold-standby-next-action. Update Purpose after archive.
## Requirements
### Requirement: Edge 本地开关默认开启并可禁用

Edge SHALL include a browser cold-standby switch that defaults to enabled. The local switch MUST be able to disable cold standby even when cloud publishes an eligible hint, and disabling it MUST prevent browser close/restart automation caused by cold-standby hints.

#### Scenario: 默认开启
- **WHEN** the desktop app starts with no cold-standby override
- **THEN** the local cold-standby setting is enabled

#### Scenario: 本地禁用覆盖云端提示
- **WHEN** the local setting or environment override disables browser cold standby
- **AND** cloud publishes `browserStandby.eligible=true`
- **THEN** edge records/skips the hint but MUST NOT close the browser for cold standby

### Requirement: Edge 仅在安全状态下关闭并按预测时间恢复

Edge SHALL treat `browserStandby` as advisory and perform local safety checks before closing the browser. It MAY close the browser only when the hint is eligible, the local switch is enabled, the wait exceeds the local threshold, the session is running/resting without pending pause/close/remove/auth/blocker state, and there is no known in-flight operation that requires the browser. Edge SHALL keep the cloud engine connection intact where the core protocol supports it, and SHALL restart/resume the environment at `wakeAt - warmupMs` or earlier if manually requested.

#### Scenario: 安全长等待关闭浏览器并提前唤醒
- **WHEN** edge receives an eligible long-wait hint while the environment is safely idle or resting
- **THEN** edge closes the browser, records cold-standby status, and schedules wake before `wakeAt` by the configured warmup buffer

#### Scenario: 手工操作取消自动恢复
- **WHEN** an operator manually pauses, closes, removes, or restarts an environment while a cold-standby timer exists
- **THEN** edge cancels the cold-standby timer and does not perform the old automatic wake action

#### Scenario: 不安全状态拒绝关闭
- **WHEN** edge receives an eligible hint but the environment is closing, paused, occupied, auth-gated, blocked, removed, or has an unsafe in-flight operation
- **THEN** edge MUST NOT close the browser for cold standby and SHOULD expose a skipped reason for diagnostics

### Requirement: 协议兼容现有 ui.snapshot

The `browserStandby` payload SHALL be optional and backward compatible on `ui.snapshot`. Existing edge builds that ignore unknown fields MUST continue to process other snapshot fields, and new edge builds MUST sanitize the payload before forwarding it as structured UI events.

#### Scenario: 旧字段不受影响
- **WHEN** a `ui.snapshot` contains `browserStandby` together with existing fields such as presence and daily usage
- **THEN** daily usage, presence, and other existing UI behavior continue to work unchanged

### Requirement: 云端发布浏览器冷待机提示（判据＝解除阻塞是否需要浏览器）

Cloud SHALL publish an optional `browserStandby` object on the existing `ui.snapshot` stream whenever it can determine that automated browser work is blocked by a wait that **does not require the browser to stay open in order to be resolved**. The payload MUST include whether the feature is enabled, whether the current wait is eligible, a machine-readable reason, `waitMs`, `wakeAt`, `generatedAt`, `source`, `minWaitMs`, and `warmupMs`.

**准入判据 SHALL 是「解除这个阻塞需不需要浏览器」，MUST NOT 是「有没有确定的恢复时刻」。** 前一版判据（无确定恢复时刻即不让位）把**冻结账号**——等待最长、可能永远不再干活的那一类——恰好排除在让位之外，使最不该占着浏览器的账号占得最牢。

- **需要浏览器才能解除的阻塞 MUST NOT 产出可待机提示**：验证码、登录、运维在浏览器里手动介入、未知的调度器状态、环境被他处占用。这些情形 MUST 保持既有的诚实告警 / 在线状态行为。

  **这一半 MUST 有真实输入，MUST NOT 只写在规范里。** 判据是「解除阻塞需不需要浏览器」，若系统只接了「不需要」那一半的证据、而「需要」那一半无人提供，判据就只剩半边，所有阻塞都会被当成「不需要浏览器」。**「需要浏览器」的事实 SHALL 由云端权威持有**（当前来源：该边缘是否正处于验证码暂停态），**MUST NOT 依赖边缘自报的浮层标志**——那个标志会被「浏览循环结束」等无关事件清掉。该闸 SHALL 压在**所有**停工来源之前一票否决：验证码期间，账号同样可能排期外 / 时长满 / 配额耗尽，若只在某一个来源分支上补闸，其余来源仍会让位。
- **不需要浏览器即可解除的等待 SHALL 产出可待机提示**（等待时长 ≥ 门槛时 `eligible=true`），覆盖**全部**使账号停工的来源，而不只是风控配额：
  1. 风控配额窗口未释放（`source='risk'`，既有行为）
  2. 周历排期关闭 / 活跃时段窗口外（`source='session'`）
  3. 每日续场场数或累计分钟已满（`source='session'`）
  4. 风控状态 `restricted` / `frozen`（`source='risk'`，无固定恢复时刻，见下条 requirement）

**待机门槛 SHALL 默认 5 分钟**，且云端与边缘两端的默认值 MUST 一致。

#### Scenario: 排期外停工 SHALL 让出槽位
- **WHEN** 某账号因周历排期关闭或活跃时段窗口外而不再自动续场，距下一个可活跃时刻超过门槛
- **THEN** 云端产出 `browserStandby.eligible=true`、`source='session'`、`wakeAt` 等于下一个可活跃时刻，边缘据此关闭浏览器让出槽位

#### Scenario: 每日时长跑满 SHALL 让出槽位
- **WHEN** 某账号当日续场场数或累计在线分钟已达上限，距下一个本地日界超过门槛
- **THEN** 云端产出 `browserStandby.eligible=true`、`source='session'`、`wakeAt` 等于下一个本地日界

#### Scenario: 冻结账号 SHALL 让出槽位而非攥住
- **WHEN** 某账号风控状态为 `frozen`（或 `restricted` 致其不再续场），且解除该状态不需要浏览器
- **THEN** 云端产出 `browserStandby.eligible=true`，MUST NOT 因「没有确定的恢复时刻」而回退成 `eligible=false, waitMs=0`

#### Scenario: 需要浏览器才能解除的阻塞 MUST NOT 让位
- **WHEN** 账号需要过验证码、需要重新登录、或需要运维在浏览器里手动介入
- **THEN** 云端 MUST NOT 置 `eligible=true`，浏览器保持打开，既有的诚实告警行为不变

#### Scenario: 验证码把账号打成受限时 MUST NOT 让位
- **WHEN** 边缘上报验证码 → 风控信号把账号迁到 `restricted` → 续场闸据此判停工
- **AND** 该边缘正处于验证码暂停态
- **THEN** 云端 MUST 置 `eligible=false`、`reason='hard_blocker'`——**绝不能关掉运维正要去解验证码的那个浏览器**。
  注：`ui.snapshot` 有意豁免验证码暂停闸（它是界面数据、不是页面命令），故提示**会**送达该边缘；边缘侧的浮层标志会被「浏览循环结束」清掉，**MUST NOT 被当作这条的防线**。

#### Scenario: 验证码期间任何停工来源都 MUST NOT 让位
- **WHEN** 边缘正处于验证码暂停态，且该账号同时满足某个让位来源（排期外 / 每日上限已满 / 配额耗尽 / 周历关闭）
- **THEN** 云端 MUST 一律置 `eligible=false`——该闸 SHALL 压在所有来源之前，MUST NOT 只补在受限那一支

#### Scenario: 验证码解除后恢复正常让位
- **WHEN** 验证码已解除，边缘不再处于暂停态，而账号仍因某个来源停工
- **THEN** 云端按正常判据产出可待机提示——该闸 MUST NOT 永久禁用让位

#### Scenario: 短等待不触发待机
- **WHEN** 距下一次可执行动作的预计等待时间低于门槛（默认 5 分钟）
- **THEN** 云端不产出可待机提示，或产出 `eligible=false` 且 `reason='short_wait'`

### Requirement: 无固定恢复时刻的阻塞 SHALL 让位，且 MUST 有一条不依赖「恢复时刻」的唤醒路径

对**永远算不出恢复时刻**的停工来源，云端 SHALL 仍然让边缘关闭浏览器让出槽位；但让位 MUST 与一条唤醒路径成对出现——只按门槛关掉、却没有任何路径能把它叫醒，MUST NOT 视为本 requirement 的实现。

这类来源当前有二：风控 `frozen` / `restricted`（其唯一出口是运营手动改状态——状态机里虽有恢复常量与恢复函数，但**无人调用、也从不发出恢复信号**），以及周历整周全关（运营显式停号）。它们**最该让出槽位**（账号可能永远不再干活），却恰恰是旧判据（「无确定恢复时刻即不让位」）排除掉的那一类。

只关不唤醒，是拿一个 700MB 的资源浪费，换一个更糟的静默故障（账号解冻后永远醒不过来）——「自愈不自残」红线在待机链路上的具体形态。

两条唤醒路径 SHALL 同时成立：

1. **主路径 —— 待机提示的周期性重发**：`ui.snapshot` 已有一条约 60 秒的周期链，且冷待机期间核心进程与云端连接不断、该链继续。账号一旦恢复可工作，下一跳提示即 `eligible=false`，边缘据此唤醒。**因此本能力 MUST NOT 新建「状态变化即推送」的通道**（既有周期链已覆盖，最坏延迟约 60 秒）。
2. **兜底路径 —— 回访时刻**：这类提示的 `wakeAt` SHALL 被赋予一个**回访时刻**（默认 6 小时后）。其语义 SHALL 是「**多久之后回来再问一次**」，**MUST NOT 被解读为「那时一定能恢复」**——`wakeAt` 在此表达的是边缘确实会在那时醒来这一事实，而非对恢复的承诺。**MUST NOT 用「最早可恢复时刻」之类推算值伪造 `wakeAt`**（那是假承诺：没有任何代码会在那时真的恢复它）。周期链健在时，每跳都会把回访时刻顺延，回访因而**只在周期链断掉时才真正触发**——它是一道死人开关，不是常规路径。

**周期链 MUST NOT 因「今日用量为空」而断开**：重排下一跳的条件 SHALL 是「推送成功 **且**（今日用量 **或** 待机提示 任一存在）」。旧条件只看今日用量——待机提示还在、链却已死，唤醒路径便悬空。

采用「回访时刻」而非新增协议字段，使本能力 **零协议改动**（`UiBrowserStandbyPayload` 字段不变），避免触碰两份 `protocol.ts` 这一热点文件。

#### Scenario: 解冻后账号自动醒来
- **WHEN** 某冻结账号已因让位关闭浏览器，随后运营把其风控状态改回可工作态
- **THEN** 下一跳周期提示即 `eligible=false`（最坏约 60 秒），边缘据此唤醒浏览器、重新排入槽位队列

#### Scenario: 周期链断掉时回访兜底
- **WHEN** 某冻结账号已让位待机，其待机提示的周期链因故中断（推送失败、边缘短暂断线等）
- **THEN** 边缘在回访时刻自行醒来并重新评估；若已恢复则复工，若仍被阻塞则重新进入待机——**MUST NOT 永久睡死**

#### Scenario: 今日用量为空不得使周期链断开
- **WHEN** 某账号的今日用量数据缺失，但待机提示仍在产出
- **THEN** 周期链 MUST 继续重排下一跳，唤醒路径保持有效

#### Scenario: 无任何唤醒路径时 MUST NOT 让位
- **WHEN** 某停工来源既算不出恢复时刻、也无法赋予回访时刻、周期链也不覆盖它
- **THEN** 云端 MUST NOT 产出可待机提示（宁可让它占着浏览器，也绝不把账号做成再也醒不过来的砖）

### Requirement: 最短持有时长 SHALL 防止浏览器频繁开关

边缘在唤醒浏览器后 SHALL 至少保持其开启一段**最短持有时长**（默认 3 分钟）才允许再次进入冷待机，即使期间收到了 `eligible=true` 的待机提示。

一次待机的净收益 = 让出时长 − 热身时长（默认 90s）；一次唤醒的成本 ≈ 40s 的**全局串行启动队列**占用（唤醒为原地重开浏览器、不重启核心进程，见 `browser-slot-scheduling`）。盈亏平衡点约在 2 分 10 秒，故 5 分钟门槛留有约 2.3 倍余量。最短持有时长是把「不频繁开关」从**推断**变成**保证**的那道机械闸。

#### Scenario: 刚醒来的环境不得立刻再次待机
- **WHEN** 某环境刚被唤醒不足最短持有时长，云端又推来一条 `eligible=true` 的待机提示
- **THEN** 边缘 MUST NOT 进入待机，SHALL 记录一个可诊断的 skipped 原因（如 `min_hold`），并在持有时长满足后按最新提示重新判定

#### Scenario: 小时级等待不受最短持有时长影响
- **WHEN** 某账号因排期外 / 时长满而停工（等待为小时级），且已开启超过最短持有时长
- **THEN** 边缘正常进入待机，一天最多经历一次关闭与一次唤醒

### Requirement: 待机门槛的默认值 SHALL 两端一致

待机门槛在云端与边缘各持有一份默认值，而边缘取的是两者的**较大值**（`Math.max(本地门槛, 云端提示里的门槛)`）。因此调整门槛 MUST 两端同改；**只改一端 MUST NOT 视为完成**——只改云端时，边缘仍会按自己那份旧门槛把提示拦下来，改动完全不生效且无任何报错。

两端的默认门槛 SHALL 为 5 分钟。任一端的门槛 SHALL 可经设置项 / 环境变量覆盖，用于按机器调优或秒级回滚。

#### Scenario: 只改一端不生效
- **WHEN** 仅把云端默认门槛下调、边缘仍持旧值
- **THEN** 边缘取较大值（旧门槛）判定，低于旧门槛的等待一律不待机——此为已知陷阱，回归测试 MUST 覆盖两端默认值一致

#### Scenario: 门槛可按机器覆盖
- **WHEN** 运维在某台机器上经环境变量调整待机门槛
- **THEN** 该机器按覆盖值判定，无需改代码或重新发版

### Requirement: 任务安全收敛后 SHALL 立即重判最新待机提示

当 Edge 任务租约释放、排队任务为空、在途发布写者已经收敛且普通浏览恢复到安全边界后，核心 SHALL 通知 Electron 外壳重新应用该环境最新的 `browserStandby` 提示。该通知只触发既有待机判定，MUST NOT 直接关闭浏览器或绕过本地开关、最短持有时长、认证/验证码/暂停状态、任务租约和 in-flight 操作安全闸。

#### Scenario: 发布结束且长期无工作时及时归还槽位
- **WHEN** 一次发布任务完成，环境没有下一条租约，最新待机提示仍为 eligible 且所有本地安全闸通过
- **THEN** Edge 无需等待下一次 Cloud 快照即可进入既有冷待机流程，关闭浏览器归还槽位并触发 FIFO 下一环境

#### Scenario: 发布结束但仍有工作时不强制关闭
- **WHEN** 一次发布任务完成，但最新提示不存在、不再 eligible，或环境仍有浏览/点赞工作、下一条租约、验证码/认证阻塞
- **THEN** 重判只产生 no-op 或 skipped，浏览器保持开启，MUST NOT 因“发布结束”被强制驱逐

#### Scenario: 新任务竞态由既有安全闸拦截
- **WHEN** 核心发出安全空闲提示后、Electron 请求待机前又有新任务取得或排队租约
- **THEN** 核心的任务租约安全闸拒绝进入待机，MUST NOT 从新任务底下关闭浏览器

### Requirement: 环境 SHALL 可从浏览器缺席态出生并复用冷待机唤醒

当环境已取得可信控制面引导但没有浏览器槽位时，Edge SHALL 可直接初始化为 cold-standby/browser-absent 状态。该路径 MUST NOT 启动 AdsPower、附着 CDP、启动浏览循环或平台 watcher；其后取得槽位时 SHALL 复用既有 FIFO wake 路径。

#### Scenario: 首次启动无槽位不打开浏览器
- **WHEN** 环境首次启动时浏览器并发已满且控制面引导成功
- **THEN** 核心进入 standby 并连接 Cloud，而 AdsPower browser 保持关闭
- **AND** 浏览器槽位计数不增加

#### Scenario: 队头取得槽位后完成唤醒
- **WHEN** 一个运行环境进入冷待机并释放槽位
- **THEN** 等待队头的 browser-absent 环境经串行启动队列打开浏览器、重附着 CDP并复核身份
- **AND** 无需操作员再次点击启动

#### Scenario: 唤醒失败仍保持可恢复
- **WHEN** AdsPower 启动、CDP 附着、身份复核或 Cloud 重连任一步失败
- **THEN** Edge 归还浏览器槽位、保持控制面可诊断且允许后续再次唤醒
- **AND** MUST NOT 把环境永久卡成运行中或已暂停

