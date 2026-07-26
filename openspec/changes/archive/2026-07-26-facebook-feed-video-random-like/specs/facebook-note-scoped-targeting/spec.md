## MODIFIED Requirements

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
