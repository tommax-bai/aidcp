## Why

Real Facebook `group_join` commands can reach the correct group page and still fail as `native Facebook command returned an invalid bounded result`. The Native adapter currently collapses wrapper, result-kind, missing-value, and typed-field decoding failures into that one message, so the three observed `native_effect_ambiguous` outcomes cannot identify the incompatible producer field and any direct field fix would be guesswork.

The same real group page also exposed a separate bounded-scope false negative: after Facebook confirmed membership, the header control `已加入` was classified as a member signal but excluded from the current-group scope. The repair must preserve exact-target, fail-closed actuation while recognizing the real current-group header layout.

## What Changes

- Add bounded, content-free Native result diagnostics that identify the command stage, decode stage, expected result kind, failing typed field path, and actual JSON value category without returning evaluated source, DOM text, selectors, credentials, or raw page payloads.
- Preserve the existing stable error code and effect-phase honesty while making pre-actuation versus post-actuation failures observable.
- Use the diagnostic build against the already-open `Tianxing Bai` Facebook group page to determine whether the failure is a wrapper, typed-field, or evaluated-router exception before changing its contract.
- Repair only the result-production/decoding fault demonstrated by that real capture and add a regression fixture for the observed shape or exception condition.
- Extend current-group scope resolution to include the real group-header action region so a positive `已加入` member control is recognized, while recommendation and unrelated group controls remain out of scope and never become join targets.
- Validate source, Native binary, focused/full Edge suites, and the exact real browser read path separately. Do not package, inject, sign, install, or claim an updated desktop client as part of this change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `native-page-engine`: Native typed-result failures gain bounded field-path and operation-stage diagnostics while retaining protocol correlation, stable error classification, and redaction guarantees.
- `facebook-group-join-resilience`: Native Facebook group join recognizes the real current-group header membership control without widening join actuation to unrelated page regions, and the observed bounded-result production fault is repaired at its actual boundary.

## Impact

- Edge Native Rust adapter and protocol error records under `aidcp-edge/native/page-engine`.
- Edge TypeScript Native client/logging surfaces that consume bounded Native failures.
- Embedded Facebook group-join router and its router/Rust fake-CDP regression fixtures.
- One small Rust dependency may be added if needed to report Serde field paths without exposing raw values.
- No Cloud, Console, database, deployment, OL, installer, signing, or packaging behavior changes.
