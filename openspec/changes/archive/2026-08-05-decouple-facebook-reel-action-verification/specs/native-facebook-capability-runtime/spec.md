## MODIFIED Requirements

### Requirement: Facebook capability owners preserve the complete platform transaction
Each state-changing Facebook capability SHALL own its complete `admit → locate → fresh revalidate → commit → same-target verify → classify` transaction. The target witness carried across that transaction MUST retain the canonical identity and association evidence required by the capability and MUST NOT be reduced to a stale coordinate. A live React element or operation marker used to establish the one-time commit or reaction-picker association MUST NOT become terminal verification authority when the same canonical target and current state can be freshly re-resolved. Established behavior that requires active-Reel/author association, current-group scope, or composer generation MUST remain proven through verification.

#### Scenario: React-owned control requires in-page activation
- **WHEN** recorded Facebook behavior requires fresh in-page activation of the current React-owned Feed Like, Reel primary Like, or Group Join element
- **THEN** the owning capability re-resolves that exact element at the commit boundary and invokes it once inside the Native browser router
- **AND** the generic engine does not replace that commit with a saved coordinate click

#### Scenario: Capability uses trusted pointer input
- **WHEN** recorded Facebook behavior requires pointer input for a unique scoped reaction-picker item or author-bound Reel Follow control
- **THEN** the owning capability validates the current target and returns one bounded pointer target for at most one dispatch
- **AND** verification remains bound to the same canonical post or Reel witness

#### Scenario: Same canonical Reel replaces an action control after dispatch
- **WHEN** a Reel write was dispatched once and Facebook replaces the clicked Like or Follow DOM node while the same canonical Reel and required author association remain freshly provable
- **THEN** the capability verifies the current action state from the freshly resolved replacement control within the existing bounded window
- **AND** it does not replay the commit or require the original DOM node to survive

#### Scenario: Target witness is lost after dispatch
- **WHEN** a write was dispatched but its canonical card or Reel identity, required author binding, current-group scope, or composer witness can no longer be proven
- **THEN** the capability returns an ambiguous non-success terminal result without replaying the commit
