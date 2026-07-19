## MODIFIED Requirements

### Requirement: Facebook checkpoint and login states are detected by URL/location

For Facebook platform sessions, overlay detection SHALL include URL/location classification in addition to DOM masks/dialogs/iframes. Positive captcha evidence—captcha vendor iframe/URL or explicit human-verification/captcha semantics—MUST be classified as `captcha` and reported immediately through the existing captcha/risk incident path. A generic `/checkpoint` route or broad security-check copy without positive captcha evidence MUST remain blocking and fail closed, but SHALL be classified as `unknown` and use the existing persistence-confirmed incident path rather than being called a captcha solely from the route. Login walls, account recovery, and two-step verification routes SHALL be classified as identity/login blocks. Detection MUST fail closed before posting or other account-scoped actions.

#### Scenario: Generic checkpoint stops automation without claiming captcha evidence
- **WHEN** a Facebook session navigates to a URL containing `/checkpoint` but the scan has no captcha iframe and no explicit human-verification/captcha text
- **THEN** Edge immediately stops account-scoped automation, classifies the page as `unknown`, and reports it only after the existing persistence confirmation
- **AND** Edge MUST NOT report `kind:'captcha'` solely because the URL contains `/checkpoint`

#### Scenario: Checkpoint with positive captcha evidence remains immediate
- **WHEN** a Facebook checkpoint page contains a captcha vendor iframe or explicit human-verification/captcha semantics
- **THEN** Edge classifies it as `captcha`, immediately reports the incident through the existing risk/captcha path, and does not continue browsing or commenting

#### Scenario: Login wall stops automation
- **WHEN** a Facebook session lands on a login, recovery, or two-step-verification wall while account-scoped work is expected
- **THEN** Edge reports login/identity loss and stops assigning work to that account, rather than treating the page as empty results or a proven captcha

## ADDED Requirements

### Requirement: AIDCP persona notice cannot be captcha evidence

Facebook captcha classification SHALL be derived from the controlled page URL, page-readable semantics, and captcha iframe/vendor evidence. The Electron-injected AIDCP persona notice host or its Shadow DOM content MUST NOT count as captcha evidence and MUST NOT alter the Facebook location classification.

#### Scenario: Persona notice is present on a normal Facebook page
- **WHEN** the AIDCP persona reminder is injected while the Facebook URL and page contain no blocking evidence
- **THEN** overlay classification remains `none` and no captcha/risk incident is reported

