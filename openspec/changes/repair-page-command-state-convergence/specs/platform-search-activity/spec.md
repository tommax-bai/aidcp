## ADDED Requirements

### Requirement: Native search admission failures SHALL retain the Cloud activity correlation
When a negotiated search command is rejected or fails before page actuation, Edge MUST emit exactly one schema-valid terminal for the original activity and MUST NOT cause Cloud to wait for a step timeout or record a search fact.

#### Scenario: Task-lane search is rejected before submission
- **WHEN** Native search cannot be admitted before any page-side search submission
- **THEN** Edge SHALL emit `action.completed` with the original `activityId`, `purpose`, and `scope`, `ok=false`, `actuated=false`, and `searchOutcome=not_submitted`

#### Scenario: Native search results are reported with one correlated terminal
- **WHEN** Native search returns a page-card result set for a correlated search activity
- **THEN** Edge SHALL report the cards and one terminal carrying `results_ready` or `no_results` with the observed result count
