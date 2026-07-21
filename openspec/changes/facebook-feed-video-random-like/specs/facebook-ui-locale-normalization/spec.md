## ADDED Requirements

### Requirement: Existing Vietnamese Facebook sessions use bounded exact post-action labels

While en-US remains the normative interface locale for provisioned Facebook environments, Edge SHALL support the exact verified Vietnamese post-level controls needed by existing localized sessions: neutral like `Thích`, selected/unlike `Gỡ Thích` and `Bỏ thích`, reacted word `Thích`, and comment `Viết bình luận`. Numeric reaction summaries such as `Thích: 27K người` MUST remain distinct from the neutral like toggle and MUST NOT be clicked as the action target. Missing or ambiguous labels MUST continue to fail closed.

#### Scenario: Vietnamese neutral like is clicked and verified
- **WHEN** one exact target card contains neutral `Thích` and the same card changes to `Gỡ Thích` after the click
- **THEN** Edge confirms the existing like success for that card

#### Scenario: Vietnamese reaction count is not the toggle
- **WHEN** a card contains both `Thích` and a numeric summary `Thích: 27K người`
- **THEN** Edge targets only the post-level neutral control and may parse the numeric summary as a count

#### Scenario: Vietnamese comment control anchors the post action boundary
- **WHEN** a lightweight video card contains `Viết bình luận` beside its like control
- **THEN** Edge may use it as the same-card action-boundary witness without interpreting caption text as a control

#### Scenario: Unknown localized state fails closed
- **WHEN** a localized card lacks every supported neutral/selected/comment witness or exposes multiple matching controls
- **THEN** Edge returns no target or ambiguous target and does not click by DOM order
