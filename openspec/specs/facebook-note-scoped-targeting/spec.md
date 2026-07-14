# facebook-note-scoped-targeting Specification

## Purpose
TBD - created by archiving change facebook-note-scoped-targeting. Update Purpose after archive.
## Requirements
### Requirement: Facebook post identity is a canonical post id, not a URL

Facebook note-scoped targeting MUST key on a canonical post identity `fb:<postId>` derived from the card-header canonical link, where postId is taken from `posts/<id>`, `permalink/<id>`, `story_fbid`, `multi_permalinks`, the `pfbid` path segment, or the video id (`videos/<id>`, `reel/<id>`, `watch?v=`). Derivation MUST apply a post-permalink **shape whitelist** — a href that is not shaped like a post permalink (author profile links such as `/people/<slug>/pfbid…/`, photo links, group/page home links) MUST NOT derive an identity, because such links appear **before** the timestamp permalink in card-header DOM order and would otherwise define the card's identity as the author's. Derivation MUST also exclude `comment_id` / `reply_comment_id` links, links inside a nested `[role="article"]` (comment) subtree, and links inside share/attachment subtrees. Derivation that cannot produce a post id MUST return a null sentinel, never an empty string, so that a malformed href never compares equal to another and re-selects an arbitrary card. All matching, deduplication, and locating across the like and comment executors MUST use this one identity, replacing any divergent URL-pathname key. The identity MUST NOT be qualified by a container (group/page) segment: Facebook post ids are already globally unique, while a container derived from a page vanity slug in one link form and from a numeric page id in another would give the **same post two identities** and turn a legitimate command into a deterministic `no_target`.

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

The edge MUST perform like location, click, and post-verification against the same article: it MUST tag the resolved article with a transient marker, and post-verification MUST read only the tagged node and re-derive its canonical post id to equal the command's. If the tagged node is gone before verification, the edge MUST return `verify_indeterminate` and MUST NOT retry the click. The reaction-count numeric guard MUST be preserved so a count control (for example `赞：N位用户`) is never treated as a like toggle, and post-level versus comment-level reaction disambiguation MUST be structural (the react control shares an action bar with a comment/share sibling and is not inside a nested `[role="article"]`).

#### Scenario: Disappearing target is not reported as a successful like

- **WHEN** the tagged target article is removed from the DOM between click and verification
- **THEN** the edge returns `verify_indeterminate`
- **AND** it does not report the like as reacted and does not click again

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

Before locating the reaction control, the edge MUST bring the target article into view with a bounded, humanized scroll (read the target's position, step incrementally with human-like deltas, re-scan each step, bounded rounds/time), replacing any unconditional instant centering. If the target cannot be brought into view within the bound, the edge MUST return a truthful non-success reason rather than acting on whatever is currently centered.

#### Scenario: Off-screen target is reached without teleporting

- **WHEN** the target article is in the DOM but below the viewport
- **THEN** the edge scrolls to it with bounded humanized steps before locating its reaction control
- **AND** it does not instantly center-jump to it

