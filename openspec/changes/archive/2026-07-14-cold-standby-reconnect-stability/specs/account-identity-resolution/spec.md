## ADDED Requirements

### Requirement: 昵称采集只在完整浏览器启动后的首个 feed 卡片触发

For XHS accounts, cloud SHALL treat platform nickname capture as a startup-time browser readiness step. It MUST arm nickname capture only after a full browser startup or full browser restart reaches feed readiness and the first `page.cards` for that browser generation is observed. Cloud MUST NOT arm nickname capture on cloud hello, cloud WebSocket reconnect, cold-standby cloud recovery, or other transport-only lifecycle events. Each browser generation SHALL trigger nickname capture at most once.

#### Scenario: 完整浏览器启动后首个 page.cards 触发一次采集
- **WHEN** a full browser startup or full browser restart reaches the feed and edge reports the first `page.cards` for that browser generation
- **THEN** cloud arms and runs nickname capture once for that browser generation

#### Scenario: cloud reconnect 不触发昵称采集
- **WHEN** an existing browser/core session only reconnects the cloud WebSocket
- **THEN** cloud MUST NOT arm nickname capture solely because of hello/reconnect

#### Scenario: 冷待机内部恢复云连接不触发昵称采集
- **WHEN** an environment remains in cold standby and only cloud connectivity is recovering
- **THEN** cloud MUST NOT arm nickname capture and MUST NOT send profile navigation or recovery `back` commands for nickname capture

#### Scenario: 同一浏览器代次只采一次
- **WHEN** multiple `page.cards` events arrive for the same browser generation
- **THEN** nickname capture is armed at most once for that generation
