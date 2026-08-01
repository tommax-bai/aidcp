## ADDED Requirements

### Requirement: Fleet UI SHALL expose the exact controlled Facebook manual-login state

The Electron supervisor SHALL accept a generation-scoped local auth-required notification from the running core, retain the exact safe reason `credential_fill_unavailable`, and project the environment as requiring Facebook login while the browser remains controlled. The serial launch wait SHALL be released, but the browser execution slot SHALL remain occupied until login succeeds or browser close is confirmed.

#### Scenario: Credential fill reason is visible
- **WHEN** the core reports `manual_login_required` with reason `credential_fill_unavailable`
- **THEN** the client shows “需要登录：AdsPower 未填充账号密码” for that environment
- **AND** “显示浏览器” remains available

#### Scenario: Waiting environment does not block serial launch startup
- **WHEN** one environment enters controlled manual-login wait
- **THEN** Electron releases that environment's serial launch-ready waiter so another admitted environment may start
- **AND** it continues counting the retained browser as an occupied execution slot

#### Scenario: Stable identity clears manual attention
- **WHEN** the same core reports the existing stable account identity event
- **THEN** Electron clears the manual-login reason and projects the normal authenticated startup state
