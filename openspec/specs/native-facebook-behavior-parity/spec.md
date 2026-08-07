# native-facebook-behavior-parity Specification

## Purpose
TBD - created by archiving change restore-native-facebook-behavior-parity. Update Purpose after archive.
## Requirements
### Requirement: Native-only Facebook preserves the established platform command boundary

The Facebook Native-only adapter SHALL implement only commands covered by the Facebook platform contract. Supported behavior SHALL include identity and page probes, Feed/Reels browse, search, note detail, exact-target like (`facebook.note.like` / `facebook.video.like`), Reel follow (`facebook.user.follow`), comment (`facebook.note.comment`), group join, and the existing Facebook publish atom subset. Facebook collect, comment-like, carousel browse, comment scroll, notifications, and author-profile browse MUST be refused before any page actuation: the platform-scoped rename makes all of them structurally xiaohongshu-only (`xiaohongshu.note.collect` / `xiaohongshu.comment.like` / `xiaohongshu.note.browse_images` / `xiaohongshu.note.scroll_comments` / `xiaohongshu.notification.*` / `xiaohongshu.profile.open`) so the platform-segment gate rejects them at the edge entrance before dispatch, and no platform-generic interaction command name remains. The hand-maintained Facebook unsupported-command set is retired with the last two shared names; platform nonsupport SHALL be derived from the name table plus the platform-segment gate, not from a second hand-copied list. A command name carrying another platform's segment MUST NOT create an implicit Facebook capability.

#### Scenario: Unsupported command does not touch the page

- **WHEN** a Facebook Native session receives `xiaohongshu.note.collect`, `xiaohongshu.comment.like`, `xiaohongshu.note.browse_images`, `xiaohongshu.note.scroll_comments`, a `xiaohongshu.notification.*` command, or `xiaohongshu.profile.open`
- **THEN** Edge refuses the command at the platform-segment gate at the edge entrance (`platform_mismatch`) — without router evaluation, navigation, scrolling, clicking, typing, or risk accounting

#### Scenario: Supported command stays Native-only

- **WHEN** a supported Facebook command is executed
- **THEN** the Rust Native Page Engine owns CDP inspection, actuation, and verification, and Edge MUST NOT invoke the retired TypeScript Facebook page executor or a JavaScript fallback process

### Requirement: Native Feed scanning preserves stateful continuation truth

The Native Facebook session SHALL distinguish validated cards, visible unreportable articles, loading, explicit empty, and exhausted Feed states. A validated Feed identity SHALL be projected from the declared identity kind: absent or `permalink` kind requires the existing Facebook content-URL validation and uses the canonical Facebook post identity extracted by the existing permalink parser; explicit `content_ref` kind requires the existing exact `aidcp:facebook-group-feed-post:v1:<64 lowercase hex>` format and retains its type in the identity key. Native MUST NOT infer the identity kind from the value's shape. A malformed or kind/value-mismatched card has no validated identity.

Native SHALL use that same typed projection for `page.cards` output, session seen deduplication, settle/bottom-confirmation identity vectors, and the command-local non-empty-feed witness. It SHALL report an unseen validated identity, including `content_ref`, before it may classify the viewport as exhausted. Only after the current observation contains no unseen validated card may Native consider the five-sample confirmation. The session seen set SHALL use the typed identity key, so a previously reported card is filtered consistently without a permalink-only side path. Existing `content_ref` capability and lifetime limits remain unchanged: it is session-scoped, list-surface/document-generation-bound, not persisted, not navigable, and not eligible for cross-session deduplication.

Native SHALL use loading-aware card-set settling, continue downward for up to the established bounded rounds when visible articles lack a validated identity, filter validated identities already reported by that session, and report a previously non-empty canonical home Feed as `feed_exhausted` only after the fixed five-sample no-growth, near-bottom, same-document, no-new-card confirmation evidence. Near-bottom SHALL mean no more than one actual scrolling-container viewport of remaining distance; exact mathematical bottom is not required, and a nested feed scroller SHALL use its own client height rather than the browser-window height. It MUST NOT authorize or perform a Reels transition merely because the current viewport has no reportable permalink.

The fixed confirmation samples SHALL occur at `t=0 / 5 / 7.5 / 10 / 12.5s`. Every sample SHALL remain on the same canonical home URL, the same non-zero document time origin, and the same document generation; keep `document_age_ms` from moving backward relative to the immediately preceding sample; remain non-loading and near-bottom using the actual scroll viewport; grow no more than 100px relative to the initial sample (`>100px` invalidates); and retain the same ordered validated Feed identity vector. Only the fifth valid structural sample SHALL confirm exhaustion. The adapter MAY retain `explicit_end` as bounded observation and diagnostic evidence, but a missing or unstable marker MUST NOT block structurally confirmed exhaustion only when the commanded list context began on home and this command observed a validated identity on the same home URL and document time origin. A `content_ref` may establish that witness only inside the command, URL, and document-time-origin window that observed it; a later command or replacement document MUST NOT inherit it. Marker-free structural confirmation MUST NOT extend to search/group contexts or to a search/group command redirected to home before confirmation.

The bounded terminal taxonomy SHALL be identical for the startup Feed scan and for every Cloud-commanded Feed scroll. When a commanded scroll exhausts its bounded rounds without producing a reportable card, the Native session SHALL apply the same evidence ladder the startup scan applies before falling back to a bare no-target result: a confirmed home surface carrying physical card evidence, not loading and not blocked, SHALL be reported as the present-but-unreportable list state; an otherwise confirmed empty home SHALL be reported as the explicit empty list state. Only when neither ladder rung holds MAY the session return the loading / continuation-unconfirmed / no-target classification. A commanded scroll MUST NOT return a terminal result that leaves the account on the same viewport with no Cloud-consumable observation, because the sole remaining recovery would be the Cloud idle watchdog.

Loading-aware card-set settling SHALL treat a zero-card viewport as unsettled. The settle loop MAY return early only once it has observed at least one extractable card in a stable, non-loading sample; a viewport that is merely stable at zero cards SHALL keep polling until its bounded budget is spent, so that lazy-loaded batches have time to render between scrolls.

This requirement adds no new receipt reason code and no new protocol field: structurally confirmed exhaustion reuses `feed_exhausted`, while the present-but-unreportable and explicit-empty observations reuse the existing zero-card `page.cards` list states that Cloud already consumes.

#### Scenario: Visible unreportable first viewport continues in Feed

- **WHEN** the initial Facebook Feed viewport contains visible hydrated articles but no trusted canonical permalink and a later bounded viewport contains a canonical card
- **THEN** Native scrolls within Feed, reports the later card, and does not emit explicit empty or navigate to Reels

#### Scenario: Loading zero-card viewport is not empty

- **WHEN** no canonical card is currently extractable and the Feed has an accessibility loading signal
- **THEN** Native waits within the bounded settle budget and, if still loading at the deadline, returns a retryable loading/no-target result rather than an empty card batch

#### Scenario: Recycled cards are not reported as new

- **WHEN** virtualized Feed scrolling renders permalink or `content_ref` typed identities already reported in the same Native session
- **THEN** Native filters those identities and continues the bounded search for new cards

#### Scenario: A fresh validated content reference is reported before exhaustion

- **WHEN** a Feed probe contains a card explicitly typed as `content_ref`, its value passes the existing strict prefix-and-digest validator, and its typed identity is not in the session seen set
- **THEN** Native emits that card through the normal `page.cards` path, records the same typed key in session seen-state, and does not return `feed_exhausted` from that observation

#### Scenario: A seen content reference remains command-local non-empty evidence

- **WHEN** the same valid `content_ref` is observed again by a home scroll command on the same URL and non-zero document time origin after session deduplication filters it from new-card output
- **THEN** Native MAY use it in that command's validated identity vector and non-empty witness
- **AND THEN** Native reports exhaustion only if no unseen identity remains and the complete five-sample structural window succeeds

#### Scenario: Malformed or mismatched typed identity fails closed

- **WHEN** a card's declared kind and value disagree, or a declared `content_ref` fails the exact existing prefix, digest-length, or lowercase-hex validation
- **THEN** Native neither reports nor records that value, excludes it from structural identity vectors, and does not let it establish an exhaustion witness

#### Scenario: Home exhaustion requires the complete structural schedule

- **WHEN** a commanded scroll whose list context began on home has observed a validated Feed identity on the same home URL and document time origin and all five fixed samples retain that non-zero origin and URL, keep adjacent document age nondecreasing, remain non-loading and within one actual scroll viewport of the bottom, grow no more than 100px, and retain the same ordered validated identity vector
- **THEN** Native reports `feed_exhausted` only after the `t=12.5s` sample, whether or not `explicit_end` is present
- **AND THEN** Native does not report exhaustion after any of the first four samples

#### Scenario: Structural invalidation remains continuation

- **WHEN** loading, growth above 100px, any ordered validated-identity-vector change, navigation, document-time-origin change, a backward adjacent document-age reset, generation change, surface change, or departure from near-bottom occurs before the fifth sample
- **THEN** Native does not report `feed_exhausted` from that window and retains the existing bounded continuation or zero-card evidence path

#### Scenario: A content-reference witness cannot cross a command or document

- **WHEN** a valid `content_ref` was observed only by a prior command, another URL, or another document time origin and the current command has observed no validated identity in its current home document
- **THEN** Native does not reuse that witness and MUST NOT report marker-free `feed_exhausted`

#### Scenario: Commanded scroll exhausting its rounds over physical cards reports present-but-unreportable

- **WHEN** a Cloud-commanded Feed scroll spends all of its bounded rounds without a reportable card, and the final observation is a confirmed home surface that still carries physical card evidence, is not loading, and is not login/captcha/consent blocked
- **THEN** Native reports a zero-card `page.cards` observation carrying the present-but-unreportable list state, exactly as the startup Feed scan does, and does not return a bare no-target receipt

#### Scenario: Commanded scroll exhausting its rounds over a confirmed empty home reports explicit empty

- **WHEN** a Cloud-commanded Feed scroll spends all of its bounded rounds without a reportable card, the final observation carries no physical card evidence, and the existing stable explicit-empty confirmation succeeds
- **THEN** Native reports a zero-card `page.cards` observation carrying the explicit empty list state and does not return a bare no-target receipt

#### Scenario: Blocked or non-home exhaustion keeps today's honest failure

- **WHEN** a commanded scroll exhausts its rounds while the final observation is loading, login-like, captcha-like, consent-blocked, off the home surface, or carries no physical card evidence and fails explicit-empty confirmation
- **THEN** Native returns the existing honest failure classification, reports neither present-but-unreportable nor explicit empty, and never transitions to Reels through the marker-free home path

#### Scenario: Zero-card viewport is not settled by stability alone

- **WHEN** two consecutive settle samples of a non-loading viewport both extract zero cards
- **THEN** Native keeps polling until the bounded settle budget is spent instead of returning immediately, so a lazy-loaded batch arriving later in the budget is still observed

#### Scenario: A settled non-empty card set still returns early

- **WHEN** two consecutive settle samples of a non-loading viewport extract the same non-empty card set
- **THEN** Native returns that sample immediately without spending the remainder of the settle budget

### Requirement: Native navigation preserves the active Facebook list surface

The Native Facebook session SHALL establish Feed on startup, retain the current home or search list URL, return from detail to that originating list surface, and refresh home Feed through a bounded SPA home action with a changed non-empty top-card postcondition. A raw reload MUST NOT be the primary refresh path and SHALL obey the existing three-minute fallback floor.

#### Scenario: Persisted non-Feed page is not accepted as startup baseline

- **WHEN** AdsPower opens on a Reel, profile, group, search, or detail page
- **THEN** Native establishes Facebook home Feed before reporting initial Feed cards

#### Scenario: Search detail returns to search

- **WHEN** a note is opened from a Facebook search result and navigation back is requested
- **THEN** Native returns to the same search result URL and does not reset to home

#### Scenario: Refresh proves a new batch

- **WHEN** Feed refresh is requested
- **THEN** Native reports success only after the home SPA action yields a non-empty top canonical identity different from the pre-action identity, or otherwise returns an honest bounded failure

### Requirement: Native blocker and consent gates match Facebook safety policy

Before Facebook page actuation, Native SHALL distinguish login, positive captcha, generic checkpoint/security blocking, Facebook soft throttle, and cookie consent. Captcha SHALL require positive captcha evidence; generic checkpoint and throttle SHALL be reported as unknown blockers with same-source bounded evidence. Cookie consent SHALL honor `accept_all` versus `necessary_only`, use the matching unique button, verify disappearance, and stop after the established bounded attempts.

#### Scenario: Generic checkpoint is unknown, not captcha

- **WHEN** the page is on a checkpoint/security route without positive captcha controls or semantics
- **THEN** Native blocks actuation and reports an unknown blocking incident rather than claiming a captcha

#### Scenario: Facebook throttle copy is reported with evidence

- **WHEN** a recognized Facebook soft-throttle message is visible
- **THEN** Native blocks the action and reports the unknown blocker with bounded text from the same scan that caused classification

#### Scenario: Necessary-only policy never clicks accept-all

- **WHEN** cookie consent is visible and the configured policy is `necessary_only`
- **THEN** Native clicks only the unique necessary-only control and returns `blocked_by_consent` if that control is unavailable or the dialog remains after bounded attempts

### Requirement: Native note-scoped actions never fall back to DOM order

A Facebook action carrying a canonical `noteId` SHALL resolve exactly one matching top-level post or active Reel, scroll that target into view, and bind pre- and post-action evidence to the same identity. Missing, recycled, duplicated, or ambiguous targets MUST fail without clicking, typing, or selecting the first available article.

#### Scenario: Missing target does not like the first card

- **WHEN** the commanded `noteId` is absent but another likeable post is visible
- **THEN** Native returns `target_not_found` and does not actuate any reaction control

#### Scenario: Comment uses only the requested post editor

- **WHEN** multiple post editors exist on the page
- **THEN** Native types and submits only in the unique top-level article matching the commanded `noteId`, or fails before submission

### Requirement: Native write actions use trusted actuation and preserve terminal truth

Facebook like, follow, comment, join, and publish writes SHALL use trusted CDP input for the committing interaction, re-probe the same scoped target, and distinguish not-started, confirmed, already-complete, pending/rejected, and ambiguous outcomes. Synthetic DOM keyboard events, direct content mutation, visibility disappearance alone, or a single short observation MUST NOT be treated as confirmed external effect.

#### Scenario: Ambiguous comment is not retryable failure

- **WHEN** a comment submit was dispatched but no server comment identity, same-account acknowledgement, pending-review signal, or explicit rejection can be established within the bounded verification window
- **THEN** Edge returns `verification_ambiguous` with an ambiguous effect phase so Cloud does not automatically retry the uncertain write

#### Scenario: Pending group comment is distinct from public confirmation

- **WHEN** Facebook acknowledges a submitted group comment as pending review
- **THEN** Edge returns `pending_group_approval` and MUST NOT claim a publicly confirmed comment

#### Scenario: Join waits for a durable post-click state

- **WHEN** a unique in-scope Join control is actuated
- **THEN** Native polls within the established bounded window and returns joined, pending, questionnaire-required, explicit failure, or ambiguous truth based on durable post-click evidence

#### Scenario: Publish submit requires commit and verification evidence

- **WHEN** the Facebook composer submit atom is executed
- **THEN** Native verifies full input readback before trusted submit and reports confirmed success only from the established composer/post evidence; a dispatched but unverified submit remains ambiguous

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

### Requirement: Native Facebook production dependencies exclude retired page-rule modules

The Edge production distribution SHALL keep Native Facebook orchestration dependencies separate from retired TypeScript Facebook page executors and injected JavaScript page-rule bundles. Shared pure helpers, including canonical post-identity parsing and presentation classification, MUST be provided from a module whose transitive dependency graph does not import those retired page-rule modules. Compatibility exports for development-only consumers MUST NOT make the mixed legacy façade reachable from Native production orchestration.

#### Scenario: Native orchestration shares post identity without shipping legacy rules

- **WHEN** the production Edge TypeScript distribution is built after Native Facebook browse orchestration imports canonical Reel or Feed-video identity helpers
- **THEN** the build succeeds with the helper behavior preserved and the production graph contains none of the forbidden migrated Facebook page-rule JavaScript modules

#### Scenario: A pure helper import reintroduces a legacy dependency

- **WHEN** a Native production module transitively imports a retired Facebook page executor or injected JavaScript rule bundle through a shared helper
- **THEN** production distribution verification fails instead of allowlisting or silently shipping that dependency

### Requirement: Native Feed card discovery covers non-semantic layouts

Facebook serves Feed layouts that expose neither a `role="feed"` container nor hydrated `role="article"` cards. The Native Facebook session SHALL NOT depend on those semantic roles alone to find Feed cards. It SHALL additionally discover cards by seeding from post-body markers and walking outward to the nearest ancestor that carries an author link, treating that ancestor as the card boundary. Seeds already inside a semantic Feed container SHALL be left to the semantic path. Discovered candidates SHALL be reduced to outermost elements only, ordered by document position, and merged with the semantic result so that one post never yields two cards.

Discovery MUST remain evidence-bound: when no ancestor carrying an author link is found, the seed SHALL yield no card. The session MUST NOT promote the page body, the main region, or any container lacking author evidence into a card, and MUST NOT borrow a neighbouring card's author or identity.

#### Scenario: Layout without a semantic feed container still yields cards

- **WHEN** the home Feed renders no `role="feed"` container and its only `role="article"` elements are unhydrated shells, while post-body markers with author links are present
- **THEN** Native discovers one card per post-body marker at its author-bearing ancestor and reports those cards through the normal Feed path

#### Scenario: Semantic layout is unchanged

- **WHEN** the home Feed renders a semantic Feed container with hydrated article cards
- **THEN** Native reports exactly the cards the semantic path already produced, and the fallback discovery contributes no duplicate for the same post

#### Scenario: Nested candidates collapse to the outermost card

- **WHEN** a shared or quoted post produces a post-body marker nested inside another discovered card
- **THEN** only the outermost card survives, so one post never yields two cards and identities are never attributed across card boundaries

#### Scenario: A seed without author evidence yields nothing

- **WHEN** a post-body marker has no ancestor carrying an author link before reaching the document body
- **THEN** Native discovers no card for that seed and neither fabricates a boundary nor falls back to a page-level container

### Requirement: Physical Feed card evidence requires hydration

The Native Facebook session SHALL count a Feed card as physical card evidence only when that card is hydrated — that is, it carries an author link or a post-body marker. Visibility and layout height alone MUST NOT qualify. Virtualized placeholder shells, which Facebook renders with reserved height but no content, MUST NOT be counted as physical cards and MUST NOT, on their own, justify the present-but-unreportable observation that authorizes a Reels transition.

#### Scenario: Placeholder shells do not count as physical cards

- **WHEN** the only card-shaped elements on a confirmed home Feed are virtualized placeholders with reserved height, no author link, and no post-body marker
- **THEN** Native reports zero physical cards, and the present-but-unreportable path is not taken on that evidence

#### Scenario: Hydrated but unidentifiable cards still count

- **WHEN** a card carries an author link or post-body marker but exposes no acceptable post permalink
- **THEN** Native counts it as physical card evidence and the existing present-but-unreportable observation remains available

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

