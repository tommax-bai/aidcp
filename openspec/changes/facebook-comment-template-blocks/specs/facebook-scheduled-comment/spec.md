## MODIFIED Requirements

### Requirement: Facebook account config supports generated or template comment bodies

Each Facebook account's comment configuration SHALL include a comment-body mode. `generated` mode SHALL use the existing Facebook composer after the target post is opened and read. `template` mode SHALL choose from operator-configured account templates and MUST skip LLM comment generation for the body. Both modes SHALL still require configured search keywords, target selection from the account joined-group ledger, deterministic validation, human review when configured/required, edge submit, server-confirmed verification, and honest audit outcomes.

Template mode MUST fail closed when the account has no valid templates; it MUST NOT silently fall back to generated mode. Generated mode MUST NOT require templates. Templates MUST be stored per account, may contain multiple entries, and SHALL be sanitized for empties/duplicates while preserving meaningful internal whitespace.

**A template is a block, not a line.** Operator editors SHALL separate templates by a line containing only `------` (six or more hyphens), so a single template may span multiple lines and keep its own line breaks. The same separator SHALL be used when rendering stored templates back into the editor. Line breaks inside a block are part of that template's body and MUST NOT split it into separate templates. This applies to both the per-account template editor and the region-wide template editor.

#### Scenario: Generated mode uses the composer
- **WHEN** a Facebook account is configured for `generated` mode and a target post is opened
- **THEN** the pipeline calls the Facebook composer with the keyword, group label, post text, and discussion sample before validating and reviewing the produced body

#### Scenario: Template mode skips generation
- **WHEN** a Facebook account is configured for `template` mode and has valid templates
- **THEN** the pipeline selects a template body and does not call the Facebook composer for that comment attempt

#### Scenario: Template mode without templates fails closed
- **WHEN** a Facebook account is configured for `template` mode but has no valid templates
- **THEN** the pipeline records/returns an honest no-op or compose-skipped outcome and MUST NOT fall back to generated comments

#### Scenario: A multi-line block is one template
- **WHEN** an operator enters several lines of text with no `------` separator line
- **THEN** the editor stores exactly one template whose body keeps those line breaks

#### Scenario: Separator lines split templates
- **WHEN** an operator enters two blocks of text separated by a line containing only `------`
- **THEN** the editor stores exactly two templates, and neither body contains the separator line

### Requirement: Template comments use the same safety and contact lanes as generated comments

Template comment bodies SHALL pass the **structural** deterministic validators before any submit attempt: empty, low-signal, minimum length, and maximum length. A rejected template MUST NOT be repaired and posted.

Template bodies SHALL NOT be subject to the **content-policy** validators (URL/bare-domain, contact-info text, `@mention`, spam phrase, relevance). Those validators exist because an unattended generated body has no human author to answer for it; a template's author is the operator, who owns its content. Applying them to operator-written campaign copy rejects legitimate material — real-machine evidence 2026-07-28: a recruitment template carrying its own phone number is rejected as `contains_contact` and never posts. The operator's decision of record (2026-07-28) is that template content is their responsibility and that a template carrying contact details alongside the account contact string is intended, not a conflict.

The maximum-length validator is retained for templates because it is a physical constraint rather than a policy one: the edge types a comment character by character at human cadence inside a bounded platform step budget, so an over-long body ends as a typing-deadline failure instead of a posted comment.

Contact-info comments SHALL keep the template/generated body separate from the account contact string: the body is sent as `text`, and the contact string is injected through the existing contact-info lane after human review.

#### Scenario: Operator template with contact text is accepted
- **WHEN** a template body contains a phone number or other contact text
- **THEN** the body validator does not reject it, and the comment proceeds to the existing review and submit lanes

#### Scenario: Generated body with contact text is still rejected
- **WHEN** an unattended generated (non-template) body contains a phone number, email, WeChat-like contact phrase, bare domain, `@mention`, or spam phrase
- **THEN** the body validator rejects it before submit, exactly as before

#### Scenario: Over-long template is still rejected
- **WHEN** a template body exceeds the platform body length limit
- **THEN** the validator rejects it, because the edge cannot finish typing it inside the platform step budget

#### Scenario: Contact template comment appends account contact info separately
- **WHEN** a contact comment uses template mode and the account has configured contact info
- **THEN** the review card shows the template body plus the account contact string, and edge receives the body as `text` plus the contact string in the existing `groupChatCode`/contact-info field
