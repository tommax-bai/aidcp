## ADDED Requirements

### Requirement: Facebook automatic browse establishes Feed before its initial scan

Every new or resumed Native-only Facebook automatic browse session SHALL navigate to the canonical Facebook home Feed before reading or reporting its first card batch. The Edge MUST NOT treat the fingerprint browser's persisted last page as the session baseline, even when that page is a valid Facebook Reel, profile, group, search, notification, publish, or content-detail surface. Only a later explicit Cloud command may move the session away from Feed. Failure to establish or inspect the canonical Feed MUST surface honestly and MUST NOT fall back to reporting cards from the persisted page.

#### Scenario: Persisted Reel is reset to Feed

- **WHEN** a Facebook automatic browse session starts while the attached browser is on `/reel/<id>`
- **THEN** the Native adapter navigates to `https://www.facebook.com/` before its initial scan and reports only the resulting Feed state

#### Scenario: Persisted excursion page is reset to Feed

- **WHEN** a Facebook automatic browse session starts or resumes on a profile, group, search, notification, publish, or content-detail page
- **THEN** the Native adapter establishes the canonical home Feed before reporting the first card batch

#### Scenario: Failed Feed reset does not reuse the old page

- **WHEN** the canonical home navigation or its post-navigation readiness check fails
- **THEN** the startup command returns an honest failure and emits no card batch derived from the persisted page

#### Scenario: Other platforms keep their startup behavior

- **WHEN** a Xiaohongshu or WeChat Channels runtime starts
- **THEN** it does not execute the Facebook home-baseline branch and retains its existing platform startup behavior
