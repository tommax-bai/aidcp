## ADDED Requirements

### Requirement: 首次连接与断线重连是两种处境，绝不共用一句话

The desktop client SHALL distinguish "this core run has never reached the cloud yet" from "this core run was connected and lost it". The status projection SHALL carry a per-core-run fact recording whether the cloud connection has ever been established on the current core process. A missing cloud connection MUST NOT be presented as "正在重新连接" unless that fact is true — the prefix「重」asserts a prior connection, and asserting one that never happened is a lie of the same family as treating "unknown" as "no".

The fact SHALL be reset to false whenever a new core process is spawned (including crash respawn and explicit restart), and set to true when the core reports the cloud connection is up. Cold-standby wake MUST NOT reset it: the cloud connection is held open across standby by design, so a woken core has indeed been connected.

#### Scenario: 冷启动全程呈现为启动中
- **WHEN** an environment is started and its core is still bringing the browser up — the core has printed log lines (so the engine is demonstrably alive) but has not yet reported the cloud connection
- **THEN** the client presents the environment as「启动中」throughout, and MUST NOT present it as「正在重新连接」

#### Scenario: 正常冷启动绝不冒充需要人工
- **WHEN** an environment is in that same first-connect window
- **THEN** the environment rail shows it at the launching level with no action needed, and it MUST NOT be raised to the attention level or floated to the top of the rail alongside genuine login / captcha / risk-control interventions

#### Scenario: 真正的断线仍然如实报重连
- **WHEN** the cloud connection has been established on the current core run and is subsequently lost while the session is running
- **THEN** the client presents「正在重新连接」at the attention level and marks it as needing attention

#### Scenario: 换核心即失去连上过的资格
- **WHEN** the core process is restarted (explicit restart, or respawn after a crash) — even though the previous core had connected
- **THEN** the new core run starts out having never connected, and its startup window is presented as「启动中」, not as「正在重新连接」

#### Scenario: 冷待机唤醒不退回未连接
- **WHEN** an environment wakes from cold standby, where the cloud connection was deliberately held open while only the browser was closed
- **THEN** the client still regards the cloud as having been connected on this core run, and no first-connect window is re-entered
