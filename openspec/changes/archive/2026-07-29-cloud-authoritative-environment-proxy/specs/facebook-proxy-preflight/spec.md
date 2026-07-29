## ADDED Requirements

### Requirement: Proxy preflight SHALL bind one Cloud authority revision
For an environment AdsPower reports as proxy-configured, Edge SHALL fetch the exact Cloud proxy authority before preflight and freeze its revision and configuration for the resulting startup attempt. The local system-upstream switch SHALL choose either the original Cloud proxy or a GOST loopback whose second hop is that same original proxy. Environments AdsPower or Cloud explicitly report as `no_proxy` SHALL skip Cloud proxy-authority resolution, proxy preflight, and proxy mutation.

#### Scenario: Direct mode tests the Cloud original proxy
- **WHEN** the environment has a configured Cloud proxy and system-upstream mode is disabled
- **THEN** preflight SHALL test the frozen original proxy directly
- **AND** a successful preflight SHALL retain the public egress observed through that proxy for a possible Active-browser takeover gate

#### Scenario: Double-hop mode tests the generated loopback
- **WHEN** the environment has a configured Cloud proxy and system-upstream mode is enabled
- **THEN** Edge SHALL construct the GOST chain from the local system proxy to the frozen Cloud original proxy
- **AND** preflight SHALL test the generated loopback endpoint
- **AND** a successful preflight SHALL retain the public egress observed through that effective route for a possible Active-browser takeover gate

#### Scenario: No-proxy environment bypasses proxy gates
- **WHEN** AdsPower or Cloud authority is explicit `no_proxy`
- **THEN** Edge SHALL not require a second hop, start GOST, probe an expected proxy egress, or block startup on proxy preflight

#### Scenario: Cloud is unavailable
- **WHEN** Edge cannot resolve a required Cloud authority revision
- **THEN** preflight and managed startup SHALL fail closed with an authority-unavailable result
- **AND** SHALL NOT reuse AdsPower's current proxy as the original
