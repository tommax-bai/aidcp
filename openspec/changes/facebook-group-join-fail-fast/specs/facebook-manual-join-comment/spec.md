## MODIFIED Requirements

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
