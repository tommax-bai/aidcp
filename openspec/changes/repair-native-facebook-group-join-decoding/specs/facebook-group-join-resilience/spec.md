## ADDED Requirements

### Requirement: Native Facebook group join SHALL repair only observed bounded-result faults

The Native Facebook group-join router and Rust consumer SHALL produce and decode every bounded result used by the complete group-join path. Before changing a producer field, router helper, or consumer type in response to an `invalid bounded result`, the implementation MUST capture the real failure's operation stage and decode stage plus its field path/JSON category or safely classified exception evidence with the diagnostic-only build. It MUST repair the observed boundary and add that exact condition to a regression fixture; it MUST NOT add broad coercion or compatibility fallbacks for unobserved shapes.

#### Scenario: Real diagnostic identifies the repair

- **WHEN** the diagnostic-only Native binary runs the full observation-only join path against the exact failing browser page
- **THEN** the captured typed path/category or safely classified exception condition is recorded before the producer/consumer boundary is changed, and the regression test uses that observed condition

#### Scenario: Sampled probes do not substitute for the full command

- **WHEN** isolated consent or join probes decode successfully but the full group-join command still fails
- **THEN** the repair follows the full command's diagnostic stage and MUST NOT guess a field from the isolated samples

#### Scenario: Transient null document body does not throw

- **WHEN** the readiness join probe runs while Facebook navigation has no `document.body` and therefore no main action root
- **THEN** the router reports no composer and unresolved/not-ready scope as bounded data, allowing the existing readiness loop to continue, rather than throwing before a result exists

### Requirement: Target group header membership SHALL be recognized without widening actuation scope

The Native Facebook group-join scope resolver SHALL include the target group's real primary header action region when it is positively related to the unique current-group heading, including layouts where the heading and action controls are siblings inside a common target-owned header container. A member-classified control such as `已加入` in that region SHALL contribute a positive current-group membership signal.

The resolver MUST continue to exclude controls owned by a different-group navigation reference or recommendation/suggestion card, MUST keep candidates out of scope by default when target ownership is unresolved or ambiguous, and MUST never use the expanded membership scope as a page-wide Join fallback. An in-scope Join control SHALL continue to contradict and prevent an `already_member` verdict.

#### Scenario: Real current-group header reports already member

- **WHEN** the exact target page has one positively resolved group heading and its sibling primary header control is member-classified as `已加入`
- **THEN** that control is in target scope and the observation-only command reports the target as already a member without clicking

#### Scenario: Suggested-group member control remains excluded

- **WHEN** a recommendation card contains a member-classified control for another group
- **THEN** that control remains out of target scope and cannot establish membership for the current group

#### Scenario: Suggested-group Join remains ineligible

- **WHEN** the target header relation is expanded to cover a sibling action region and the page also contains Join controls in recommendation cards
- **THEN** only a uniquely target-owned in-scope Join can be eligible for actuation and no recommendation Join is admitted by the expansion

#### Scenario: Ambiguous target ownership still fails closed

- **WHEN** more than one heading/action region can plausibly own the current group's controls
- **THEN** the resolver reports unresolved or ambiguous scope and clicks nothing rather than choosing by document order
