# native-page-engine-platform-coverage Specification

## Purpose
TBD - created by archiving change native-page-engine-platform-cutover. Update Purpose after archive.
## Requirements
### Requirement: Native owns every production Facebook page operation
The Edge SHALL route every production Facebook page read, page classification, page movement, interaction, group join, comment, publish, overlay, consent, and post-action verification through the Native Page Engine. Production JavaScript MUST NOT contain or execute Facebook selectors, browser scripts, raw CDP page operations, local page-recovery rules, or a fallback implementation after cutover.

#### Scenario: Facebook command reaches the page
- **WHEN** an admitted Facebook browse, interaction, group, comment, or publish command requires browser page access
- **THEN** Edge sends a typed semantic command to a Facebook-bound Native session
- **AND** only Native attaches to the selected page target and dispatches the required CDP operations

#### Scenario: Native is unavailable
- **WHEN** the required Native executable is missing, incompatible, fails startup, or loses its session
- **THEN** Edge reports an explicit unavailable or effect-aware ambiguous outcome
- **AND** it MUST NOT invoke a JavaScript Facebook executor

### Requirement: Native Facebook commands are typed and selector-free
The Native protocol SHALL expose only versioned, bounded semantic Facebook commands and results. Edge MUST NOT supply arbitrary JavaScript, selectors, XPath, raw CDP methods, unbounded DOM data, or caller-defined retry programs.

#### Scenario: Facade requests a page read
- **WHEN** the Facebook facade requests feed cards or exact post state
- **THEN** its input contains only typed business parameters and identity hints
- **AND** Native selects and executes its own page rules

#### Scenario: Arbitrary browser input is attempted
- **WHEN** an IPC command contains an unknown field, raw CDP method, selector, XPath, or JavaScript payload
- **THEN** protocol validation rejects it before browser dispatch

### Requirement: Native preserves Facebook outcome honesty
Native SHALL own bounded local recovery and post-action verification and SHALL return an explicit effect phase for every command. A write that may have been dispatched MUST NOT be reported as not started, automatically replayed after a crash, or retried through another executor.

#### Scenario: Facebook comment dispatch is not verified
- **WHEN** Native may have submitted a comment but cannot prove the expected comment after bounded verification
- **THEN** it returns an ambiguous effect with bounded diagnostic data
- **AND** Edge MUST NOT resubmit the comment automatically

#### Scenario: Cancellation arrives before browser input
- **WHEN** cancellation is observed at a declared safe point before any Facebook input dispatch
- **THEN** Native returns a not-started cancellation result and performs no page write

### Requirement: Production probes follow the execution boundary
Every production-reachable Facebook probe that classifies page structure, locates an editor or media/composer surface, gates submit, fingerprints page state, or verifies an outcome SHALL execute inside Native. Calibration-only and development probes MUST remain outside the production import graph and final package.

#### Scenario: Runtime needs editor discovery
- **WHEN** a production comment flow probes for the Facebook editor
- **THEN** the probe runs as part of a typed Native command and returns a bounded semantic result

#### Scenario: Development probe exists in the repository
- **WHEN** the desktop production artifact is assembled
- **THEN** no development probe script, source map, standalone browser router, or calibration-only probe module is present in ASAR or packaged resources

### Requirement: WeChat browser-session capture is Native and whitelisted
The WeChat Channels local browser sidecar SHALL obtain cookies, user agent, and authentication request context through a typed Native session. Native SHALL capture only the allowed WeChat host/request shape, return only the bounded declared session-candidate fields, and MUST NOT expose arbitrary requests, storage, DOM, or raw browser data.

#### Scenario: Valid authentication context is observed
- **WHEN** Native is attached to an allowed WeChat Channels target and observes the exact whitelisted authentication request after Network enablement and reload
- **THEN** it returns only matching WeChat cookies, user agent, and validated request-context fields

#### Scenario: Capture is incomplete or mismatched
- **WHEN** the request host/path/body/headers are invalid, cookies are absent, user agent is empty, or the deadline expires
- **THEN** Native returns no session candidate or an explicit bounded failure
- **AND** Edge MUST NOT synthesize missing session material

### Requirement: Platform sessions and commands cannot cross
Each Native session SHALL be bound to exactly one supported platform, task identity, and browser target. Native MUST reject commands for another platform and MUST select targets only from that platform's declared host allowlist.

#### Scenario: Facebook command enters a WeChat session
- **WHEN** a Facebook command is submitted to a `wechat_channels` Native session
- **THEN** Native rejects the command before CDP dispatch

#### Scenario: Target host is outside the platform allowlist
- **WHEN** target discovery finds only pages outside the session platform's allowed hosts
- **THEN** session open fails explicitly without attaching to an unrelated page
