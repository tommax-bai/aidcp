## ADDED Requirements

### Requirement: Native search admission failures SHALL retain the Cloud activity correlation
When a negotiated search command is rejected or fails before page actuation, Edge MUST emit exactly one schema-valid terminal for the original activity and MUST NOT cause Cloud to wait for a step timeout or record a search fact.

#### Scenario: Task-lane search is rejected before submission
- **WHEN** Native search cannot be admitted before any page-side search submission
- **THEN** Edge SHALL emit `action.completed` with the original `activityId`, `purpose`, and `scope`, `ok=false`, `actuated=false`, and `searchOutcome=not_submitted`

#### Scenario: Native search results are reported with one correlated terminal
- **WHEN** Native search returns a page-card result set for a correlated search activity
- **THEN** Edge SHALL report the cards and one terminal carrying `results_ready` or `no_results` with the observed result count

### Requirement: Native Xiaohongshu AI search SHALL use verified trusted actuation
Native search MUST support the live visible AI-search textarea as well as compatible input variants, MUST verify that the intended keyword is present before submission, and MUST keep route arrival distinct from result-card readiness.

#### Scenario: Visible AI-search textarea receives a keyword
- **WHEN** Native search resolves one visible Xiaohongshu AI-search textarea for the current page
- **THEN** it SHALL focus, clear, insert, verify, and submit the keyword through trusted CDP input rather than relying on synthetic DOM keyboard events

#### Scenario: Matching AI-search route is already active
- **WHEN** the browser is already on a `search_result_ai` route whose decoded keyword matches the command
- **THEN** Native SHALL reuse that route without resubmitting the search

#### Scenario: Result cards hydrate after route arrival
- **WHEN** the matching AI-search route is confirmed before its result cards are readable
- **THEN** Native SHALL poll within a fixed budget and report only the cards actually observed at the end of that budget
