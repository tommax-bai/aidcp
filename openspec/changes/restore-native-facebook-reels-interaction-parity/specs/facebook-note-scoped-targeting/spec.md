## ADDED Requirements

### Requirement: Native Reel interactions preserve exact-target platform semantics

For a Facebook like or follow command targeting a canonical Reel, the Native-only Edge runtime MUST freshly resolve the uniquely active video and MUST bind every eligible control and post-condition to that same canonical Reel. Control resolution MUST support the established multilingual neutral/reacted and follow/following label families, including author-qualified accessible labels, while excluding reaction counts, unrelated post controls, and controls associated with another visible Reel. The runtime MUST NOT restrict resolution to the video's nearest DOM parent when the action rail or author CTA is rendered in a structurally separate sibling branch, and MUST NOT fall back to the first matching control in document order.

Before a like write, Native MUST freshly resolve and activate the supported primary React control at most once. If that activation opens a reaction picker, Native MAY dispatch at most one trusted pointer commit to a unique visible Like item inside a unique visible multi-reaction picker associated with the same active Reel. Success MUST require a positive selected-state witness on the same Reel. Follow MUST dispatch at most one trusted pointer click to the unique author-bound Follow control and MUST require the same Reel to expose an established following-state witness.

Pre-dispatch target/control absence or ambiguity MUST remain not-started. Movement, target loss, or unproven state after dispatch MUST remain ambiguous and MUST NOT be displayed, budgeted, or recorded as a successful interaction.

#### Scenario: Reel action rail is a sibling of the video root

- **WHEN** the uniquely active canonical Reel renders its like and follow controls in a visible sibling action rail rather than inside the video's nearest article or parent
- **THEN** Native resolves only the controls spatially and semantically bound to that Reel
- **AND** it does not return control-not-found merely because the controls are outside the nearest DOM root

#### Scenario: Real multilingual CTA variants remain eligible

- **WHEN** the active Reel exposes a neutral reaction label such as `留下心情` or `Bày tỏ cảm xúc Thích…`, or an author-qualified follow label such as `关注<author>` or `Follow <author>`
- **THEN** Native classifies the control using the established Facebook semantic label families
- **AND** count controls, following-state controls, and unrelated buttons remain excluded from a write target

#### Scenario: Primary activation opens a reaction picker

- **WHEN** one fresh primary activation leaves the same Reel unselected and opens one visible multi-reaction picker
- **THEN** Native dispatches at most one trusted pointer click to the unique picker-scoped Like item
- **AND** reports success only after the same Reel exposes a positive selected-state witness

#### Scenario: Reel moves after a write

- **WHEN** the canonical active Reel, active video identity, or bound control is lost or changes after like or follow actuation
- **THEN** Native returns an ambiguous non-success result without another primary click
- **AND** the interaction is not counted or displayed as successful

### Requirement: Native Facebook action receipts retain bounded terminal diagnostics

For every Native Facebook action receipt, Edge MUST retain a local bounded diagnostic containing the action, final `ok` value, effect phase, and terminal reason token when present. The diagnostic MUST NOT contain page body text, comment content, cookies, credentials, or unbounded URLs, and it MUST NOT change the Edge-Cloud protocol payload.

#### Scenario: Pre-dispatch Reel control failure is diagnosable

- **WHEN** a Reel like or follow command terminates before actuation because its exact target or supported control cannot be resolved
- **THEN** the local Edge log records the action, `not_started` effect phase, and bounded reason token
- **AND** Cloud still receives the existing honest `action.completed{ok:false,reason}` payload
