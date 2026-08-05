## MODIFIED Requirements

### Requirement: Ordered trusted-input navigation

The Facebook Reels driver SHALL resolve one unique safe active video before input and SHALL determine a working keyboard actuator from verified active-Reel transition rather than requiring one structural navigation axis first. Fresh structural evidence MAY order the first key; otherwise a session-local previously verified key MAY be preferred, followed by a deterministic default order. Each of `ArrowRight` and `ArrowDown` SHALL be attempted at most once per command, with bounded observation and a fresh same-Reel pre-commit probe between them. The driver SHALL stop as soon as any method proves an active-video transition and SHALL NOT execute later writes after success or after an observed transition awaiting canonical identity. Only after both keys leave the original Reel unchanged MAY a freshly proven vertical layout use its trusted wheel and safe button fallbacks or a freshly proven horizontal layout use its safe button fallback; the driver MUST NOT invent a horizontal wheel fallback.

#### Scenario: ArrowRight discovers a working actuator

- **WHEN** `ArrowRight` changes the active video to a canonically identified Reel regardless of whether DOM structure had classified an axis
- **THEN** the driver reports the new Reel, prefers `ArrowRight` for later commands in that session, and sends no later input

#### Scenario: ArrowDown discovers a working actuator after ArrowRight misses

- **WHEN** `ArrowRight` leaves the exact Reel unchanged, a fresh same-Reel probe authorizes the next attempt, and `ArrowDown` changes active-video identity
- **THEN** the driver reports the new canonically identified Reel and prefers `ArrowDown` for later commands in that session

#### Scenario: A prior key moves late

- **WHEN** active-video identity changes after the first key but before the other key is committed
- **THEN** the driver suppresses the other key, wheel, and button input and verifies the moved-to Reel

#### Scenario: Both keys unchanged before a vertical fallback

- **WHEN** both keyboard directions leave the exact Reel unchanged and a fresh structural probe uniquely proves a vertical layout
- **THEN** the driver may continue with the existing bounded vertical wheel and safe-button ladder

#### Scenario: Axis cannot be resolved and neither key moves

- **WHEN** the active video is safe and unique, structural evidence cannot distinguish an axis, and both bounded key attempts leave its identity unchanged
- **THEN** the driver emits an honest post-dispatch ambiguous failure and dispatches no pointer or wheel fallback

### Requirement: Fail-closed button fallback

The button fallback SHALL exclude page-header, reaction, and in-video media controls and SHALL scope candidates relative to the freshly active video. Structural classification SHALL use viewport-normalized relationships among clipped visible control rectangles, the active video, and the viewport and SHALL provide only an input-order hint plus safe pointer-fallback evidence. Multiple, disabled, occluded, or otherwise inconclusive controls MUST NOT block bounded keyboard probing against one safe active Reel, but they MUST NOT authorize a pointer click. A vertical pointer fallback SHALL require one unique enabled lower forward control from a semantic outer-side rail. A horizontal pointer fallback SHALL require one unique enabled right forward control from an opposite-side rail. Unknown same-side controls MUST NOT authorize a vertical click; viewport-scale overlays and disabled controls MUST NOT be clicked. Pointer coordinates SHALL be exposed only for an enabled, fully visible, viewport-proportional control whose center-point hit test resolves to that control or its descendant. Any active-video or target drift before commit MUST suppress the click.

#### Scenario: Competing in-video next control does not block keyboard discovery

- **WHEN** one active Reel has a viewport-scale right-side next overlay plus a disabled in-video `Next items` control
- **THEN** the driver may still discover `ArrowRight` through verified transition and clicks neither control

#### Scenario: First vertical Reel exposes a safe lower control

- **WHEN** the previous control is disabled and one enabled next control forms a unique vertical rail beside the active video
- **THEN** the router may hint vertical input order and expose only the lower enabled next control for a later pointer fallback

#### Scenario: Reaction controls do not authorize a click

- **WHEN** two same-side controls with unknown or reaction semantics occupy positions that otherwise resemble an outer vertical pair
- **THEN** the driver exposes no pointer target while preserving bounded keyboard discovery

#### Scenario: Disabled or occluded forward control blocks only pointer fallback

- **WHEN** a structural forward control is disabled or not topmost at its center point
- **THEN** the driver emits no coordinates and never clicks it
- **AND** that control alone does not prevent verified keyboard probing against the safe active Reel

#### Scenario: Ambiguous next controls remain unclicked

- **WHEN** multiple credible forward controls remain after semantic and structural scoping
- **THEN** the driver performs zero button clicks and relies only on bounded verified keyboard probing
