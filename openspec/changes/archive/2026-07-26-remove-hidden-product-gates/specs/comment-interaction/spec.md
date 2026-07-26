## MODIFIED Requirements

### Requirement: Facebook comments require human review by default

All Facebook comments — whether or not they carry contact info — SHALL pass the Feishu human-review gate before edge submit by default. The exceptions are explicit structured product policy: a detail-confirmed mandatory rule whose actions include comment and whose `comment_approval` is `auto_approve`, or an account/source approval policy that explicitly authorizes automatic approval. An automatic path MUST send the required readable notice before submit according to that policy and MUST fail closed when a mandatory notice is unavailable. A process environment variable MUST NOT disable review or create an automatic-approval exception. An unwired approval port, review timeout, rejection, or failed mandatory notice MUST produce an honest non-submitting outcome with no success mark.

#### Scenario: Non-contact FB comment waits for review by default
- **WHEN** a Facebook comment has no valid structured automatic-approval policy
- **THEN** it MUST request Feishu approval and MUST NOT submit until approved

#### Scenario: Structured standing approval notifies then submits
- **WHEN** full-detail matching confirms an account rule with comment plus `comment_approval:auto_approve`
- **THEN** the system MUST send the required final-comment notification first and MAY submit only after that send succeeds

#### Scenario: Review or auto-approval notification failure is honest no-submit
- **WHEN** review is unwired/timed out/rejected, or a mandatory auto-approval notice fails
- **THEN** the run MUST audit a non-success reason, MUST NOT call edge submit, and MUST NOT record the target as commented

#### Scenario: Environment cannot disable review
- **WHEN** an inherited or deployed `AIDCP_FB_COMMENT_REVIEW_ALL=false` is present but no structured account/source policy authorizes automatic approval
- **THEN** the comment still requires review and the environment value has no effect

#### Scenario: Red-line reversal — implicit auto-post is forbidden
- **WHEN** an implementation auto-posts because of free-form persona wording, account id, nickname, a global heuristic, or an environment variable rather than a validated structured policy
- **THEN** it MUST be treated as a violation and not merged
