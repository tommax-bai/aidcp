## MODIFIED Requirements

### Requirement: Environment rail avatar cycles select, show-on-primary, and re-park
Clicking an environment's rail entry SHALL act as a three-state control for that environment. The first click (on a not-yet-selected environment) selects it and highlights it with a distinct color. On the already-selected environment, the next click moves that environment's driven browser to the primary-screen inspection bounds and then restores the AIDCP companion as the foreground window, leaving the driven browser immediately below the client rather than covering it; the following click sends the browser back to its parked slot; further clicks continue to toggle between shown-below-client and parked. The selected-environment highlight MUST be visually distinct, and the shown state MUST be visually distinguishable from the merely-selected state. The show and re-park actions MUST reuse the existing per-environment control channel and MUST honestly surface failure; a failed or timed-out action (for example, the browser is not yet ready) MUST NOT advance the toggle phase. Switching to a different environment MUST reset the toggle phase. The persona icon on a rail entry MUST NOT trigger this toggle. Guided login and explicit browser recovery MAY continue to focus the driven browser because they express a different operator intent.

#### Scenario: First click selects with a distinct highlight
- **WHEN** the operator clicks a rail entry that is not currently selected
- **THEN** that environment becomes selected and is highlighted with the distinct selected color
- **AND** no browser show / re-park command is sent

#### Scenario: Second click shows the browser below AIDCP
- **WHEN** the operator clicks the already-selected environment's rail entry and its browser is parked
- **THEN** the companion moves that environment's browser to the primary-screen inspection bounds
- **AND** after the browser move completes, the AIDCP companion is restored to the foreground above it
- **AND** the rail entry reflects the shown state

#### Scenario: Third click re-parks the browser
- **WHEN** the operator clicks the already-selected environment's rail entry while its browser is shown below AIDCP
- **THEN** the companion requests that environment's browser return to its parked slot
- **AND** the shown state is cleared

#### Scenario: Honest failure does not advance the toggle
- **WHEN** a show or re-park request fails or times out because the environment's browser is not running/ready
- **THEN** the companion surfaces the failure
- **AND** the toggle phase does not advance

#### Scenario: Guided login still focuses the browser
- **WHEN** the operator uses the guided login or explicit recovery action because direct browser interaction is required
- **THEN** the companion MAY leave that driven browser in the foreground
- **AND** the avatar-specific below-client policy does not change that action

