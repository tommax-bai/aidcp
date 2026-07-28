## ADDED Requirements

### Requirement: First-post scroll continuation is measured and actuated on the element that actually scrolls

The bounded first-post scroll search SHALL move and measure the same scrolling element that the list probe already resolves. When the document itself does not scroll — the document scroll height equals the viewport height and the window scroll position stays at zero while an ancestor container of the feed holds the real scrollbar — the probe MUST NOT report window or document coordinates as its displacement and bottom evidence.

Exhaustion ("did not move and is at the bottom") SHALL be decided from that element's own metrics. The specified scroll budget MUST be spendable in full on such layouts; a layout that never scrolls the document MUST NOT cause the loop to exit after its first round.

#### Scenario: Group layout scrolls an inner container, not the document
- **WHEN** the first-post probe scrolls a group discussion stream whose real scrollbar is on an ancestor of the feed
- **THEN** the probe actuates that container and reports its displacement and bottom state
- **AND** the bounded scroll loop continues while that container still moves or is not at its bottom

#### Scenario: Ordinary window-scrolling layout is unchanged
- **WHEN** the document itself scrolls
- **THEN** displacement and bottom evidence come from the window as before
- **AND** the observable behaviour of the bounded scroll loop does not change

#### Scenario: Exhaustion is still reported honestly
- **WHEN** the resolved scrolling element neither moves nor has further content after the bounded rounds
- **THEN** the probe reports exhaustion
- **AND** it does not report a candidate it did not find

### Requirement: The first-post open budget chain is coherent from inner window to Cloud step

The first-post comment path SHALL size its identity readback window, its comment editor binding window, the enclosing Native command ceiling, and the Cloud first-post open step so that an inner window can be reached before any enclosing deadline fires.

Edge SHALL answer first: Cloud's step ceiling is a backstop only. Cloud MUST NOT fire before Edge's own ceiling plus transport slack, because doing so relabels an honest Edge outcome as a timeout and destroys the diagnosis without saving any comment.

The keyword-search open step keeps its existing ceiling; only the empty-keyword first-post step is widened. Group-join budgets are out of scope and MUST NOT be raised by this requirement.

#### Scenario: Slow but successful hydration completes inside the widened windows
- **WHEN** a group page hydrates the selected post's identity slower than the previous window allowed but within the widened one
- **THEN** Edge completes the identity readback and proceeds to compose and approve
- **AND** no enclosing deadline pre-empts it

#### Scenario: Enclosing ceiling never pre-empts an inner window
- **WHEN** the first-post path runs its worst-case sequence of navigation, bounded scrolling, editor binding and identity readback
- **THEN** the Native command ceiling for that command exceeds the sum of those windows
- **AND** the Cloud first-post step ceiling exceeds the Native ceiling plus transport slack

#### Scenario: Genuine failure is still reported honestly and promptly
- **WHEN** the selected post's identity or editor cannot be confirmed within the widened windows
- **THEN** Edge reports its own specific non-submit reason
- **AND** Cloud records that reason rather than a timeout

#### Scenario: Keyword search targeting is not widened
- **WHEN** a comment run supplies a search keyword
- **THEN** its open step keeps the previously established ceiling
- **AND** the widened first-post ceilings do not apply to it
