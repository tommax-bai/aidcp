## ADDED Requirements

### Requirement: Facebook keyword configuration selects search or first-post targeting

For every Facebook group-comment run, configured search keywords SHALL be a targeting-mode selector rather than an enablement prerequisite. When the account has one or more non-empty keywords, the pipeline MUST choose one configured keyword and use the existing container-scoped search path. When the account has no keywords, the pipeline MUST NOT dispatch `search.execute`; it SHALL open the target group discussion stream and select the first hydrated top-level post that exposes both a canonical group-post permalink and a post-level comment affordance.

The two paths MUST NOT silently fall back to each other. A configured-keyword search with no result remains an honest search-path no-target outcome. An empty-keyword first-post selection with no eligible post remains an honest first-post no-target outcome. The first-post path MUST NOT skip to another post because the first eligible post is already in the account's comment dedupe ledger.

#### Scenario: Configured keyword keeps the search path
- **WHEN** a Facebook comment run has at least one configured non-empty keyword
- **THEN** Cloud dispatches the existing container-scoped search before opening the selected permalink
- **AND** it does not inspect the group feed as a first-post fallback

#### Scenario: Empty keywords open the first eligible group post without search
- **WHEN** a Facebook comment run has no configured keywords
- **THEN** Cloud dispatches no `search.execute`, and Edge selects and opens the first hydrated top-level group post with a stable permalink and post-level comment affordance

#### Scenario: Obfuscated timestamp href uses Facebook's explicit canonical story URL
- **WHEN** a hydrated top-level group post has a post-level comment affordance but its rendered timestamp `href` is only the group root plus an opaque fragment
- **AND** Facebook's React link/story data for that same rendered anchor explicitly contains a canonical group-post permalink
- **THEN** Edge MAY use that explicit canonical permalink for the candidate
- **AND** it MUST NOT infer or synthesize a post ID from the opaque fragment, text, or feed order

#### Scenario: First post already deduped does not advance to the second post
- **WHEN** empty-keyword mode selects the first eligible post and the account has already commented on that permalink
- **THEN** the run ends with an honest dedupe/no-strong-candidate outcome
- **AND** it does not substitute a later post or keyword search

### Requirement: First-post selection is a bounded read-open operation

Cloud SHALL request first-post selection through the existing `note.open` protocol message with a Facebook-only selection discriminator, the target group container, and the current task lease ID. Edge SHALL navigate the group discussion stream, select one eligible permalink, navigate that permalink, and emit the existing `note.detail` shape with the selected permalink as `noteId`. This operation MUST NOT emit a search activity receipt or be counted/reported as keyword search.

When the container is invalid, the group feed cannot be opened, the page is blocked, no eligible post hydrates within the bounded window, or the selected permalink cannot be opened and bound, Edge SHALL return an honest `open_note` failure and MUST NOT emit a fabricated detail.

#### Scenario: First-post read returns the selected permalink as detail identity
- **WHEN** the first eligible group post is successfully selected and opened
- **THEN** Edge emits `note.detail` whose `noteId` is that post's canonical navigable permalink and whose content belongs to the same post

#### Scenario: Cloud accepts an equivalent multi-permalink identity
- **WHEN** Edge returns `https://www.facebook.com/groups/<group>?multi_permalinks=<post>` for the selected first post
- **THEN** Cloud accepts it as a canonical group-post permalink when `<post>` derives a stable Facebook post identity
- **AND** Cloud continues to reject non-group posts, empty identities, and unknown URL shapes

#### Scenario: No eligible feed post is an honest non-submit
- **WHEN** no top-level post with a stable group-post permalink and comment affordance hydrates within the bounded selection window
- **THEN** Edge returns an explicit open failure and Cloud does not compose, approve, or submit a comment

## MODIFIED Requirements

### Requirement: A pinned just-joined group is a valid comment container with keywords from account config

The Facebook comment pipeline SHALL accept a container PINNED to a single just-joined group URL supplied by the caller, in place of choosing from the operator-configured container list or the LRU coverage window. Targeting mode SHALL still come from the account's Facebook comment configuration: non-empty keywords use container-scoped search inside the pinned group; no keywords use the pinned group's first eligible post without search. The pinned path MUST never use whole-site search or a blind DOM-order post. It SHALL update the membership ledger's coverage bookkeeping for that group (mark-commented on verified success; the existing left/inaccessible signal on the relevant failures), exactly as the coverage loop does.

#### Scenario: Pinned container overrides config selection
- **WHEN** a join-then-comment run supplies just-joined group G as the pinned container and the account has configured keywords
- **THEN** the pipeline searches inside G (not a config-listed or LRU-selected container) and runs the unchanged compose/validate/server-verify path

#### Scenario: Pinned path with no keywords uses the first eligible post
- **WHEN** the account has no configured Facebook keywords and a join-then-comment run pins group G
- **THEN** the pipeline performs no search, opens G's first eligible group post, and runs the unchanged compose/validate/approval/server-verify path

#### Scenario: Verified pinned comment updates the ledger
- **WHEN** a pinned comment on group G is server-confirmed as posted
- **THEN** the membership row for (account, G) records the coverage timestamp/count, consistent with the background coverage loop

### Requirement: Facebook account config supports generated or template comment bodies

Each Facebook account's comment configuration SHALL include a comment-body mode. `generated` mode SHALL use the existing Facebook composer after the target post is opened and read. `template` mode SHALL choose from operator-configured account templates and MUST skip LLM comment generation for the body. Both modes SHALL use target selection from the account joined-group ledger or a caller-pinned just-joined group, deterministic validation, configured approval, edge submit, server-confirmed verification, and honest audit outcomes. Search keywords are optional and select the targeting path; they MUST NOT determine whether generated mode is enabled.

Template mode MUST fail closed when the account has no valid templates; it MUST NOT silently fall back to generated mode. Generated mode MUST NOT require templates or keywords. Templates MUST be stored per account, may contain multiple entries, and SHALL be sanitized for empties/duplicates while preserving meaningful internal whitespace.

#### Scenario: Generated mode with keywords uses the composer after search
- **WHEN** a Facebook account is configured for `generated` mode with at least one keyword and a target post is opened from search
- **THEN** the pipeline calls the Facebook composer with the keyword, group label, post text, and discussion sample before validating and reviewing the produced body

#### Scenario: Generated mode without keywords uses target context without an empty keyword instruction
- **WHEN** a Facebook account is configured for `generated` mode with no keywords and the first eligible group post is opened
- **THEN** the composer is grounded in the post text and discussion sample and does not receive a fabricated or empty keyword requirement
- **AND** deterministic URL/contact/mention/spam/length/signal validation plus the configured approval policy remain active without fabricating a lexical keyword anchor

#### Scenario: Template mode skips generation
- **WHEN** a Facebook account is configured for `template` mode and has valid templates
- **THEN** the pipeline selects a template body and does not call the Facebook composer for that comment attempt

#### Scenario: Template mode without templates fails closed
- **WHEN** a Facebook account is configured for `template` mode but has no valid templates
- **THEN** the pipeline records/returns an honest no-op or compose-skipped outcome and MUST NOT fall back to generated comments
