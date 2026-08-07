## MODIFIED Requirements

### Requirement: Group join uses a distinct capability and never the browse capability string

The Facebook driver SHALL expose a distinct `join` capability for group joining and MUST NOT reuse the `browse` capability string (which would attach the xhs browse session on a Facebook edge). The `facebook.group.join` command MUST be routed through the Facebook command handler and MUST appear in the edge active-command whitelist so it is not silently dropped.

#### Scenario: Join does not attach a browse session
- **WHEN** a Facebook edge receives a `facebook.group.join` command
- **THEN** it is handled by the Facebook command handler without starting an xhs browse session or watchdog
