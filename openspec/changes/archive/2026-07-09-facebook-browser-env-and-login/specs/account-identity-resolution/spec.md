## ADDED Requirements

### Requirement: Facebook identity reader returns stable platform id or fails honestly

The Facebook platform driver SHALL implement identity reading that returns a stable Facebook account identifier suitable for `accounts.account_id` registration/routing, plus an optional display name. Identity candidates MUST come from logged-in page/session signals that are stable enough for routing; raw session tokens, cookies, or display names alone MUST NOT be used as the account primary key. If no stable id can be read or candidates conflict, edge MUST fail honestly and MUST NOT fall back to `default`.

#### Scenario: Stable Facebook id read succeeds
- **WHEN** a logged-in Facebook AdsPower profile exposes a consistent stable account id through approved identity signals
- **THEN** edge uses that stable id in hello/account routing and may expose display name separately

#### Scenario: Display name alone is insufficient
- **WHEN** Facebook UI shows a name but no stable id candidate can be verified
- **THEN** edge does not use the name as account id, fails identity resolution honestly, and does not start account-scoped actions

#### Scenario: Conflicting identity candidates fail
- **WHEN** two identity candidates disagree for the same profile/session
- **THEN** edge treats identity as inconclusive, reports failure, and does not guess or fall back to `default`

### Requirement: Facebook login probe distinguishes logged-out from empty content

The Facebook identity/login probe SHALL distinguish logged-out/login-wall/checkpoint states from a legitimate page with no candidate posts. Logged-out or blocked states MUST produce login/blocking outcomes, not `no_strong_candidate`, empty feed, or other harmless browse outcomes.

#### Scenario: Logged-out page is not empty feed
- **WHEN** a Facebook target renders login UI or redirects to login while probing
- **THEN** the probe returns a login-required/blocking result and prevents account work, rather than reporting no candidate posts
