## ADDED Requirements

### Requirement: Blocking-state surveillance SHALL run on every Native browse platform

The edge's Native browse runtime MUST run a periodic blocking-state observation for **every** platform whose browse sessions it drives, not only for Facebook. Platform identity MAY select which classifier is applied, but it MUST NOT decide whether any observation runs at all: a supported browse platform without a running blocking observation is an unguarded session and MUST NOT be started as if it were guarded.

For Xiaohongshu the observation MUST at minimum distinguish a captcha/verification challenge state and a login-wall state from a non-blocking state, and it MUST act on them:

- Captcha state MUST fail closed immediately: the edge MUST stop ordinary browse locally and MUST send `risk.captcha_detected{kind:'captcha'}` carrying the edge id, the owning account id when known, and the observed location.
- Login-wall state MUST stop ordinary browse locally. The edge MUST NOT report a login wall as an account-level captcha incident, and MUST NOT report any browse command that was suppressed by it as successful.
- Returning to a non-blocking state MUST send exactly one paired `risk.captcha_cleared` when — and only when — a `risk.captcha_detected` was actually sent for that episode. A suppressed or never-reported episode MUST NOT produce an orphan `cleared`, and a reported episode MUST NOT be left with a `detected` that is never cleared.

While the edge is locally stopped for a blocking state, browse commands that arrive MUST receive a truthful not-started result; they MUST NOT be silently dropped and MUST NOT be answered as if the page action had happened.

This requirement MUST NOT add or remove protocol message types; the two `protocol.ts` copies keep the same `MessageType` enumeration and message count.

#### Scenario: Xiaohongshu captcha reaches the cloud

- **WHEN** a Xiaohongshu browse session's periodic observation classifies the current page as a captcha/verification challenge
- **THEN** the edge stops ordinary browse locally and sends one `risk.captcha_detected{kind:'captcha'}` with the edge id and observed location
- **AND** the cloud can migrate the owning account's risk state and offer remote assistance, exactly as it does for the Facebook path

#### Scenario: Self-healed Xiaohongshu block sends one paired clear

- **WHEN** a Xiaohongshu blocking state for which `risk.captcha_detected` was sent disappears and the page returns to a non-blocking state
- **THEN** the edge sends exactly one `risk.captcha_cleared` and resumes ordinary browse
- **AND** it does not send a second `detected` for the same episode

#### Scenario: Never-reported episode produces no orphan clear

- **WHEN** a blocking observation never resulted in a `risk.captcha_detected` and the page returns to a non-blocking state
- **THEN** the edge sends no `risk.captcha_cleared`
- **AND** the cloud sees no pause/resume disturbance for that edge

#### Scenario: Login wall is not reported as an account-level captcha incident

- **WHEN** a Xiaohongshu browse session observes a login wall
- **THEN** the edge stops ordinary browse locally and waits for login
- **AND** it does not send `risk.captcha_detected` for the login wall, and it does not report the suppressed browse commands as successful

#### Scenario: A supported browse platform is never left unobserved

- **WHEN** the Native browse runtime starts a session for a platform it declares as supporting browse
- **THEN** a periodic blocking-state observation is running for that session
- **AND** no platform is excluded from observation by a platform-identity guard placed ahead of the observation itself

### Requirement: Unavailable blocking classifications SHALL be declared absent, never simulated

The low-confidence `unknown` blocking bucket requires a real blocking-overlay classifier (shape/iframe/wording heuristics over a visible obstructing surface). Where no such classifier exists for a platform, the edge MUST treat that bucket as **declared absent** and MUST NOT synthesize it from an unrelated signal.

Specifically, a generic "the page type was not recognized" outcome MUST NOT be mapped to a blocking report. Those two facts are different: "I did not recognize this page" is not evidence of an obstructing surface, and mapping one to the other turns every page-recognition miss into an account risk downgrade.

Evidence text carried with a blocking report MUST come from the same page text that produced the classification, bounded in length; the edge MUST NOT fabricate evidence text, and MUST NOT loosen the classification thresholds in order to produce evidence.

When the low-confidence bucket is absent for a platform, the delayed-confirmation gate that governs it has nothing to gate; the immediate fail-closed handling of the captcha and login-wall classes MUST remain in force regardless.

#### Scenario: Unrecognized page type is not a blocking report

- **WHEN** a Xiaohongshu periodic observation returns a page whose type could not be recognized, with no captcha or login-wall classification
- **THEN** the edge sends no `risk.captcha_detected`
- **AND** the owning account's risk state is not migrated and the edge is not paused

#### Scenario: Absent bucket does not weaken the fail-closed classes

- **WHEN** a platform has no low-confidence blocking classifier
- **THEN** its captcha and login-wall classes are still handled immediately and fail closed
- **AND** the absence of the low-confidence bucket is recorded as a declared gap rather than covered by a substitute signal

#### Scenario: Evidence text is never fabricated

- **WHEN** a blocking report is sent but the classification produced no usable page text
- **THEN** the report omits evidence text rather than carrying invented or unrelated text
- **AND** the classification decision itself is unchanged by the absence of evidence text

### Requirement: High-risk Xiaohongshu actions SHALL re-check the blocking state immediately before dispatch

A cached blocking state read by the pause gate can be up to one observation tick stale, and the human-like pause between the gate and the actual click is exactly where a challenge tends to appear. Therefore every high-risk Xiaohongshu action — like, collect, follow, comment submission — MUST perform a fresh blocking-state probe **immediately before dispatching** the action, in the runtime that dispatches it.

When that fresh probe classifies the page as a captcha/verification challenge or as a login wall, the action MUST NOT be dispatched at all (zero page writes) and the receipt MUST carry a truthful blocked reason distinguishing the two, reusing the existing reason vocabulary rather than inventing new codes.

When the fresh probe itself fails to produce a verdict, the runtime MUST fail closed and skip the dispatch: missing a like is cheap, clicking into a risk wall is expensive.

A page whose **type** could not be recognized MUST NOT be treated as blocked by this gate: that outcome is not evidence of an obstructing surface (same reasoning as the declared-absent low-confidence bucket), and treating it as blocked would stop all interaction on picture-viewing, AI-search-result and detail-overlay pages.

#### Scenario: Captcha appearing inside the pre-click pause is not clicked through

- **WHEN** the pause gate has already let a Xiaohongshu like through, and a captcha appears during the pause before the click is dispatched
- **THEN** the pre-dispatch probe observes it, no click is dispatched, and the receipt reports the blocked-by-captcha reason
- **AND** the receipt does not claim the interaction happened

#### Scenario: A failed pre-dispatch probe is treated as blocked

- **WHEN** the pre-dispatch blocking probe for a high-risk Xiaohongshu action cannot produce a verdict
- **THEN** the action is not dispatched and the receipt reports a truthful not-started outcome
- **AND** the runtime does not proceed on the grounds that no block was observed

#### Scenario: An unrecognized page type does not block the action

- **WHEN** the pre-dispatch probe returns a page whose type was not recognized, with no captcha and no login-wall classification
- **THEN** the action proceeds on the coordinator's ordinary terms
- **AND** no blocking report is produced for that observation

### Requirement: A blocking-state pause SHALL keep its termination and takeover exits

While a Native browse session is locally paused for a blocking state, the wait MUST have three exits, and each MUST be observable in a regression test:

- a local stop request ends the wait;
- a session-termination command that has already arrived MUST bypass the pause and terminate the session — otherwise a standing login wall makes the session impossible to end from the cloud;
- an exclusive-task takeover signal MUST abort the waiting command by raising, so the command is voided with zero page side effects and yields immediately. Returning normally MUST NOT be used for this exit: the command would continue and keep acting against the blocking surface, and the takeover would keep waiting for a command that is waiting for a challenge only that takeover can clear — a closed-loop deadlock that stops the whole machine.

Commands suppressed by the pause MUST receive a truthful not-started result; the pause MUST NOT answer a termination command with that same suppressed result.

#### Scenario: Session termination is not blocked by a standing login wall

- **WHEN** a Xiaohongshu session is paused on a login wall that does not clear, and a session-termination command arrives
- **THEN** the termination bypasses the pause and the session ends
- **AND** it is not answered with a suppressed not-started result that leaves the session running

#### Scenario: Task takeover voids the waiting command instead of resuming it

- **WHEN** an exclusive-task takeover signal arrives while a command is waiting in the blocking pause
- **THEN** the waiting command is aborted with zero page side effects and the takeover proceeds without waiting for it
- **AND** the command does not continue to act on the page after the pause returns

#### Scenario: Suppressed browse command answers truthfully

- **WHEN** an ordinary browse command arrives while the session is paused for a blocking state and the pause does not clear within its wait
- **THEN** the command receives a truthful not-started result
- **AND** it is neither silently dropped nor reported as if the page action had happened

### Requirement: Blocking observation lifecycle SHALL follow executor connection health

The periodic blocking observation MUST be a managed observer with an explicit lifecycle, not a bare timer:

- When the browser executor connection reaches an unrecoverable terminal state, every periodic observation MUST be stopped. Otherwise the observers keep polling a dead connection and emit one probe-failure record per tick until the process exits.
- When the connection is restored, the observations MUST be restarted as a batch, and starting MUST be idempotent (already-running observers are unaffected; stopped ones resume cleanly).
- The observer MUST expose a liveness measure — how long since the last successful probe — so that "the probe has been failing" is externally distinguishable from "nothing is happening". Treating "cannot observe" as "nothing observed" is a sensing-layer false success and MUST NOT happen.
- The observation interval MUST be configurable/injectable rather than a hard-coded constant, and the probe-failure fallback policy (hold the previous state, or reset) MUST be an explicit choice that a test pins down.
- When a session is assembled while standby or paused, the fact that observation is **assembled but not started** MUST be recorded, so an operator can tell "not wired" from "wired but idle".

#### Scenario: Unrecoverable executor connection stops every observation

- **WHEN** the browser executor connection reaches its unrecoverable terminal state while a browse session is running
- **THEN** every periodic blocking observation for that session stops
- **AND** no observation keeps polling the dead connection or emitting per-tick probe-failure records

#### Scenario: Reconnection restarts the observations idempotently

- **WHEN** the executor connection is restored after having been stopped
- **THEN** the observations are restarted as a batch and resume producing classifications
- **AND** issuing the start again for an already-running observation changes nothing

#### Scenario: Persistent probe failure is distinguishable from a quiet page

- **WHEN** the blocking probe fails on every tick for an extended period
- **THEN** the liveness measure shows how long since the last successful probe, and the failure is visible to the layer above
- **AND** the state is not presented as "no blocking observed"

#### Scenario: Assembled but not started is recorded

- **WHEN** a session is assembled while automation is in standby or paused, so observation is wired but not running
- **THEN** that state is recorded as assembled-but-not-started
- **AND** it is not indistinguishable from a session with no observation wired at all

## MODIFIED Requirements

### Requirement: 协助键入的证据必须分级诚实

edge 回执 SHALL 携带 `typeReport`：焦点分级、焦点元素 tag（供事后取证，MUST NOT 据此分支）、清空三态、**实际派发字符数**、回读三态（`match` / `mismatch` / `unverifiable`）、是否已提交。

`typed` MUST 是实际派发的字符数，MUST NOT 用 `typed || text.length` 之类回退到意图值。被抢占或超预算中断时，edge MUST 尽力清场、如实回报 `typed`、MUST NOT 执行提交。

**取证 MUST 由真正派发字符的执行体产出，MUST NOT 由请求载荷推断。** 无论键入由哪个运行时执行（TypeScript 或已编码的页面引擎），焦点分级、清空三态、实际派发字符数、回读三态与是否已提交这五类事实 MUST 从那一次执行里带出，并由宿主逐字段透传到回执。宿主 MUST NOT 用「请求里带了文本」之类的意图信号替代任何一项。

**`inputMode:'click_type'` MUST 只在确有字符被派发时出现。** 下发了文本而执行体未回带任何键入取证时，edge MUST NOT 标 `click_type`——那会让云端「下发了文本却只点了击」的版本偏斜探测永久静默，把一次未执行的键入呈现成键入成功。此时如实回落到只点击的口径、让该探测器触发，是本条要求的正确结果。

运营 MUST 能从回执区分「答案打错了」（`verified:'match'` + `still_blocked`）与「字根本没打进去」（`focus:'none'` 或 `verified:'unverifiable'`）。把不可验证抹平成成功，与静默假成功同罪。

#### Scenario: 打进去了但答案不对
- **WHEN** `editable` 焦点、回读与答案一致、提交后仍被阻断
- **THEN** 回执为 `still_blocked` + `verified:'match'`，协助页展示「字打进去了，但答案不对」

#### Scenario: 不可验证不得报成成功
- **WHEN** `opaque` 焦点、提交后仍被阻断
- **THEN** 回执为 `still_blocked` + `verified:'unverifiable'`，MUST NOT 声称字符已落入

#### Scenario: 中断时如实回报已派发数
- **WHEN** 键入进行到第 3 个字符时租约被夺或超出预算
- **THEN** 回执 `typed === 3`、尽力清场、MUST NOT 执行提交、MUST NOT 报 `cleared`

#### Scenario: 取证缺席不得冒充键入成功
- **WHEN** 云端下发了文本，但执行体回带的回执里没有任何键入取证
- **THEN** edge MUST NOT 标 `inputMode:'click_type'`、MUST NOT 编造 `typeReport`
- **AND** 云端「下发了文本却只点了击」的探测 MUST 触发，控制台如实告知键入未执行

#### Scenario: 取证不得由请求推断
- **WHEN** 请求携带文本且执行体真的派发了字符
- **THEN** 回执里的焦点分级、清空三态、派发字符数、回读三态与是否提交 MUST 全部来自那一次执行
- **AND** 其中任何一项 MUST NOT 由请求载荷的存在与否或文本长度推导
