## ADDED Requirements

### Requirement: Unverified WeChat writes are restricted to the named development runtime

The Electron companion SHALL inject the unverified WeChat write-test token only for an unpackaged development process whose selected Cloud environment is exactly `dev` and whose platform is exactly `wechat_channels`. Packaged clients and `ol` or custom Cloud selections MUST NOT receive this token. Without the exact token, candidate write descriptors and unverified capability bypasses MUST remain unavailable.

#### Scenario: Unpackaged dev WeChat environment receives the test token

- **WHEN** an unpackaged Electron client starts a `wechat_channels` environment connected to the named `dev` Cloud selection
- **THEN** the child Edge process receives the exact unverified-write test token

#### Scenario: Packaged or non-dev environment remains closed

- **WHEN** the client is packaged or its Cloud selection is `ol` or custom
- **THEN** the child Edge process does not receive the unverified-write test token
- **AND** unverified comment and DM descriptors remain blocked before fetch

### Requirement: Dev write testing bypasses only per-channel write grants and prior-probe evidence

When the exact dev token is active, Edge MAY treat the comment-reply and DM-text Cloud per-channel write booleans and prior-write-probe evidence gates as satisfied. Edge MUST still require a valid scoped/versioned Cloud runtime-control snapshot, active authentication, matching identity, healthy and Cloud-enabled channel reads, enabled global/local writes, closed kill switches, and a closed channel circuit. Cloud approval, policy, risk-state, account/thread rate-limit, CAS, idempotency, and dispatch gates MUST remain unchanged except for the documented reviewed-dev login/quota-only compatibility rule.

#### Scenario: Healthy dev account reports both text writes available

- **WHEN** the exact dev token is active and every non-probe comment and DM gate is satisfied
- **THEN** Edge reports `commentsReply=true` and `dmSendText=true`
- **AND** it records diagnostics identifying the unverified dev override

#### Scenario: Auth, read control, or control-snapshot validity still closes writes

- **WHEN** the exact dev token is active but authentication is inactive, identity mismatches, the channel read control is false, or the scoped Cloud-control snapshot is missing or invalid
- **THEN** the affected effective write capability remains false

#### Scenario: Dev token overrides false per-channel write booleans

- **WHEN** the exact dev token is active, the scoped Cloud-control snapshot is valid, the affected channel read is healthy and enabled, and only its per-channel write boolean is false
- **THEN** Edge reports the corresponding text-write capability as true
- **AND** diagnostics identify that the dev write-control override is active

### Requirement: Candidate write dispatch and confirmation remain honest

The dev override SHALL permit only the candidate comment-create and DM-text descriptors identified from the current first-party bundle. Both descriptors MUST remain non-retry-safe and MUST retain an evidence label distinct from capture-backed production descriptors. Edge MUST confirm a comment only from a platform-returned comment identifier and MUST confirm a DM only from a successful platform base response plus a server message identifier. Missing acknowledgements, changed schemas, platform rejection, and lost responses MUST remain failed or ambiguous according to dispatch evidence and MUST NOT be reported as sent.

#### Scenario: Platform server identifier confirms a test write

- **WHEN** the candidate request is dispatched and the platform returns the channel-specific successful response with a server identifier
- **THEN** Edge reports the attempt as confirmed with `verification=platform_ack`

#### Scenario: Candidate response cannot prove acceptance

- **WHEN** a candidate request leaves the process but its response lacks the required successful shape or server identifier
- **THEN** Edge does not report the attempt as confirmed
- **AND** schema drift opens only the affected endpoint circuit

#### Scenario: Candidate write is never retried blindly

- **WHEN** the candidate write times out or its response is lost after dispatch
- **THEN** Edge preserves the attempt as ambiguous
- **AND** recovery performs history verification without resending the platform write

### Requirement: Legacy-schema write testing is restricted to the named dev Cloud deployment

Cloud MUST keep the pre-0046 interaction schema read-only outside dev. Cloud MAY enable reviewed text writes on that exact schema only when `AIDCP_DEPLOY_ENV` is exactly `dev` and the existing global interaction-write switch is enabled. No additional Cloud write-test token is required. Missing base schema and partially migrated or inconsistent 0046 shapes MUST remain disabled. The override MUST NOT execute or emulate migration 0046 and MUST preserve the legacy database's unconditional idempotency uniqueness and `retryable=false` default.

#### Scenario: Existing dev write switch admits the pre-0046 schema

- **WHEN** Cloud is deployed as `dev`, the global write switch is enabled, and startup classifies the database as the exact pre-0046 shape
- **THEN** Cloud projects the stored comment-reply and DM-text controls without forcing them false
- **AND** normal approval, policy, risk, quota, CAS, attempt, dispatch, and result gates still apply

#### Scenario: Non-dev or invalid schema remains read-only

- **WHEN** the deployment is not exactly `dev`, the global write switch is off, or schema classification is missing or inconsistent
- **THEN** outbound interaction writes remain disabled before an attempt is created

#### Scenario: Compatibility mode does not add retry semantics

- **WHEN** a dev compatibility write has already consumed the legacy schema's deterministic idempotency key
- **THEN** Cloud does not weaken or replace the legacy uniqueness constraint
- **AND** no automatic resend is introduced by this override

#### Scenario: Reviewed dev send bypasses only local login and zero-default quota gates

- **WHEN** the named dev deployment has global interaction writes enabled and an already approved send is blocked only by post-login cooldown or a RiskController `quota:*` reason
- **THEN** Cloud continues admission without writing shared `quota_config`
- **AND** restricted or frozen risk state, interaction account/thread limits, auth, capability, approval, CAS, idempotency, dispatch, and result gates still apply

#### Scenario: Client distinguishes local admission from platform throttling

- **WHEN** Cloud returns `INTERACTION_RATE_LIMITED`
- **THEN** the client describes a Cloud-local send restriction and does not claim the platform rate-limited the request
- **AND** only `WECHAT_RATE_LIMITED` is described as platform throttling
