## ADDED Requirements

### Requirement: /comment --join accepts a specific group URL

The Feishu command `/comment <昵称> --join=<群链接>` SHALL join the specified Facebook group URL for the resolved account, then comment in that group. The URL form MUST be parsed as a trailing switch (any order with `--contact`), leaving the rest as the nickname; a mid-nickname `--join=` token stays part of the nickname (trailing-only). Bare `--join` (no URL) keeps its existing next-from-library behavior. The targeted group MUST be scoped to this account only: the implementation MUST NOT register the URL as a shared, broadly auto-joinable target for other accounts.

#### Scenario: Join a specific URL then comment
- **WHEN** an operator sends `/comment <昵称> --join=<url>` for a Facebook account that is not yet a member of that group
- **THEN** the system MUST join that specific group, and on confirmed membership MUST comment inside it (with contact info only if `--contact` was also given, still via human review)

#### Scenario: Already a member → skip join, comment directly
- **WHEN** the account is already a confirmed member of the specified group URL
- **THEN** the system MUST skip the join edge round-trip and comment directly in that group

#### Scenario: Invalid group URL → honest failure
- **WHEN** the `--join=<url>` value is not a valid Facebook group URL
- **THEN** the system MUST return an honest failure receipt (`invalid_group_url`) and MUST NOT join or comment

#### Scenario: Group owned by another account → honest failure
- **WHEN** the specified group URL is already held by a different account's membership row
- **THEN** the system MUST return an honest failure receipt (`owned_by_other_account`), MUST NOT comment, and MUST NOT impersonate membership

#### Scenario: Non-Facebook account → rejected
- **WHEN** `--join=<url>` is used on a non-Facebook account
- **THEN** the system MUST reject with the existing "仅支持 Facebook" honest receipt

#### Scenario: Red-line reversal — URL form silently falls back to a random library group (forbidden)
- **WHEN** `--join=<url>` is given but the specific-join path is unwired or the URL is invalid, and an implementation instead joins the next group from the shared library
- **THEN** it MUST be treated as a violation and not merged; the URL form MUST fail honestly, never join a different group

#### Scenario: Red-line reversal — URL form creates a shared auto-join target (forbidden)
- **WHEN** an implementation registers the `--join=<url>` group as an `enabled` shared target so the auto-join sweep hands it to other accounts
- **THEN** it MUST be treated as a violation and not merged; the target row backing the per-account membership MUST be `enabled=false`
