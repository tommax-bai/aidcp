# facebook-group-comment-coverage Specification

## Purpose
TBD - created by archiving change facebook-group-join-and-commenting. Update Purpose after archive.
## Requirements
### Requirement: Daily coverage iterates an account's joined groups oldest-covered-first

The coverage selector SHALL, per account, select from that account's own joined groups the least-recently-covered ones past a per-group cooldown floor, then pick within a small window to avoid lock-step ordering. It MUST guarantee eventual coverage of every joined group without repeatedly commenting in the same few groups, and MUST only comment in groups the account itself has joined. When no joined group satisfies warmup/cooldown and the relaxed fallback is enabled, the selector SHALL fall back to joined groups ordered least-recently-commented; the relaxed result MUST be flagged for human review and MUST still exclude non-joined or left groups.

**放开兜底的默认极性 SHALL 为关闭**，且 MUST 只能由显式配置开启。缺少配置、配置为空或取值无法识别时，选群口 SHALL 走严格模式：一个合规群都没有就本轮不评论，MUST NOT 退而求其次去评一个不满足预热或仍在冷却中的群。

该默认值 MUST 由代码承载，MUST NOT 仅依赖运行时配置来维持。理由是失效模式：运行时配置文件不进版本库、部署时被显式排除，因此「它应该是关的」这件事在代码库里没有任何记录；换机、重建或从更早备份恢复都会让它静默回到开启，而且**不报错、不告警、日志里也看不出来**。把默认极性放在代码里，是让这条安全姿态跟着版本走、而不是跟着某一台机器上的一个文件走。

放开兜底 SHALL 被理解为一次**具名的临时放宽**，而不是一个常备档位：它在最需要预热与冷却的时刻把这两道闸丢掉，因此开启它 MUST 是一个显式且可追溯的决定。

#### Scenario: Coverage rotates and does not hammer
- **WHEN** an account has many joined groups and a daily coverage slice
- **THEN** the least-recently-covered eligible group is chosen and a just-commented group is not selected again until its cooldown floor passes

#### Scenario: Only joined groups are commented
- **WHEN** the coverage selector runs for an account
- **THEN** it never comments in a group that account has not joined

#### Scenario: Relaxed fallback still chooses least-recently-commented joined groups
- **WHEN** all of an account's joined groups are inside warmup or cooldown and relaxed fallback is enabled
- **THEN** the selector chooses from `status='joined'` groups ordered by least-recently-commented and flags the result as relaxed for review

#### Scenario: 未配置时走严格模式
- **WHEN** 放开兜底的配置缺失、为空或取值无法识别，且账号名下所有已加入群都处在预热期或冷却中
- **THEN** 本轮不评论、不加群，如实回报无可用目标，MUST NOT 选中任何不合规的群

#### Scenario: 只有显式开启才放开
- **WHEN** 运维显式把放开兜底配置为开启，且账号名下所有已加入群都不合规
- **THEN** 选群口按最久没评排序选出一个已加入群，并把结果标记为放开态交人把关

### Requirement: Auto contextual comments run unattended and carry no contact info

Mode (a) auto-generated contextual comments SHALL run on the existing unattended hard-validator path and MUST NOT contain contact info, URLs, or spam phrases (the existing Facebook validators reject these). This is the scalable daily-coverage mode.

#### Scenario: Contact info in an auto comment is rejected
- **WHEN** an auto contextual coverage comment would contain contact info
- **THEN** the existing validators reject it and no submit occurs, and it is not repaired into a post

### Requirement: Contact comments route through the human-reviewed lane, not the unattended path

Mode (b) contact/lead-gen comments SHALL route through the existing human-reviewed lane (per-account verbatim contact injection plus Feishu approval before the edge posts), never the unattended validator path. The account's contact string missing MUST fail closed by default (no post, no silent downgrade to a no-contact comment). A validator carve-out MUST exempt only the injected contact span, not the composed body.

A single named exception SHALL exist: when the caller explicitly declares a plain-comment fallback, a missing contact string MAY instead produce a comment without contact info. This exception is granted only to the Facebook rule-mode join-contact leg. The fallback intent MUST be passed explicitly per invocation and the shared gate's default MUST remain fail-closed.

A comment produced by that fallback SHALL be treated as a plain comment for approval purposes: its effective approval mode MUST be resolved from the account's plain-comment approval configuration, NOT from the contact-comment configuration. An account-level blanket auto-approval MUST likewise be applied per the plain-comment lane. Cloud MUST NOT let an authorization granted for contact comments extend to a body that was never authorized under that lane.

Enabling the fallback SHALL be understood as authorizing a real platform join that would not otherwise occur: with the contact gate no longer stopping the chain before the join stage, the join executes and consumes its own risk quota and session budget even when the comment later fails.

#### Scenario: Contact comment requires approval before posting
- **WHEN** a contact/lead-gen comment is composed for a joined group
- **THEN** it is sent to Feishu human review and is posted only after a human approves it

#### Scenario: Missing contact string fails closed
- **WHEN** a contact comment is requested for an account with no configured contact string and no fallback was declared
- **THEN** the system produces an honest no-op and does not post a contactless comment

#### Scenario: Declared fallback posts a plain comment under the plain-comment lane
- **WHEN** the rule-mode join-contact leg declares the fallback for an account with no contact string
- **THEN** the composed body is routed by the plain-comment approval configuration and MUST NOT inherit the contact-comment lane's auto-approval

#### Scenario: Contact-lane auto-approval does not silently release a fallback comment
- **WHEN** an account has contact comments set to auto-approve and plain comments set to human review, and the fallback produces a plain comment
- **THEN** that comment goes to human review

#### Scenario: Fallback makes the join really happen
- **WHEN** the fallback is declared for an account with no contact string
- **THEN** the join stage executes against its own risk and budget gates rather than the chain terminating before the join

### Requirement: An account does not comment in a group the day it joined it

The ordinary coverage loop SHALL enforce a join-to-first-comment warmup interval: a group becomes eligible for unpinned coverage only after a bounded delay following its `joined_at`, so ordinary coverage, persona-mode comments and standalone automatic joins do not join and immediately comment in the same group on the same day.

The sole exception SHALL be a caller-pinned group joined by the same fixed Facebook rule batch. After the join stage returns platform-confirmed `joined` or `already_member` for the exact group, slow start is confirmed not active, and every comment/contact/approval/risk gate passes, that batch MAY continue to a contact comment without waiting for ordinary coverage warmup. The exception MUST NOT make the group generally warmup-eligible, MUST NOT apply to an ambiguous/pending/failed join, and MUST NOT be inferred from a bare group URL or membership row without the rule batch correlation.

#### Scenario: Same-day ordinary coverage is not commented
- **WHEN** an account joined a group earlier the same day and an unpinned coverage run considers it
- **THEN** the coverage loop does not select that group until the warmup interval has elapsed

#### Scenario: Confirmed rule batch may continue in its pinned group
- **WHEN** the same Facebook rule batch joined exact group G with a platform-confirmed result, slow start is not active and all comment gates allow
- **THEN** the batch may select and contact-comment in pinned group G without making G available to ordinary coverage

#### Scenario: Slow start prevents the scoped exception
- **WHEN** slow start becomes active before the rule batch's comment dispatch
- **THEN** the comment is not dispatched and the same-day warmup exception is not applied

#### Scenario: Unconfirmed join never receives the exception
- **WHEN** the rule batch's join result is pending, ambiguous, gated, failed or lacks the exact confirmed group identity
- **THEN** no comment starts and ordinary warmup behavior remains unchanged

### Requirement: Ledger demotion is not driven by unreliable whole-page signals

Demoting a membership from `joined` to `left` SHALL NOT be driven by an unreliable whole-page membership text signal. Demotion MUST require repeated confirmation across attempts, aligning with the anti-pollution stage/promote discipline. A group that is confirmed deleted or permanently inaccessible MUST also be demotable so it stops consuming coverage slots.

#### Scenario: A single ambiguous permission signal does not demote a valid membership
- **WHEN** one coverage attempt sees an ambiguous permission-gated signal in a group the account is actually a member of
- **THEN** the membership is not immediately demoted to `left`; demotion requires repeated confirmation

### Requirement: Coverage shares single-flight and activity budget with the join loop

The coverage loop and the join loop SHALL run on the same per-account single-flight so a Facebook edge (physically single-slot) is never asked to join and comment at once, and their combined daily activity MUST be bounded against platform tolerance rather than each cap being spent independently.

#### Scenario: Join and comment do not run concurrently on one account
- **WHEN** an account has both a pending join slot and a pending coverage slot
- **THEN** only one is dispatched at a time under the per-account single-flight lock

#### Scenario: Low membership degrades gracefully
- **WHEN** an account has very few joined groups
- **THEN** the per-group cooldown floor limits coverage to a small safe volume rather than repeatedly commenting the same groups, and zero joined groups is a clean no-op

### Requirement: Joined-group coverage selector is the normal Facebook comment container source

The Facebook comment pipeline SHALL use the joined-group coverage selector as the normal source of comment containers for unpinned Facebook comment attempts. The selector MUST only return groups the account itself has joined (`status='joined'`) and MUST return one concrete group URL for edge to use as `search.execute.container`. It MUST NOT return operator-configured container rows, random imported targets, or any whole-site search sentinel.

#### Scenario: Normal comment uses an account joined group
- **WHEN** an unpinned Facebook comment attempt starts for account A
- **THEN** the selected search container is one of account A's own joined membership rows and edge receives that group URL as the scoped search container

#### Scenario: No joined group does not fall back to legacy containers
- **WHEN** account A has no joined membership rows
- **THEN** the attempt ends with an honest no-targets result and MUST NOT fall back to legacy account-configured containers or whole-site search

