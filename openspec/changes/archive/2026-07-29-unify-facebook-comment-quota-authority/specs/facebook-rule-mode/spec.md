## ADDED Requirements

### Requirement: Rule-mode join-contact preflights comment capacity before joining

Before a Facebook rule round dispatches its join-contact orchestrator, Cloud SHALL preflight both the comment `RiskController` decision and the active session comment budget. If either is unavailable, blocked or exhausted, the round MUST terminate without dispatching a group join and MUST persist a truthful partial outcome with `join_state=not_started`, `comment_state=risk_suppressed` and the stable blocker.

The preflight MUST NOT reserve quota or replace the existing just-in-time comment gates. After membership is confirmed and immediately before comment submission, Cloud SHALL re-read the comment gate so a state or quota change fails closed.

#### Scenario: Daily comment quota is full before join

- **WHEN** a rule round reaches its join-contact position and `RiskController.explain('comment')` returns `quota:day`
- **THEN** Cloud MUST NOT dispatch the group join
- **AND** the round records `join_state=not_started`, `comment_state=risk_suppressed` and `blocker=quota:day`

#### Scenario: Comment session budget is exhausted before join

- **WHEN** the durable safety quota allows comment but the active session has no remaining comment budget
- **THEN** Cloud MUST NOT dispatch the group join
- **AND** the round records the stable `comment_session_budget` blocker

#### Scenario: Admission changes after preflight

- **WHEN** the comment preflight allowed the round but the just-in-time comment gate rejects after membership confirmation or before submission
- **THEN** Cloud MUST preserve the confirmed join outcome, MUST NOT submit the comment and MUST report the current rejection reason

### Requirement: Rule-mode result notifications identify their real source

Combined join-comment result notifications created by `facebook_rule_batch` SHALL identify themselves as `Facebook 规则模式`. They MUST NOT use the default manual `/comment` command label. Manual `/comment` result notifications SHALL retain their existing command label.

#### Scenario: Automatic rule result is not presented as a manual command

- **WHEN** a Facebook rule batch produces a combined join-comment terminal notification
- **THEN** the notification source is `Facebook 规则模式`
- **AND** the card MUST NOT claim that an operator issued `/comment`

#### Scenario: Manual command keeps its label

- **WHEN** an operator-issued `/comment --join` produces a combined result notification
- **THEN** the notification continues to identify the manual `/comment` source
