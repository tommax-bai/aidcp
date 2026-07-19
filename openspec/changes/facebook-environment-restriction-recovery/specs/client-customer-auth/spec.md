## ADDED Requirements

### Requirement: Customer can read authoritative risk state for an owned Facebook environment

The customer-auth API SHALL provide an environment-scoped risk-state read. On every request Cloud MUST authenticate the customer, re-check enabled state and current environment ownership, resolve the persistent environment-to-account binding, and verify the bound account platform is Facebook. The response SHALL contain the requested `envKey` and public risk state only; it MUST NOT expose `accountId`, other environments, signal reasons, or internal controller selectors. Unowned, unbound, contended, unavailable, or non-Facebook environments MUST fail closed with distinguishable errors rather than returning a fabricated `normal` state.

#### Scenario: Stopped owned Facebook environment reads persisted restricted state
- **WHEN** a customer requests risk state for an owned, uniquely bound Facebook environment whose Edge is offline and whose persisted Cloud state is `restricted`
- **THEN** Cloud returns that environment's authoritative `restricted` state without requiring a live Edge session
- **AND** the response does not contain `accountId`

#### Scenario: Risk read cannot cross environment ownership
- **WHEN** a customer requests risk state for another customer's environment or a contended binding
- **THEN** Cloud rejects the request and returns no account or risk-state data

#### Scenario: Non-Facebook environment cannot use the Facebook risk surface
- **WHEN** a customer requests the risk-state route for an owned environment bound to a non-Facebook account
- **THEN** Cloud rejects the request as unsupported and does not expose or mutate that account's risk state

### Requirement: Customer restricted recovery is environment-scoped and Cloud-authoritative

The customer-auth API SHALL provide a recovery action that accepts only an empty object and an environment key in the route. The client MUST NOT submit `accountId`, risk signal kind, target status, or audit reason. Cloud SHALL resolve those facts after ownership and Facebook-platform validation, generate the audit reason, and serialize the mutation through the bound account's existing `RiskController`.

The action SHALL change `restricted` to `normal` using `operator_override_recover`, clear the associated signal window through the existing state-machine transition, persist the write-after state, and resume Cloud command delivery to currently connected edges for that account. An already-`normal` state SHALL be an idempotent no-op; `warned` and `frozen` MUST be refused without mutation. The response SHALL return the write-after public state, whether it changed, and the actual number of resumed edges, without exposing `accountId`.

#### Scenario: Owner recovers a restricted Facebook environment
- **WHEN** the authenticated owner confirms recovery for an owned, uniquely bound Facebook environment currently in `restricted`
- **THEN** Cloud persists `normal`, clears the previous risk signal window, resumes paused Cloud delivery for the account's connected edges, and returns `changed:true` with the real resumed-edge count

#### Scenario: Repeated recovery after success is idempotent
- **WHEN** the same environment is already `normal` because recovery completed elsewhere
- **THEN** Cloud returns the unchanged authoritative `normal` state with `changed:false` and MUST NOT create a new risk transition

#### Scenario: Warned or frozen cannot be self-recovered by this route
- **WHEN** the bound account is `warned` or `frozen`
- **THEN** Cloud rejects the recovery and leaves the state unchanged

#### Scenario: Client cannot smuggle account or signal selectors
- **WHEN** a recovery body contains `accountId`, `kind`, `status`, `reason`, or any other key
- **THEN** Cloud rejects the entire request before mutation

