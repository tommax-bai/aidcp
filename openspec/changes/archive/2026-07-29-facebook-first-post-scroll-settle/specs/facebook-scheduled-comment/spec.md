## ADDED Requirements

### Requirement: First-post scroll settles before candidate probing

For `selection=first_commentable_group_post`, Edge SHALL retain the existing smooth-scroll completion wait and then wait an additional fixed 2 seconds after each bounded same-container downward scroll before probing rendered feed cards for that round. The candidate snapshot returned from the scroll operation MUST be collected after this additional settle interval, not before it.

The initial pre-scroll probe, maximum scroll-round count, exact-group binding, canonical-permalink and comment-affordance eligibility, stop conditions, and honest failure behavior SHALL remain unchanged. The additional wait MUST NOT apply to keyword-search targeting or create a fallback to search.

#### Scenario: Slow first post hydrates during the post-scroll settle

- **WHEN** the first bounded scroll completes and a commentable group post hydrates during the following 2-second settle interval
- **THEN** Edge probes after the settle and can select that hydrated post in the same scroll round
- **AND** it does not dispatch the next scroll before that probe

#### Scenario: Every exhausted scroll round remains bounded

- **WHEN** no eligible post appears after the additional settle in a scroll round
- **THEN** Edge may continue only within the existing fixed maximum scroll-round count
- **AND** it still returns an honest non-success when no eligible candidate appears

#### Scenario: Keyword search is unaffected

- **WHEN** a Facebook group-comment run has configured search keywords
- **THEN** it uses the existing search targeting path without the first-post post-scroll settle
