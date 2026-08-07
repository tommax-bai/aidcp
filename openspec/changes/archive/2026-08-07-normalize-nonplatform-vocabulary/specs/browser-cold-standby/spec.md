## RENAMED Requirements

- FROM: `### Requirement: 协议兼容现有 ui.snapshot`
- TO: `### Requirement: 协议兼容现有 ui.push_snapshot`

## MODIFIED Requirements

### Requirement: 云端发布浏览器冷待机提示（判据＝解除阻塞是否需要浏览器）

Cloud SHALL publish an optional `browserStandby` object on the existing
`ui.push_snapshot` stream whenever it can determine that automated browser work is
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
  正要去解验证码的那个浏览器**。注：`ui.push_snapshot` 有意豁免验证码暂停闸（它是界面数据、
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

1. **主路径 —— 待机提示的周期性重发**：`ui.push_snapshot` 已有一条约 60 秒的周期链，且冷待机期间核心进程与云端连接不断、该链继续。账号一旦恢复可工作，下一跳提示即 `eligible=false`，边缘据此唤醒。**因此本能力 MUST NOT 新建「状态变化即推送」的通道**（既有周期链已覆盖，最坏延迟约 60 秒）。
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

### Requirement: 受限账号恢复后经既有唤醒路径归队

受限账号冷待机期间,恢复 SHALL 复用既有唤醒路径,MUST NOT 新增边缘侧机制:周期链健在时,扫描器把状态翻回 `warned` 后的下一跳提示不再 eligible,边缘据此唤醒;周期链断掉时按提示 `wakeAt`(= 恢复时刻)兜底唤醒。本 change 对 `ui.push_snapshot` 的待机载荷 MUST NOT 新增或删除字段。

#### Scenario: 状态翻转经周期链唤醒

- **WHEN** 冷待机中的受限账号被扫描器恢复为 `warned`
- **THEN** 下一跳周期链提示不再 eligible,边缘唤醒浏览器并恢复浏览闭环

### Requirement: 协议兼容现有 ui.push_snapshot

The `browserStandby` payload SHALL be optional and backward compatible on `ui.push_snapshot`. Existing edge builds that ignore unknown fields MUST continue to process other snapshot fields, and new edge builds MUST sanitize the payload before forwarding it as structured UI events.

#### Scenario: 旧字段不受影响
- **WHEN** a `ui.push_snapshot` contains `browserStandby` together with existing fields such as presence and daily usage
- **THEN** daily usage, presence, and other existing UI behavior continue to work unchanged
