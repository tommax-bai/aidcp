## ADDED Requirements

### Requirement: Every delivery is bound to an exact current target
Before dispatch, the delivery service SHALL resolve the originating normalized inbound record and verify that its account, source kind, stable event identity, conversation or content target, and current session identity still match the delivery request. Missing, ambiguous, moved, deleted, unauthorized, or mismatched targets MUST fail closed before a platform write. Delivery adapters MUST receive typed target fields and MUST NOT accept arbitrary selectors, scripts, endpoints, cookies, or raw protocol envelopes from the UI or chat-llm boundary.

#### Scenario: Comment target no longer belongs to the account video
- **WHEN** a generated reply references a comment whose current video or author ownership cannot be verified for the selected account
- **THEN** dispatch fails before submission with an exact-target validation reason and no fallback target is attempted

#### Scenario: Direct-message conversation matches
- **WHEN** the stored inbound message, current session identity, and resolved conversation participant all match the selected account
- **THEN** the typed direct-message delivery may proceed to its configured adapter

### Requirement: Direct-message delivery does not require persistent Chromium
In real mode, direct-message replies SHALL use the authenticated account web-IM delivery adapter and MUST NOT launch or depend on a continuously running Chromium instance. The adapter MUST validate the platform response schema and SHALL classify success only from a stable platform message identity or explicit accepted receipt. In fixture mode, delivery SHALL return a deterministic local receipt and MUST NOT contact Douyin.

#### Scenario: Real direct-message receipt is explicit
- **WHEN** the web-IM adapter submits to the verified conversation and receives a schema-valid accepted receipt with a stable platform message identity
- **THEN** the delivery is recorded as confirmed and the receipt identity is retained for audit and deduplication

#### Scenario: Fixture direct-message reply is sent
- **WHEN** a fixture-mode reply targets a valid deterministic fixture conversation
- **THEN** the fixture adapter produces the documented local confirmed receipt without any browser or Douyin request

### Requirement: Real writes require a separate startup gate
Selecting real platform mode SHALL permit read-only account and source operation but MUST NOT by itself enable a platform write. Any real direct-message or comment dispatch MUST additionally require the process-level real-write setting to be explicitly enabled and the account's applicable delivery capability to be ready. When real writes are disabled, delivery SHALL terminate as blocked before dispatch and MUST NOT construct or invoke a real reply adapter.

#### Scenario: Real mode starts read-only
- **WHEN** the service starts in real mode without explicit real-write enablement
- **THEN** authorization and enabled reads may operate, but every direct-message and comment reply is blocked before platform dispatch

### Requirement: Comment delivery has exactly three configured capability states
Each account SHALL expose exactly one comment-reply capability: official_api, chromium_worker, or unavailable. The selected capability MUST be explicit configuration and MUST NOT silently fall back to another route after admission or delivery failure. The official route MUST verify the required application permission, authorized account, and ownership scope before submission. The unavailable route MUST reject comment delivery before dispatch while leaving comment reads, AI drafts, and direct-message operation available.

#### Scenario: Official permission is unavailable
- **WHEN** an account is configured for official_api but the required comment permission or authorized-video ownership cannot be verified
- **THEN** comment delivery fails closed before submission and MUST NOT fall back to Chromium

#### Scenario: Comment replies are unavailable
- **WHEN** an account with capability unavailable receives an eligible new comment
- **THEN** the item remains visible with reply unavailable and no platform write is attempted

### Requirement: Headed Chromium comment workers are bounded per account
For an account configured as chromium_worker, the service SHALL start a headed Chromium worker only after one eligible exact-target comment reply has acquired that account's delivery ownership. At most one comment write SHALL be in flight per account. The worker MUST restore the bound session, resolve a fresh exact target, dispatch one reply, inspect the platform response or postcondition, and close after a confirmed, rejected, failed_not_submitted, submitted_unknown, or blocked outcome. It MUST NOT remain running between eligible comment writes or be reused as a direct-message receiver.

#### Scenario: Eligible Chromium comment reply is confirmed
- **WHEN** an eligible reply acquires the account lock, the fresh target matches, and the platform returns an explicit accepted receipt
- **THEN** the worker records confirmed, releases delivery ownership, and closes its Chromium instance

#### Scenario: Two comment writes target one account
- **WHEN** two eligible comment replies become ready for the same account at the same time
- **THEN** the service serializes them so at most one headed Chromium worker performs a platform write at a time

### Requirement: Delivery outcomes preserve submission uncertainty
Every delivery attempt SHALL terminate as confirmed, rejected, failed_not_submitted, submitted_unknown, or blocked. Only a schema-valid explicit target-matching platform acceptance receipt or verified fresh postcondition MAY produce confirmed. An explicit platform refusal SHALL produce rejected; a transport or validation failure proven to occur before dispatch SHALL produce failed_not_submitted; and an authorization, capability, policy, or operator-state gate SHALL produce blocked. A timeout, disconnect, browser loss, unreadable response, or unverifiable postcondition when dispatch may have occurred MUST produce submitted_unknown rather than any proven outcome. Transport completion, DOM click completion, request emission, and handing work to a worker MUST NOT alone prove confirmation.

#### Scenario: Connection drops after dispatch
- **WHEN** the adapter emits a write request and loses the connection before an acceptance receipt or postcondition can be verified
- **THEN** the attempt terminates as submitted_unknown with dispatch evidence and is not counted as confirmed

#### Scenario: Platform explicitly rejects before accepting
- **WHEN** the platform returns a schema-valid rejection proving that the reply was not accepted
- **THEN** the attempt terminates as rejected with the sanitized rejection reason

#### Scenario: Validation fails before dispatch
- **WHEN** exact-target validation fails before any adapter can submit a platform write
- **THEN** the attempt terminates as failed_not_submitted and records no dispatch timestamp

### Requirement: Submitted-unknown attempts are terminal and never retried
A submitted_unknown attempt SHALL release generation and account in-flight ownership but MUST remain terminal for that reply identity. Automatic retry, process-restart replay, queue redrive, route fallback, and duplicate delivery of the same reply MUST NOT occur. The operations UI SHALL require a separately auditable operator decision before any later message is authored, and that later message MUST be a new delivery identity rather than mutation or retry of the unknown attempt.

#### Scenario: Service restarts after unknown outcome
- **WHEN** the service restarts with a reply durably recorded as submitted_unknown
- **THEN** recovery loads it as terminal, schedules no retry, and does not count it as successful

#### Scenario: Operator reviews unknown outcome
- **WHEN** an operator opens a submitted_unknown timeline item
- **THEN** the UI offers no retry of that delivery identity and preserves its uncertainty and dispatch evidence

### Requirement: Delivery claims prevent duplicate dispatch
The service SHALL create a durable delivery identity and atomically acquire its dispatch claim before invoking any platform adapter. A generated reply MUST have at most one dispatching or terminal delivery attempt unless the platform definitively rejects it before any possible submission and policy explicitly allows a fresh, separately identified attempt. Concurrent workers and restart recovery MUST respect the durable claim and terminal outcome.

#### Scenario: Concurrent workers claim one reply
- **WHEN** two workers attempt to dispatch the same generated reply concurrently
- **THEN** exactly one worker acquires the durable claim and the other performs no platform action
