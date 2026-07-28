## MODIFIED Requirements

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
