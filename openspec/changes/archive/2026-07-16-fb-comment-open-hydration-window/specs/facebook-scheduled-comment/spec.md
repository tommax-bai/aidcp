## ADDED Requirements

### Requirement: Comment target open waits for detail hydration on the same evidence as the read path

The comment path's open-target step SHALL allow the post detail to hydrate for a bounded window sized on the **same real-machine evidence** as the browse/read path's detail open, and SHALL NOT report open-failure before that window elapses. The comment path has its own open implementation, separate from the read path's; a widening applied to one does not reach the other, so the two windows SHALL be justified by the same observed hydration range and kept in agreement.

Facebook post detail hydrates measurably later than feed (observed 7–12s on real machines). A window narrower than the observed range makes open-failure a function of page speed rather than of the post being unavailable, which drops targets that were successfully found by the preceding search step — and reports them as if no suitable target existed.

The waiting budget for detail hydration SHALL be a **dedicated** budget, not shared with probes that run inside per-round retry loops (search-candidate probing and comment-editor coaxing). Widening a shared probe budget multiplies through those loops and overruns the step deadline, converting an honest open-failure into a timeout without changing the outcome the operator sees.

The cloud's open-step deadline SHALL be large enough to contain the edge's bounded window plus its own slack, so that the **edge answers first** with an honest terminal reason rather than the cloud cutting the step short. The submit step already deviates from the shared step deadline for the same reason.

Bounded-ness and honesty are unchanged: the window remains bounded, and a post whose detail never renders within it is still reported as an honest open-failure — never as success, and never as "no candidate found".

#### Scenario: Slow-hydrating post detail is not reported as open-failure

- **WHEN** the comment path opens a target permalink whose detail article renders within the observed hydration range but later than the previous narrow window
- **THEN** the open step succeeds and the comment proceeds, instead of reporting open-failure

#### Scenario: Never-rendering post detail is still an honest open-failure

- **WHEN** the comment path opens a target permalink whose detail article does not render within the bounded window
- **THEN** the step reports open-failure honestly, and does not report success

#### Scenario: Widened detail budget does not widen in-loop probes

- **WHEN** the detail-hydration budget is widened
- **THEN** the search-candidate probe and the comment-editor coaxing probe keep their original per-round budgets, and the open step's worst-case duration stays within the cloud's open-step deadline

#### Scenario: Edge answers before the cloud deadline

- **WHEN** the edge's open step runs its full bounded window without the detail rendering
- **THEN** the edge's honest open-failure reaches the cloud before the cloud's open-step deadline fires, so the recorded reason is open-failure rather than timeout
