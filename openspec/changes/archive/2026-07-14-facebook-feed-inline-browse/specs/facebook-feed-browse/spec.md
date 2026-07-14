## ADDED Requirements

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
