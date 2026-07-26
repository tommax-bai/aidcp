## ADDED Requirements

### Requirement: Interaction workspace exposes guarded test reset controls
InteractionWorkspace SHALL show a “测试数据” reset surface only when the current interaction list response reports `testTools.dataResetEnabled=true`. It SHALL offer separate comment and DM actions, explain that the operation deletes only Cloud copies and rereads the platform, and state that it neither deletes platform data nor sends a reply. Each action MUST require entry of the channel-specific confirmation phrase before invoking a named IPC method.

#### Scenario: User confirms comment reset
- **WHEN** the dev tool is enabled and the user selects comment reset, reads the warning, and enters `重置评论`
- **THEN** the client sends one current-env comment reset request with a fresh idempotency key and disables both reset buttons while it is pending

#### Scenario: Confirmation text does not match
- **WHEN** the confirmation phrase is missing or does not exactly match the selected channel
- **THEN** the client performs no IPC call and keeps the current inbox visible

#### Scenario: Tool is unavailable
- **WHEN** list data reports the reset tool disabled or unavailable
- **THEN** the destructive reset controls are not rendered as actionable controls

### Requirement: Reset UI reports accepted, refused, and partial states honestly
After an accepted reset the workspace SHALL clear only the selected channel from its local list/selection, display “已清空，正在重新拉取”, and refresh from Cloud. It MUST NOT claim that platform data was deleted or that a sample returned until list data proves it. Safety-gate rejection and post-delete dispatch failure SHALL be shown as distinct human-readable states without hiding the currently loaded other-channel data.

#### Scenario: Reset is accepted
- **WHEN** customer-auth returns accepted for DM reset
- **THEN** the current DM selection is removed, comment items remain visible where applicable, and the workspace polls the real inbox for reread results

#### Scenario: Cloud cleared but Edge dispatch failed
- **WHEN** customer-auth returns the partial-completion error
- **THEN** the workspace says the Cloud DM copy was cleared but automatic reread did not start and offers a retry without claiming success
