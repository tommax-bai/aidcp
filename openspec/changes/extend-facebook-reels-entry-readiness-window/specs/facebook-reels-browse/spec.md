## ADDED Requirements

### Requirement: Facebook Reels entry allows thirty seconds of document readiness per navigation attempt

For every authorized Facebook Reels entry path, Edge SHALL allow each initial and existing optional retry `Page.navigate` attempt up to 30 seconds to observe an `interactive` or `complete` document on the exact bound page. The 30-second timer SHALL apply separately to each navigation attempt and SHALL remain separate from canonical Reel identity/card hydration. A ready document or route acknowledgement alone MUST NOT count as entry success; success SHALL still require the existing canonical `page.cards{listKind:'reels'}` postcondition. Cancellation, command deadline exhaustion, blocker state, or target/document drift MAY terminate the path earlier and MUST retain their existing fail-closed outcomes.

#### Scenario: Slow Reels landing becomes ready inside thirty seconds

- **WHEN** an authorized Reels entry navigation reaches an `interactive` or `complete` document after the former eight-second boundary but no later than 30 seconds
- **THEN** Edge continues with the existing Reels-surface and canonical-card verification instead of terminating the command at the former readiness boundary
- **AND** it does not count a Reel until canonical card evidence is available

#### Scenario: Optional retry uses the same readiness window

- **WHEN** the existing exact-target foreground recovery authorizes its one optional fresh Reels navigation retry
- **THEN** Edge gives that retry its own bounded 30-second document-readiness window
- **AND** it adds no further navigation retry

#### Scenario: Document remains unready after thirty seconds

- **WHEN** a Reels entry navigation still has no `interactive` or `complete` document at the end of its 30-second window
- **THEN** Edge returns the existing honest failure and does not fabricate route arrival, a Reel card, or a view

#### Scenario: Outer timeout chain remains larger than the entry path

- **WHEN** the two readiness windows and two possible canonical-card hydration windows are combined with explicit probe and receipt margin
- **THEN** the sum remains below the existing 180-second Facebook scroll request, admission, engine, and session ceilings
- **AND** Cloud retains its existing 240-second idle watchdog
