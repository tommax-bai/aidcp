## ADDED Requirements

### Requirement: 冷待机状态在云恢复期间必须保持待机语义

The Electron companion SHALL present browser cold standby as standby even when the cloud WebSocket is temporarily reconnecting or degraded. It MUST NOT replay ordinary startup activity, show repeated login/browse-start/browse-end events, or present the state as a generic engine crash while no browser wake has been requested.

#### Scenario: 冷待机云恢复中不显示重新登录循环
- **WHEN** an environment is in cold standby and cloud connectivity is reconnecting or degraded
- **THEN** the primary state remains cold standby, with cloud recovery as a subordinate detail
- **AND** the activity stream MUST NOT add synthetic or repeated "account ready / cloud connected / browse started / browse ended" entries unless a real browser startup and browsing session occurred

#### Scenario: 唤醒后才离开冷待机
- **WHEN** the scheduled wake time arrives or the operator manually resumes the environment
- **THEN** the companion may transition from standby into starting/running states and show real startup events from the new browser session
