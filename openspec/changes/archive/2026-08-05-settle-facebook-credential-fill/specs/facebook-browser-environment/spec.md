## ADDED Requirements

### Requirement: Facebook credential fill SHALL be observed as settled before login submission

AdsPower fills Facebook credentials by simulated per-character typing, so a non-empty credential field is evidence that filling has **started**, never that it has **finished**. Edge SHALL treat a login form as submittable only after observing that both credential fields stopped changing. The actionable `login_submit_ready` signal id SHALL bind the observed **character counts** of the username and password fields in addition to its existing target, document generation, signal kind, and candidate evidence, so that any further typing produces a different signal id. Edge MUST NOT include credential characters in the signal id, in any receipt, or in any log line — only counts participate, and the counts themselves are never emitted.

#### Scenario: Credential fill still in progress is not submittable

- **WHEN** both credential fields are non-empty but the `login_submit_ready` signal id differs from the previously observed one, or the same signal id has been observed for less than the 1.5-second settle window
- **THEN** edge SHALL continue bounded re-probing and dispatch no login action
- **AND** it MUST NOT treat a non-empty password field as evidence that filling completed

#### Scenario: Settled credentials authorize one submission

- **WHEN** the identical `login_submit_ready` signal id has been observed continuously across a span of at least 1.5 seconds and the submit target is unique, enabled, and topmost
- **THEN** edge SHALL dispatch exactly one `facebook_auth_submit_login` action bound to that signal id under the existing one-signal/one-action contract

#### Scenario: Typing resumes after the settle window opened

- **WHEN** a further character reaches either credential field after edge started counting a settle window
- **THEN** the observed signal id changes and edge SHALL restart the settle window from that new observation
- **AND** it MUST NOT carry the elapsed span of the superseded signal id forward

#### Scenario: Action-time refusal on a superseded signal is recoverable

- **WHEN** a dispatched `facebook_auth_submit_login` is refused at action time because the credential fill changed, and the receipt reports that no input was started
- **THEN** edge SHALL discard that observation, re-probe, and continue reconciliation within the remaining login budget for at most 5 such refusals
- **AND** it MUST NOT report a terminal authentication failure, close the browser, or replay the superseded signal id
- **AND** an ambiguous receipt or any receipt that may have dispatched input SHALL retain its existing terminal handling

#### Scenario: Refusal budget is exhausted honestly

- **WHEN** more than 5 consecutive action-time refusals occur for credential-fill changes
- **THEN** edge SHALL fail honestly with a reason that distinguishes this from a rejected credential
- **AND** it MUST NOT record the outcome as a wrong password or as a completed submission

## MODIFIED Requirements

### Requirement: Facebook first-login assistance reconciles one independent signal at a time

The first-login reconciler MUST treat login submission, 2FA entry, 2FA submission, stale-code clearing, automated-behavior warning dismissal, Facebook push-blocker closure, and Facebook Remember Password confirmation as independent signals and actions. It MUST NOT require or assume a contiguous or fixed signal order. Each actionable observation SHALL carry a non-secret signal id bound to the target, document generation, signal kind, and exact candidate; for login submission the signal id SHALL additionally bind the observed credential-field character counts. Each pass SHALL use a fresh Native Page Engine observation, execute at most one action that exactly matches and fresh-revalidates that signal id, verify a same-page or navigation postcondition, discard the observation, and re-probe before any later action. The same signal id MUST NOT be dispatched twice, including after an ambiguous receipt.

#### Scenario: Optional signals are absent or reordered
- **WHEN** Facebook omits a warning, delays Remember Password, or presents supported signals in a different order
- **THEN** the reconciler acts only on the currently observed unique signal and does not synthesize or pre-empt the absent next step

#### Scenario: One observation permits only one action
- **WHEN** one fresh probe identifies a unique supported signal
- **THEN** edge dispatches at most one matching Native CDP action
- **AND** it MUST obtain a verified postcondition and a fresh probe before dispatching another action

#### Scenario: Unchanged signal cannot be clicked repeatedly
- **WHEN** an action does not remove its signal, change the bound document, or satisfy its defined postcondition
- **THEN** the reconciler fails that action honestly and MUST NOT retry the click or key input against the unchanged observation

#### Scenario: Stale or ambiguous signal is not replayed
- **WHEN** the target, document generation, signal kind, credential-field character counts, or candidate no longer match the supplied signal id, or the prior action receipt is ambiguous
- **THEN** Native dispatches no new input for that observation
- **AND** the coordinator MUST NOT replay the same signal id
- **AND** a refusal that reports no input was started MAY be followed by a fresh observation carrying a different signal id, which is a new observation rather than a replay

#### Scenario: Long page URL retains a bounded document generation
- **WHEN** a supported Facebook page has a long page-controlled query string
- **THEN** Native represents the document generation with a fixed bounded value whose size is independent of the raw URL length
- **AND** the value remains stable for the unchanged document and URL state, changes after a full navigation or route/query transition, and does not expose the raw query

#### Scenario: Login submission requires settled AdsPower-filled fields
- **WHEN** the exact visible Facebook login form is uniquely identified
- **THEN** Native MAY submit it only after confirming the username and password fields are non-empty, have stopped changing for the defined settle window, and the submit target is topmost
- **AND** edge MUST NOT obtain or type the stored password
- **AND** a field that is merely non-empty MUST NOT authorize submission

### Requirement: Unavailable Facebook credential fill SHALL preserve a controlled manual-login session

When one visible Facebook login form exposes both credential fields but they do not reach a settled filled state within the bounded fill grace, edge SHALL enter `manual_login_required` with reason `credential_fill_unavailable`. The fill grace SHALL be 45 seconds measured from the first observation in which both credential fields are present, not from document load, because the form itself and the simulated typing both begin well after the document starts loading. Observations in which the login form or its fields have not yet rendered SHALL NOT consume that grace. Edge MUST stop automated auth actions, keep the current core/browser/CDP generation alive, and MUST NOT exit or relaunch solely because credential fill is unavailable.

#### Scenario: Empty credential fields enter manual login
- **WHEN** the unique Facebook login form still has an empty credential field 45 seconds after both fields were first observed
- **THEN** edge enters `manual_login_required` with reason `credential_fill_unavailable`
- **AND** the core remains alive with browser control available and dispatches no further automated login action

#### Scenario: Fields wiped by a page re-render do not shorten the grace
- **WHEN** Facebook re-renders the login area and clears partially typed credentials
- **THEN** edge SHALL keep waiting against the same grace anchored on the first observation of both fields
- **AND** it MUST NOT type, re-trigger, or synthesize any credential content

#### Scenario: Unrendered form does not consume the grace
- **WHEN** no login form, or a form without both credential fields, has been observed yet
- **THEN** the fill grace SHALL NOT be running
- **AND** edge MUST NOT report `credential_fill_unavailable` from elapsed document age alone

#### Scenario: Manual login resumes in place
- **WHEN** the operator completes login while the environment is waiting for manual login
- **THEN** edge confirms a stable identity through the existing identity gate and continues startup in the same core and browser generation
- **AND** it MUST NOT call browser launch or perform a new CDP attachment for that recovery

#### Scenario: Manual login wait is explicitly closed
- **WHEN** the operator pauses or closes an environment waiting for manual login
- **THEN** edge closes and confirms the owned AdsPower browser through the existing lifecycle close path before releasing the browser slot
- **AND** the supervisor MUST NOT automatically restart that intentional stop
