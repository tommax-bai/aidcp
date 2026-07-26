## Why

The Facebook Native-only cutover retained the `group.join` command surface but did not preserve the proven join executor contract: it dispatches a coordinate click to a React-owned control, uses a weaker current-group scope, and caps the whole command at 30 seconds even though the established readiness, hydration, and post-click verification path can require about 78.5 seconds. This can make a valid join silently fail, risk selecting a recommended-group control, or report an ambiguous result before Facebook has rendered the durable state.

## What Changes

- Make the Native join probe positively resolve the current target group's own header/action region, exclude recommendation controls, and fail closed when the target region or join control is ambiguous.
- Re-resolve the unique in-scope primary Join control immediately before actuation and invoke its in-page click behavior required by Facebook's React control, while retaining honest no-click outcomes.
- Restore the established 30-second readiness, 2-second hydration settle, 1.5-second immediate settle, and 45-second post-click verification contract.
- Give only Native `group.join` a 90-second host-to-engine timeout budget for that established contract plus navigation/CDP margin; keep other Native commands on their existing 30-second budget.
- Preserve honest `observation_only`, `already_member`, `pending`, `questionnaire_required`, `not_ready`, `no_button`, joined, and ambiguous classifications without changing Cloud policy or the Cloud/Edge command schema.
- Make the longer Native join cancellable at safe semantic boundaries: cancellation before actuation is not-started, while cancellation after the in-page click is honestly ambiguous.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-group-join-resilience`: Apply the existing target-scope, React-compatible actuation, bounded readiness/hydration/post-verification, and honest-outcome requirements to the Native-only Facebook join implementation.

## Impact

- Edge Native Facebook router, Rust page engine, host Native session facade, and focused Native tests.
- Host-to-Native local session timeout validation for the join-specific budget; no Cloud protocol, database, packaging, deployment, or real Facebook join.
