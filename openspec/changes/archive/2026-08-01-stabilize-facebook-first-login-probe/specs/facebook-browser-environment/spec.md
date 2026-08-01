## ADDED Requirements

### Requirement: Facebook first-login probing SHALL wait for successful Native page evidence

After a fresh AdsPower browser start, edge SHALL treat a confirmed typed `facebook_auth_probe` observation as the readiness evidence for first-login reconciliation. Browser-process reachability, TypeScript CDP attachment, elapsed wall-clock delay, or document ready state alone MUST NOT authorize a login action. Before any action, Native MUST still fresh-revalidate the exact signal id and candidate under the existing one-signal/one-action contract.

#### Scenario: Fresh target is still navigating
- **WHEN** the first read-only Native auth probe encounters an allowlisted endpoint, target, CDP, or engine-transport failure before any page mutation
- **THEN** edge discards the affected Native owner session and retries the read-only probe against a fresh session using bounded backoff for at most 20 seconds and never beyond the existing login budget
- **AND** it dispatches no login input because of that failed observation

#### Scenario: A later probe supplies readiness evidence
- **WHEN** a bounded retry returns one confirmed typed Facebook auth observation
- **THEN** edge continues reconciliation in the original process and browser generation
- **AND** a supported actionable signal still requires Native action-time fresh revalidation before input

#### Scenario: Contract failure is not stabilized by waiting
- **WHEN** a Native auth probe fails with an invalid request, invalid protocol, ownership mismatch, unsupported command, engine-internal failure, or unknown error
- **THEN** edge reports a bounded safe failure and starts no account-scoped work
- **AND** it MUST NOT convert the failure into `none`, `authenticated`, or an actionable signal

#### Scenario: Transient stabilization window expires
- **WHEN** allowlisted read-only Native auth failures continue for 20 seconds without a confirmed typed observation
- **THEN** edge stops automated login actions and enters the existing controlled manual-login wait in the same core and browser generation with reason `auth_probe_unavailable`
- **AND** it MUST NOT exit solely to trigger a supervisor restart or transfer fresh-start policy proof to another process

#### Scenario: Action exception is never retried as startup churn
- **WHEN** a Native login action throws after its signal was dispatched or may have been dispatched
- **THEN** edge treats the action receipt as terminal or ambiguous according to the available evidence
- **AND** it MUST NOT retry that action, transfer its fresh-start authorization to another process, or replay the same signal id

#### Scenario: Startup diagnostics remain non-secret
- **WHEN** a Native auth command fails during first-login reconciliation
- **THEN** edge logs only a bounded command kind, Native error code, effect phase when available, and retry or terminal disposition
- **AND** it MUST NOT log raw errors, stderr, page URLs, cookies, credentials, TOTP material, or AdsPower responses
