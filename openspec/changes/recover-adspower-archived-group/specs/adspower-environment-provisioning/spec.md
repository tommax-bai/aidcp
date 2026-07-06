## ADDED Requirements

### Requirement: 专用分组失效时自动恢复一次
When AdsPower rejects `user/create` because the dedicated group is deleted or archived, the desktop app SHALL treat that as a recoverable dedicated-group state drift. It SHALL clear any cached dedicated group id, re-resolve or recreate the dedicated group through AdsPower local API, and retry the environment creation at most once. The app MUST NOT retry unrelated creation failures, MUST NOT loop indefinitely, and MUST still surface the final AdsPower failure honestly if the retry also fails.

#### Scenario: Cached group was deleted or archived
- **WHEN** the desktop app attempts to create an AdsPower environment using a cached dedicated group id
- **AND** AdsPower rejects `user/create` with `group is deleted or archived`
- **THEN** the app clears that cached group id, resolves or creates a current dedicated group, and retries `user/create` once

#### Scenario: Unrelated creation failure remains honest
- **WHEN** AdsPower rejects `user/create` for a reason unrelated to deleted or archived groups
- **THEN** the app reports the failure without clearing group cache or retrying
