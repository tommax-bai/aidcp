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

Edge SHALL treat `browserStandby` as advisory and perform local safety checks
before closing the browser. It MAY close the browser only when the hint is
valid and eligible, the visible local switch is enabled, the current remaining
wait meets the Cloud-advertised `minWaitMs`, and every local safety check
passes. Edge SHALL keep the cloud engine connection intact where the core
protocol supports it, and SHALL restart/resume the environment at
`wakeAt - warmupMs` or earlier if manually requested.

The local safety checks SHALL be evaluated **only** against facts that are
verifiable at decision time — the core child process is alive, the cloud engine
link is connected, the automation intent is neither paused nor stopped, and
there is no in-flight operation that requires the browser.

Every input to the admission decision SHALL have a demonstrable live source on
**every supported platform**, and that source SHALL be pinned by a regression
assertion. Edge MUST NOT gate admission on a lifecycle label whose only writer
has been retired on the platform in question: such a label freezes at whatever
value it was last given, and a stale value there silently converts a
recoverable wait into a permanently held browser slot with no diagnostic trace.
In particular, the browse-session lifecycle label — whose only writers are
log-phrase matches emitted by the retired page-automation path — MUST NOT be an
admission condition.

Having a live writer is a **necessary but not sufficient** condition for
admission input. The browse-session lifecycle label SHALL remain excluded from
the admission decision **even after it is rewired to a live structured source**,
and re-adding it SHALL require amending this requirement rather than citing the
restored writer. The governing reason is not whose writer is alive: that label
describes the target's **posture** (whether a browse round happens to be running
right now), not the target's **identity** (which environment and account would
be acted upon). Per the stop-or-continue criterion, a posture condition MUST NOT
by itself be grounds for refusing to act; only an identity condition may be.

#### Scenario: 安全长等待关闭浏览器并提前唤醒
- **WHEN** edge receives an eligible long-wait hint while the environment is
  safely idle or resting
- **THEN** edge closes the browser, records cold-standby status, and schedules
  wake before `wakeAt` by the configured warmup buffer

#### Scenario: 推断出来的生命周期标签陈旧时仍然让位
- **WHEN** edge receives an eligible long-wait hint while the core process is
  alive, the cloud engine link is connected, and automation is neither paused
  nor stopped, but a log-derived lifecycle label still carries a stale value
  such as `idle`
- **THEN** edge closes the browser for cold standby anyway, because that label
  is not an admission condition

#### Scenario: 会话轴接上活写入方之后仍不得进入准入闸
- **WHEN** the browse-session lifecycle label is rewired to a live structured
  session source that is written on every supported platform, and that label
  reports no browse round in progress while an eligible long-wait hint arrives
- **THEN** admission SHALL be decided without consulting that label, and edge
  SHALL close the browser for cold standby exactly as it would have before the
  rewiring
- **AND** a structural assertion SHALL fail if that label reappears among the
  admission inputs

#### Scenario: 手工操作取消自动恢复
- **WHEN** an operator manually pauses, closes, removes, or restarts an
  environment while a cold-standby timer exists
- **THEN** edge cancels the cold-standby timer and does not perform the old
  automatic wake action

#### Scenario: 不安全状态拒绝关闭
- **WHEN** edge receives an eligible hint but the environment is closing,
  paused, occupied, auth-gated, blocked, removed, disconnected from Cloud, or
  has an unsafe in-flight operation
- **THEN** edge MUST NOT close the browser for cold standby and MUST expose a
  named skipped reason for diagnostics

### Requirement: 协议兼容现有 ui.snapshot

The `browserStandby` payload SHALL be optional and backward compatible on `ui.snapshot`. Existing edge builds that ignore unknown fields MUST continue to process other snapshot fields, and new edge builds MUST sanitize the payload before forwarding it as structured UI events.

#### Scenario: 旧字段不受影响
- **WHEN** a `ui.snapshot` contains `browserStandby` together with existing fields such as presence and daily usage
- **THEN** daily usage, presence, and other existing UI behavior continue to work unchanged

### Requirement: 云端发布浏览器冷待机提示（判据＝解除阻塞是否需要浏览器）

Cloud SHALL publish an optional `browserStandby` object on the existing
`ui.snapshot` stream whenever it can determine that automated browser work is
blocked by a wait that **does not require the browser to stay open in order to
be resolved**. The payload MUST include whether the feature is enabled, whether
the current wait is eligible, a machine-readable reason, `waitMs`, `wakeAt`,
`generatedAt`, `source`, `minWaitMs`, and `warmupMs`.

**准入判据 SHALL 是「解除这个阻塞需不需要浏览器」，MUST NOT 是「有没有确定的恢复时刻」。**
前一版判据（无确定恢复时刻即不让位）把**冻结账号**——等待最长、可能永远不再干活的那一类——
恰好排除在让位之外，使最不该占着浏览器的账号占得最牢。

- **需要浏览器才能解除的阻塞 MUST NOT 产出可待机提示**：验证码、登录、运维在浏览器里手动介入、
  未知的调度器状态、环境被他处占用。这些情形 MUST 保持既有的诚实告警 / 在线状态行为。

  **这一半 MUST 有真实输入，MUST NOT 只写在规范里。** 判据是「解除阻塞需不需要浏览器」，
  若系统只接了「不需要」那一半的证据、而「需要」那一半无人提供，判据就只剩半边，所有阻塞
  都会被当成「不需要浏览器」。**「需要浏览器」的事实 SHALL 由云端权威持有**（当前来源：
  该边缘是否正处于验证码暂停态），**MUST NOT 依赖边缘自报的浮层标志**——那个标志会被
  「浏览循环结束」等无关事件清掉。该闸 SHALL 压在**所有**停工来源之前一票否决：验证码期间，
  账号同样可能排期外 / 时长满 / 配额耗尽，若只在某一个来源分支上补闸，其余来源仍会让位。
- **不需要浏览器即可解除的等待 SHALL 产出可待机提示**（等待时长 ≥ 门槛时
  `eligible=true`），覆盖**全部**使账号停工的来源，而不只是风控配额：
  1. 风控配额窗口未释放（`source='risk'`，既有行为）
  2. 周历排期关闭 / 活跃时段窗口外（`source='session'`）
  3. 每日续场场数或累计分钟已满（`source='session'`）
  4. 风控状态 `restricted` / `frozen`（`source='risk'`，无固定恢复时刻，见下条 requirement）

**待机门槛 SHALL 由 Cloud 单一持有且默认 5 分钟。** Cloud MUST 将当前门槛写入
`browserStandby.minWaitMs`，Edge 不得持有另一份策略门槛。

#### Scenario: 排期外停工 SHALL 让出槽位
- **WHEN** 某账号因周历排期关闭或活跃时段窗口外而不再自动续场，距下一个可活跃时刻超过门槛
- **THEN** 云端产出 `browserStandby.eligible=true`、`source='session'`、`wakeAt`
  等于下一个可活跃时刻，边缘据此关闭浏览器让出槽位

#### Scenario: 每日时长跑满 SHALL 让出槽位
- **WHEN** 某账号当日续场场数或累计在线分钟已达上限，距下一个本地日界超过门槛
- **THEN** 云端产出 `browserStandby.eligible=true`、`source='session'`、`wakeAt`
  等于下一个本地日界

#### Scenario: 冻结账号 SHALL 让出槽位而非攥住
- **WHEN** 某账号风控状态为 `frozen`（或 `restricted` 致其不再续场），且解除该状态不需要浏览器
- **THEN** 云端产出 `browserStandby.eligible=true`，MUST NOT 因「没有确定的恢复时刻」
  而回退成 `eligible=false, waitMs=0`

#### Scenario: 需要浏览器才能解除的阻塞 MUST NOT 让位
- **WHEN** 账号需要过验证码、需要重新登录、或需要运维在浏览器里手动介入
- **THEN** 云端 MUST NOT 置 `eligible=true`，浏览器保持打开，既有的诚实告警行为不变

#### Scenario: 验证码把账号打成受限时 MUST NOT 让位
- **WHEN** 边缘上报验证码 → 风控信号把账号迁到 `restricted` → 续场闸据此判停工
- **AND** 该边缘正处于验证码暂停态
- **THEN** 云端 MUST 置 `eligible=false`、`reason='hard_blocker'`——**绝不能关掉运维
  正要去解验证码的那个浏览器**。注：`ui.snapshot` 有意豁免验证码暂停闸（它是界面数据、
  不是页面命令），故提示**会**送达该边缘；边缘侧的浮层标志会被「浏览循环结束」清掉，
  **MUST NOT 被当作这条的防线**。

#### Scenario: 验证码期间任何停工来源都 MUST NOT 让位
- **WHEN** 边缘正处于验证码暂停态，且该账号同时满足某个让位来源（排期外 / 每日上限已满 /
  配额耗尽 / 周历关闭）
- **THEN** 云端 MUST 一律置 `eligible=false`——该闸 SHALL 压在所有来源之前，
  MUST NOT 只补在受限那一支

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

### Requirement: Cloud SHALL be the single standby wait-threshold authority

Cloud SHALL be the sole policy authority for the browser cold-standby wait
threshold. Edge MUST use the validated `browserStandby.minWaitMs` from the
current Cloud hint when rechecking `wakeAt - now`; it MUST NOT combine that
value with an Edge default, persisted setting, or Edge environment override.
The visible local enable switch and all local execution safety gates remain
authoritative vetoes.

#### Scenario: Legacy Edge threshold does not override Cloud
- **WHEN** an upgraded client loads a legacy
  `browserColdStandbyMinWaitMs=1200000` value and receives a valid Cloud hint
  with `minWaitMs=300000`
- **THEN** Edge ignores the legacy value and evaluates the current remaining
  wait against 300000 milliseconds

#### Scenario: Delayed hint is rechecked against the Cloud threshold
- **WHEN** Edge receives or re-applies a valid eligible hint whose current
  `wakeAt - now` is shorter than that hint's `minWaitMs`
- **THEN** Edge rejects standby with `short_wait` even if the hint was eligible
  when Cloud generated it

#### Scenario: Missing Cloud threshold does not use a local fallback
- **WHEN** a standby hint is missing, malformed, or lacks a valid `minWaitMs`
- **THEN** Edge MUST revoke any cached hint and pending post-hold recheck for
  an awake browser and MUST NOT enter a new cold-standby cycle from that hint

#### Scenario: Invalid non-positive Cloud threshold is rejected
- **WHEN** a standby hint advertises `minWaitMs` below Cloud's supported
  positive threshold
- **THEN** Edge treats the hint as malformed and keeps an awake browser open

#### Scenario: Existing standby keeps its deterministic wake
- **WHEN** a browser is already in cold standby from a previously valid hint
  and a later snapshot omits or malforms `browserStandby`
- **THEN** Edge retains that cycle's existing wake timer, but the stale hint
  MUST NOT start another standby cycle after the browser wakes

#### Scenario: Legacy threshold cannot be re-persisted
- **WHEN** an upgraded client loads or is asked to save a settings object that
  contains `browserColdStandbyMinWaitMs`
- **THEN** the value has no runtime effect, is omitted from settings readback,
  and is omitted from the next successful settings write

### Requirement: 拒绝让位 MUST 留痕，且连续拒绝 MUST 与单次拒绝可分辨

每一次拒绝进入冷待机 SHALL 在该环境的待机状态上留下**具名原因**，并 SHALL 同时记录
**连续拒绝次数**与**首次连续拒绝时刻**；该原因与计数 SHALL 在开发者详情中可读。Edge
SHALL 另按环境记录一行日志，使拒绝在事后可回溯。

留痕 MUST 覆盖全部拒绝理由，MUST NOT 只覆盖其中一部分。单次拒绝是正常的（例如刚醒来
不足最短持有时长），而**连续拒绝**意味着该环境正在无限期占用一个浏览器槽位；二者若在
呈现与日志上长得一样，运营就无法把后者识别出来。

一次成功进入冷待机、或提示转为不再 eligible，SHALL 重置连续拒绝计数。

#### Scenario: 单次拒绝留下具名原因
- **WHEN** edge evaluates an eligible hint and any local safety check fails
- **THEN** edge records the named refusal reason on that environment's standby
  status and writes one per-environment log line, without closing the browser

#### Scenario: 连续拒绝可被识别
- **WHEN** edge refuses the same environment on consecutive hints
- **THEN** the recorded state carries a consecutive-refusal count and the
  timestamp of the first refusal in that streak, so an environment that has
  been holding a browser slot for many consecutive hints is distinguishable
  from one that refused once

#### Scenario: 让位成功后计数复位
- **WHEN** an environment enters cold standby, or a subsequent hint reports the
  environment as no longer eligible
- **THEN** the consecutive-refusal count and streak start time are reset

### Requirement: 进入冷待机失败 MUST NOT 把健康环境打成暂停态

核心侧拒绝或未能完成进入冷待机时，Edge SHALL 留在**浏览器仍然开启**的运行态，记录一条
具名的、**可重试**的失败，并 SHALL 在后续提示到达时重新判定。Edge MUST NOT 因此把该
环境写成暂停态。

「此刻不能待机」是非结构性的——同一步在下一次提示上重来完全可能成功。把它落成暂停态
会让一个健康环境永久占住浏览器槽位，并被排除出等槽位队列：这比不尝试待机更坏，而本次
改动正是要让待机尝试变得频繁得多。

#### Scenario: 核心拒绝进入待机
- **WHEN** the shell asks the core to enter cold standby and the core does not
  confirm
- **THEN** the environment stays in its running state with the browser open, a
  named retryable failure is recorded, and the next eligible hint is evaluated
  again

### Requirement: 冷待机期间被拒绝的浏览器命令 MUST NOT 静默丢弃

浏览器已因冷待机关闭时收到需要浏览器的命令，Edge SHALL 以具名原因如实拒绝并留痕，
MUST NOT 静默丢弃。该拒绝 SHALL 与「已执行」在本地呈现上可分辨。

#### Scenario: 待机期间收到浏览器命令
- **WHEN** the browser is closed for cold standby and a command requiring the
  browser arrives
- **THEN** edge refuses it with a named reason and records that refusal, rather
  than dropping it without a trace

### Requirement: 让位判决 SHALL 向云端回执，且该回执 MUST NOT 进入准入

宿主层每一次冷待机准入判决 SHALL 向云端上报一条只读回执（内容与节流规则见能力
`host-standby-decision-telemetry`）。这是宿主层持有槽位决策权的**对价**：一个没人能质询的
本地决定，正是 2026-08-05 那次「连续 32 分钟拒绝让位、锁死一个浏览器槽位、界面与日志零痕迹」
故障的形状；补上的本地留痕只在有人坐在那台机器前时有用，而车队是跨机器的。

该回执 MUST NOT 反向影响准入：它 MUST NOT 成为准入判据的输入，云端 MUST NOT 因其内容
下发任何强制让位或禁止让位的指令。准入的输入集合 SHALL 不因本要求而增加任何一项。

上报失败、云端不可达或对端不支持该能力时，**准入 SHALL 完全不受影响**——
回执是观测，MUST NOT 成为让位的前置条件。否则一次云端抖动就会让整批环境停止让出槽位，
把一条观测通道变成新的可用性依赖。

#### Scenario: 上报不可达时让位照常发生
- **WHEN** 宿主层判定应当让位，但回执因云端不可达或对端不支持该能力而未能送出
- **THEN** 边缘 SHALL 照常关闭浏览器进入冷待机
- **AND** 准入结果 SHALL 与回执是否送达无关

#### Scenario: 准入输入集合不因回执而增加
- **WHEN** 回执能力启用后重新评估准入
- **THEN** 准入判据 SHALL 与启用前逐项相同
- **AND** 结构断言 SHALL 在回执相关状态出现于准入输入中时失败

### Requirement: 受限账号的待机提示携带真实恢复时刻

自动恢复接活后,`restricted` 属于**有固定恢复时刻**的阻塞。云端产出待机提示时:续场闸对 `restricted` 的裁决 SHALL 携带由恢复策略同源推导的恢复时刻;待机提示 SHALL 据此产出带真实等待时长的定时让位提示(等待 ≥ 让位阈值即 eligible),MUST NOT 再对 restricted 走「回访」语义,也 MUST NOT 因 `state:restricted` 不带 `quota:` 前缀而落进「硬阻塞不让位」兜底。`frozen` 与周历整周全关等仍无恢复时刻的阻塞 SHALL 维持既有回访语义。

#### Scenario: full_pause 受限产出定时让位

- **WHEN** 全局策略为 `full_pause`,账号 `restricted` 且距恢复时刻尚余大于让位阈值的等待
- **THEN** 待机提示 eligible=true、等待时长 = 恢复时刻 − 当前时刻,边缘据此关闭浏览器让出槽位

#### Scenario: browse_only 受限在会话结束后同样让位

- **WHEN** 全局策略为 `browse_only`,受限账号当前会话已结束、续场闸以 `risk_state` 拦停
- **THEN** 待机提示按续场闸携带的恢复时刻产出定时让位,而非回访

#### Scenario: 冻结维持回访

- **WHEN** 账号为 `frozen`
- **THEN** 待机提示维持既有回访语义(让位 + 无恢复承诺的回访时刻)

### Requirement: 受限让位不得越过「解除阻塞需要浏览器」一票否决

「正卡在验证码 / 阻断弹窗、解除需要该浏览器」的一票否决 SHALL 保持压在包括受限定时让位在内的所有提示来源之前。受限往往正由弹窗信号触发,MUST NOT 出现「信号升级为 restricted → 定时让位 → 关掉运维正要去解弹窗的浏览器」的路径;弹窗清除、验证码暂停解除后,后续周期链才可以产出受限的定时让位提示。

#### Scenario: 受限 + 验证码待解时不让位

- **WHEN** 账号因阻断弹窗升级为 `restricted`,该边缘的验证码暂停仍未解除
- **THEN** 待机提示为硬阻塞、不让位;弹窗清除后的下一跳才可能产出定时让位

### Requirement: 受限账号恢复后经既有唤醒路径归队

受限账号冷待机期间,恢复 SHALL 复用既有唤醒路径,MUST NOT 新增边缘侧机制:周期链健在时,扫描器把状态翻回 `warned` 后的下一跳提示不再 eligible,边缘据此唤醒;周期链断掉时按提示 `wakeAt`(= 恢复时刻)兜底唤醒。本 change 对 `ui.snapshot` 的待机载荷 MUST NOT 新增或删除字段。

#### Scenario: 状态翻转经周期链唤醒

- **WHEN** 冷待机中的受限账号被扫描器恢复为 `warned`
- **THEN** 下一跳周期链提示不再 eligible,边缘唤醒浏览器并恢复浏览闭环

