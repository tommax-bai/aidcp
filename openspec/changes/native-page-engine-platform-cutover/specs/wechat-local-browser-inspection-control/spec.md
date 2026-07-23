## ADDED Requirements

### Requirement: WeChat local inspection uses Native capture without changing lease truth
The WeChat local browser inspection flow SHALL delegate browser-session material capture to Native while Edge retains transient browser lease ownership and confirmed teardown. A failed or cancelled Native capture MUST NOT cause Edge to release the transient lane before the physical browser/process close is confirmed.

#### Scenario: Native capture succeeds
- **WHEN** Native returns a valid bounded WeChat session candidate
- **THEN** Edge applies the existing identity, persistence, and API-session validation rules before accepting it

#### Scenario: Native capture fails after browser launch
- **WHEN** the Native session fails or times out after the provider opens the browser
- **THEN** Edge performs bounded teardown and releases the transient lease only after confirmed close
