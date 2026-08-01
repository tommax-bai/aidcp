## ADDED Requirements

### Requirement: Managed task entry SHALL use an API-to-Automation owner port

Phase-one CreateTask, CancelTask, and QueryTask SHALL use a versioned API→Automation narrow port. API SHALL authenticate the customer/operator/Agent actor and account scope; Automation SHALL own task admission, compilation, persistence, execution, and trace projection. API MUST NOT construct Automation stores, submit SQL handles, or call Edge task executors directly.

Every request SHALL carry the supported contract version, server-selected execution target, correlation identity, and the direction-specific internal Bearer. CreateTask and CancelTask SHALL additionally carry stable command ids and canonical payload hashes. Transport unavailable, owner rejection, duplicate, collision, and result unknown SHALL remain distinguishable.

#### Scenario: Authorized create crosses the owner boundary
- **WHEN** API accepts an actor's account-scoped CreateTask request
- **THEN** it SHALL call the authenticated Automation route and return the Automation receipt without writing task authority locally

#### Scenario: API-to-Automation response is lost
- **WHEN** Automation may have committed CreateTask or CancelTask but API receives no verifiable response
- **THEN** API SHALL return `result_unknown`, preserve the command id for explicit lookup, and MUST NOT automatically submit a new command id

#### Scenario: Route is disabled or not ready
- **WHEN** the managed task route or Automation readiness gate is closed
- **THEN** API SHALL return a named unavailable response and MUST NOT fall back to the legacy delegated-task store or direct Edge dispatch
