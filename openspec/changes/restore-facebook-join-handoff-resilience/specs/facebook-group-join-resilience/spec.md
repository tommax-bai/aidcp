## ADDED Requirements

### Requirement: Native Facebook task release SHALL preserve the current page until deliberate navigation

After an exclusive Facebook page task releases, the Native host SHALL unblock command handling and resume passive page observation without issuing an autonomous home/feed navigation. The current group page MUST remain available to the next join or comment leg. A later deliberate feed command SHALL remain responsible for validating and restoring the retained active feed/search list before it scrolls.

#### Scenario: Observe release does not navigate home before click
- **WHEN** a Facebook group observe leg finishes on the canonical target group page and releases its task lease
- **THEN** Native resume performs no `initial_scan` navigation, and the following click leg can reuse that exact group page

#### Scenario: Deliberate feed work still restores the active list
- **WHEN** a task leaves Facebook on a group or post page and the next authorized command is a feed scroll
- **THEN** the feed command validates the current surface against the retained active list and navigates to that list if required before scrolling

## MODIFIED Requirements

### Requirement: Slow-render observations SHALL receive one bounded no-click recovery before terminal failure

When the first readiness observation ends with a no-click `not_ready` or `nav_error`, the scheduler SHALL run exactly one fresh observe leg within the same logical join invocation. The recovery observe SHALL navigate the canonical group URL again, SHALL be audited as a non-terminal recovery, and SHALL NOT write a retry cooldown or retain a database assignment between invocations. If the recovery produces a minimally ready observation, the existing judge and click flow proceeds. If it produces another execution failure, the cloud SHALL mark the current membership `failed` with the final concrete reason. The system MUST NOT call the fail-closed model on an unready observation.

#### Scenario: Slow first render recovers on a fresh observe
- **WHEN** the first observe reaches its readiness deadline with `clicked=false` and `reason=not_ready`, and a second canonical observe becomes minimally ready
- **THEN** the scheduler audits one recovery, evaluates only the ready observation, and may continue to the existing click leg without writing a cooldown

#### Scenario: Repeated slow render is terminal without target-pool blockage
- **WHEN** both the first and bounded recovery observes return `not_ready`
- **THEN** the membership becomes `failed` with the final not-ready reason, no cooldown is written, and another scoped target remains claimable on a later invocation

#### Scenario: Pre-click model call remains gated behind minimal readiness
- **WHEN** an observation is not minimally ready and the bounded recovery has not produced a ready observation
- **THEN** the cloud does not spend a fail-closed pre-click model call and returns the honest final current-attempt failure

### Requirement: Join execution failures SHALL fail after bounded no-click recovery while account-level blockers retain pause

Pure execution failures before confirmed membership—including observe/confirm timeouts, no-observation, navigation errors, not-ready, lease-unavailable, and post-confirmation slow render—SHALL retain the original reason in audit and SHALL write no retry cooldown. Only a no-click `not_ready` or `nav_error` receives the single in-invocation recovery defined above. After that recovery is exhausted, or for every other execution failure, the current membership SHALL immediately become `failed` and stop occupying the account's unfinished-assignment slot so a later invocation can select another scoped target. Account-level login-required and captcha/checkpoint states SHALL retain their existing account pause, long backoff, and bounded-attempt behavior. Already-joined coverage cooldowns SHALL remain unchanged.

#### Scenario: Repeated navigation failure is terminal for this target
- **WHEN** opening the claimed group page returns `nav_error` and the one fresh observe recovery also returns `nav_error`
- **THEN** the membership becomes `failed`, the result reports the final `nav_error`, no cooldown is written, and the command does not comment

#### Scenario: Next invocation selects another target
- **WHEN** a previous target is terminal `failed` after its bounded no-click recovery and the account still has another eligible scoped group
- **THEN** the next invocation can claim the other group without waiting for a retry timer

#### Scenario: Clicked ambiguity is never replayed
- **WHEN** a join result reports `clicked=true` but membership verification remains slow or ambiguous
- **THEN** the scheduler MUST NOT run the no-click observe recovery or issue another Join click, and MUST preserve an honest non-success outcome

#### Scenario: Lease failure keeps current fail-fast behavior
- **WHEN** a join attempt cannot acquire or retain its Edge task lease
- **THEN** the membership becomes `failed` with the concrete lease reason, without a cooldown or hidden retry

#### Scenario: Account-level failure keeps the long backoff
- **WHEN** a join attempt encounters login-required or captcha
- **THEN** the account pause and long cooldown behavior apply unchanged rather than treating the account-wide blocker as one target's ordinary failure

#### Scenario: Joined coverage behavior is unchanged
- **WHEN** navigation fails while checking comment coverage for a membership already recorded `joined`
- **THEN** the existing left-confirmation/cooldown protection remains in force and the joined fact is not demoted by this change
