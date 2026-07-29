# facebook-reels-navigation Specification

## Purpose
TBD - created by archiving change facebook-reels-navigation-fallbacks. Update Purpose after archive.
## Requirements
### Requirement: Ordered trusted-input navigation
The Facebook Reels driver SHALL resolve one unambiguous navigation axis before input and SHALL attempt only that axis's forward-navigation ladder. For a vertical layout the order SHALL be trusted ArrowDown input, one trusted downward wheel gesture, then the scoped vertical next-control click. For a horizontal layout the order SHALL be trusted ArrowRight input, then the scoped horizontal next-control click; the driver MUST NOT invent a horizontal wheel fallback. It SHALL stop the ladder as soon as a method proves any active-video transition and SHALL NOT execute later writes after success or after an observed transition awaiting canonical identity.

#### Scenario: ArrowDown moves a vertical Reel
- **WHEN** a structurally proven vertical layout receives ArrowDown and the active video changes to a canonically identified Reel
- **THEN** the driver SHALL report the new Reel and SHALL NOT send wheel or button input

#### Scenario: ArrowRight moves a horizontal Reel
- **WHEN** a structurally proven horizontal layout receives ArrowRight and the active video changes to a canonically identified Reel
- **THEN** the driver SHALL report the new Reel and SHALL NOT send wheel or button input

#### Scenario: Vertical wheel is the first successful fallback
- **WHEN** ArrowDown leaves the vertical Reel unchanged and the subsequent wheel gesture changes active-video identity
- **THEN** the driver SHALL report the new canonically identified Reel and SHALL NOT click the next control

#### Scenario: Axis-specific button is the first successful fallback
- **WHEN** the axis-specific key and any permitted vertical wheel leave the Reel unchanged and the freshly scoped next-control click changes active-video identity
- **THEN** the driver SHALL report the new canonically identified Reel

#### Scenario: Axis cannot be resolved
- **WHEN** the active video is unique but structural evidence cannot distinguish a vertical from horizontal navigation layout
- **THEN** the driver SHALL dispatch no keyboard, wheel, or pointer input and SHALL fail closed

### Requirement: Randomized bounded wheel gesture
The vertical-layout wheel fallback SHALL send exactly one positive integer delta selected from the inclusive range 70 through 100 pixels for that attempt. The driver MUST use trusted CDP mouse-wheel input over the freshly resolved active video and MUST NOT use DOM `scrollBy` as the fallback. A horizontal layout MUST NOT receive this wheel fallback.

#### Scenario: Lower random boundary
- **WHEN** the injected random source selects its lower boundary for a vertical layout
- **THEN** the emitted downward wheel delta SHALL be 70 pixels

#### Scenario: Upper random boundary
- **WHEN** the injected random source approaches or reaches its upper boundary for a vertical layout
- **THEN** the emitted downward wheel delta SHALL not exceed 100 pixels

#### Scenario: Horizontal layout skips wheel
- **WHEN** ArrowRight leaves a structurally proven horizontal Reel unchanged
- **THEN** the driver SHALL proceed only to a freshly scoped horizontal next control and SHALL emit no wheel event

### Requirement: Per-method movement proof
Every navigation method SHALL be followed by bounded observation against the pre-navigation canonical route when present and the stable active-video element/content identity. Viewport coordinates MUST NOT form the active-video identity because transition animation moves the existing element. Input dispatch alone MUST NOT be reported as navigation success. Any observed active-video transition SHALL suppress later writes; external success still requires a canonical post-transition Reel card.

#### Scenario: All methods leave identity unchanged
- **WHEN** all methods permitted for the resolved axis leave the original route and video identity unchanged
- **THEN** the driver SHALL return no next Reel and the session SHALL emit one honest post-dispatch failure receipt

#### Scenario: A prior method moves late
- **WHEN** the active-video identity changes before a fallback write is dispatched
- **THEN** the driver SHALL suppress that fallback and verify the moved-to Reel without another input

#### Scenario: Existing video moves during transition animation
- **WHEN** the same video element changes viewport coordinates but canonical route and stable video identity remain unchanged
- **THEN** the driver SHALL continue bounded verification and MUST NOT treat coordinate movement alone as a new Reel

#### Scenario: Video changes before route hydration
- **WHEN** a distinct active video is proven while canonical Reel identity is temporarily absent
- **THEN** the driver SHALL suppress all later inputs and wait within a bounded window for canonical identity
- **AND** if identity does not hydrate, it SHALL return an ambiguous failure and MUST NOT report or deduplicate a fabricated Reel

### Requirement: Fail-closed button fallback
The button fallback SHALL exclude page-header and in-video media controls and SHALL scope candidates relative to the freshly active video. It SHALL identify a vertical rail from predominantly Y-separated previous/next controls and select only its unique lower forward control, or identify a horizontal rail from predominantly X-separated controls on opposite sides of the video and select only its unique right forward control. Disabled previous controls MAY establish layout structure but MUST NOT be clicked. Semantic previous/next labels MAY identify roles, while an unknown candidate MUST belong to one unique structural pair. Ambiguous, single generic, moved, or axis-drifting controls MUST NOT be clicked.

#### Scenario: First vertical Reel with disabled previous control
- **WHEN** the previous control is disabled and a unique enabled next control forms one vertical rail with it beside the active video
- **THEN** the driver SHALL classify the layout as vertical and select only the lower enabled next control

#### Scenario: Horizontal previous and next controls
- **WHEN** one previous control is left of the active video and one enabled next control is right of it on the same horizontal rail
- **THEN** the driver SHALL classify the layout as horizontal and select only the right control

#### Scenario: Ambiguous next controls
- **WHEN** multiple credible axes or forward controls remain after semantic and structural scoping
- **THEN** the driver SHALL perform zero button clicks and SHALL return no next Reel

### Requirement: One view per presented Reel
Cloud SHALL record one `view` interaction for every single-card Facebook `page.cards` payload whose `listKind` is `reels`, because that single canonically identified active video has already been presented to the account. This accounting SHALL NOT depend on the content evaluator selecting the Reel for deeper reading or interaction. An anonymous `/reel/` bootstrap observation, an empty payload, or a malformed multi-card Reels payload SHALL fail closed without view accounting.

#### Scenario: Reel is skipped by content evaluation
- **WHEN** Edge reports one canonically identified active Reel and the content evaluator decides it is irrelevant to the persona
- **THEN** Cloud SHALL still record exactly one view before continuing to the next Reel

#### Scenario: Selected Reel later reports detail
- **WHEN** a presented Reel was already counted and its matching `note.detail` later arrives for quality or interaction appraisal
- **THEN** Cloud SHALL preserve the detail event but SHALL NOT record a second view for that Reel

#### Scenario: Normal feed detail remains unchanged
- **WHEN** a normal feed card reports `note.detail`, or the detail note id does not match the currently counted Reel
- **THEN** Cloud SHALL retain the existing detail-based view accounting

#### Scenario: Anonymous Reels landing observation
- **WHEN** Edge resolves one visible active video on `/reel/` but cannot derive a canonical Reel identity
- **THEN** Edge SHALL emit no card for that video and Cloud SHALL record no view

#### Scenario: Empty Reels report
- **WHEN** `listKind` is `reels` but no card is present
- **THEN** Cloud SHALL record no view

#### Scenario: View quota is reached after skipped Reels
- **WHEN** presented Reels have consumed the active view quota and content evaluation keeps rejecting them
- **THEN** the next shared scroll command SHALL enter the existing bounded view-quota sleep and SHALL NOT continue an unbounded Reel loop

### Requirement: Viewing does not force liking
Reel view accounting SHALL remain separate from like intent and confirmed like accounting. A like SHALL still require the existing content-quality, interaction-appraisal, risk, cooldown, target, and post-condition gates.

#### Scenario: Persona rejects a Reel
- **WHEN** a Reel is viewed but its content is rejected or skipped by the persona-bound evaluation chain
- **THEN** Cloud SHALL count the view and SHALL NOT fabricate or force a like

