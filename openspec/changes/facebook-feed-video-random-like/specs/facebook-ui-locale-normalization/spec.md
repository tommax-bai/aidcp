## ADDED Requirements

### Requirement: Existing Vietnamese Facebook sessions use bounded exact post-action labels

While en-US remains the normative interface locale for provisioned Facebook environments, Edge SHALL support the exact verified Vietnamese post-level controls needed by existing localized sessions: neutral like `Thích`, selected/unlike `Gỡ Thích` and `Bỏ thích`, reacted word `Thích`, and comment `Viết bình luận`. The shared localized-control classifier MUST combine exact labels with their same-card structure. A neutral/selected candidate MUST share a bounded post action bar with exactly one supported post-level comment control and MUST NOT be inside a reaction-summary toolbar. Numeric text rendered inside an otherwise exact action control MUST NOT by itself demote the control. Numeric reaction summaries such as `Thích: 27K người`, and reaction-word controls inside a summary toolbar, MUST remain distinct from the neutral like toggle and MUST NOT be clicked as the action target. Scan identity, action location, and post-action verification MUST use the same classification semantics. Missing or structurally ambiguous controls MUST continue to fail closed.

#### Scenario: Vietnamese neutral like is clicked and verified
- **WHEN** one exact target card contains neutral `Thích` and the same card changes to `Gỡ Thích` after the click
- **THEN** Edge confirms the existing like success for that card

#### Scenario: Vietnamese reaction count is not the toggle
- **WHEN** a card contains both `Thích` and a numeric summary `Thích: 27K người`
- **THEN** Edge targets only the post-level neutral control and may parse the numeric summary as a count

#### Scenario: Vietnamese neutral action may render its count inside the button
- **WHEN** the same-card post action bar contains one control with exact label `Thích` and visible text `866`, beside one `Viết bình luận` control, while a separate summary toolbar exposes `Thích: 825 người`
- **THEN** Edge classifies the exact action-bar control as the unique neutral like target, keeps the summary distinct, and permits the strict video card identity

#### Scenario: Shared structural semantics apply across supported locales
- **WHEN** the equivalent post-action and summary layout uses a supported Chinese, English, Spanish, or Vietnamese neutral label
- **THEN** the same shared classifier distinguishes the action from the summary without a locale-specific DOM-order fallback

#### Scenario: Numeric reaction word without unique action structure is ambiguous
- **WHEN** an exact reaction word with numeric text is not uniquely bound to a post-level comment control or is inside a reaction-summary toolbar
- **THEN** Edge does not use it as the like target or as the strict video action witness

#### Scenario: Vietnamese comment control anchors the post action boundary
- **WHEN** a lightweight video card contains `Viết bình luận` beside its like control
- **THEN** Edge may use it as the same-card action-boundary witness without interpreting caption text as a control

#### Scenario: Unknown localized state fails closed
- **WHEN** a localized card lacks every supported neutral/selected/comment witness or exposes multiple matching controls
- **THEN** Edge returns no target or ambiguous target and does not click by DOM order
