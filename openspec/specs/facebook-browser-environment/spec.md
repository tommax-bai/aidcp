# facebook-browser-environment Specification

## Purpose
TBD - created by archiving change facebook-browser-env-and-login. Update Purpose after archive.
## Requirements
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

### Requirement: Facebook storage probe redacts all secret values

The Facebook storage probe SHALL inspect cookies, localStorage, sessionStorage, IndexedDB, and service-worker/cache presence only to the extent needed to understand persistence shape. Probe output MUST NOT include raw cookie values, token values, raw localStorage/sessionStorage key names, raw IndexedDB/cache names, IndexedDB record payloads, request headers, or credentials. It MAY include origin names, counts, expiry presence, value length buckets, redacted key/name hashes, and boolean/token-like presence markers.

#### Scenario: Storage summary omits values
- **WHEN** the storage probe runs on a logged-in Facebook profile
- **THEN** the output contains only redacted metadata such as counts/origins/key-name hashes and contains no raw cookie, token, localStorage key, sessionStorage key, IndexedDB/cache name, IndexedDB payload, or header values

### Requirement: Facebook page structure probes map Page, Group, and post surfaces

Read-only Facebook probes SHALL collect current page URL, page type, post container candidates, permalink/id candidates, author/text/comment-count candidates, visible comment region shape, and virtualization/expand-controls observations for operator-specified Page, Group, and post URLs. Probes MUST NOT click publish/submit controls or mutate account state unless an explicit gated-post mode is enabled.

#### Scenario: Read-only structure probe does not mutate
- **WHEN** the page structure probe runs against a Facebook Page, Group, or post URL without gated-post mode
- **THEN** it records structural observations and screenshots/logs safe metadata only, and does not submit comments, reactions, follows, joins, or posts

### Requirement: Facebook comment editor probe is read-only by default

The comment editor probe SHALL locate and focus the Facebook comment editor, test whether text enters the controlled model, observe send-button enablement, then clear or abandon the editor without submitting by default. Any real submit test MUST require an explicit env flag, a disposable account, and an operator-supplied test target.

#### Scenario: Editor input probe does not submit by default
- **WHEN** the comment editor probe runs without the gated submit flag
- **THEN** it may focus/type/clear in the editor but MUST NOT press Enter or click a submit/send control that posts a comment

#### Scenario: Gated submit requires explicit target
- **WHEN** the gated submit flag is set but no disposable test target URL is provided
- **THEN** the probe refuses to submit and reports configuration error

### Requirement: Phase-0 gates block scheduled comment implementation

`facebook-browser-env-and-login` SHALL define and record Phase-0 outcomes before `facebook-scheduled-comment` can start: F1 server-confirmed comment verification feasibility, F2 URL/location checkpoint/login detection, and F3 AdsPower/CDP profile stability under low-frequency realistic use. Any failed gate MUST stop the scheduled-comment change until the design is revised.

#### Scenario: F1 failure blocks later commented success path
- **WHEN** the gated post probe cannot distinguish optimistic local rendering from server-confirmed comment acceptance
- **THEN** later Facebook automation MUST NOT report `commented`; `facebook-scheduled-comment` remains blocked pending redesign

#### Scenario: F2 failure blocks later automation
- **WHEN** checkpoint/login/full-page blocked states cannot be reliably detected by URL/location and page state
- **THEN** later automation remains blocked because it cannot fail closed safely

#### Scenario: F3 failure blocks later automation
- **WHEN** a disposable AdsPower Facebook profile checkpoints quickly under low-frequency probe operation
- **THEN** later scheduled-comment automation remains blocked pending provider/fingerprint/operator workflow review

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

### Requirement: Unavailable Facebook credential fill SHALL preserve a controlled manual-login session

When Native confirms one visible Facebook login form but AdsPower has not filled its credential fields after the bounded fill grace, edge SHALL enter `manual_login_required` with reason `credential_fill_unavailable`. Edge MUST stop automated auth actions, keep the current core/browser/CDP generation alive, and MUST NOT exit or relaunch solely because credential fill is unavailable.

#### Scenario: Empty credential fields enter manual login
- **WHEN** the unique Facebook login form remains empty after the credential-fill grace
- **THEN** Native returns `manual_login_required` with reason `credential_fill_unavailable`
- **AND** the core remains alive with browser control available and dispatches no further automated login action

#### Scenario: Manual login resumes in place
- **WHEN** the operator completes login while the environment is waiting for manual login
- **THEN** edge confirms a stable identity through the existing identity gate and continues startup in the same core and browser generation
- **AND** it MUST NOT call browser launch or perform a new CDP attachment for that recovery

#### Scenario: Manual login wait is explicitly closed
- **WHEN** the operator pauses or closes an environment waiting for manual login
- **THEN** edge closes and confirms the owned AdsPower browser through the existing lifecycle close path before releasing the browser slot
- **AND** the supervisor MUST NOT automatically restart that intentional stop

### Requirement: Facebook authentication checkpoints SHALL receive bounded structural hydration

When Facebook navigates to a checkpoint document during authentication, Edge SHALL allow that exact document up to 15 seconds to hydrate into a supported authentication signal before classifying an otherwise unknown checkpoint as terminal. This classification SHALL NOT depend on whether the preceding step was login submission, TOTP, or another supported transition. During this window Native SHALL only re-probe structure and MUST NOT replay any preceding action. Explicit credential/code rejection, human verification, restriction or account-lock evidence, ambiguous supported-warning structure, and unsafe action targets SHALL retain their existing fail-closed behavior without gaining action authority from elapsed time.

#### Scenario: TOTP Continue reaches an incomplete checkpoint
- **WHEN** Native has confirmed the TOTP submit action and the newly navigated checkpoint is less than 15 seconds old but has not hydrated a supported structure
- **THEN** Edge SHALL keep the authentication transition pending and re-probe without replaying TOTP entry or submit
- **AND** it MUST NOT report `unsupported_facebook_checkpoint` solely from the checkpoint path during that window

#### Scenario: Automation warning independently hydrates within the window
- **WHEN** any authentication checkpoint stabilizes within 15 seconds as “We suspect automated behavior on your account” with one unique visible topmost `Dismiss` control in the supported scope
- **THEN** Native SHALL emit `automation_warning_dismiss` with a fresh signal id and exact bound target
- **AND** the coordinator SHALL dispatch the existing `facebook_auth_dismiss_warning` action at most once and verify disappearance or document change before continuing
- **AND** this action SHALL NOT require evidence that TOTP or any other particular step preceded the warning page

#### Scenario: Unknown checkpoint remains after the window
- **WHEN** the exact checkpoint document reaches 15 seconds without a supported signal or stable authenticated identity
- **THEN** Edge SHALL fail closed with the safe unsupported-checkpoint reason and SHALL NOT start account-scoped work

#### Scenario: Explicit blocker appears during hydration
- **WHEN** the checkpoint exposes human verification, rejected authentication, restriction/account-lock evidence, ambiguous warning structure, or an unsafe Dismiss target before 15 seconds elapse
- **THEN** Native SHALL preserve the corresponding terminal or blocked result and MUST NOT click or extend action authority because the hydration budget remains

### Requirement: Facebook startup SHALL reconcile supported post-login blockers before account-scoped work

After Native first confirms stable Facebook authentication, Edge SHALL keep the single startup authentication coordinator active for a 15-second quiet window before reading final identity and connecting to Cloud. During this window it SHALL re-probe the current Facebook document serially, MAY execute only explicitly supported fresh Native prompt actions, and MUST NOT start browsing, commenting, Cloud connection, or other account-scoped work while a supported blocker or manual choice remains unresolved.

#### Scenario: Late prompt appears after authentication cookies
- **WHEN** Native first reports `authenticated` and a supported post-login prompt appears during the next 15 seconds
- **THEN** Edge SHALL keep startup in the automatic-login phase and reconcile that prompt through the same Native auth owner
- **AND** it MUST NOT connect to Cloud from the earlier cookie observation

#### Scenario: Authenticated page remains quiet
- **WHEN** Native reports authenticated page state without a supported blocker for 15 continuous seconds
- **THEN** Edge SHALL continue to the existing stable-identity gate and MAY connect to Cloud only after that gate succeeds

#### Scenario: Remember Password appears after authentication
- **WHEN** the exact Facebook Remember Password modal and its unique visible enabled topmost `OK` control appear during the authenticated quiet window
- **THEN** Native SHALL move the CDP pointer to the fresh target, press and release once, and require the existing prompt-disappearance postcondition before startup continues
- **AND** a loading or disabled-button observation alone MUST NOT be reported as confirmed success

### Requirement: Facebook ad-data review introduction SHALL be independently recognized

Native SHALL recognize the first-time Facebook ad-data review introduction only from the conjunction of Facebook origin, `/privacy/consent/`, `flow=ad_free_subscription`, `afs_variant=first_time`, the supported introduction content, and exactly one visible enabled topmost `Get started` control. It MUST NOT reuse the cookie-consent overlay classifier or match a same-label Feed card.

#### Scenario: Exact first-time introduction is actionable
- **WHEN** the supported first-time ad-data review introduction contains one fresh visible enabled topmost `Get started` control
- **THEN** Native SHALL emit `ad_data_review_get_started` with a document-bound signal id and exact pointer target

#### Scenario: Same-label Feed card is not the introduction
- **WHEN** Facebook Feed contains a “manage your ad experience” card with a `Get started` link but the page is not the exact review introduction route and structure
- **THEN** Native MUST NOT emit `ad_data_review_get_started` and MUST NOT click that link under this capability

#### Scenario: Introduction target is ambiguous or unsafe
- **WHEN** the exact introduction has zero or multiple matching controls, or its candidate is hidden, disabled, covered, out of viewport, or not topmost
- **THEN** Native SHALL fail closed before input with a bounded safe reason

### Requirement: Ad-data review start SHALL use Native pointer input and verify the exact successor

For a fresh `ad_data_review_get_started` signal, Native SHALL move the CDP pointer to the target before one atomic left-button press/release. It SHALL observe the original button state and page loading state for up to 30 seconds, but SHALL confirm the action only when the exact successor subscription-versus-free-with-ads choice structure appears. The action MUST NOT use DOM `click()` and MUST NOT replay after any possible dispatch.

#### Scenario: Successor choice hydrates after loading
- **WHEN** Native dispatches the authorized `Get started` pointer action, the original control disappears or becomes disabled during loading, and the exact successor choice structure hydrates within 30 seconds
- **THEN** Native SHALL report the action confirmed once and expose the successor as a manual-choice state

#### Scenario: Loading state does not become a supported successor
- **WHEN** the original control changes or disappears but no supported successor is confirmed within 30 seconds
- **THEN** Native SHALL report an ambiguous post-input outcome and MUST NOT click `Get started` again

#### Scenario: Fresh action probe no longer matches
- **WHEN** action-time revalidation does not reproduce the same document-bound signal id and target
- **THEN** Native SHALL report not-started `stale_auth_signal` and dispatch no pointer input

### Requirement: Facebook ad-data choice SHALL remain manual and retain the current session

When the exact subscription-versus-free-with-ads successor appears, Edge SHALL emit enumerated reason `facebook_ad_data_choice_required`, project the environment as needing attention, and retain the same core/browser/CDP generation without connecting to Cloud. Edge MUST NOT select a subscription, free-with-ads, personalized, less-personalized, Continue, Agree, or OK action on the operator's behalf.

#### Scenario: Manual data choice blocks identity completion
- **WHEN** the exact ad-data choice page is present while Facebook authentication cookies are valid
- **THEN** the retained startup preflight SHALL defer the next identity read and keep the environment in “需要处理”
- **AND** valid cookies alone MUST NOT bypass the unresolved choice

#### Scenario: Operator completes the choice in place
- **WHEN** the operator completes the Facebook choice flow and the same retained browser reaches an authenticated page with no supported blocker for a new 15-second quiet window
- **THEN** Edge SHALL perform the existing stable-identity read and continue startup in the same process/browser/CDP generation

#### Scenario: Operator pauses or closes during the choice
- **WHEN** pause or close is requested while the ad-data choice remains unresolved
- **THEN** Edge SHALL use the existing confirmed AdsPower browser-close path before exiting and releasing the browser slot

### Requirement: Facebook startup lifecycle interruption SHALL confirm owned browser teardown

Before the normal runtime lifecycle controller is available, Edge SHALL treat an operator pause or close during Facebook startup authentication as a request to stop and confirm the currently owned AdsPower browser. Edge MUST NOT advance to identity, Cloud connection, or account-scoped work after that interruption unless the operator explicitly resumes.

#### Scenario: Close during authenticated quiet-window confirmation

- **WHEN** a Facebook startup authentication coordinator is observing an authenticated quiet window and the operator closes the environment
- **THEN** Edge calls the existing confirmed close operation for that owned AdsPower browser and emits browser-close evidence before exiting the core
- **AND** Electron displays closed only after receiving evidence scoped to the same lifecycle generation

#### Scenario: Startup browser close cannot be confirmed

- **WHEN** the owned browser close operation cannot confirm that the profile CDP endpoint is dark
- **THEN** Edge emits the existing close-failed result, keeps the core at the blocked startup boundary, and releases no browser slot as confirmed closed
- **AND** Electron MUST NOT display the browser as closed or advance the environment to account-scoped work

#### Scenario: Operator retries close after an unconfirmed startup close

- **WHEN** startup is blocked after an unconfirmed close and the operator requests pause or close again
- **THEN** Edge retries the same existing confirmed close operation for the same owned browser generation
- **AND** it exits only after confirmed browser-close evidence is delivered

#### Scenario: Operator resumes after an unconfirmed startup close

- **WHEN** startup is blocked after an unconfirmed close and the operator explicitly resumes
- **THEN** Edge resumes Facebook authentication reconciliation in the same retained browser generation
- **AND** it MUST NOT open a second profile browser or bypass the stable-identity gate

#### Scenario: Intentional core exit lacks browser-close evidence

- **WHEN** an Edge core exits under a local pause or close intent without generation-matched browser-close evidence
- **THEN** Electron reports that browser closure is unconfirmed instead of displaying the browser as closed

### Requirement: Facebook suspension appeal entry is one bounded operator handoff

For a proven fresh managed Facebook start, the reconciler SHALL treat the observed account-suspension appeal entry as one independent `suspension_appeal_start` signal and `facebook_auth_start_suspension_appeal` action. The signal MUST require Facebook origin, a numeric checkpoint route with the canonical Facebook next destination, the observed suspension and appeal instruction structure, and exactly one visible enabled topmost control whose accessible label is `Appeal`. The action SHALL fresh-revalidate the target-bound signal id, use Native CDP pointer movement and press/release, and MUST NOT be replayed after any committed or ambiguous receipt.

The action is confirmed only after bounded polling proves that the original suspension entry is gone and a distinct, complete, non-loading Facebook checkpoint step is present. Confirmation means only that the appeal entry advanced. Edge SHALL then retain the owned browser as `facebook_suspension_appeal_step_required`, block runnable account identity/Cloud startup, and perform no later appeal input or submission.

#### Scenario: Loaded suspension entry has one actionable Appeal clone
- **WHEN** the exact observed suspension checkpoint is complete and its DOM contains a hidden disabled `Appeal` clone plus one visible enabled topmost `Appeal` control
- **THEN** Native binds only the visible enabled topmost control and emits one suspension-appeal signal
- **AND** the hidden clone does not make the actionable target ambiguous

#### Scenario: Appeal entry advances after trusted input
- **WHEN** action-time revalidation returns the same target-bound signal and Native CDP pointer input activates it
- **THEN** Edge polls through bounded loading and confirms only after the original suspension entry is gone and a distinct complete non-loading Facebook checkpoint step is present
- **AND** it reports `facebook_suspension_appeal_step_required`, retains the browser/CDP, and does not establish a runnable account

#### Scenario: Loading or button mutation is not success
- **WHEN** the `Appeal` control disappears, becomes disabled, is covered, or the page shows only loading after the pointer press
- **THEN** Native continues bounded postcondition polling without treating those intermediate changes as success
- **AND** timeout or unreadable/unsupported destination returns an honest ambiguous result with no click replay

#### Scenario: Exact page or target contract is absent
- **WHEN** the origin, numeric checkpoint route, canonical next destination, suspension content, accessible label, visibility, enabled state, uniqueness, or top-hit check does not match
- **THEN** Edge dispatches no pointer input and reports the checkpoint as unsupported or blocked

#### Scenario: Later appeal steps remain operator owned
- **WHEN** a confirmed entry action reaches a later checkpoint step
- **THEN** Edge performs no option selection, text entry, confirmation, verification, or appeal submission
- **AND** a later unsupported checkpoint remains a deferred manual state only in the context of the confirmed appeal-entry handoff, while CAPTCHA and other failures still fail closed

#### Scenario: Operator clears the checkpoint
- **WHEN** the retained browser later reaches a supported authenticated non-checkpoint page after operator handling
- **THEN** the normal fresh auth probe and stable identity gate may resume
- **AND** account/Cloud startup still requires canonical identity readback rather than the earlier Appeal action receipt

### Requirement: Terminal Facebook startup authentication failure SHALL close the owned browser

When the Facebook startup authentication coordinator reaches a terminal failure, Edge SHALL report the existing authentication failure, call the existing confirmed close operation for the AdsPower browser owned by that startup, and then exit the core. It MUST NOT retain that browser merely because normal runtime lifecycle assembly was not reached.

#### Scenario: Unsupported checkpoint stops startup

- **WHEN** startup authentication terminates with `unsupported_facebook_checkpoint`
- **THEN** Edge reports the existing structured authentication failure and invokes the existing owned-browser confirmed close operation before process exit
- **AND** confirmed closure is reported through the existing generation-scoped browser-close evidence

#### Scenario: Browser closure cannot be confirmed

- **WHEN** the existing owned-browser close operation cannot confirm that the startup browser is dead
- **THEN** Edge exits with the original authentication failure and supplies no false browser-close evidence
- **AND** the existing supervisor projection keeps browser closure unconfirmed

#### Scenario: Manual login is still required

- **WHEN** startup authentication returns the existing controlled `manual_required` result
- **THEN** Edge retains the current browser and CDP session under the existing manual-login contract
- **AND** MUST NOT treat that non-terminal state as a terminal authentication failure

