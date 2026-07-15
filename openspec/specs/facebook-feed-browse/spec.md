# facebook-feed-browse Specification

## Purpose
TBD - created by archiving change facebook-feed-inline-browse. Update Purpose after archive.
## Requirements
### Requirement: Facebook feed stays continuous instead of reloading to top

The Facebook feed reader MUST make its feed navigation idempotent: it MUST skip the feed re-navigation only when the current URL equals the active feed URL, the feed is hydrated, and no blocking overlay is present, and it MUST otherwise re-navigate as today. Skipping re-navigation MUST NOT skip the blocking-overlay and login/captcha recheck, which run every scroll. Card scanning MUST report only newly-appeared top-level, non-nested, hydrated cards keyed by a session-level post-id-set cursor rather than a DOM-order watermark, so recycled top cards reappearing are not misread as new. When a scan yields no new cards, the edge MUST do a bounded continued scroll and, if still none, MUST honestly return an exhausted-feed signal.

#### Scenario: Scrolling does not reload the same first cards

- **WHEN** the account scrolls the Facebook home feed while already on the hydrated feed URL with no blocking overlay
- **THEN** the reader does not re-navigate to the top
- **AND** it reports only the newly-appeared top-level cards, and the safety front door still runs

#### Scenario: Exhausted feed is reported honestly

- **WHEN** bounded continued scrolling surfaces no new top-level cards
- **THEN** the edge returns an exhausted-feed signal rather than silently idling
- **AND** recycled top cards reappearing are not counted as new cards

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

