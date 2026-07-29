## ADDED Requirements

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
