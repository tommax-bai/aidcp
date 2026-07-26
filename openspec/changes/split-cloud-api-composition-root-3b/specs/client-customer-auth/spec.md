## MODIFIED Requirements

### Requirement: Customer restricted recovery is environment-scoped and Cloud-authoritative

The customer-auth API SHALL provide a recovery action that accepts only an empty object and an environment key in the route. The client MUST NOT submit `accountId`, risk signal kind, target status, or audit reason. Cloud SHALL resolve those facts after ownership and Facebook-platform validation, generate the audit reason, and submit a durable restricted-only recovery command to the automation owner. The api process MUST NOT call `RiskController`, write the automation outbox directly, resume Edge on command acceptance, or infer a successful state transition.

Every recovery submission and result read SHALL authenticate the customer, re-check enabled state and current environment ownership, resolve the current persistent environment-to-account binding, and verify that the command belongs to that same environment-bound account and execution target. The customer result endpoint SHALL be scoped as `GET /environments/:envKey/risk-state/recovery-commands/:commandId`; a command from another customer, environment, account, or target MUST be rejected without revealing whether that command exists. Customer responses MUST NOT expose `accountId`, internal controller selectors, outbox rows, or database details.

For a bound account currently in `restricted`, Cloud SHALL submit the asynchronous recovery command and MAY wait only for a bounded quick-completion window. If automation reaches `applied` within that window, Cloud SHALL return the existing `200` write-after receipt. If the command remains `processing`, Cloud SHALL return `202` with only the requested `envKey`, `commandId`, and an explicit processing discriminator; acceptance MUST NOT be described as recovery success. The customer SHALL use the environment-scoped result endpoint to continue reading the same command rather than submitting another recovery merely because the first response was `202`.

Automation SHALL serialize the restricted-only mutation through the bound account's existing `RiskController`. It SHALL change `restricted` to `normal` using `operator_override_recover`, clear the associated signal window through the existing state-machine transition, and persist the write-after state. Only after that mutation is applied SHALL automation resume Cloud command delivery to currently connected edges for the account and record an `applied` result containing the write-after public state, whether it changed, and the actual number of resumed edges. The api process MUST NOT resume Edge before this `applied` result.

An already-`normal` state SHALL remain an idempotent no-op and MAY return the existing `200` write-after receipt without creating a new transition. `warned` and `frozen`, including a state that changes to either before automation applies the command, MUST produce a distinct `refused` result without mutation or Edge resume. A command application or result-recording failure MUST remain `failed`, and a command absent from the authorized account/target ledger MUST remain `unknown`; `refused`, `failed`, and `unknown` MUST NOT be collapsed into `processing`, `applied`, or one generic success response.

#### Scenario: Owner receives a quick write-after recovery receipt
- **WHEN** the authenticated owner confirms recovery for an owned, uniquely bound Facebook environment currently in `restricted` and automation applies the command within the bounded quick-completion window
- **THEN** automation persists `normal`, clears the previous risk signal window, and only then resumes paused Cloud delivery for that account's connected edges
- **AND** Cloud returns `200` with the requested `envKey`, write-after `normal`, `changed:true`, and the real resumed-edge count without exposing `accountId`

#### Scenario: Recovery remains in progress after the quick-completion window
- **WHEN** the restricted-only command is durably accepted but automation has not produced a terminal result before the bounded quick-completion window ends
- **THEN** Cloud returns `202` with the requested `envKey`, `commandId`, and `processing`
- **AND** the response contains no fabricated write-after state, `changed:true`, resumed-edge count, or recovery-success claim

#### Scenario: Authorized polling observes the applied result
- **WHEN** the same enabled customer polls the command through the same owned environment and that environment is still bound to the command's account
- **THEN** `processing` continues to return an explicit non-success in-progress response
- **AND** an automation-recorded `applied` result returns `200` with the write-after public state and real resumed-edge count

#### Scenario: Recovery result cannot cross customer or environment scope
- **WHEN** a customer polls a real command through another customer's environment, a different owned environment, a changed account binding, or another execution target
- **THEN** Cloud rejects the request without revealing whether the command exists, its account, its outcome, or its Edge count

#### Scenario: State changes before the recovery command is applied
- **WHEN** the account was `restricted` at submission but is `warned` or `frozen` when automation serializes the restricted-only mutation
- **THEN** automation records `refused`, leaves the state unchanged, and does not resume any Edge
- **AND** customer-auth returns that refusal distinctly from `failed`, `unknown`, `processing`, and `applied`

#### Scenario: Failed and unknown outcomes remain distinguishable
- **WHEN** an authorized recovery command fails during owner application or result recording
- **THEN** customer-auth reports `failed` with a stable public reason and MUST NOT return recovery success or resume Edge
- **AND** when no command exists for the authorized account and target, customer-auth reports `unknown` rather than `processing` or `failed`

#### Scenario: Repeated recovery after success is idempotent
- **WHEN** the same environment is already `normal` because recovery completed elsewhere
- **THEN** Cloud returns the unchanged authoritative `normal` state with `changed:false` and MUST NOT create a new risk transition

#### Scenario: Warned or frozen cannot be self-recovered by this route
- **WHEN** the bound account is already `warned` or `frozen` when the recovery request is admitted
- **THEN** Cloud rejects the recovery, leaves the state unchanged, and does not submit or apply a recovery command

#### Scenario: Client cannot smuggle account or signal selectors
- **WHEN** a recovery body contains `accountId`, `kind`, `status`, `reason`, or any other key
- **THEN** Cloud rejects the entire request before command submission or mutation
