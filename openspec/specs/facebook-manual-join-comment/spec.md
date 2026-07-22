# facebook-manual-join-comment Specification

## Purpose
TBD - created by archiving change facebook-manual-join-comment. Update Purpose after archive.
## Requirements
### Requirement: `/comment` accepts `--join` and combines with `--contact` in any trailing order

The Feishu `/comment <昵称> …` command SHALL accept an optional `--join` flag in addition to the existing `--contact` flag. The parser SHALL consume TRAILING flag tokens (each of `--join` / `--contact`, case-insensitive) in any order, set the corresponding switches, and treat the remaining leading tokens as the account nickname. A flag-looking token that is NOT trailing (appears before a non-flag token) MUST NOT be consumed and stays part of the nickname (the existing trailing-only invariant is preserved). Absence of `--join` MUST behave exactly as before (zero regression).

#### Scenario: `--join` and `--contact` parse in either order
- **WHEN** an operator sends `/comment 工程师大白 --join --contact` or `/comment 工程师大白 --contact --join`
- **THEN** the command resolves nickname `工程师大白`, `joinGroup=true`, and `injectContact=true` in both cases

#### Scenario: `--join` alone
- **WHEN** an operator sends `/comment 工程师大白 --join`
- **THEN** the command resolves nickname `工程师大白`, `joinGroup=true`, and `injectContact` unset

#### Scenario: No `--join` is unchanged
- **WHEN** an operator sends `/comment 工程师大白` or `/comment 工程师大白 --contact`
- **THEN** parsing and behavior are identical to before this change (`joinGroup` unset)

### Requirement: `--join` joins one new group then comments inside it, Facebook-only, human-authorized

With bare `--join`, the resolved account SHALL join exactly ONE new target group from the account's current account-group scoped pool per invocation through the existing group-join scheduler (scoped lazy-claim → scope revalidation → observe → fail-closed judgment → click once → server-verify → membership ledger) and, ONLY on a judgment-confirmed join (`joined`) or an existing membership (`already_member`), publish a comment INSIDE that just-joined group. An ungrouped account or account group with no available mapped target MUST receive an honest `no_targets` outcome and MUST NOT fall back to the global catalog. A page, navigation, observation, render, or lease failure after a target has been claimed MUST be returned as that current attempt's concrete failure and MUST NOT be translated into `no_targets` through a retained cooldown assignment. `--join` SHALL be Facebook-only; for a non-Facebook account it MUST return an honest unsupported outcome and MUST NOT join or comment. The command MUST be human-authorized (subject to the same management-chat scope gate as every other account command) and MUST NOT bulk-join (exactly one join per command). The explicit `/comment <昵称> --join=<url>` form SHALL remain a human-authorized specific-target override outside automatic scope selection while preserving canonical URL validation, global one-group-one-account ownership, platform, kill-switch, single-flight, and physical execution gates.

#### Scenario: Confirmed scoped join then comment in the joined group
- **WHEN** `/comment <昵称> --join` runs for an online Facebook account and the scoped join scheduler returns `outcome=joined` for group G
- **THEN** the command publishes a comment inside group G (search-in-G → open → compose → validate → server-verify) and reports a combined join+comment outcome

#### Scenario: No confirmed join means no comment
- **WHEN** the join scheduler returns any non-member outcome (`gated_skip`, `pending`, `ambiguous_skip`, `join_failed`, `nav_error`, `no_targets`, `scope_mismatch`, `disabled`, `edge_offline`, `quota_denied`, `session_budget`, `running`)
- **THEN** the command MUST NOT publish any comment and MUST report the honest join reason

#### Scenario: Navigation failure is not target exhaustion
- **WHEN** `/comment <昵称> --join` claims a target but opening that group returns `nav_error`
- **THEN** the result reports “打开群页失败” for this attempt and MUST NOT report “没有可加入的新群目标”

#### Scenario: Non-Facebook account is rejected honestly
- **WHEN** `/comment <昵称> --join` targets an account whose platform is not Facebook
- **THEN** the command returns an honest "join is Facebook-only" outcome and neither joins nor comments

#### Scenario: Explicit URL remains a human override
- **WHEN** a human-authorized operator sends `/comment <昵称> --join=<url>` and that URL is not mapped to the account's current group
- **THEN** the specific-target path may still join it for that account, but it MUST NOT enable the target for automatic selection or steal a group globally owned by another account

### Requirement: `--join --contact` posts a contact comment through the human-reviewed lane only

With `--join --contact`, the comment published in the just-joined group SHALL be a contact/lead-gen comment routed through the EXISTING human-reviewed approval lane (verbatim contact-info injection), never the unattended path. If the account has no configured contact info, the command MUST fail closed BEFORE joining is not required — the contact check MAY run before the join — and MUST NOT post a comment without the contact info. `--join` without `--contact` SHALL publish an unattended-style auto contextual comment that MUST NOT carry contact info.

#### Scenario: Contact comment requires configured contact info
- **WHEN** `/comment <昵称> --join --contact` targets an account with no configured contact info
- **THEN** the command returns an honest "contact info not configured" outcome and MUST NOT post any comment (and never a comment without the contact info)

#### Scenario: Contact comment goes through approval
- **WHEN** `/comment <昵称> --join --contact` reaches the comment step after a confirmed join
- **THEN** the composed body plus the verbatim contact info is sent for human approval and is submitted only after approval; on rejection/timeout it is not posted

#### Scenario: Non-contact join-comment carries no contact info
- **WHEN** `/comment <昵称> --join` (no `--contact`) reaches the comment step
- **THEN** the composed comment is validated to carry no contact info and is posted through the unattended composition path

### Requirement: The manual join-comment is single-flight and reports one honest combined outcome

The manual join-then-comment SHALL run under a per-account single-flight lock so a second manual comment/join for the same account is refused while it runs, and it MUST run sequentially (the join fully completes before the comment begins) so one account is never double-driven. The system SHALL post exactly one honest Feishu result card reflecting the true combined terminal state (join outcome and, when applicable, comment outcome), colored by honest-status (never coloring a non-success as success). Background-loop joins/comments for the same account MUST NOT be started while the manual flow holds the lock.

#### Scenario: Second manual command is refused while one runs
- **WHEN** a manual `/comment <昵称> --join` is running for an account and a second `/comment <昵称>` (with or without `--join`) arrives for the same account
- **THEN** the second is refused with an honest "a comment task is already running" outcome and does not drive the edge concurrently

#### Scenario: Combined result card is honest
- **WHEN** the manual join-comment reaches its terminal state
- **THEN** one result card reports the real join outcome and comment outcome, and a partial success (joined but comment failed) is NOT colored as full success

