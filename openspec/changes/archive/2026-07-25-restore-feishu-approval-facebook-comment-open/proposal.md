## Why

DEV revealed two independent production-composition failures in the Facebook approval path: Feishu card decisions could reach the receiver without the durable approval write port, and Native-only `note.open` could return an unrelated hydrated post while the requested permalink was still loading. The former made approval buttons unusable; the latter caused Cloud to ignore mismatched detail evidence until timeout, so comment preparation never reached approval-card creation.

## What Changes

- Wire every production `FeishuWsReceiver` composition to the existing durable, first-writer-wins approval write authority; retain an explicit unavailable response if a future composition omits that authority.
- Correlate Facebook comment-open evidence by canonical Facebook post identity rather than raw URL equality.
- Make the Edge Native Facebook `note.open` path wait within the established detail-hydration budget until the requested post identity is present, discarding unrelated hydrated details and returning an honest bounded failure otherwise.
- Add composition, identity-correlation, hydration, and bounded-failure regressions.
- Keep protocol v2 unchanged. Do not add a file-signalling fallback, retry knob, compatibility branch, service-mode migration, or installer/release work.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `console-write-operations`: Require every service composition that creates the Feishu approval receiver to inject the same durable approval write authority used by Web/client approval ingress.
- `facebook-scheduled-comment`: Require target-open success to be bound to the requested canonical Facebook post identity, including equivalent permalink forms, before composition or approval begins.

## Impact

- Cloud: Feishu receiver composition, Facebook comment open correlation, and acceptance/unit tests.
- Edge: Native Page Engine Facebook post-identity validation and hydration polling, plus Rust tests.
- Control: OpenSpec contract and task evidence.
- Runtime delivery: Cloud DEV deployment and local Edge Native-binary rebuild only. OL deployment and Edge installer packaging are outside this change.
