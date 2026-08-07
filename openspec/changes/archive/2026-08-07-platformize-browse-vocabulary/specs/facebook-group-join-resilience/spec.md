## MODIFIED Requirements

### Requirement: Native Facebook group join SHALL preserve the established scoped actuation and bounded verification contract

For current-group scope, React-compatible actuation, readiness, hydration, post-click verification, and honest outcome classification, the Native-only Facebook adapter SHALL apply the established Facebook group-join executor semantics. This requirement does not assert parity with the legacy coordinator-visible 18.5-second commit window, because the current host-to-Native lifecycle does not expose the engine's internal click boundary. The adapter MUST NOT treat a command being dispatched, a click being attempted, cancellation, or a timeout expiring as proof that the account joined the group.

The adapter SHALL positively resolve the target group's own heading/action region from the current `/groups/<id>` page and SHALL classify Join, member, and pending controls only within that region. It SHALL retain bounded out-of-scope candidate evidence but MUST NOT use a recommendation control to establish the target group's state or to actuate a join. Unresolved or ambiguous scope MUST fail closed without a click.

Immediately before actuation, the adapter SHALL re-resolve exactly one enabled in-scope Join control and invoke that current React-owned element's in-page click behavior. It MUST NOT rely on coordinates captured by an earlier readiness probe as the join actuation.

The join command SHALL permit the established bounded sequence of up to 30 seconds readiness polling, a 2-second pre-click hydration settle, a 1.5-second immediate post-click settle, and up to 45 seconds durable verification. This longer budget SHALL apply only to Native Facebook `facebook.group.join`; ordinary Native commands SHALL retain their existing deadline.

The Native join SHALL honor cancellation during readiness and hydration and immediately before actuation as a not-started result. Once the in-page click has been invoked, cancellation SHALL stop bounded verification with `clicked=true` and an ambiguous `preempted_by_task` result; it MUST NOT report joined or replay the click.

#### Scenario: Unique current-group React control is re-resolved and joined state is confirmed

- **WHEN** the target group page resolves one enabled in-scope Join control and its React handler changes the page to a positive member state
- **THEN** the Native adapter re-resolves that element at the actuation boundary, invokes its in-page click behavior, and reports joined only after the member state is observed

#### Scenario: Recommended-group Join is excluded

- **WHEN** the current target group is pending or otherwise has no in-scope Join control while a recommendation region contains an identically labelled Join control for another group
- **THEN** the Native adapter reports the current group's pending or no-target state, records the recommendation as out of scope, and never clicks it

#### Scenario: Ambiguous target region fails closed

- **WHEN** more than one heading/action region can plausibly resolve as the target group or more than one in-scope Join control remains
- **THEN** the Native adapter reports a retryable not-ready/ambiguous no-click outcome and MUST NOT select by document order

#### Scenario: Existing terminal state short-circuits before actuation

- **WHEN** the scoped pre-click observation positively establishes already-member, pending, or questionnaire-required state
- **THEN** the Native adapter returns that honest outcome without invoking any Join control

#### Scenario: Slow hydration and durable state remain inside the join budget

- **WHEN** the Join control appears near the end of the 30-second readiness window and Facebook needs the established hydration and post-click verification windows before rendering a durable state
- **THEN** the host and Native session allow the bounded join sequence to complete instead of truncating it at the ordinary 30-second command deadline

#### Scenario: Dispatched click without durable proof is ambiguous

- **WHEN** the in-scope Join control was invoked but no member, pending, questionnaire, or structural membership transition can be proven within the bounded post-click window
- **THEN** the Native adapter reports `join_verification_ambiguous` with a dispatched/ambiguous effect and MUST NOT report joined

#### Scenario: Cancellation before actuation is not started

- **WHEN** takeover cancellation arrives before the in-page Join invocation
- **THEN** the Native adapter returns a not-started cancellation and clicks nothing

#### Scenario: Cancellation after actuation is ambiguous

- **WHEN** takeover cancellation arrives after the Join invocation but before durable verification
- **THEN** the Native adapter returns `preempted_by_task` with `clicked=true` and an ambiguous effect, without replay or claimed membership
