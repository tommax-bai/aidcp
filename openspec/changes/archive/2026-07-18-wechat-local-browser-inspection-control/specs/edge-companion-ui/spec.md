## ADDED Requirements

### Requirement: Video-channel overview prioritizes engine and authentication over browser state

The video-channel interaction overview SHALL present environment engine connectivity and WeChat Channels authentication as the primary status pair. Browser state SHALL be presented only in a secondary manual-inspection area and an unconfirmed browser state MUST NOT visually replace or obscure the primary engine/authentication state.

The manual "打开浏览器" action SHALL remain visible for a valid selected local WeChat Channels environment regardless of the engine lifecycle state or WeChat authentication state. Its success copy SHALL state that browser visibility is auxiliary and that authentication remains determined by the separate WeChat status.

#### Scenario: Engine and authentication are healthy

- **WHEN** the environment engine is running and Cloud-connected and WeChat authentication is active
- **THEN** the overview shows primary success states for both "引擎" and "视频号"
- **AND** browser state and "打开浏览器" appear in the secondary manual-inspection area

#### Scenario: Browser state is unconfirmed while core states are known

- **WHEN** browser state is unconfirmed but engine connectivity and WeChat authentication have known values
- **THEN** the known engine and authentication values remain the primary status display
- **AND** browser state is labeled as an auxiliary unconfirmed report rather than the workspace's main blocker

#### Scenario: Engine is stopped or authentication needs login

- **WHEN** the selected local WeChat Channels environment's engine is stopped or its authentication is not active
- **THEN** the primary chips truthfully show those states
- **AND** "打开浏览器" remains available without enabling or starting the engine
