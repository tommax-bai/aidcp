## ADDED Requirements

### Requirement: Video-channel authorization guidance is actionable and identity-aware
The Edge client SHALL explain first authorization, successful identity binding, reauthorization, challenge, and identity mismatch using structured interaction auth data. It MUST NOT instruct ordinary users to configure internal account IDs or infer success from a request-accepted response.

#### Scenario: First authorization is required
- **WHEN** the selected video-channel environment has `status=login_required` and no bound identity projection
- **THEN** the workspace explains that the opened profile will bind the currently scanned video-channel account, names the selected environment, and offers one explicit action to open the login window

#### Scenario: Reopen request is accepted
- **WHEN** customer-auth accepts `interaction.auth.reopen` but no later active auth status has arrived
- **THEN** the workspace displays that the browser-open request was accepted and continues to show authorization pending rather than success

#### Scenario: Finder identity mismatches the binding
- **WHEN** auth state reports `WECHAT_IDENTITY_MISMATCH`
- **THEN** the workspace explains that the browser is logged into another video-channel account, keeps historical content readable, disables all writes, and directs the user to switch to the originally bound account

### Requirement: Edge capability copy reflects Cloud-applied account controls
The workspace SHALL render current comment/DM availability from the effective capabilities reported by Edge after applying the account-scoped Cloud control version. It MUST NOT present a saved Console configuration as proof that the Edge applied it.

#### Scenario: Control is saved while Edge is offline
- **WHEN** Cloud stores a newer runtime-control version but the selected Edge is offline or has not reported capabilities from that version
- **THEN** the client distinguishes saved account configuration from current Edge availability and keeps affected actions disabled
