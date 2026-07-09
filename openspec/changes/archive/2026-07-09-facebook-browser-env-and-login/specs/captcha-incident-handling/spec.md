## ADDED Requirements

### Requirement: Facebook checkpoint and login states are detected by URL/location

For Facebook platform sessions, overlay detection SHALL include URL/location classification in addition to DOM masks/dialogs/iframes. URLs or routes indicating `/checkpoint`, login walls, account recovery, temporarily blocked states, or equivalent full-page blocking states MUST be classified as blocking incidents and reported through the existing captcha/risk incident path. Detection MUST fail closed before posting or other account-scoped actions.

#### Scenario: Checkpoint URL stops automation
- **WHEN** a Facebook session navigates to a URL containing a checkpoint route
- **THEN** edge classifies the page as blocked, reports the incident through the existing risk/captcha path, and does not continue browsing or commenting

#### Scenario: Login wall stops automation
- **WHEN** a Facebook session lands on a login wall while account-scoped work is expected
- **THEN** edge reports login/identity loss and stops assigning work to that account, rather than treating the page as empty results

### Requirement: Facebook overlay detection runs before submit attempts

Facebook comment submit or other account-scoped actions SHALL perform a fresh blocking-state check immediately before the action. If URL/location or DOM classification indicates checkpoint/login/temporarily blocked state, the action MUST fail honestly and MUST NOT submit.

#### Scenario: Fresh pre-submit check blocks unsafe submit
- **WHEN** a Facebook comment editor was previously available but the page enters checkpoint/login state before submit
- **THEN** the pre-submit blocking check fails the action honestly and no submit key/click is sent
