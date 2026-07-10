## ADDED Requirements

### Requirement: Driven browser denies permission prompts by default
The edge browser startup path SHALL prevent native permission prompts (notifications, geolocation, camera, microphone, and other capability prompts) from interrupting automated browsing in the driven fingerprint browser, for both the AdsPower and self providers. Suppression SHALL deny rather than grant, and MUST NOT remove or replace any web permission API in a way that diverges from a normal browser where the user has blocked the permission.

#### Scenario: Fresh launch suppresses prompts before any page loads
- **WHEN** a driven browser is launched by either provider
- **THEN** the launch arguments include a switch that auto-denies permission prompts, so no permission dialog is shown for the first or any subsequent page

#### Scenario: A site requests notification permission
- **WHEN** the driven page requests notification permission
- **THEN** the request is denied without a visible prompt
- **AND** the browser does not surface an "allow notifications" dialog to the operator

#### Scenario: Reported permission state stays internally consistent under anti-detection
- **WHEN** anti-detection injection is active (self provider) and notifications are denied
- **THEN** `navigator.permissions.query({name:'notifications'})` reports `denied`, matching `Notification.permission`
- **AND** it does not report `prompt` while `Notification.permission` is `denied`, which would be a detectable inconsistency

### Requirement: Permission-prompt suppression survives reuse and reconnect
Because a launch switch cannot reach an already-running browser, the edge attach path SHALL apply an authoritative CDP permission override that denies the same set of permissions after CDP attach, and SHALL re-apply it after every reconnect. The override SHALL be best-effort: a failing permission override MUST NOT abort attach or crash the session.

#### Scenario: Reused browser instance is still silenced
- **WHEN** edge attaches to a browser that was already running before this launch (AdsPower hands back a live profile, or self reuses an open CDP port) and therefore never received the launch switch
- **THEN** edge applies the CDP permission denial after attach so prompts are still suppressed

#### Scenario: Reconnect re-applies the denial
- **WHEN** edge transparently reconnects to the driven page after a dropped CDP connection
- **THEN** it re-applies the permission denial together with domain re-enable and anti-detection re-injection

#### Scenario: Permission override failure is non-fatal
- **WHEN** a CDP permission override call rejects (e.g. an unsupported permission name on a given browser build)
- **THEN** edge continues attach and operation normally rather than aborting or reporting a false failure
