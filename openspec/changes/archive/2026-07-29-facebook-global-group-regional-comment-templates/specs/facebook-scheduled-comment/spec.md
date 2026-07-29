## MODIFIED Requirements

### Requirement: Facebook account config supports generated or template comment bodies

Each Facebook account's comment configuration SHALL support an explicit comment-body mode and SHALL persist whether that mode was explicitly configured independently of the mode value and template array. Explicit `generated` mode SHALL use the existing Facebook composer after the target post is opened and read. Explicit `template` mode SHALL first use valid operator-configured account templates; when the account template set is empty, it SHALL resolve the selected target group's region and use that region's configured common templates. When the account has no explicit comment-body configuration, the effective mode SHALL default to `template` and use the same regional-template resolution. Explicit `generated` MUST remain authoritative and MUST NOT be replaced merely because account templates are empty. The explicit-mode fact SHALL survive the existing Cloud internal sync-read path.

Both modes SHALL still require configured search keywords, target selection from the account joined-group ledger, deterministic validation, human review when configured/required, edge submit, server-confirmed verification, and honest audit outcomes. Regional fallback MUST fail closed when the target has no region or the region has no valid templates; it MUST NOT fall back to generated comments, another region, or arbitrary text. Account and regional templates SHALL be sanitized for empties/duplicates while preserving meaningful internal whitespace.

#### Scenario: Explicit generated mode uses the composer
- **WHEN** a Facebook account is explicitly configured for `generated` mode and a target post is opened
- **THEN** the pipeline calls the Facebook composer with the keyword, group label, post text, and discussion sample before validating and reviewing the produced body

#### Scenario: Explicit template mode uses account template first
- **WHEN** a Facebook account is explicitly configured for `template` mode and has valid account templates
- **THEN** the pipeline selects an account template body and does not call the Facebook composer or replace it with a regional template

#### Scenario: Template mode without account templates uses target region
- **WHEN** a Facebook account's effective mode is `template`, its account templates are empty, and the selected target group has valid common templates for its region
- **THEN** the pipeline selects a common template for that target region and does not call the Facebook composer

#### Scenario: Missing explicit mode defaults to regional template
- **WHEN** a Facebook account has no explicit body mode, has configured search keywords, and the selected target group has valid common templates for its region
- **THEN** the effective mode is `template` and the pipeline selects a regional common template

#### Scenario: Missing regional template fails closed
- **WHEN** the effective mode is `template`, account templates are empty, and the selected target has no region or no valid common templates for its region
- **THEN** the pipeline records/returns an honest non-submit outcome and MUST NOT fall back to generated comments

#### Scenario: Missing keywords remains no-op
- **WHEN** a Facebook account has no configured keywords even though a regional common template is available
- **THEN** the pipeline records/returns no targets and does not search or submit a blind comment
