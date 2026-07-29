## ADDED Requirements

### Requirement: Feed post identity is acquired by bounded trusted pointer movement

Facebook may withhold a Feed post's permalink from the DOM until a trusted pointer lands on that post's timestamp control. When a discovered Feed card carries no acceptable permalink, the Native session SHALL attempt to acquire one by dispatching a trusted pointer movement onto that card's identity candidate, then re-reading the card set. Acquisition SHALL run after the scan settles and before the scroll's terminal outcome is decided, so that a successful acquisition can still be reported as an ordinary card batch.

Acquisition SHALL dispatch pointer movement only. It MUST NOT dispatch pointer press or release, MUST NOT click, and MUST NOT otherwise produce any platform-visible write. Synthetic in-page events MUST NOT be used as a substitute, because the platform does not honour them.

Cards that already carry an acceptable permalink SHALL be skipped, since an acquired address persists for the remainder of the document generation.

#### Scenario: A card without a permalink gains one after acquisition

- **WHEN** a discovered home Feed card has no acceptable permalink and its identity candidate is inside the viewport
- **THEN** Native dispatches a trusted pointer movement onto that candidate, re-reads the card set, and reports the card through the normal Feed path once the permalink appears

#### Scenario: Acquisition never presses

- **WHEN** any acquisition attempt runs
- **THEN** the only input Native dispatches for it is pointer movement, and no press, release, click, or key event is dispatched on the candidate

#### Scenario: Already identified cards are not revisited

- **WHEN** a card already carries an acceptable permalink
- **THEN** Native performs no acquisition for that card

#### Scenario: Failed acquisition preserves today's honest outcome

- **WHEN** acquisition yields no permalink for any card in the round
- **THEN** the scroll falls through to its existing terminal classification unchanged, and Native neither fabricates an identity nor reports a card without one

### Requirement: Identity candidates are selected by structural evidence

An identity candidate SHALL be a link inside the card that resolves to the site root, is visible, lies inside the viewport, carries text content, contains no icon element, and carries no accessibility label. Controls implemented as links — such as the hide-post control, which is icon-only, labelled, and has no destination at all — MUST NOT be treated as identity candidates. When a card yields no candidate under these rules, Native SHALL perform no acquisition for that card rather than probing links indiscriminately.

Candidate geometry MUST be read immediately before each pointer movement. Coordinates captured in an earlier probe MUST NOT be reused, because lazy-loaded content inserted above the card invalidates them within seconds.

#### Scenario: The timestamp control is preferred over the hide control

- **WHEN** a card exposes both a wide short text link with no accessibility label and a square icon link carrying a hide-post label, both resolving to the site root
- **THEN** only the text link is treated as an identity candidate

#### Scenario: No candidate means no attempt

- **WHEN** every site-root link inside a card is icon-only or labelled
- **THEN** Native performs no acquisition for that card and records it as unresolved

#### Scenario: Stale coordinates are never used

- **WHEN** the card set is re-read between acquisition attempts and content shifts the card's position
- **THEN** the next pointer movement uses freshly read geometry, and a candidate that has left the viewport is skipped rather than targeted at its old position

### Requirement: Acquisition is bounded and degrades silently

Acquisition SHALL be bounded by a per-card candidate limit, a per-round card limit, and a per-round wall-clock limit. Reaching any limit SHALL end the acquisition round immediately; Native SHALL continue with whatever identities it already holds and MUST NOT retry within the same round. The wall-clock limit SHALL remain well below the Cloud idle watchdog interval so that a slow acquisition round can never be mistaken for a stalled session.

An acquisition failure MUST NOT fail the scroll. If the platform stops honouring pointer-driven identity disclosure entirely, the scroll SHALL behave exactly as it does today.

#### Scenario: Hitting a limit ends the round without retry

- **WHEN** the per-round wall-clock limit is reached mid-acquisition
- **THEN** Native stops acquiring, reports the cards it has already identified, and does not retry the remaining candidates in that round

#### Scenario: Unacquired cards remain eligible in a later round

- **WHEN** a card is skipped because a limit was reached
- **THEN** it remains eligible for acquisition when a later round brings it into the viewport again

#### Scenario: Platform withdrawal degrades to today's behaviour

- **WHEN** no candidate in a round yields a permalink
- **THEN** the scroll's outcome, receipts, and reason codes are identical to those produced without acquisition
