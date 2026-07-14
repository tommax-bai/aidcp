## ADDED Requirements

### Requirement: Browser-control-unavailable acquisition SHALL fail immediately and explicitly

Before quiescing browse or granting a task lease, edge task coordination MUST check browser-control readiness. If control is recovering or unavailable, it MUST NOT acquire task ownership, MUST NOT dispatch a page-writing command, and MUST emit `edge.task.released` with reason `cdp_unhealthy` for the requested task id. This negative acknowledgement SHALL be idempotent and MUST NOT leave a queued or active lease behind.

#### Scenario: Human publish arrives during CDP recovery
- **WHEN** a human-priority publish lease request arrives while browser control is recovering
- **THEN** the edge immediately returns `edge.task.released{reason:'cdp_unhealthy'}` without calling browse quiescence and without waiting for the normal acquire timeout

#### Scenario: Duplicate release after unhealthy rejection
- **WHEN** cloud later sends a release for a task already rejected as `cdp_unhealthy`
- **THEN** the edge responds idempotently and MUST NOT resume or freeze browse because of that duplicate release
