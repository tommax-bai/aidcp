## ADDED Requirements

### Requirement: Facebook scheduled contact comment joins a new group before commenting

For a Facebook account, the scheduled internal action key `contact_comment` SHALL execute as “加群评论（联系）”: it MUST invoke the existing join-then-comment orchestrator with `injectContact=true`, `joinFirst=true`, automatic priority, and the account's configured approval mode. It MUST NOT set manual override or force flags. The comment stage MAY begin only after the join stage returns platform-confirmed `joined` or `already_member` with the exact group URL; every pending, gated, ambiguous, failed, or unconfirmed join outcome MUST terminate without commenting.

After membership confirmation, target selection SHALL follow the Facebook keyword rule: configured keywords use group search; no keywords use the group's first eligible post. Existing contact-info, attempt-cap, comment-risk, approval, dedupe, server-verification, account single-flight, and honest combined-result behavior SHALL remain in force.

Non-Facebook scheduled contact comments MUST retain their existing non-join behavior.

#### Scenario: Facebook scheduled contact comment joins then comments
- **WHEN** a Facebook account hits an enabled `contact_comment` schedule slot and all preflight gates pass
- **THEN** the system first attempts one automatic new-group join and only after confirmed membership selects a post, composes/approves, and submits a contact comment

#### Scenario: Unconfirmed join never advances to comment
- **WHEN** the scheduled join returns pending, gated, ambiguous, failed, or otherwise not platform-confirmed as a member
- **THEN** the combined task reports an honest non-commented outcome and dispatches no post selection, approval, or comment submit

#### Scenario: Non-Facebook contact comments do not acquire join semantics
- **WHEN** a non-Facebook account hits its existing scheduled contact-comment slot
- **THEN** the system uses the existing contact-comment path without `joinFirst`

### Requirement: Standalone Facebook automatic join remains join-only

The independent scheduled Facebook `join_group` action SHALL continue to invoke only the Facebook group-join scheduler. Enabling or executing that action MUST NOT implicitly start post selection, composition, approval, or either ordinary or contact comment submission.

#### Scenario: Standalone automatic join has no comment side effect
- **WHEN** the independent Facebook automatic-join action confirms a new membership
- **THEN** it records the join outcome and ends without opening a group post or creating a comment

### Requirement: Facebook scheduled contact comment is labeled 加群评论（联系）

Facebook-facing Console action labels and scheduled execution/result notifications SHALL render the `contact_comment` action as “加群评论（联系）”. The internal action key, API fields, and persistence schema SHALL remain `contact_comment`-compatible. Non-Facebook product surfaces MAY retain the existing contact-comment label.

Clearing all Facebook search keywords MUST be accepted without an error or disabled-state warning. The Console MUST NOT add a “当前使用群内首帖” status label or equivalent explicit current-mode indicator.

#### Scenario: Facebook automation page shows the new action name
- **WHEN** an operator filters the automation page to Facebook
- **THEN** the contact-comment action column and controls are labeled “加群评论（联系）”

#### Scenario: Empty keywords show no first-post mode status
- **WHEN** an operator clears and saves all Facebook comment search keywords
- **THEN** the save is accepted and the configuration dialog shows no “当前使用群内首帖” status or empty-keyword error

#### Scenario: Persisted contract remains compatible
- **WHEN** the renamed action is read or written through existing APIs
- **THEN** the system continues using the existing `contact_comment` action and `contactComment*` fields without a database migration
