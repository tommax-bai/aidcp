## MODIFIED Requirements

### Requirement: Ordered trusted-input navigation
The Facebook Reels driver SHALL freshly resolve one unique active video and one unambiguous navigation axis before input. It SHALL dispatch exactly one trusted axis-specific forward key per `page.scroll`: ArrowDown for a vertical layout or ArrowRight for a horizontal layout. It MUST NOT dispatch a wheel gesture, click a next control, try the opposite axis, or append another write in the same command. A later command SHALL perform a new probe and MUST NOT be blocked by a prior command's identity or transition result.

#### Scenario: ArrowDown presents a canonical vertical Reel
- **WHEN** a freshly proven vertical layout receives ArrowDown and bounded post-actuation observation resolves a different canonical Reel
- **THEN** the driver SHALL report that Reel and SHALL dispatch no other input

#### Scenario: ArrowRight presents a canonical horizontal Reel
- **WHEN** a freshly proven horizontal layout receives ArrowRight and bounded post-actuation observation resolves a different canonical Reel
- **THEN** the driver SHALL report that Reel and SHALL dispatch no other input

#### Scenario: Axis cannot be resolved
- **WHEN** the active video is unique but structural evidence cannot distinguish a vertical from horizontal navigation layout
- **THEN** the driver SHALL dispatch no input and SHALL return one honest pre-dispatch failure

#### Scenario: Prior failure does not block the next command
- **WHEN** one scroll command ends with missing, unchanged, or ambiguous canonical identity and Cloud later sends another admitted scroll command
- **THEN** the driver SHALL freshly probe and MAY dispatch that command's one trusted input without consulting a cross-command transition latch

### Requirement: Per-method movement proof
The one navigation actuation SHALL be followed by bounded observation of the freshly active Reel's canonical `noteId`. Input dispatch, document position, video coordinates, media URL, DOM element identity, and media-segment changes MUST NOT prove progress. For a canonically identified pre-state, success requires a different canonical post-state `noteId`; for an anonymous pre-state, success requires any canonical post-state `noteId`. If that proof does not appear, the command SHALL return one honest terminal failure and retain no transition state.

#### Scenario: Canonical identity changes after input
- **WHEN** the post-actuation active Reel has a canonical `noteId` different from the canonical pre-state
- **THEN** the driver SHALL report one fresh Reels card batch for the post-state

#### Scenario: Anonymous entry gains canonical identity after input
- **WHEN** the pre-state has no canonical `noteId` and the post-actuation active Reel gains one within the bounded window
- **THEN** the driver SHALL report that canonical Reel once

#### Scenario: Media or DOM changes without canonical progress
- **WHEN** media URL, media segments, or the active video DOM element changes while canonical `noteId` is missing or unchanged
- **THEN** the driver SHALL NOT report navigation success and SHALL NOT preserve that implementation change as later command state

#### Scenario: Canonical identity remains unresolved
- **WHEN** the bounded post-actuation window ends without an eligible canonical post-state `noteId`
- **THEN** the driver SHALL return an honest terminal failure and the next admitted command SHALL remain independently executable

## REMOVED Requirements

### Requirement: Randomized bounded wheel gesture
**Reason**: A fallback wheel is a second write whose safety previously depended on unstable active-video identity.

**Migration**: Each Reels scroll command now dispatches one axis-specific trusted key; later progress uses a new independently admitted command.

### Requirement: Fail-closed button fallback
**Reason**: Button fallback is removed with the within-command multi-actuator ladder.

**Migration**: Structural control analysis remains responsible for establishing the navigation axis, but no next control is clicked by Reels scrolling.
