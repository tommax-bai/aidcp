## ADDED Requirements

### Requirement: Facebook post identity is a canonical post id, not a URL

Facebook note-scoped targeting MUST key on a canonical post identity `fb:<container>:<postId>` derived from the card-header canonical link (container = group/page id; postId taken from `posts/<id>`, `story_fbid`, `multi_permalinks`, or the `pfbid` path segment). Derivation MUST exclude `comment_id` links, links inside a nested `[role="article"]` (comment) subtree, and links inside share/attachment subtrees. Derivation that cannot produce a post id MUST return a null sentinel, never an empty string, so that a malformed href never compares equal to another and re-selects an arbitrary card. All matching, deduplication, and locating across the like and comment executors MUST use this one identity, replacing any divergent URL-pathname key.

#### Scenario: Two same-group multi_permalinks posts do not collide

- **WHEN** two posts in the same group are rendered as `multi_permalinks`-form permalinks in the feed
- **THEN** each derives a distinct canonical post id
- **AND** a like command for one MUST NOT resolve to the other

#### Scenario: Malformed link yields no target, not the first card

- **WHEN** the only permalink-shaped href on a card is `javascript:` / a fragment / otherwise unparseable
- **THEN** canonical id derivation returns the null sentinel
- **AND** the command resolves to `no_target` while the DOM-first card is left untouched

### Requirement: Note-scoped actions resolve exactly one target article and never fall back to DOM order

For any note-scoped command (like, comment), the edge MUST resolve exactly one target `[role="article"]` using the command's canonical post id via a three-stage procedure: (1) scope = the last-opened visible `[role="dialog"]` if present, else `div[role="feed"]`; (2) candidate = a top-level article whose ancestor chain contains no other `[role="article"]` (excluding nested comment articles); (3) identity = the candidate's card-header canonical post id equals the command's. Resolving zero MUST return `no_target`; resolving more than one at the same level MUST return `ambiguous_target`. The edge MUST NOT fall back to the DOM-order first article, first reaction control, or first editor under any circumstance.

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

The comment editor lookup MUST be narrowed to the target article subtree resolved from the command's canonical post id. When there is no comment editor within that scope, the edge MUST return `editor_not_found` and MUST NOT fall back to the document-first editor.

#### Scenario: Multi-editor page does not misfire into another post

- **WHEN** the page contains contenteditable comment editors belonging to several posts
- **THEN** input is focused into the editor within the target article subtree
- **AND** if that subtree has no editor, the edge returns `editor_not_found` without using another post's editor

### Requirement: Target is scrolled into view before acting

Before locating the reaction control, the edge MUST bring the target article into view with a bounded, humanized scroll (read the target's position, step incrementally with human-like deltas, re-scan each step, bounded rounds/time), replacing any unconditional instant centering. If the target cannot be brought into view within the bound, the edge MUST return a truthful non-success reason rather than acting on whatever is currently centered.

#### Scenario: Off-screen target is reached without teleporting

- **WHEN** the target article is in the DOM but below the viewport
- **THEN** the edge scrolls to it with bounded humanized steps before locating its reaction control
- **AND** it does not instantly center-jump to it
