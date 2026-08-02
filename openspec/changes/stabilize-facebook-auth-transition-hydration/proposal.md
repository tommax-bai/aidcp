## Why

Real first-login runs show that AdsPower credential filling and the Facebook checkpoint reached after TOTP submission can remain structurally incomplete for several seconds. Edge currently classifies those transient states too early, briefly projects a recoverable automatic login as requiring manual login, and can stop on `unsupported_facebook_checkpoint` before the already-supported automation-warning `Dismiss` control has hydrated.

## What Changes

- Give the managed Facebook credential-fill transition a 25-second bounded observation window before reporting `credential_fill_unavailable`.
- Give a newly navigated Facebook checkpoint 15 seconds to hydrate into a supported structural signal before classifying it as an unfamiliar checkpoint, regardless of which prior authentication step led there.
- Keep automatic-login lifecycle projection in the existing `启动中 · 登录中` state while either bounded transition is still pending.
- Independently trigger the existing Native `automation_warning_dismiss` action whenever an auth probe sees the exact warning and one unique visible `Dismiss` control; retain fail-closed behavior after the window or for ambiguous/unsafe targets.
- Preserve the existing one-signal/one-action, trusted Native pointer, no-replay, stable-identity, and non-secret diagnostic boundaries.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-browser-environment`: Define a 15-second hydration window for any authentication checkpoint and independent continuation through the existing automation-warning dismissal signal.
- `pluggable-browser-provider`: Define the 25-second managed AdsPower credential-fill observation before manual-login classification.
- `edge-fleet-console`: Keep bounded automatic credential/checkpoint transitions in the existing login-starting projection rather than showing premature manual attention.

## Impact

- Affects the Edge Facebook Native auth router, first-login coordinator/lifecycle projection, focused Native/router/coordinator/UI tests, and control-repo OpenSpec artifacts.
- Does not change Cloud protocol, account risk state, AdsPower secret access, browser lifecycle ownership, platform action accounting, or deployment topology.
- Source validation does not update the installed desktop client; packaging, installation, and real-account retry remain separate explicit steps.
