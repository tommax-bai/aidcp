## MODIFIED Requirements

### Requirement: 昵称采集只在完整浏览器启动后的首个 feed 卡片触发

For XHS **and Facebook** accounts, cloud SHALL treat platform nickname capture as a startup-time browser readiness step. It MUST arm nickname capture only after a full browser startup or full browser restart reaches feed readiness and the first `page.cards` for that browser generation is observed. Cloud MUST NOT arm nickname capture on cloud hello, cloud WebSocket reconnect, cold-standby cloud recovery, or other transport-only lifecycle events. Each browser generation SHALL trigger nickname capture at most once.

采集**时机**跨平台统一（同一「首个 feed 卡片 / 浏览器代号」触发点、同一去重与有界重试）；采集**读法**按平台分叉——XHS 进本人主页读、Facebook 就地读（见 `facebook-identity`），二者共用同一触发、完成判定与持久化路径。触发的读法差异 MUST NOT 改变时机（何时武装、去重、重试上界、超时兜底对所有支持平台一致）。

#### Scenario: 完整浏览器启动后首个 page.cards 触发一次采集
- **WHEN** a full browser startup or full browser restart reaches the feed and edge reports the first `page.cards` for that browser generation
- **THEN** cloud arms and runs nickname capture once for that browser generation

#### Scenario: Facebook 与 XHS 同一时机触发
- **WHEN** 一个 Facebook 连接在完整浏览器启动后报出该代号的首批 `page.cards`
- **THEN** cloud 在该点武装一次本人昵称采集（与 XHS 同一触发/去重/重试语义），采集读法由 Facebook 平台就地读实现

#### Scenario: cloud reconnect 不触发昵称采集
- **WHEN** an existing browser/core session only reconnects the cloud WebSocket
- **THEN** cloud MUST NOT arm nickname capture solely because of hello/reconnect

#### Scenario: 冷待机内部恢复云连接不触发昵称采集
- **WHEN** an environment remains in cold standby and only cloud connectivity is recovering
- **THEN** cloud MUST NOT arm nickname capture and MUST NOT send profile navigation or recovery `back` commands for nickname capture

#### Scenario: 同一浏览器代次只采一次
- **WHEN** multiple `page.cards` events arrive for the same browser generation
- **THEN** nickname capture is armed at most once for that generation
