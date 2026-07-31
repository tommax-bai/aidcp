## MODIFIED Requirements

### Requirement: Facebook profile startup uses AdsPower/CDP without credential automation

edge SHALL support starting or attaching to a Facebook AdsPower profile through the existing browser-provider/CDP boundary. A profile that is already logged in SHALL proceed directly to the stable-identity gate. A newly started imported profile that is logged out MAY receive the bounded first-login assistance defined below, using AdsPower first-open password filling and Native CDP actions; edge MUST NOT request or type the stored password. CAPTCHA, human verification, device confirmation, recovery, account lock, unfamiliar checkpoints, missing profile id, missing debug port, unavailable credential fill, or unreadable final identity MUST fail honestly before account-scoped work.

#### Scenario: Logged-in Facebook profile attaches through CDP
- **WHEN** `AIDCP_PLATFORM=facebook` and a valid logged-in AdsPower profile id is configured
- **THEN** edge starts or attaches through the existing provider, obtains a CDP endpoint, opens or selects a Facebook tab, performs no login action, and proceeds only after identity probing succeeds

#### Scenario: Cookie names alone do not prove authentication
- **WHEN** the Facebook cookie jar contains auth-cookie names but lacks either a non-empty `xs` value or a numeric `c_user` value satisfying the stable-identity Facebook-domain checks
- **THEN** the Native auth probe MUST NOT emit `authenticated`
- **AND** edge continues fresh structural signal classification or fails honestly without bypassing the stable-identity gate

#### Scenario: Imported logged-out profile receives bounded assistance
- **WHEN** a newly started imported Facebook profile presents one of the explicitly supported first-login signals and the required AdsPower startup policy was applied
- **THEN** edge MAY execute the one matching Native action and re-probe the page
- **AND** it MUST still pass the existing stable-identity gate before browsing, commenting, Cloud connection, or any other account-scoped work

#### Scenario: Unsupported login state fails honestly
- **WHEN** the profile presents CAPTCHA, human verification, device confirmation, recovery, account lock, an unfamiliar checkpoint, empty login credentials, an ambiguous control, or no stable identity before the bounded budget ends
- **THEN** edge reports a safe login/identity failure and does not start account-scoped work

## ADDED Requirements

### Requirement: Facebook first-login assistance reconciles one independent signal at a time

The first-login reconciler MUST treat login submission, 2FA entry, 2FA submission, stale-code clearing, automated-behavior warning dismissal, Facebook push-blocker closure, and Facebook Remember Password confirmation as independent signals and actions. It MUST NOT require or assume a contiguous or fixed signal order. Each actionable observation SHALL carry a non-secret signal id bound to the target, document generation, signal kind, and exact candidate. Each pass SHALL use a fresh Native Page Engine observation, execute at most one action that exactly matches and fresh-revalidates that signal id, verify a same-page or navigation postcondition, discard the observation, and re-probe before any later action. The same signal id MUST NOT be dispatched twice, including after an ambiguous receipt.

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
- **WHEN** the target, document generation, signal kind, or candidate no longer matches the supplied signal id, or the prior action receipt is ambiguous
- **THEN** Native dispatches no new input for that observation
- **AND** the coordinator MUST NOT replay the same signal id

#### Scenario: Long page URL retains a bounded document generation
- **WHEN** a supported Facebook page has a long page-controlled query string
- **THEN** Native represents the document generation with a fixed bounded value whose size is independent of the raw URL length
- **AND** the value remains stable for the unchanged document and URL state, changes after a full navigation or route/query transition, and does not expose the raw query

#### Scenario: Login submission requires AdsPower-filled fields
- **WHEN** the exact visible Facebook login form is uniquely identified
- **THEN** Native MAY submit it only after confirming the username and password fields are non-empty and the submit target is topmost
- **AND** edge MUST NOT obtain or type the stored password

### Requirement: Facebook TOTP entry and submission preserve a ten-second validity floor

TOTP assistance SHALL use a fresh Facebook server-time observation and a 30-second TOTP window. Before code generation and entry, if fewer than 10 seconds remain, edge MUST perform no page mutation, wait for the next window, and re-probe. Code entry and code submission SHALL be separate signal/actions. Before submission, edge MUST recheck server time; if fewer than 10 seconds remain or the entered-code window changed, it MUST clear the field as one action and obtain a new code instead of submitting the old code.

#### Scenario: Entry waits for the next window
- **WHEN** the exact 2FA entry signal is present and the current code has fewer than 10 seconds remaining
- **THEN** edge waits without typing or clicking until a new window is observable
- **AND** it requests and enters only a code generated for that new window

#### Scenario: Fresh code is entered but not implicitly submitted
- **WHEN** at least 10 seconds remain and a profile-bound TOTP code is available
- **THEN** Native enters the code and verifies input readback as the only action for that observation
- **AND** submission requires a later fresh `totp_submit_ready` observation

#### Scenario: Associated label identifies the unique 2FA input
- **WHEN** a confirmed Facebook 2FA page has one visible editable text input whose own attributes have no code meaning but whose browser-associated `label` has exact 2FA code meaning
- **THEN** Native recognizes that input through the `HTMLInputElement.labels` association, including `for`/`id` or a wrapping label, without hard-coding a dynamic id
- **AND** it emits an entry signal only when the matching input is unique and topmost

#### Scenario: Retained manual login advances to supported 2FA
- **WHEN** missing AdsPower credential fill has placed the same owned fresh-start browser in controlled manual-login wait and that page later presents a supported unique 2FA signal
- **THEN** edge serially re-enters the existing Facebook authentication coordinator in the same core and browser generation so that signal has exactly one consumer
- **AND** TOTP entry and submission retain their existing fresh-probe, signal-id, server-time, ten-second floor, and one-action-per-observation requirements

#### Scenario: Manual wait does not create a second auth consumer
- **WHEN** the retained browser remains on the unchanged login page or the next identity poll is due
- **THEN** edge runs authentication reconciliation and identity reading serially under the same lifecycle cancellation
- **AND** it dispatches no login action for another `manual_login_required` result and does not start a parallel DOM watcher

#### Scenario: Retained session lacks current mutation authority
- **WHEN** the retained core no longer owns the browser generation, fresh-start policy evidence is unavailable, or the page presents CAPTCHA, ambiguity, or an unsupported checkpoint
- **THEN** edge performs no automated authentication input and preserves the existing honest manual or terminal outcome

#### Scenario: Nearby text does not label an input
- **WHEN** 2FA wording is present elsewhere on the page but is not browser-associated with a visible editable input, or more than one associated input matches
- **THEN** Native emits no actionable TOTP input signal and dispatches no input

#### Scenario: Code becomes stale before submission
- **WHEN** the 2FA submit signal is observed but fewer than 10 seconds remain or the server-time window differs from the entered-code window
- **THEN** Native clears the code as that pass's only action and edge returns to fresh code entry
- **AND** it MUST NOT submit the stale code

#### Scenario: Server time or TOTP is unavailable
- **WHEN** Facebook server time cannot be read, the exact profile has no valid 2FA key, or the generated code is rejected
- **THEN** edge fails closed and does not fall back to unchecked local time, another profile, a cached code, or repeated submissions

### Requirement: Supported Facebook post-login prompts use exact page signals

The reconciler MAY handle only the observed non-CAPTCHA automated-behavior warning, Facebook push-notification alertdialog, and Facebook Remember Password prompt. Each handler SHALL require an exact visible unique structural target, a top-hit check, Native CDP input, and a verified disappearance or navigation postcondition.

#### Scenario: Automated-behavior warning is dismissible
- **WHEN** the exact observed non-CAPTCHA automation-warning checkpoint and its unique Dismiss control are visible
- **THEN** Native clicks Dismiss once and verifies that the checkpoint signal is gone before re-probing

#### Scenario: Facebook push blocker is closed
- **WHEN** the exact Facebook push-notification alertdialog and its unique top-left Close control are visible and topmost
- **THEN** Native clicks Close once and verifies that the alertdialog no longer blocks the page

#### Scenario: Facebook Remember Password is confirmed
- **WHEN** the exact Facebook Remember Password page modal and its unique OK control are visible and topmost
- **THEN** Native clicks OK once and verifies that the modal is gone

#### Scenario: Browser-chrome prompts are not page signals
- **WHEN** a browser Save Password or native permission bubble would otherwise appear
- **THEN** edge relies on startup and permission policy to suppress it
- **AND** the Facebook reconciler MUST NOT use page DOM, screen coordinates, or GUI automation to operate browser chrome
