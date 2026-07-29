## ADDED Requirements

### Requirement: Feed cards without a platform address carry a content-derived session reference

Facebook withholds post permalinks from the DOM. On some post kinds no permalink is obtainable without interaction at all. When a discovered Feed card carries no acceptable platform address, the Native session SHALL issue a content-derived session reference for it instead of discarding the card, reusing the existing evidence-and-digest mechanism rather than introducing a second one.

The reference SHALL be derived from card-local evidence that includes the author name, the normalised author profile path, the post body, stable in-card links, and image/video identifiers. Evidence MUST be recomputed and compared whenever the reference is resolved back to an element; a mismatch SHALL fail as a stale target rather than resolving to a different card. A reference that resolves to more than one element SHALL fail as ambiguous.

The reference SHALL be scoped to the active list surface and document generation. Leaving that surface or advancing to a new generation SHALL invalidate it. The reference MUST NOT be persisted, MUST NOT be reused across sessions, and MUST NOT be presented anywhere a permalink is expected.

#### Scenario: A permalinkless card becomes reportable

- **WHEN** a discovered Feed card exposes no acceptable platform address after the existing acquisition attempts
- **THEN** the session issues a content-derived reference for that card and reports the card, instead of dropping it

#### Scenario: Evidence drift fails instead of resolving elsewhere

- **WHEN** a reference is resolved after the underlying element has been recycled to a different post
- **THEN** recomputed evidence does not match, resolution fails as a stale target, and no action is taken on the recycled element

#### Scenario: Ambiguous resolution fails closed

- **WHEN** a reference resolves to more than one element on the page
- **THEN** resolution fails as ambiguous and no action is taken

#### Scenario: Surface or generation change invalidates the reference

- **WHEN** the active list surface changes, or the list advances to a new document generation
- **THEN** previously issued references are no longer resolvable and are not carried forward

### Requirement: Post identity kind is declared explicitly, never inferred from the value

Every reported Feed card SHALL declare which kind of identity it carries: a platform address, or a content-derived session reference. Consumers MUST decide capability from that declaration and MUST NOT infer it by inspecting the identity value's format. When the declaration is absent, consumers SHALL treat the identity as a platform address, so that an edge build predating this contract behaves exactly as it does today.

#### Scenario: Absent declaration means platform address

- **WHEN** a card arrives without an identity-kind declaration
- **THEN** it is treated as carrying a platform address and every existing behaviour applies unchanged

#### Scenario: Capability is not inferred from the string

- **WHEN** a consumer needs to decide whether a card may be navigated to
- **THEN** it reads the declared identity kind, and a consumer that inspects the identity string instead is a defect

### Requirement: Session references permit evaluation, view accounting and in-place liking only

A card identified by a content-derived session reference SHALL be eligible for content evaluation, for view accounting, and for in-place liking. In-place liking SHALL relocate the card by resolving the reference and SHALL confirm the outcome from the reaction control's observed state change, not from an identity comparison.

Such a card MUST NOT be navigated to, MUST NOT be opened as a detail page, MUST NOT be targeted by a directed comment, MUST NOT be handed to an operator as a link, and MUST NOT be used for cross-session deduplication. Cloud MUST NOT dispatch any address-requiring command against it; failing closed at the Edge is a backstop, not the contract.

#### Scenario: Evaluation and view accounting accept the reference

- **WHEN** a card carrying a session reference is reported
- **THEN** it is evaluated for content and counted as a view exactly as an addressed card would be

#### Scenario: In-place like confirms by control state

- **WHEN** an in-place like is requested against a session reference
- **THEN** the Edge relocates the card by that reference, actuates the reaction control, and confirms from the control's state change

#### Scenario: Navigation is never dispatched against a session reference

- **WHEN** the browse loop considers opening a post whose identity is a session reference
- **THEN** it does not dispatch a navigation or detail-open command for it

#### Scenario: A session reference is never handed to a human

- **WHEN** a post is queued for operator follow-up
- **THEN** a card carrying only a session reference is not queued, because the reference cannot be opened outside this session

### Requirement: Deduplication scope of session references is stated, not silently narrowed

Content-derived references deduplicate within their issuing session only. The same post encountered in a later session SHALL be counted again. This widening of the view-count meaning SHALL be stated in the browse accounting contract so it is not later diagnosed as a counting defect.

Reference collisions between genuinely distinct posts SHALL degrade to under-counting — the colliding post is treated as already seen — and MUST NOT cause an action to be taken against the wrong post, because every action re-resolves the reference and re-verifies evidence first.

#### Scenario: Same post in a new session counts again

- **WHEN** a post already viewed in an earlier session appears again in a new session
- **THEN** it is counted as a new view, and this is the defined behaviour rather than a defect

#### Scenario: A collision never misdirects an action

- **WHEN** two distinct posts produce the same reference
- **THEN** at most one is treated as already seen, and any action still re-resolves and re-verifies evidence before actuating
