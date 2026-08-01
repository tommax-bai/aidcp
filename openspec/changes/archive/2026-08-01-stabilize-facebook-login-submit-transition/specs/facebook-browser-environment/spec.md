## ADDED Requirements

### Requirement: Facebook submit postconditions SHALL distinguish obstruction from disappearance

Before Native dispatches a Facebook login or 2FA submit action, the exact target MUST remain visible, unique, and topmost. After that action has been dispatched, the bounded postcondition verifier MUST NOT treat the still-present target becoming temporarily non-topmost as proof that the observed signal disappeared. It SHALL observe at a 200 ms cadence for at most 35 polls without replaying input until the bound document changes, the exact signal is structurally gone, or the 7-second receipt budget expires. Ambiguity or budget exhaustion MUST remain an unconfirmed receipt and MUST NOT authorize another action.

#### Scenario: Pre-action cover still blocks login submission
- **WHEN** the Facebook login submit control is covered before Native dispatches input
- **THEN** Native reports no actionable login submit signal and performs no click

#### Scenario: Post-click loading cover is transitional evidence
- **WHEN** Native has dispatched the bound login submit action and the same submit control remains structurally present but becomes non-topmost under a loading cover
- **THEN** the postcondition remains unsatisfied and does not report the signal gone
- **AND** Native continues only the existing bounded postcondition observation without replaying the click

#### Scenario: Navigation confirms the submitted login action
- **WHEN** a temporarily covered login submit control is followed by a bound document or route transition to the supported Facebook 2FA page
- **THEN** Native confirms the original action from the document transition
- **AND** the coordinator discards the old observation and obtains a fresh 2FA probe before any further input

#### Scenario: Unchanged target after the receipt budget is not replayed
- **WHEN** the loading cover clears or the bounded receipt budget ends without document movement or structural signal disappearance
- **THEN** Native does not confirm the action and the coordinator MUST NOT replay the consumed signal id

#### Scenario: TOTP submit uses the same post-action distinction
- **WHEN** an already-dispatched Facebook 2FA submit control becomes temporarily non-topmost while the bound document is unchanged
- **THEN** that cover does not prove the 2FA submit signal disappeared
- **AND** Native preserves the same bounded, no-replay, fail-closed receipt behavior

### Requirement: Facebook TOTP entry SHALL use one guarded CDP insertion

For the Facebook TOTP field only, Native MUST bind one unique, visible, editable, topmost input in the current document, focus it through CDP, and insert the complete six-digit broker code with one CDP `Input.insertText` call. It MUST NOT assign the DOM value or synthesize JavaScript input or keyboard events. The input binding MUST remain stable across value-driven geometry changes, and Native MUST confirm an exact six-digit same-field readback before allowing submission.

#### Scenario: Email login advances through a paste-like TOTP entry
- **WHEN** a freshly started Facebook environment advances from the filled email/password login page to a supported empty TOTP page
- **THEN** Native enters the complete broker code in one guarded CDP insertion
- **AND** obtains an exact same-field readback before dispatching the bound Continue control

#### Scenario: TOTP layout reflows after insertion
- **WHEN** inserting the code changes the TOTP input's geometry without replacing the input or document
- **THEN** the stable structural binding still identifies the same focused input
- **AND** geometry change alone does not turn the confirmed full insertion into a one-digit or target-lost result

#### Scenario: Continue hydrates after confirmed TOTP entry
- **WHEN** Native has confirmed the complete six-digit value in the coordinator-owned window but zero exact Continue controls are currently rendered
- **THEN** Edge performs no click and continues bounded read-only polling with the entered-window witness intact
- **AND** a later unique topmost Continue may become actionable while ambiguity or occlusion remains blocked

#### Scenario: Continue is outside the TOTP input form
- **WHEN** the supported TOTP page contains one exact visible Continue control outside the input's nearest form and the control shares a non-root structural ancestor with that exact input
- **THEN** Native may bind that page-wide unique visible control to the TOTP submit signal
- **AND** it still requires enabled and topmost state before any CDP click

#### Scenario: Hidden Continue template accompanies the visible action
- **WHEN** one eligible visible Continue and one or more hidden exact-label templates exist in the current document
- **THEN** hidden templates do not compete with the visible action candidate
- **AND** post-action verification still inventories them so the original bound target becoming hidden cannot prove disappearance

#### Scenario: Continue is not yet actionable
- **WHEN** the unique structurally bound Continue control is hidden, native-disabled, has a `disabled` attribute, or declares `aria-disabled=true`
- **THEN** Edge performs no click and treats the state as bounded hydration
- **AND** a fresh enabled observation is required before Native may dispatch input

#### Scenario: Out-of-form candidates remain fail-closed
- **WHEN** visible exact Continue controls are multiple, the unique visible control is covered, belongs to another form or dialog, or shares only the page root with the TOTP input
- **THEN** Native emits no actionable submit signal and performs no click
- **AND** post-action observation cannot use that state or geometry-only movement as proof that a previously bound signal disappeared

#### Scenario: TOTP expires while Continue is hydrating
- **WHEN** the owned TOTP window becomes stale before a unique topmost Continue control appears
- **THEN** Native clears the exact unchanged field through CDP, confirms it empty, and obtains a new broker code for a fresh window
- **AND** no old code or submit action is replayed

### Requirement: Orphan TOTP text SHALL recover without unsafe submission or restart loops

A TOTP value without the current coordinator's entered-window witness MUST NOT be submitted. On a proven fresh browser start, Native MAY clear the exact bound non-empty TOTP field and confirm it empty before requesting a new code. On an already-active browser without fresh-start authority, Edge MUST perform no TOTP mutation and SHALL retain the session as manual-required instead of terminating with a process error. Non-confirmed auth actions SHALL preserve their bounded Native receipt reason for diagnosis.

#### Scenario: Fresh start finds a partial orphan code
- **WHEN** a proven fresh browser start reaches a supported TOTP field containing residual text without a coordinator-owned entered window
- **THEN** Native clears the exact field, confirms it empty, and obtains a fresh probe before any new code entry
- **AND** never submits the residual value

#### Scenario: Fresh start finds a complete orphan code
- **WHEN** a proven fresh browser start reaches a supported TOTP field containing six residual digits without a coordinator-owned entered window
- **THEN** the clear action re-probes the same value as clear-only refresh evidence and never manufactures an entered-window submit witness
- **AND** a changed value invalidates the observed clear signal before any key event

#### Scenario: Active browser finds orphan TOTP text
- **WHEN** an already-active browser lacks fresh-start authority and contains residual TOTP text
- **THEN** Edge performs no input or submit action
- **AND** reports manual-required while retaining the browser instead of entering an abnormal restart loop

#### Scenario: Active-browser orphan field becomes empty
- **WHEN** an already-active browser lacks fresh-start authority and its retained TOTP field becomes empty
- **THEN** Edge still performs no automatic TOTP input and remains manual-required
- **AND** the desktop reports a 2FA `需处理` state rather than exiting the child process with code 1

#### Scenario: Read-only authentication probes remain unavailable
- **WHEN** bounded transient authentication probes exhaust their retry budget and the retained browser requires inspection
- **THEN** Electron accepts only the explicit probe-unavailable manual reason, releases the serial launch waiter, and reports `需处理`
- **AND** unknown probe or coordinator failures remain outside the manual allowlist
