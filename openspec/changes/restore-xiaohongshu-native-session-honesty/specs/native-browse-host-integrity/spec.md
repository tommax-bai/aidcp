## ADDED Requirements

### Requirement: Browse-session start failures SHALL leave the process

Every browse-session start site SHALL route its failure through one named reporting path that reports to the cloud, moves the host's runtime posture off normal, and classifies the failure as structural or not. The periodic observation loop MUST be armed regardless of whether the first scan succeeded.

A browse session's first scan is the ignition of the whole browse loop: the cloud's role graph starts on the edge's first structured page report. If that first scan fails and the failure stays inside the edge process, the cloud does not learn that a session was attempted — no watchdog fires, no escalation happens, and no operator-visible state changes. The session is dead and every other signal reads healthy.

Every browse-session start site — first start, restart after identity re-establishment, resume from pause, and wake from cold standby — MUST route its failure through one named reporting path rather than terminating in a per-site log statement.

That path MUST do all of the following:

- **Report to the cloud.** A start failure MUST be observable outside this process. Being unable to reach the cloud at that moment does not remove the obligation; it defers it.
- **Move the host's runtime posture off "normal".** The shell decides whether the core has halted from a named set of signals. A start failure that is not in that set leaves automation projected as ready-and-idle, which is what lets a dead session be presented as a working one.
- **Classify the failure as structural or not, and say which.** Structural means: the identical step, replayed on a freshly loaded page, cannot produce a different result — admission rejections and unsupported-capability refusals are structural. Endpoint-unreachable, browser-not-ready and comparable conditions are not. A structural failure MAY reach a terminal state and its receipt MUST state why a retry cannot change the outcome. A non-structural failure MUST NOT reach a terminal state and MUST retain a bounded self-heal path.

**Arming the periodic observation loop MUST NOT be conditional on the first scan succeeding.** A first scan that fails is precisely the state in which periodic re-observation is the only remaining route back to a working session; sequencing the arming after the scan removes the recovery path exactly when it is needed, and no start site re-triggers it.

#### Scenario: A start failure reaches the cloud
- **WHEN** a browse session's first scan fails at any start site
- **THEN** the failure is reported to the cloud rather than terminating in a local log line

#### Scenario: A start failure is visible in the host's runtime posture
- **WHEN** a browse session fails to start while the core process is alive and the transport is connected
- **THEN** the host's runtime posture leaves the normal state
- **AND** automation is not projected as ready-and-idle

#### Scenario: A structural start failure states why retrying cannot help
- **WHEN** a session is refused at the engine's admission
- **THEN** the receipt records a structural failure and states that an identical retry cannot change the result

#### Scenario: A non-structural start failure keeps a bounded recovery path
- **WHEN** a session fails to start because the browser endpoint is not reachable
- **THEN** the failure is not recorded as terminal
- **AND** a bounded self-heal path remains armed

#### Scenario: Periodic observation is armed despite a failed first scan
- **WHEN** the first scan of a browse session fails
- **THEN** the periodic observation loop is still armed
