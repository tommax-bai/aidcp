## MODIFIED Requirements

### Requirement: Native Facebook Reels scrolling uses a surface-specific trusted actuator

When the Native-only Facebook runtime receives `page.scroll` while the observed list surface is Reels, the Edge SHALL resolve exactly one active video independently from canonical Reel identity and SHALL resolve exactly one structural navigation axis before dispatch. A vertical layout SHALL use bounded trusted CDP input in this order: ArrowDown, one small wheel over the freshly active video, then one geometrically constrained vertical next-button click. A horizontal layout SHALL use ArrowRight and then one geometrically constrained horizontal next-button click. The axis-specific keyboard input SHALL remain the first write when fresh structure proves one axis and the router explicitly reports the forward control as geometry-only pointer-unsafe. A missing, ambiguous, disabled, or occluded forward control MUST remain pre-dispatch. It MUST NOT use document `window.scrollBy`, a horizontal wheel guess, or both keyboard axes in one command. Before each fallback write, the Edge MUST freshly re-probe the active video and axis so late movement suppresses the next input.

#### Scenario: Anonymous landing Reel advances vertically

- **WHEN** `/reel/` has one active video without `noteId`, a vertical rail is uniquely resolved, and trusted ArrowDown changes to a different active video with canonical identity
- **THEN** the Edge reports the newly active Reel and does not dispatch wheel or button input

#### Scenario: Identified Reel advances horizontally

- **WHEN** one identified active Reel and a horizontal rail are uniquely resolved and trusted ArrowRight changes its stable identity
- **THEN** the Edge reports the newly active Reel and does not dispatch wheel or button input

#### Scenario: Axis-only horizontal evidence advances by keyboard

- **WHEN** viewport-normalized structure uniquely proves a horizontal rail but its forward overlay is not eligible for a pointer fallback
- **THEN** the Edge dispatches trusted ArrowRight as the first and only initial write
- **AND** it reports success only if the active-video transition and canonical next identity are proven

#### Scenario: Disabled forward control dispatches nothing

- **WHEN** the router reports a structurally related but disabled forward control
- **THEN** the Edge returns a pre-dispatch failure and emits no keyboard, wheel, or pointer input

#### Scenario: Occluded forward control dispatches nothing

- **WHEN** the router cannot prove that the forward control is topmost at its center point
- **THEN** the Edge returns a pre-dispatch failure and emits no keyboard, wheel, or pointer input

#### Scenario: Vertical keyboard is unchanged and wheel advances

- **WHEN** ArrowDown leaves the vertical Reel unchanged but one wheel over the freshly resolved active video changes its stable identity
- **THEN** the Edge reports the newly active Reel and does not click the next button

#### Scenario: Late movement suppresses a fallback write

- **WHEN** the active video changes after a prior attempt but before the next fallback input is committed
- **THEN** the fresh pre-commit probe accepts that transition, verifies canonical identity, and does not dispatch the fallback input
