## MODIFIED Requirements

### Requirement: Video-channel overview prioritizes engine and authentication over browser state

The video-channel interaction overview SHALL present environment engine connectivity and WeChat Channels authentication as the primary status pair. Browser state SHALL be presented only in a secondary manual-inspection area and an unconfirmed browser state MUST NOT visually replace or obscure the primary engine/authentication state.

The manual "打开浏览器" action SHALL remain visible for a valid selected local WeChat Channels environment regardless of the engine lifecycle state or WeChat authentication state. Its default help copy SHALL be “仅用于人工查看，引擎以上方鉴权状态为准”. The desktop action SHALL occupy a visibly larger proportional width than a content-fit button while the narrow layout SHALL remain responsive. Dynamic success copy SHALL state that browser visibility is auxiliary and that authentication remains determined by the separate WeChat status.

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

#### Scenario: Manual inspection is idle on desktop

- **WHEN** no browser-open action notice is active and the workspace uses the desktop layout
- **THEN** the help copy is exactly “仅用于人工查看，引擎以上方鉴权状态为准”
- **AND** the browser action occupies 18% of the manual-inspection row with a usable minimum width

#### Scenario: Manual inspection is shown in a narrow window

- **WHEN** the workspace width reaches the narrow responsive breakpoint
- **THEN** the manual-inspection content and browser action stack vertically
- **AND** the browser action stretches within the available row without horizontal overflow

## ADDED Requirements

### Requirement: Electron client startup windows use a 900px default width

The Electron login window and authenticated main window SHALL each use 900px as their initial default width. Their existing minimum width, default height, minimum height, and native frame behavior SHALL remain unchanged.

#### Scenario: Client starts without a valid customer session

- **WHEN** the Electron client opens the login window
- **THEN** the login window initial width is 900px

#### Scenario: Client starts or proceeds with a valid customer session

- **WHEN** the Electron client opens the authenticated main window
- **THEN** the main window initial width is 900px
