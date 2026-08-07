# facebook-note-scoped-targeting Specification

## Purpose
TBD - created by archiving change facebook-note-scoped-targeting. Update Purpose after archive.
## Requirements
### Requirement: Facebook post identity is a canonical post id, not a URL

Facebook note-scoped targeting MUST key on a canonical post identity `fb:<postId>` derived from the card-header canonical link or, only for a strict lightweight video card with no usable permalink, from its unique numeric `data-video-id`. Link-derived postId is taken from `posts/<id>`, `permalink/<id>`, `story_fbid`, `multi_permalinks`, the `pfbid` path segment, or the video id (`videos/<id>`, `reel/<id>`, `watch?v=`). Derivation MUST apply a post-permalink **shape whitelist** — a href that is not shaped like a post permalink (author profile links such as `/people/<slug>/pfbid…/`, photo links, group/page home links) MUST NOT derive an identity, because such links appear **before** the timestamp permalink in card-header DOM order and would otherwise define the card's identity as the author's. Derivation MUST also exclude `comment_id` / `reply_comment_id` links, links inside a nested `[role="article"]` (comment) subtree, and links inside share/attachment subtrees.

The `data-video-id` fallback SHALL be valid only when the same card boundary contains exactly one numeric video id, exactly one video, publisher or story-message evidence, and one post-level like/comment action boundary. If an explicit canonical link exists, it SHALL win only when its canonical post id agrees with the video id; multiple ids or disagreement MUST return the null sentinel. A valid fallback SHALL expose the existing navigable noteId as `https://www.facebook.com/watch?v=<video-id>`. Feed scanning, deduplication, inline reading, like/comment target resolution, exclusive-region checks, and post-action verification MUST use this same identity helper.

Derivation that cannot produce a post id MUST return a null sentinel, never an empty string, so that a malformed href never compares equal to another and re-selects an arbitrary card. All matching, deduplication, and locating across the like and comment executors MUST use this one identity, replacing any divergent URL-pathname key. The identity MUST NOT be qualified by a container (group/page) segment: Facebook post ids are already globally unique, while a container derived from a page vanity slug in one link form and from a numeric page id in another would give the **same post two identities** and turn a legitimate command into a deterministic `no_target`.

#### Scenario: Two same-group multi_permalinks posts do not collide

- **WHEN** two posts in the same group are rendered as `multi_permalinks`-form permalinks in the feed
- **THEN** each derives a distinct canonical post id
- **AND** a like command for one MUST NOT resolve to the other

#### Scenario: One post rendered in different link forms is one identity

- **WHEN** the same post is reachable as `/<page>/posts/<id>` on one surface and as `/permalink.php?story_fbid=<id>&id=<numeric page id>` on another
- **THEN** both derive the same canonical post id
- **AND** a command carrying either form resolves to that post

#### Scenario: Author profile link never becomes the card identity

- **WHEN** a card header contains an author profile link of the form `/people/<slug>/pfbid…/` before the timestamp permalink
- **THEN** the author link derives the null sentinel and the card identity comes from the timestamp permalink
- **AND** a like command for that card resolves normally

#### Scenario: Malformed link yields no target, not the first card

- **WHEN** the only permalink-shaped href on a card is `javascript:` / a fragment / otherwise unparseable
- **THEN** canonical id derivation returns the null sentinel
- **AND** the command resolves to `no_target` while the DOM-first card is left untouched

#### Scenario: Strict video id supplies the missing permalink identity
- **WHEN** a lightweight card has no canonical post link but has one video id `1632570071375207`, one video, author/caption, and one post action boundary
- **THEN** scanning and action resolution use canonical identity `fb:1632570071375207` and navigable noteId `https://www.facebook.com/watch?v=1632570071375207`

#### Scenario: Explicit and data-derived video identities disagree
- **WHEN** a lightweight card carries `/watch?v=111` but its unique `data-video-id` is `222`
- **THEN** the card identity is the null sentinel, no action target resolves, and neither adjacent card is touched

#### Scenario: Adjacent lightweight video cards remain isolated
- **WHEN** two adjacent lightweight video cards each have their own author, caption, action boundary, and distinct video id
- **THEN** a command for one id resolves only inside that card and verification MUST NOT consume the other card's selected state

### Requirement: Note-scoped actions resolve exactly one target article and never fall back to DOM order

For any note-scoped command (like, comment), the edge MUST resolve exactly one target `[role="article"]` using the command's canonical post id via a three-stage procedure: (1) scope = the last-opened visible `[role="dialog"]` **that actually contains a top-level article**, else a visible `div[role="feed"]` containing one, else the document — an overlay with no post in it (chat, cookie consent, composer) MUST NOT capture the scope, or every note-scoped command would fail for as long as it is open; (2) candidate = a top-level article whose ancestor chain contains no other `[role="article"]` (excluding nested comment articles); (3) identity = the candidate's card-header canonical post id equals the command's. Resolving zero MUST return `no_target`; resolving more than one at the same level MUST return `ambiguous_target`. The edge MUST NOT fall back to the DOM-order first article, first reaction control, or first editor under any circumstance. Using the document as a scope is not such a fallback: an identity match remains mandatory in every scope.

#### Scenario: Feed-context like targets the commanded card, not the first one

- **WHEN** a like command carrying the Nth card's canonical post id arrives while the page shows a multi-article feed
- **THEN** only the Nth card's post-level reaction control is acted upon
- **AND** the first card's reaction state is unchanged

#### Scenario: Detail dialog with nested comment articles locks the main post only

- **WHEN** a permalink detail dialog contains the main post article plus per-comment `[role="article"]` nodes and a background feed card sharing the same key
- **THEN** three-stage resolution locks the top-level main post article only
- **AND** it does not resolve to a comment article or return `ambiguous_target`

### Requirement: Like verification is bound to the acted-upon card

The edge MUST perform like location, click, and post-verification against the same article: it MUST tag the resolved article with a transient operation marker, and post-verification MUST read only the node carrying that same marker and re-derive its canonical post id to equal the command's. Native Feed initial actuation MUST freshly resolve the target and invoke the unique structural post-level reaction control with its in-page DOM `click()`; it MUST NOT convert this primary control into a generic coordinate click. A reaction-count control (for example `赞：N位用户`) MUST never be treated as a like toggle, and post-level versus comment-level reaction disambiguation MUST be structural: the react control belongs directly to the target card, shares an action bar with one post-level comment control, and is not inside a nested `[role="article"]` or reaction-summary toolbar.

If the tagged node is gone or its identity changes after dispatch, the edge MUST return `verify_indeterminate` and MUST NOT retry the click. If the same tagged card remains but its unique reaction control does not expose a positive reacted state within the bound, the edge MUST return `state_unchanged`; absence of a positive state MUST NOT be promoted to success. The marker MUST be cleared best-effort at terminal completion.

#### Scenario: Disappearing target is not reported as a successful like

- **WHEN** the tagged target article is removed from the DOM between click and verification
- **THEN** the edge returns `verify_indeterminate`
- **AND** it does not report the like as reacted and does not click again

#### Scenario: Recycled target identity is not accepted

- **WHEN** the tagged article remains in the DOM but its canonical post identity changes after dispatch
- **THEN** the edge returns `verify_indeterminate`
- **AND** it does not rebind verification to a replacement card carrying the original identity

#### Scenario: Reaction summary does not capture the primary commit

- **WHEN** the exact card contains a reaction-count control plus one post-level reaction control sharing the action bar with its comment control
- **THEN** Native Feed like invokes only the post-level control through its DOM click handler
- **AND** no primary CDP coordinate click is dispatched

#### Scenario: Same card never exposes a positive reaction

- **WHEN** the DOM click was dispatched and the tagged card keeps the commanded identity but its unique post-level control remains neutral through the bounded verification
- **THEN** the edge returns `state_unchanged`
- **AND** it does not report success or repeat the primary DOM click

### Requirement: Comment editor is scoped to the target article

The comment editor lookup MUST be narrowed to the target post resolved from the command's canonical post id: first the target article's own subtree; and, because Facebook commonly renders a post's comment box as a sibling of its article rather than inside it, otherwise the target post's **exclusive region** — the largest ancestor of the target article that contains no other top-level article **anywhere in the document**, never climbing above the scope root — taking only editors in that region that lie outside every `[role="article"]` (so a comment's reply box can never receive a post-level comment) and only when that region yields **exactly one** such editor. When no editor is resolved this way, the edge MUST return `editor_not_found` and MUST NOT fall back to the document-first editor. Computing the exclusive region against only the current scope, or letting it climb to `document.body`, MUST NOT happen: with the target post open in a dialog over the feed, that admits the background feed's inline editors and a comment is written under someone else's post.

Post-submission confirmation MUST be scoped the same way: it MUST NOT fall back to the DOM-first article or to a URL-substring match, and it MUST NOT degenerate to treating the whole post article as a comment row — an un-submitted draft still sitting in the editor, plus the author's own avatar link and the post's own action bar, would otherwise satisfy every confirmation signal and report a comment that was never posted.

#### Scenario: Multi-editor page does not misfire into another post

- **WHEN** the page contains contenteditable comment editors belonging to several posts
- **THEN** input is focused into the editor within the target post's scope
- **AND** if that scope has no editor, the edge returns `editor_not_found` without using another post's editor

#### Scenario: Target post open in a dialog over the feed

- **WHEN** the target post is open in a `[role="dialog"]` while the feed behind it still renders other posts with their own inline comment editors
- **THEN** only the target post's editor is eligible
- **AND** the edge never focuses or types into a background post's editor

#### Scenario: Nothing was submitted, nothing is confirmed

- **WHEN** the comment text is still sitting in the editor and the target post has no comment rows yet
- **THEN** in-place acknowledgement MUST NOT be confirmed
- **AND** the edge MUST NOT report the comment as posted

### Requirement: Target is scrolled into view before acting

Before locating the reaction control, the edge MUST bring the target's unique post-level reaction control into view with a bounded, humanized scroll: read the exact target and control position, step incrementally with human-like wheel deltas, re-resolve and re-scan each step, and stop within bounded rounds/time. Merely bringing the article top into view is insufficient because a long card's action bar and its reaction picker can remain below the viewport. The edge MUST NOT use unconditional instant centering. If the target or structural control disappears, changes identity, remains ambiguous, or cannot be brought into view within the bound, the edge MUST return a truthful not-started reason and MUST NOT act on whatever is currently centered.

#### Scenario: Off-screen target control is reached without teleporting

- **WHEN** the exact target article is in the DOM but its post-level reaction control is below the viewport
- **THEN** the edge uses bounded humanized steps and fresh exact-card reads until the control is in the eligible viewport band before committing
- **AND** it does not instant-center the article or act on another visible card

#### Scenario: Target control cannot be brought into view

- **WHEN** bounded scrolling ends without one visible structural reaction control on the exact card
- **THEN** the edge returns a not-started visibility or target failure
- **AND** it dispatches neither the primary DOM click nor a picker coordinate click

### Requirement: Feed 两步点赞的反应浮层提交是 scoped 的、走真指针事件、且目标须在视口内

当 feed 态单击帖级中性反应控件（如「留下心情」）只弹出反应选择器浮层、按钮不翻转时，边缘 SHALL 补第二步在浮层里点「赞」项提交。该第二步 MUST 同时满足以下四条不变量，否则会点错帖、或点了不生效、或点在屏外空处：

1. **绑定同一个仍有效的 Feed like operation**：浮层探针 MUST 要求对应 operation marker 仍绑定在命令目标卡上且身份未变化；缺少、错误或过期 operation id 时 MUST 返回不可提交，MUST NOT 使用页面上恰好可见的无关 reaction dialog。

2. **作用域限定在打开的反应浮层内（scoped，绝不全文档搜索）**：定位「赞」反应项 MUST 只在**一个可见的反应选择器浮层容器**（`[role="dialog"]` 等、且其内含 ≥2 个反应项）内部进行，MUST NOT 在整个 document 里搜第一个 `aria-label` 为「赞」的按钮。理由：feed 里**每张卡的中性 Like 按钮 aria-label 也恰是「赞」**（反应计数汇总按钮亦然），而浮层是 portal、document 序排在**所有 feed 卡之后**——全文档搜第一个「赞」在目标**非首卡**时会命中**上方另一张卡**的 Like 按钮，既点错了别的帖（违反 note-scoped「绝不点错卡」红线），目标帖的浮层又永不提交（verify 恒 `state_unchanged`）。含 ≥2 反应项这道闸 SHALL 排除「反应人数查看」toolbar（其项形如「赞：N位用户」，MUST NOT 被当成可点的「赞」反应项）。

3. **浮层反应项走 CDP 坐标点击、绝不 in-page `element.click()`**：提交 MUST 用 CDP 坐标点击（从已标记目标卡的帖级 react 控件出发，随后 `mousePressed`/`mouseReleased`），MUST NOT 用页面内 `element.click()`。为防指针路径中途离开浮层 hover 区致其收起，移动起点 SHALL 是同一 operation 下目标 react 控件的当前坐标，且 MUST NOT overshoot。

4. **坐标点击目标须在可视视口内**：由于坐标点击只对可视区内的元素有效，滚动定位 MUST 把**帖级 react 控件**（而非仅文章顶部）带进可视视口，使其上方渲染的浮层落在屏内。定位浮层「赞」项后，若其中心坐标越出视口，边缘 MUST NOT 派发屏外坐标点击，SHALL 诚实回 `state_unchanged`，MUST NOT 静默假成功。

两步 SHALL 只补一次（防对已提交的赞二次点成撤销）。detail 态（单击即翻转、不弹浮层）MUST NOT 触发第二步，逐位不变。

#### Scenario: 目标非首卡时反应浮层「赞」项只翻转目标卡、不点到别卡
- **WHEN** 一条 like 命令携带信息流中**非首位**卡的 canonical 帖身份，单击其中性控件后弹出反应浮层，而上方其它卡也各有 `aria-label` 为「赞」的 Like 按钮
- **THEN** 边缘只在绑定该 operation 的目标卡仍有效时，在唯一浮层容器内定位并点击「赞」反应项，仅目标卡翻转为已赞态，MUST NOT 点到上方任何别的卡的 Like 按钮

#### Scenario: 错误或缺失 operation 不接管无关浮层
- **WHEN** 页面存在一个可见 reaction dialog，但请求的 Feed like operation marker 缺失、已过期或属于另一张卡
- **THEN** 浮层探针返回不可提交
- **AND** 边缘不派发任何 picker 坐标点击

#### Scenario: 浮层反应项用坐标点击提交、in-page click 视为未提交
- **WHEN** 需在反应浮层里点「赞」项提交
- **THEN** 边缘从同 operation 的目标 react 控件坐标出发，对浮层项中心派发 CDP `mousePressed`/`mouseReleased`，MUST NOT 依赖页面内 `element.click()`；提交后 verify 读到目标卡翻转（`isReactedState` 命中「移除赞」等串）才回 ok

#### Scenario: 浮层落在折叠线以下时先把 react 控件滚进视口
- **WHEN** 目标是长帖、其 Like 按钮或浮层落在可视视口以下
- **THEN** 边缘先把帖级 react 控件滚进视口再开浮层点击；若浮层「赞」项坐标仍越出视口，MUST 回 `state_unchanged`，MUST NOT 对屏外坐标空点、MUST NOT 假成功

### Requirement: Reel follow commands carry and enforce canonical note identity

`facebook.user.follow` MAY carry an optional `noteId` for Reel execution. When the Facebook session is in Reels mode, `noteId` MUST be present and MUST resolve to the canonical `https://www.facebook.com/reel/<id>` identity currently reported by the active Reel reader. The Edge MUST re-check this identity immediately before acting and MUST NOT treat `authorId`, current DOM order, or a generic Follow label as a substitute. Existing non-Reel follow callers that use `authorId` remain wire-compatible.

#### Scenario: Delayed follow command cannot hit the next Reel
- **WHEN** Cloud sends a follow command for Reel A but Reel B is active when Edge reaches the command
- **THEN** Edge returns `no_target` and performs zero clicks
- **AND** Reel B's author is not followed

#### Scenario: Existing profile follow payload remains compatible
- **WHEN** a non-Facebook-Reels caller sends the existing `{platform}.user.follow` payload with `authorId` and no `noteId`
- **THEN** protocol decoding remains valid
- **AND** the existing non-Reel execution path is unchanged

### Requirement: Facebook comment context is read from the same canonical target article

After a Facebook comment target permalink is opened, Edge SHALL derive the requested canonical post ID and resolve exactly one target card through the same scoped identity helper used by comment-editor and verification targeting. The post caption, bounded nested-comment sample, and editor readiness MUST be read from that resolved target and its exclusive region only. Background feed cards, an earlier dialog, nested comment articles, or DOM-order first articles MUST NOT contribute composition context.

If the requested target resolves to zero or multiple cards, or content extraction cannot remain bound to the requested identity, Edge MUST return `target_context_mismatch` (or an equivalently explicit non-success) and MUST NOT emit `note.detail`, request approval, focus an editor, or submit.

#### Scenario: Dialog target ignores the background feed's first post
- **WHEN** the requested post is open in a detail dialog while a different background feed post appears earlier in document order
- **THEN** the emitted caption and sampled comments come only from the requested dialog post
- **AND** the background feed post contributes no generation context

#### Scenario: Ambiguous target does not create an approval request
- **WHEN** two same-scope cards resolve to the requested canonical post ID or no card resolves to it
- **THEN** Edge reports an explicit target-context non-success and Cloud does not compose or create an approval request

#### Scenario: Read root and write root remain identical
- **WHEN** a Facebook comment proceeds from target reading through editor lookup and submission
- **THEN** caption/comments, editor, and post-submit verification are all scoped by the same canonical post identity

#### Scenario: Portal editor is uniquely covered by the canonical target card
- **WHEN** Facebook renders the post-level comment editor outside the target card DOM subtree
- **AND** the editor's rendered center is covered by exactly one physical post card whose canonical identity is the requested target
- **THEN** Edge MAY bind that unique editor to the target
- **AND** any overlap with another card, multiple candidate editors, or missing canonical target MUST return an explicit non-success without submitting

### Requirement: Reel like commit uses per-control event semantics and remains bound to the active Reel

For a Facebook like command targeting a canonical `/reel/<id>` identity, Edge MUST freshly resolve exactly one supported primary reaction control associated with the uniquely active video immediately before the write and MUST confirm that the current canonical Reel still equals the commanded identity. The primary React control SHALL be activated against the freshly resolved in-page element rather than by consuming a stale saved coordinate. Edge MUST then verify a positive selected-state witness on the same Reel.

If the primary activation does not produce a selected-state witness but opens a visible reaction picker, Edge MAY perform exactly one second-stage commit. It MUST locate a unique supported Like item only inside a unique visible picker containing multiple recognized reaction items, MUST reject ambiguous or off-screen picker targets, and MUST dispatch trusted CDP pointer events to that picker item. Edge MUST NOT search the whole document for a bare Like label and MUST NOT dispatch a second primary activation.

Across both direct-toggle and picker layouts, Edge MUST dispatch at most one primary activation and at most one picker commit. Same-Reel positive unlike/remove, `aria-pressed`, `aria-checked`, or supported reacted-word state MAY prove success; a reaction count, generic image descendant, dispatched event, or opened picker MUST NOT. Reel movement or target ambiguity after a write SHALL return `verify_indeterminate` without another click. An unchanged or unproven state SHALL return `state_unchanged`, and neither outcome may be recorded, budgeted, or displayed as a successful like.

#### Scenario: Fresh primary activation directly selects Like

- **WHEN** the commanded Reel is still uniquely active and its supported primary reaction control directly changes to a positive selected state after fresh in-page activation
- **THEN** Edge returns `ok:true` for that same Reel after one primary activation and dispatches no picker click

#### Scenario: Primary activation opens the reaction picker

- **WHEN** the commanded Reel remains uniquely active, the primary activation does not select Like, and one visible reaction picker contains multiple recognized reactions with one visible Like item
- **THEN** Edge dispatches one trusted pointer click to that picker-scoped Like item and returns success only after the same Reel exposes a positive selected-state witness

#### Scenario: Bare Like controls outside the picker are never fallback targets

- **WHEN** the document contains other controls whose label is Like while the active Reel picker is absent, ambiguous, or lacks a unique visible Like item
- **THEN** Edge dispatches no second-stage click outside the picker and returns a truthful non-success result

#### Scenario: Reel moves after the primary write

- **WHEN** the canonical active Reel or its unique active-video association changes after the primary activation and before confirmation
- **THEN** Edge returns `verify_indeterminate`, dispatches no picker or replacement primary click, and does not report success

#### Scenario: Dispatched events without selected state are not success

- **WHEN** Edge dispatches the bounded primary and optional picker events but reads no same-Reel positive selected-state witness
- **THEN** Edge returns `state_unchanged` and Cloud does not consume successful-like quota or display a successful like

### Requirement: Native Reel interactions preserve exact-target platform semantics

For a Facebook like or follow command targeting a canonical Reel, the Native-only Edge runtime MUST freshly resolve the uniquely active video and MUST bind every eligible control and post-condition to that same canonical Reel. Control resolution MUST support the established multilingual neutral/reacted and follow/following label families, including author-qualified accessible labels, while excluding reaction counts, comment/reply/share controls, unrelated post controls, and controls associated with another visible Reel. Reel like resolution MUST retain the established bounded action-rail size and right-side geometry invariants. The runtime MUST NOT restrict resolution to the video's nearest DOM parent when the action rail or author CTA is rendered in a structurally separate sibling branch, and MUST NOT fall back to the first matching control in document order.

Before a like write, Native MUST freshly resolve and activate the supported primary React control at most once. If that activation opens a reaction picker, Native MAY dispatch at most one trusted pointer commit to a unique visible Like item inside a unique visible multi-reaction picker associated with the same active Reel. Success MUST require an explicit selected-state witness on the same Reel: `aria-pressed`/`aria-checked`, an unlike label, or the established bounded reacted label/text transition. Generic CSS class names MUST NOT prove selection. These Reel-only semantics MUST NOT change the existing Feed target/state classifier. Follow MUST require a non-empty author suffix with exactly one nearby visible author witness, MUST freshly re-resolve and compare canonical note identity, video key, and author immediately before dispatch, MUST dispatch at most one trusted pointer click, and MUST require the same three identities to expose an established following-state witness.

Pre-dispatch target/control absence or ambiguity MUST remain not-started. Movement, target loss, or unproven state after dispatch MUST remain ambiguous and MUST NOT be displayed, budgeted, or recorded as a successful interaction.

#### Scenario: Reel action rail is a sibling of the video root

- **WHEN** the uniquely active canonical Reel renders its like and follow controls in a visible sibling action rail rather than inside the video's nearest article or parent
- **THEN** Native resolves only the controls spatially and semantically bound to that Reel
- **AND** it does not return control-not-found merely because the controls are outside the nearest DOM root

#### Scenario: Real multilingual CTA variants remain eligible

- **WHEN** the active Reel exposes a neutral reaction label such as `留下心情` or `Bày tỏ cảm xúc Thích…`, or an author-qualified follow label such as `关注<author>` or `Follow <author>`
- **THEN** Native classifies the control using the established Facebook semantic label families
- **AND** count controls, following-state controls, and unrelated buttons remain excluded from a write target

#### Scenario: Primary activation opens a reaction picker

- **WHEN** one fresh primary activation leaves the same Reel unselected and opens one visible multi-reaction picker
- **THEN** Native dispatches at most one trusted pointer click to the unique picker-scoped Like item
- **AND** reports success only after the same Reel exposes a positive selected-state witness

#### Scenario: Reel moves after a write

- **WHEN** the canonical active Reel, active video identity, or bound control is lost or changes after like or follow actuation
- **THEN** Native returns an ambiguous non-success result without another primary click
- **AND** the interaction is not counted or displayed as successful

#### Scenario: Nearby discussion control resembles the Reel Like control

- **WHEN** a comment, reply, or sharing region contains the only visible neutral Like label near the active Reel
- **THEN** Native excludes that control and dispatches zero clicks
- **AND** the command remains not-started rather than targeting the discussion control

#### Scenario: Generic CSS class resembles selected state

- **WHEN** a neutral Reel Like control has a generic class such as `active` or `selected` without an explicit selected-state witness
- **THEN** Native does not report the Reel as already liked or confirmed

#### Scenario: Follow author changes before dispatch

- **WHEN** the fresh pre-dispatch Follow probe has a different canonical Reel, video key, or author from the initial probe
- **THEN** Native dispatches zero pointer writes and returns a not-started non-success result

### Requirement: Native Facebook action receipts retain bounded terminal diagnostics

For every Native Facebook action receipt, Edge MUST retain a local bounded diagnostic containing the action, final `ok` value, effect phase, and terminal reason token when present. The diagnostic MUST NOT contain page body text, comment content, cookies, credentials, or unbounded URLs, and it MUST NOT change the Edge-Cloud protocol payload.

#### Scenario: Pre-dispatch Reel control failure is diagnosable

- **WHEN** a Reel like or follow command terminates before actuation because its exact target or supported control cannot be resolved
- **THEN** the local Edge log records the action, `not_started` effect phase, and bounded reason token
- **AND** Cloud still receives the existing honest `action.completed{ok:false,reason}` payload

