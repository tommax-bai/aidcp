## RENAMED Requirements

- FROM: `### Requirement: Environment rail avatar cycles select, show-on-primary, and re-park`
- TO: `### Requirement: Environment rail separates selection from exclusive browser recall`

## MODIFIED Requirements

### Requirement: Environment rail separates selection from exclusive browser recall

Clicking an environment's rail entry SHALL select that environment and highlight it with a distinct selected color; a single click MUST NOT show or re-park any browser. Double-clicking the environment avatar SHALL select that environment if necessary and request an exclusive browser recall: every other currently controllable environment browser SHALL be sent to its own configured parking position, then the target environment's fixed-size driven browser SHALL be centered on the AIDCP companion's current outer window bounds and the companion SHALL be restored above it. Repeating a double-click on the same avatar SHALL remain a recall intent and MUST NOT toggle the target back to parking. The shown target MUST be visually distinguishable from a merely selected environment. Nickname editing, persona controls, guided login, and explicit browser recovery MUST NOT be reinterpreted as this avatar gesture.

The exclusive recall SHALL use stable environment routing and bounded completion receipts. A failed target show MUST NOT advance the shown target. A superseded request MUST NOT overwrite a later request or display a stale failure. If the target is shown but one or more other controllable browsers fail to park, the client SHALL expose that incomplete parking result and MUST NOT claim that exclusivity was fully established.

#### Scenario: Single click only selects

- **WHEN** the operator single-clicks an environment rail entry
- **THEN** that environment becomes selected and highlighted
- **AND** no browser show or park command is sent, whether or not the environment was already selected

#### Scenario: Double-clicking another avatar performs one complete switch

- **WHEN** environment A is shown behind AIDCP and the operator double-clicks environment B's avatar
- **THEN** environment B becomes selected, environment A and every other controllable non-target browser are sent to their configured parking positions, and B is placed behind AIDCP
- **AND** B becomes the only shown target in renderer state

#### Scenario: Repeated target double-click is idempotent

- **WHEN** the operator double-clicks the avatar of the environment already shown behind AIDCP
- **THEN** the companion repeats or preserves that environment's recall placement
- **AND** it emits no request to park that target as a toggle side effect

#### Scenario: Latest rapid double-click determines the final target

- **WHEN** the operator double-clicks environment A and then environment B before A's placement completes
- **THEN** the operations cannot complete out of order with A as the final shown target
- **AND** B is the final browser placed behind AIDCP while the superseded result remains silent

#### Scenario: Partial non-target parking failure is honest

- **WHEN** the target browser is shown successfully but one or more other controllable browsers fail or time out while parking
- **THEN** the client identifies the incomplete parking result without claiming full exclusivity
- **AND** the target remains represented as shown

#### Scenario: Guided login still focuses the browser

- **WHEN** the operator uses guided login or explicit recovery because direct browser interaction is required
- **THEN** the companion MAY leave that driven browser in the foreground
- **AND** the avatar-specific exclusive recall policy does not change that action
