## MODIFIED Requirements

### Requirement: Native Feed scanning preserves stateful continuation truth

The Native Facebook session SHALL distinguish canonical cards, visible unreportable articles, loading, explicit empty, explicit end-of-feed, and structurally exhausted Feed states. It SHALL use loading-aware card-set and document-height settling, continue downward for up to the established bounded rounds when visible articles lack trusted permalinks, and filter canonical identities already reported by that session. Native SHALL report `feed_exhausted` only after either a visible canonical-home end-of-feed marker is stable near the bottom or the established no-growth, near-bottom state remains stable for the complete confirmation window in consecutive rounds. Bounded round exhaustion without either proof MUST return a non-terminal continuation result and MUST NOT authorize or perform a Reels transition merely because the current viewport has no reportable permalink.

#### Scenario: Visible unreportable first viewport continues in Feed

- **WHEN** the initial Facebook Feed viewport contains visible hydrated articles but no trusted canonical permalink and a later bounded viewport contains a canonical card
- **THEN** Native scrolls within Feed, reports the later card, and does not emit explicit empty or navigate to Reels

#### Scenario: Loading zero-card viewport is not empty

- **WHEN** no canonical card is currently extractable and the Feed has an accessibility loading signal
- **THEN** Native waits within the bounded settle budget and, if still loading at the deadline, returns a retryable loading/no-target result rather than an empty card batch

#### Scenario: Recycled cards are not reported as new

- **WHEN** virtualized Feed scrolling renders canonical post identities already reported in the same Native session
- **THEN** Native filters those identities and continues the bounded search for new cards

#### Scenario: Delayed height growth cancels exhaustion

- **WHEN** a near-bottom round initially has no new canonical card but document height grows within the established in-place wait budget
- **THEN** Native resets exhaustion confirmation and continues the bounded search

#### Scenario: Stable explicit terminal marker confirms exhaustion

- **WHEN** a visible localized end-of-feed marker is observed consecutively on the canonical home Feed near the bottom with no new canonical card
- **THEN** Native reports `feed_exhausted` without requiring the marker to satisfy the stronger empty-home hint

#### Scenario: Exhaustion requires bounded structural evidence

- **WHEN** a scroll command finds no new canonical cards and no explicit terminal marker
- **THEN** Native reports `feed_exhausted` only after document height remains stable for the complete confirmation window, the page is near the bottom, and that state is confirmed in consecutive rounds

#### Scenario: Round limit is not terminal evidence

- **WHEN** the bounded scroll rounds finish after seeing only recycled cards but height growth, loading, or non-bottom position prevented terminal confirmation
- **THEN** Native returns `feed_continuation_unconfirmed` and MUST NOT report `feed_exhausted`
