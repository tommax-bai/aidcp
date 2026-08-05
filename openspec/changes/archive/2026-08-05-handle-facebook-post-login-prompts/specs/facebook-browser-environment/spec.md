## ADDED Requirements

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
