# cdp-control-health-recovery Specification

## Purpose
TBD - created by archiving change edge-cdp-health-recovery. Update Purpose after archive.
## Requirements
### Requirement: Connected but unresponsive CDP input control SHALL be detected and classified

The edge SHALL measure CDP command duration and maintain an explicit browser-control health state. A timed-out `Input.*` command MUST immediately enter an unavailable state. Consecutive successful `Input.*` commands whose duration exceeds the configured slow-input threshold MUST enter a recovering state after the configured consecutive threshold. The state transition MUST emit structured, content-free diagnostics containing the triggering method, observed duration when available, classification reason, and recovery correlation id.

#### Scenario: Input command times out while CDP WebSocket remains connected
- **WHEN** `Input.dispatchMouseEvent` reaches the CDP command timeout without a response and the edge-cloud WebSocket remains connected
- **THEN** the edge marks browser control unavailable, emits an input-timeout diagnostic, and MUST NOT report the browser as healthy merely because either WebSocket remains open

#### Scenario: Repeated slow successful inputs trigger bounded recovery
- **WHEN** the configured number of consecutive `Input.*` responses each exceed the slow-input threshold without timing out
- **THEN** the edge enters recovering state and starts exactly one bounded CDP recovery attempt for that episode

### Requirement: CDP control recovery SHALL preserve command uncertainty and ownership boundaries

The edge MUST stop starting new ordinary browse commands while browser control is recovering or unavailable. It MUST NOT replay the interrupted command. A soft-stall recovery SHALL reuse target rediscovery, CDP re-enable, and anti-detection reinjection; browse may resume only after that recovery completes and the edge re-reports current page state. After an input timeout, the edge MUST retain unavailable state until a safe browser boundary is established; it MUST NOT force-stop an external or non-owned browser.

#### Scenario: Ordinary browse command is interrupted by a control stall
- **WHEN** an ordinary browse atom encounters CDP control recovery or unavailable state
- **THEN** the atom ends with an honest failure, no later browse atom starts during the state, and cloud receives a fresh page-state report only after a successful soft recovery

#### Scenario: Timed-out input belongs to an external browser
- **WHEN** an input timeout occurs on a browser that the edge does not own
- **THEN** the edge remains unavailable for page-writing work and MUST NOT stop or kill that browser; operator restart/reconnect is required before control can become available again

#### Scenario: Recovery is exhausted on an edge-owned browser
- **WHEN** the bounded recovery path for an input-control failure is exhausted and the browser is owned by the edge
- **THEN** the edge emits the existing unrecoverable lifecycle signal and delegates restart to the supervised recycle path without replaying the failed command

