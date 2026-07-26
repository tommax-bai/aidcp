## RENAMED Requirements

- FROM: `### Requirement: Facebook scheduled comments are disabled by default and fail closed`
- TO: `### Requirement: Facebook scheduled comments are authorized by scoped product controls and fail closed`

## MODIFIED Requirements

### Requirement: Facebook scheduled comments are authorized by scoped product controls and fail closed

Facebook scheduled commenting SHALL be authorized by the account's enabled comment schedule, approval mode, platform match and active account state. A plain operator `/comment <昵称>` command is explicit manual intent and SHALL enter the same targeted-comment pipeline independent of the account schedule window. Neither path SHALL require a process-global automatic or shadow environment variable.

Every path MUST still enforce persona, joined-group ownership, deterministic content validators, structured approval policy, active identity/capability, per-account risk quota and daily cap, single-flight, idempotency and server-confirmed verification. Missing or disabled scoped configuration on an unattended schedule MUST produce an honest no-op and MUST NOT claim work occurred.

#### Scenario: Disabled account schedule prevents unattended posting
- **WHEN** a Facebook account's scheduled comment action is disabled or the account is paused
- **THEN** no unattended Facebook comment is posted or risk-recorded even if stale auto/shadow environment variables are present

#### Scenario: Enabled schedule needs no global switch
- **WHEN** a Facebook account has an enabled current comment schedule and satisfies all approval, target, identity, risk and quota gates
- **THEN** the scheduled targeted-comment pipeline runs without requiring `AIDCP_FB_COMMENT_AUTO`

#### Scenario: Manual command is not silently no-op'd by deployment state
- **WHEN** an operator issues a valid plain `/comment <昵称>` command for an active Facebook account
- **THEN** the targeted-comment pipeline returns an honest terminal outcome without consulting a global auto/shadow environment switch
