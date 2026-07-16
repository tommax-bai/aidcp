## MODIFIED Requirements

### Requirement: Manual Feishu publish approvals route to the triggering conversation

When a publish generation is triggered by a Feishu command event, the generated publish approval card SHALL be sent to the same Feishu conversation that delivered that command when the event provides a source `chatId`. A private-chat `/publish` command SHALL therefore receive its approval card in that private chat, and a group-chat `/publish` command SHALL receive its approval card in that group. This routing SHALL hold regardless of whether the command reaches publish generation via the direct trigger path or via the delegated-task orchestration path; a delegated task created from a `/publish` command MUST propagate the command's source `chatId` into the approval-card target resolution.

Publish triggers **without** a source conversation SHALL resolve their approval-card target through the shared account-scoped chat resolution (`来源会话 → 账号团队群 → 默认群`, see `feishu-notification-routing`): an automatic, scheduled, panel/reference, or edge-originated publish for an account whose team key maps to a routed group SHALL send its approval card to that team group, and SHALL fall back to the default approval group only when the account has no team route (or the route lookup fails or the account is absent). Approval-card target resolution MUST NOT terminate at the default group while an account-scoped route is available — the previous "no source conversation ⇒ default group" behaviour is replaced by this three-tier resolution.

Every approval-card send site MUST resolve its target through that one shared resolution, including the edge-originated (v1) publish approval request path; MUST NOT re-implement an inline default-group lookup, because a send site that never calls the resolver produces routing failures that are indistinguishable from misconfiguration and emit no config-gap diagnostics.

The system MUST NOT treat a failed approval-card send as a successful delivery. If the resolved target rejects the card send, the system SHALL log the failed delivery and keep the draft in an honest pending state; it MUST NOT claim that the card was sent.

#### Scenario: Private command receives approval card in private chat

- **WHEN** a Feishu private-message command `/publish <nickname>` triggers a publish generation and the event includes `chatId=P`
- **THEN** the publish approval card is sent to `P`
- **AND** neither the account team group nor the default approval group is used for that manual command

#### Scenario: Group command receives approval card in triggering group

- **WHEN** a Feishu group-message command `/publish <nickname>` triggers a publish generation and the event includes `chatId=G`
- **THEN** the publish approval card is sent to `G`
- **AND** the default approval group is not used for that manual command

#### Scenario: Delegated-path command still reaches the command chat

- **WHEN** a `/publish <nickname>` command is ingested through the delegated-task orchestration path (the active production path) with source `chatId=P` and later reaches publish generation
- **THEN** the publish approval card is sent to `P`
- **AND** the card MUST NOT fall back to the default approval group merely because generation was triggered by the delegated worker rather than the direct trigger

#### Scenario: Scheduled publish approval card goes to the account team group

- **WHEN** an automatic or scheduled publish generation for account `acc-1` (team key `teamA`, `group_route` has `teamA → oc_team_a_chat`) reaches the approval step with no source Feishu `chatId`
- **THEN** the publish approval card is sent to `oc_team_a_chat`
- **AND** the card MUST NOT be sent to the default approval group merely because there is no triggering command conversation

#### Scenario: Edge-originated approval request follows the same resolution

- **WHEN** an edge-originated (v1) publish approval request is raised for account `acc-1` whose team key maps to `oc_team_a_chat`
- **THEN** its approval card is sent to `oc_team_a_chat` through the shared resolution
- **AND** MUST NOT be hard-bound to the default group by an inline lookup

#### Scenario: Unrouted account still uses the default approval group

- **WHEN** a publish generation without a source `chatId` reaches the approval step for an account that has no team key, whose team key matches no `group_route` row, or whose route lookup fails
- **THEN** the publish approval card is sent to the default approval group
- **AND** MUST NOT be silently dropped

#### Scenario: Approval card send failure is honest

- **WHEN** the chosen Feishu approval target rejects the approval card send
- **THEN** the failure is logged with the request or record context
- **AND** the system MUST NOT report that the approval card was successfully sent
