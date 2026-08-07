## MODIFIED Requirements

### Requirement: Browser command acceptance is not execution success
Cloud SHALL report browser control requests as accepted only after ownership and routing checks pass. The client MUST use a later Edge `wechat_channels.inbox.auth.status.browserState` projection as execution truth and MUST NOT infer success from enqueue, socket delivery, or HTTP acceptance.

#### Scenario: Open command is accepted but Edge has not confirmed state
- **WHEN** Cloud accepts and routes an open action but no later `browserState=open` projection has arrived
- **THEN** the client reports that the request is waiting for Edge state and MUST NOT state that the browser is open

#### Scenario: Browser launch is unavailable
- **WHEN** the owned Edge cannot launch or attach the sidecar
- **THEN** the prior API auth state remains truthfully represented, browser state is unavailable or unchanged, and the system MUST NOT fabricate an open result or fall back to another browser profile
