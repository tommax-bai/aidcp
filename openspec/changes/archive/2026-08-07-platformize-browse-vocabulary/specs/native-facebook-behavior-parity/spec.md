## MODIFIED Requirements

### Requirement: Native-only Facebook preserves the established platform command boundary

The Facebook Native-only adapter SHALL implement only commands covered by the Facebook platform contract. Supported behavior SHALL include identity and page probes, Feed/Reels browse, search, note detail, exact-target like, Reel follow, comment, group join, and the existing Facebook publish atom subset. Facebook collect, comment-like, carousel browse, comment scroll, notifications, and author-profile browse MUST be refused before any page actuation: commands for these that remain platform-generic (`interaction.collect`, `interaction.like_comment`) MUST return `capability_unsupported`, while the platform-scoped rename makes the rest structurally xiaohongshu-only (`xiaohongshu.note.browse_images` / `xiaohongshu.note.scroll_comments` / `xiaohongshu.notification.*` / `xiaohongshu.profile.open`) so the platform-segment gate rejects them at the edge entrance before dispatch. A command name carrying another platform's segment MUST NOT create an implicit Facebook capability.

#### Scenario: Unsupported generic command does not touch the page

- **WHEN** a Facebook Native session receives `interaction.like_comment`, `xiaohongshu.note.browse_images`, `xiaohongshu.note.scroll_comments`, a `xiaohongshu.notification.*` command, `interaction.collect`, or `xiaohongshu.profile.open`
- **THEN** Edge refuses the command before dispatch — the `xiaohongshu.*` names are rejected by the platform-segment gate at the edge entrance, and the platform-generic names return `capability_unsupported` — without router evaluation, navigation, scrolling, clicking, typing, or risk accounting

#### Scenario: Supported command stays Native-only

- **WHEN** a supported Facebook command is executed
- **THEN** the Rust Native Page Engine owns CDP inspection, actuation, and verification, and Edge MUST NOT invoke the retired TypeScript Facebook page executor or a JavaScript fallback process

### Requirement: Native parity is protected by behavior-level regression tests

The Edge repository SHALL contain focused Native tests derived from the established Facebook TypeScript behavior cases for Feed settling and continuation, blocker/consent classification, exact target selection, comment terminal classification, join readiness, publish integrity, unsupported command routing, **feed-surface in-place expansion with its honest terminal outcomes, and actual consumption of the cloud pacing fields**. Tests MUST assert externally meaningful state and reason codes rather than only checking that a selector exists or a router branch returns.

一条 Native 行为被判定为「已迁移」的判据 SHALL 是**行为对等**，MUST NOT 是「返回了同形状的投影结构」。任何把既有 TypeScript 页面行为搬入 Native 的任务，在其对应行为缺少上述判据的回归测试之前 MUST NOT 标记完成。

#### Scenario: Native cutover regression is rejected

- **WHEN** a Native implementation again treats loading/unreportable Feed as empty, falls back to the first post, uses a non-equivalent ambiguous reason, or actuates an unsupported Facebook command
- **THEN** a focused parity test fails before integration

#### Scenario: A rendered-text scrape cannot pass as an in-place read

- **WHEN** Native 的 feed 面 `facebook.note.open` 只返回卡片当前已渲染的文字、不做展开与校验
- **THEN** 一条聚焦的对等测试在集成前失败

#### Scenario: Silently dropping a pacing field fails a parity test

- **WHEN** Native 的映射层接收 `thinkMs` 或就地读 read floor 相关输入、执行层却不产生对应等待
- **THEN** 一条聚焦的对等测试在集成前失败

### Requirement: Native feed-surface reads perform the full in-place expansion, not a rendered-text scrape

Native 的 Facebook feed 面 `facebook.note.open` SHALL 执行 `facebook-feed-browse` 已要求的完整就地读，而不是把卡片上当前已渲染的文字抓走就返回。它 SHALL 按命令携带的规范帖身份锁定**唯一**顶层卡片；当该卡消息容器的全文已在 DOM 内、仅被视觉截断时 SHALL 走免点击捷径；否则 SHALL 只点击该消息容器内锚定的展开控件（MUST NOT 点击链接，使用页内点击）。展开前后 SHALL 校验页面 URL、弹层数量与目标卡序号三者均未变化。

三条诚实终态 MUST 成立：① 点击展开后正文渲染长度未增长 → 报「展开无效」终态，MUST NOT 当成功；② 上述三项校验中任一发生变化 → 中止就地读、回落详情页导航、以 detail 面诚实上报该帖；③ 卡片本就没有展开控件的短帖，读到什么算什么，是正常成功、MUST NOT 报 `no_target`。

Native SHALL 对规则模式与人设模式采用同一条执行路径，MUST NOT 按账号浏览模式分叉，也 MUST NOT 在客户端持有模式事实。

#### Scenario: Clamped long post is expanded before it is reported

- **WHEN** feed 面 `facebook.note.open` 命中一条正文被折叠、且展开点击前后 URL / 弹层数 / 目标卡序号均未变化的长帖
- **THEN** Native 读到展开后的完整正文并作为该帖内容上报
- **AND** 上报的正文长度大于展开前的渲染长度

#### Scenario: Full text already present is read without a click

- **WHEN** 消息容器的全文已在 DOM 内、仅被视觉截断
- **THEN** Native 走免点击捷径读全文，MUST NOT 为取全文而额外点击展开控件

#### Scenario: Expansion without growth is reported honestly

- **WHEN** Native 点击了展开控件、但该卡正文的渲染长度没有增长
- **THEN** Native 返回「展开无效」终态，MUST NOT 上报帖子详情、MUST NOT 计入一次浏览

#### Scenario: Context change aborts the in-place read and falls back to detail

- **WHEN** 展开过程中页面 URL 变化、出现弹层、或目标卡序号位移
- **THEN** Native 中止就地读，改走详情页导航读取，并以 detail 面诚实上报该帖

#### Scenario: Short post without an expand control is a normal success

- **WHEN** 目标卡片没有任何展开控件
- **THEN** Native 以读到的正文正常成功上报，MUST NOT 返回 `no_target` 或展开无效

#### Scenario: Browse mode does not change the execution path

- **WHEN** 同一条 feed 面 `facebook.note.open` 分别发生在规则模式账号与人设模式账号上
- **THEN** Native 的锁卡、展开、校验与上报行为逐条相同

### Requirement: Native consumes the cloud pacing fields it accepts

Native 的命令映射层与执行层 SHALL 实际消费云端随决策指令下发的节奏字段，MUST NOT 出现「映射层收下字段、执行层静默丢弃」。收到带 `thinkMs` 的动作命令时，Native SHALL 在**执行该动作前**等待抖动后的时长；该等待与既有最小间隔语义测同一「now → 执行本动作」跨度，两者 SHALL 取 max、MUST NOT 相加。

Native 完成一次 feed 面就地读后 SHALL 按读到的正文长度（叠当前 `tempo`）确定一条边缘本地 read floor，锚在就地读开始时刻；随后离开该内容的 `facebook.feed.scroll` SHALL 在该 read floor 与云端 `dwellMs` 的新卡锚点之间取 max、MUST NOT 相加，也 MUST NOT 因就地读比进详情页快而出现零延迟秒滚。

#### Scenario: thinkMs delays the action instead of being discarded

- **WHEN** Native 收到一条携带非零 `thinkMs` 的动作命令，且距上次操作完成的间隔尚未达到该字段值
- **THEN** Native 在触达页面前先等待抖动后的时长再执行

#### Scenario: thinkMs and the minimum action interval do not stack

- **WHEN** 同一次动作既受最小间隔约束又携带 `thinkMs`
- **THEN** 实际等待为两者的较大值，而非两者之和

#### Scenario: In-place read establishes a read floor before the next scroll

- **WHEN** Native 就地读完一条长帖，随即收到带 `dwellMs` 的 `facebook.feed.scroll`
- **THEN** 实际停留不小于「就地读 read floor」与「新卡锚点 dwell 目标」中的较大者
- **AND** 两者 MUST NOT 相加

#### Scenario: A short in-place read never becomes a zero-delay scroll

- **WHEN** 就地读在极短时间内完成
- **THEN** Native 仍补足 read floor 后才发出下一条 `facebook.feed.scroll`

### Requirement: Automatic Facebook scroll foreground activation is watchdog- or movement-scoped

The Native Facebook runtime SHALL keep ordinary automatic list scrolling background-first. It MAY invoke `Page.bringToFront` for an automatic Facebook scroll command (`facebook.feed.scroll` / `facebook.search.scroll` / `facebook.reels.scroll`) in exactly two cases, and no others: when the reason is exactly `idle_recover_nudge`, or after a completed background Feed-list wheel has bounded same-document proof of no movement on a ready, scrollable, non-terminal surface. Each command MUST activate the exact already-bound target at most once and MUST NOT switch targets.

**Reason alone never authorizes activation beyond the watchdog reason.** A `facebook.feed.scroll` / `facebook.search.scroll` / `facebook.reels.scroll` carrying `feed_scroll`, `search_scroll`, `resume_redrive`, `feed_continuation_unconfirmed`, any other non-watchdog reason, or no reason at all MUST NOT invoke `Page.bringToFront` on the strength of its reason, whether it reaches Feed, Search, Reels, a no-target result, a resume path, a continuation path, or another recovery path. The second case above is not a reason-based exception: it is earned only by measured proof of no movement after input was actually dispatched, and it MUST NOT be widened into a reason.

No-target, pre-input rejection, loading, terminal, context-drift, and already-moved paths MUST remain background-only.

This requirement applies only to the automatic Facebook scroll commands (`facebook.feed.scroll` / `facebook.search.scroll` / `facebook.reels.scroll`). Explicit operator actions that show a browser, guided login, and non-Facebook commands retain their existing independent foreground behavior.

#### Scenario: Watchdog recovery activates before input once

- **WHEN** Native receives a Facebook scroll command (`facebook.feed.scroll` / `facebook.search.scroll` / `facebook.reels.scroll`) with `reason = "idle_recover_nudge"`
- **THEN** it activates the exact bound target once before scroll actuation
- **AND** it does not switch to another target
- **AND** any later no-movement classification in that command cannot activate it again

#### Scenario: Routine scroll remains in the background on reason alone

- **WHEN** Native receives a Facebook scroll command (`facebook.feed.scroll` / `facebook.search.scroll` / `facebook.reels.scroll`) with `feed_scroll`, `search_scroll`, `resume_redrive`, `feed_continuation_unconfirmed`, another non-watchdog reason, or no reason
- **THEN** it preserves the existing bounded page inspection and input gates
- **AND** it does not invoke `Page.bringToFront` on the strength of that reason, whether or not those gates ultimately dispatch input

#### Scenario: Ordinary movement remains fully backgrounded

- **WHEN** an ordinary Facebook list scroll completes with measured movement
- **THEN** Native invokes no foreground activation for that command

#### Scenario: Ordinary proven no-movement activates once after input

- **WHEN** an ordinary background wheel completes and bounded readback proves eligible same-document no movement
- **THEN** Native activates the exact bound target once before the single recovery wheel

#### Scenario: Ordinary no-target result does not cover the desktop

- **WHEN** a non-watchdog Facebook scroll command resolves to no target or is rejected before input
- **THEN** it invokes neither `Page.bringToFront` nor scroll input

#### Scenario: No target or context drift never covers the desktop

- **WHEN** an ordinary scroll has no target, dispatches no wheel input, or changes document or surface before recovery
- **THEN** Native does not invoke `Page.bringToFront` through adaptive recovery

#### Scenario: Explicit operator foreground action is unchanged

- **WHEN** the operator explicitly requests to show a browser or enter guided login
- **THEN** the existing explicit foreground behavior remains available independently of the automatic scroll rule and of the scroll command's `reason`
