## Why

Real AdsPower runs can establish a stable Facebook identity before Facebook finishes rendering post-login blocking pages. Edge currently connects to Cloud immediately after identity establishment, so a newly observed ad-choice introduction page or a late Remember Password card can remain in front of Feed while browse commands fail with `no_target`.

## What Changes

- Add a bounded post-login startup gate between stable-identity confirmation and Cloud connection.
- Recognize the exact Facebook `ad_free_subscription` first-time introduction page as its own signal and click one unique visible/topmost `Get started` control once with Native pointer input.
- Stop at the subsequent subscription-versus-ads choice as a controlled manual-choice state; retain the same browser/CDP generation and do not choose, continue, or start account-scoped work automatically.
- Reuse the existing exact Remember Password modal recognition and `OK` Native action after identity establishment, then require the prompt to disappear before startup continues.
- Preserve fail-closed behavior for ambiguous, covered, unsupported, or unverifiable targets. Generic dialog dismissal and the existing cookie-consent overlay rules remain unchanged.
- Keep the separate transient AdsPower `user/update code=-1` startup rejection out of scope; this change does not broaden provider mutation retries.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-browser-environment`: require bounded, Native-only reconciliation of supported post-login blockers before Cloud connection and account-scoped work.

## Impact

- `aidcp-edge` Native Facebook auth page rules, command schema/parity ledger, TypeScript auth coordinator, startup lifecycle wiring, and focused tests.
- Control-repo OpenSpec contract only; no Cloud protocol, database, schema, consent policy, credentials, package, or deployment change.
