## ADDED Requirements

### Requirement: Orchestration capability words gate role registration and fail open

The orchestration capability matrix MUST include `follow`, `profile_visit`, `patrol`, and `notification`, and each MUST have a wired consumer: role registration in the dispatcher setup MUST be gated by these capabilities so a platform that does not support patrol or notification does not register the patrol roles, and a platform that does not support follow or profile visits does not register the author-evaluation and follow roles. The gate MUST fail open: only an explicit unsupported declaration skips registration, while a missing entry or a lookup exception registers as today, so a supported platform's patrol is never silently dropped on a lookup failure. No capability word may remain declared without a consumer.

#### Scenario: Facebook does not register patrol roles

- **WHEN** a Facebook session starts and Facebook declares patrol and notification unsupported
- **THEN** the patrol roles are not registered for that connection
- **AND** the capability words are actually read, not merely declared

#### Scenario: Xiaohongshu still registers all patrol roles

- **WHEN** a Xiaohongshu session starts
- **THEN** all patrol roles and the author-evaluation and follow roles register as before
- **AND** a capability lookup miss or exception still registers them rather than dropping them
