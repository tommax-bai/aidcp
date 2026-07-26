# facebook-feed-browse Specification

## Purpose
TBD - created by archiving change facebook-feed-inline-browse. Update Purpose after archive.
## Requirements
### Requirement: Facebook feed stays continuous instead of reloading to top

The Facebook list reader MUST make navigation idempotent. A ready Facebook home MUST remain in place even when it has no hydrated cards or feed container, while search and group lists MUST retain their existing list-container readiness rule. Every path MUST still run login, checkpoint, consent, captcha, and blocking-overlay checks. Card scanning MUST report only newly appeared top-level hydrated cards keyed by a session-level canonical-id cursor. A zero-card home MUST NOT be treated as exhausted or empty unless the explicit loading-aware empty-state contract in `facebook-feed-continuity` confirms it.

When the Edge reports an explicitly confirmed empty Facebook home through the existing optional `page.cards` observation fields, or honestly reports `feed_exhausted` after a non-empty Facebook list has yielded real cards and bounded navigation has found no unseen card, the Cloud SHALL authorize the fallback by sending the existing scroll command with the deployed `empty_feed_reels_fallback` compatibility reason. Only that Cloud authorization MAY switch the Edge session to Reels. The authorization SHALL be idempotent per active session. Loading, unknown layout, navigation error, login/checkpoint/consent/captcha, search, or group states MUST NOT trigger the fallback. Non-Facebook `feed_exhausted` behavior SHALL remain the existing refresh path. Once Reels cards are reported, the existing evaluation, read, interaction authorization, pacing, and risk-accounting loop SHALL continue unchanged.

#### Scenario: Scrolling does not reload the same first cards
- **WHEN** the account scrolls a ready Facebook list URL with no blocking state
- **THEN** the reader does not re-navigate to the top and reports only newly appeared cards while the safety front door still runs

#### Scenario: Confirmed empty home is authorized by Cloud
- **WHEN** an active Facebook session reports `cards:[]` with the optional observation identifying a confirmed empty home feed
- **THEN** Cloud sends exactly one existing scroll command carrying the dedicated Reels fallback reason
- **AND** Edge enters Reels only after receiving that authorization

#### Scenario: Unconfirmed zero cards do not switch lists
- **WHEN** Edge reports loading, unknown layout, navigation failure, a blocked page, or merely observes zero cards without explicit empty-state confirmation
- **THEN** Cloud MUST NOT authorize the Reels fallback and Edge MUST remain fail-closed

#### Scenario: Confirmed non-empty Facebook Feed exhaustion is authorized by Cloud
- **WHEN** an active Facebook session reports `action.completed{action:scroll,ok:false,reason:feed_exhausted}` after Edge's bounded loading-aware exhaustion check
- **THEN** Cloud sends exactly one existing scroll command carrying `reason:empty_feed_reels_fallback`
- **AND** Edge enters Reels instead of refreshing the exhausted Facebook Feed

#### Scenario: Duplicate exhaustion and other platforms preserve safe behavior
- **WHEN** the same active Facebook session repeats `feed_exhausted` after Reels fallback was already authorized
- **THEN** Cloud MUST NOT send a second fallback or refresh command
- **AND WHEN** a non-Facebook session reports `feed_exhausted`
- **THEN** Cloud retains the existing refresh behavior and MUST NOT authorize Facebook Reels

#### Scenario: Existing evaluation and risk chain continues on Reels
- **WHEN** Edge reports an active Reel as a normal card and Cloud later authorizes a like
- **THEN** content evaluation and pacing run through the existing browse loop
- **AND** only a platform-confirmed like receipt is recorded by the existing RiskController path

#### Scenario: Exhausted non-empty list is reported honestly
- **WHEN** a list has previously yielded cards and bounded continued navigation surfaces no unseen card
- **THEN** Edge returns an exhausted-feed signal instead of silently idling
- **AND** recycled cards are not counted as new
- **AND** Cloud MAY use that honest signal to authorize the platform-specific continuation without changing the Edge exhaustion proof

### Requirement: Facebook reads full post text in place on the feed when enabled

When commanded to open a note with the feed surface, the edge MUST lock exactly one top-level article by the command's canonical post id and read its full text without leaving the feed. It MUST prefer a no-click shortcut when the message container's full text content is already present but visually clamped, and otherwise MUST click only an anchored expand control inside that article's message container (never a link, using an in-page click). It MUST verify that the page URL, the dialog count, and the target card index are unchanged around the expansion; if any changes, it MUST abort the in-place read, fall back to detail navigation, and report the detail-surface note honestly. If clicking the expand control does not change the article's rendered text length, the edge MUST report an expand-no-effect outcome rather than claiming success; a short post with no expand control is a normal success, not a no-target.

#### Scenario: In-place expand补全 full text without leaving the feed

- **WHEN** a feed-surface open targets a clamped long post whose expand click keeps URL, dialog count, and card index unchanged
- **THEN** the edge reads the full expanded text and reports it as the note content
- **AND** it does not navigate into a detail page

#### Scenario: Expansion that would leave the feed falls back to detail

- **WHEN** clicking the expand control changes the URL or opens a dialog or shifts the target card
- **THEN** the edge aborts the in-place read and falls back to detail navigation
- **AND** it reports the note with the detail surface honestly

### Requirement: Navigate-purpose open does not report a decision note

When a note-open command carries the navigate purpose, the edge MUST only bring the browser to the target detail and MUST NOT report a decision note.detail (which would overwrite real reaction counts with zero). It MUST instead return an action-completed receipt carrying the independent observation and the page-derived canonical post id.

#### Scenario: Navigate open returns a witness, not a note.detail

- **WHEN** the edge receives a navigate-purpose open for an approved comment migration
- **THEN** it lands on the target detail and returns an action-completed receipt with observation and derived note id
- **AND** it does not report a note.detail that overwrites the post's real reaction counts

### Requirement: A lost feed target is reported as stale without a rollback search

When the target article has been removed from the DOM (feed virtualization) between selection and acting, the edge MUST return a stale no-target and MUST NOT roll back or search other cards for it. Only when the target is still in the DOM but off-screen may the edge bring it into view with a bounded humanized scroll. The action-completed observation MUST be sampled from the actually acted-upon article so the cloud can arbitrate attribution against the selected card.

#### Scenario: Recycled target is stale, not re-hunted

- **WHEN** the target article has been recycled out of the DOM before the like is acted upon
- **THEN** the edge returns a stale no-target
- **AND** it does not search other cards or roll the feed back to find it

### Requirement: Xiaohongshu refuses the feed surface honestly

The Xiaohongshu browse session MUST reject a feed-surface note-open with a capability-unsupported reason and MUST NOT silently fall back to detail navigation.

#### Scenario: Xiaohongshu does not silently reinterpret the feed surface

- **WHEN** the Xiaohongshu session receives a note-open with the feed surface
- **THEN** it returns capability-unsupported
- **AND** it does not navigate into a detail page as a silent fallback

### Requirement: Facebook feed 点赞资格以「已选中 + 已走到点赞判定」为据，不硬闸同级订阅者写的「已放行」集合

云端对 Facebook feed 自然互动（点赞）的资格判定 MUST NOT 硬闸一个由 `quality.pass` 的**同级订阅者**填充的「已放行」集合。理由：点赞判定角色由 `reading.done` 触发，而 `reading.done` 只可能在内容质量筛选放行（`quality.pass`）驱动深读→评论链走通后才发出——**能走到点赞判定本身即证明该帖已被质量筛选放行**。资格 SHALL 以「该帖已被选中」（`content_selected`）为闸；「已放行」集合 MAY 继续维护并写入诊断日志（作观测），但 MUST NOT 作为拦截点赞的硬条件。

此不变量是为消除 `EventBus` 同步 emit 下的**顺序竞态**：`quality.pass` 的多个同级订阅者中，深读角色先注册先跑、并在其自身处理器内**同步**一路驱动到点赞判定；若点赞闸依赖另一个同级订阅者稍后才写入的集合，检查时集合恒空 → 系统性误判「未通过质量筛选」、挡掉全部点赞。边缘用于关联的 noteId SHALL 归一到**规范帖身份**（帖数字 id），使「已选中」与「点赞判定」两处 key 在不同上报形态（feed 卡 vs 详情）下必然一致，MUST NOT 因形态差异误判不匹配。

#### Scenario: 已选中且走到点赞判定即放行、不被空集合误挡
- **WHEN** 某 Facebook feed 帖已被选中、且深读链驱动到点赞判定角色
- **THEN** 云端 MUST 放行点赞资格判定（进入 LLM 点赞决策），MUST NOT 因「已放行」集合此刻为空而回报「未通过质量筛选」拦截

#### Scenario: noteId 形态不同仍正确关联
- **WHEN** 「已选中」记录的 noteId 来自 feed 卡上报、而点赞判定处的 noteId 来自详情上报（同一帖、形态不同）
- **THEN** 云端按规范帖身份归一后判定两者为同一帖，资格关联成立，MUST NOT 因形态差异判不匹配而误挡

### Requirement: Facebook feed card targeting supports both observed layouts with one identity boundary

The Facebook feed reader and every in-feed target resolver SHALL share one locale-neutral top-level card abstraction that supports both the semantic `[role="feed"]` / `[role="article"]` layout and the lightweight story-message div layout. A lightweight card SHALL be bounded to the smallest visible structural container that contains its message and at least one linked author heading, and target-scoped reads, observations, and actions MUST remain inside that resolved card.

A discovered card MUST NOT become a reportable or actionable target unless the existing canonical-post identity parser accepts a post-shaped link inside that exact card. Photo/video resource identifiers or obfuscated timestamp links that do not satisfy that parser MUST NOT be promoted to post identity. When no reliable card target exists, the edge SHALL continue the existing bounded browse path and return an honest no-target/exhausted outcome rather than searching a neighboring card or claiming success.

#### Scenario: Semantic feed card remains resolvable
- **WHEN** a reported target came from a top-level semantic article inside `[role="feed"]`
- **THEN** the later in-feed reader and action resolver locate that exact article by canonical post id and keep all observation/action scope inside it

#### Scenario: Lightweight feed card is reported and resolved by the same rule
- **WHEN** a lightweight story-message card contains at least one linked author heading and a whitelisted canonical post link
- **THEN** the initial scanner can report it and a later in-feed reader can resolve the same exact card by the same canonical post id without leaving the feed

#### Scenario: Ambiguous media-only lightweight card fails closed
- **WHEN** a lightweight card exposes only photo/video resource identifiers or a non-canonical obfuscated timestamp link
- **THEN** the edge does not report or act on that card and MUST NOT substitute a neighboring card or fabricate a post identity

#### Scenario: Layout detection does not depend on writing language
- **WHEN** two accounts receive different UI languages but one of the two supported structural layouts
- **THEN** the same structural detector recognizes their cards without matching localized author, timestamp, menu, or expand-control text for layout classification

### Requirement: Lightweight Facebook video cards preserve exact-card identity safety

A lightweight Facebook card containing video content SHALL be reportable and actionable only when the shared scanner/target resolver finds a canonical video-post link inside that exact card, using an already accepted `watch?v`, `videos/<id>`, or `reel/<id>` shape. A `<video>` element, CDN media URL, photo/video resource id, `/` timestamp anchor, opaque timestamp text, author, or content text MUST NOT be promoted to post identity.

If the current video card has no trustworthy identity, the Edge MUST classify it as structurally present but unreportable, skip it, and continue the bounded feed path. It MUST NOT substitute an identity from a neighboring card or stop the initial browse loop merely because the unreportable video occupies the first viewport.

#### Scenario: Exact-card watch link makes a lightweight video reportable
- **WHEN** a lightweight video card contains a `watch?v=<video-post-id>` link inside its own structural card boundary
- **THEN** the scanner reports that exact card with the canonical video-post identity and later target resolution finds the same card

#### Scenario: Media-only Vietnamese first video card is skipped
- **WHEN** a visible lightweight video card contains readable Vietnamese text but exposes only a `/` timestamp anchor, media resource URLs, and no accepted post-shaped link
- **THEN** the Edge does not derive identity from the text or media, skips the card, and continues downward within the existing bounded scroll policy

#### Scenario: Neighboring canonical link cannot identify the video card
- **WHEN** an unreportable video card is adjacent to another card that contains a canonical permalink
- **THEN** the video card remains unreportable and all reads/actions stay scoped to the neighboring card only when that neighboring card is separately reported

### Requirement: Strict lightweight Feed videos are reportable only when actually presented

The Facebook Feed scanner SHALL merge semantic top-level posts with lightweight video-card roots found inside the same Feed container. A lightweight video root SHALL be reportable only when it contains exactly one numeric `data-video-id`, exactly one video, publisher or story-message evidence, and one post-level like/comment action boundary. Its video MUST have meaningful horizontal intersection and at least 35% vertical intersection with the primary viewport. If multiple strict videos satisfy the viewport threshold in one scan, Edge SHALL report only the one whose video center is closest to the viewport center and SHALL leave the others eligible for a later scan. Existing non-video card reporting MUST remain unchanged.

#### Scenario: Lightweight video inside a semantic Feed is reported
- **WHEN** a Feed contains a non-article video root with one video id, one video, author/caption evidence, one action boundary, and at least 35% viewport intersection
- **THEN** Edge reports it as one `isVideo:true` card with its extracted author and caption

#### Scenario: Off-screen mounted video is deferred
- **WHEN** a strict video card exists in the DOM but has less than 35% vertical viewport intersection
- **THEN** Edge does not report it in the current batch and does not mark its identity seen, allowing a later scroll to present it

#### Scenario: Multiple visible videos yield one primary presentation
- **WHEN** two strict video cards satisfy the viewport threshold in a large viewport
- **THEN** Edge reports only the center-nearest video in that scan and defers the other

#### Scenario: Embedded Reels rail is not a Feed video card
- **WHEN** an embedded Reels rail mounts multiple videos without one strict video id and one local post action boundary
- **THEN** Edge excludes it from ordinary-Feed video reporting and MUST NOT attribute it to an adjacent post by ancestor order

#### Scenario: Ambiguous lightweight card continues browsing
- **WHEN** a candidate contains multiple ids/videos, lacks publisher/caption/action witnesses, or has mismatched explicit and data-derived identities
- **THEN** Edge reports no synthetic card for it, performs no action on it, and retains the existing bounded continuation behavior

### Requirement: Bounded present-but-unreportable Feed transitions to Reels through Cloud authorization

When a confirmed Facebook home Feed contains physical card evidence but eight bounded continuation rounds yield no reportable card, Edge SHALL report a distinct present-but-unreportable Feed list state. Edge MUST NOT report that observation as an empty Feed, MUST NOT claim `feed_exhausted`, and MUST NOT emit an uncommanded action receipt. Cloud SHALL deduplicate the observation for the active startup/document generation and authorize one Reels transition. Edge SHALL enter Reels only after that authorization and a fresh surface/blocker check. Loading, login, consent, checkpoint, unknown, non-home, or physically cardless pages MUST NOT use this fallback.

#### Scenario: Eight unreportable rounds request one Reels transition
- **WHEN** the active Facebook home page still contains physical Feed cards but all eight continuation rounds yield no trustworthy card identity
- **THEN** Edge reports the present-but-unreportable list state, Cloud sends one Reels-fallback authorization, and Edge transitions to the dedicated Reels surface

#### Scenario: A reportable card before round eight keeps the Feed active
- **WHEN** any continuation round produces a trustworthy Feed card
- **THEN** Edge reports that card through the normal Feed path and does not request the unreportable Reels fallback

#### Scenario: Loading or blocked pages never use the unreportable fallback
- **WHEN** the final probe is loading, login-like, consent-blocked, checkpoint-like, unknown, non-home, or lacks physical card evidence
- **THEN** Edge fails closed with the truthful existing state and neither Edge nor Cloud transitions to Reels from the unreportable path

#### Scenario: Repeated observation is idempotent
- **WHEN** the same startup/document generation repeats the present-but-unreportable observation
- **THEN** Cloud emits at most one Reels-fallback authorization for that generation

