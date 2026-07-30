## Why

Facebook environments created from imported AdsPower account material can still open on a logged-out page when the imported session cookie has expired. Today AIDCP stops at the pre-identity gate and requires manual browser work, even though AdsPower already holds the account password and 2FA key and the required first-login page transitions have now been observed through CDP.

## What Changes

- Add a bounded Facebook first-login state machine before identity resolution for imported AdsPower profiles.
- Let AdsPower perform first-open credential filling, submit the Facebook login form through Native CDP input, and verify each navigation before continuing.
- Generate TOTP only from the profile's in-memory 2FA key, synchronize against Facebook server time, and wait for the next 30-second window when less than 10 seconds remain before input.
- Structurally handle only the observed non-CAPTCHA transitions: the automated-behavior warning, the Facebook push-notification blocker, and Facebook's `Remember Password` prompt.
- Start managed AdsPower browsers with Chrome password saving disabled and notification prompts suppressed so browser-chrome bubbles never become an automation dependency.
- Treat a profile as authenticated only when Facebook-domain cookies contain a numeric `c_user` satisfying the stable-identity rule and a non-empty `xs`; cookie names alone are not authentication evidence.
- Preserve fail-closed behavior for CAPTCHA/human verification, unfamiliar checkpoints, missing credentials, ambiguous targets, expired or rejected 2FA, and missing post-login identity.
- Keep passwords, 2FA keys, TOTP values, cookies, proxy credentials, and raw AdsPower responses out of settings, logs, Cloud messages, task records, and UI receipts.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-browser-environment`: Replace the unconditional ban on credential automation with a bounded, evidence-backed first-login assist for imported AdsPower profiles, followed by the existing stable-identity gate.
- `pluggable-browser-provider`: Define the managed AdsPower startup settings that enable first-open credential filling while suppressing Chrome password-save and notification permission prompts.
- `adspower-environment-provisioning`: Permit an authenticated main-process credential read for first-login assistance while retaining strict in-memory-only handling and redaction boundaries.

## Impact

- Affected repo: `aidcp-edge`.
- Likely affected areas: AdsPower Local API broker, AdsPower browser-provider startup body, Facebook startup/identity path, CDP page interaction helpers, and focused Electron/Facebook/provider tests.
- No Cloud API, protocol-v2, database, Console, deployment, or installer change is intended.
- Live acceptance is limited to explicitly operator-approved, one-at-a-time runs against only the third imported Facebook profile after code-level gates pass; the implementation never retries a failed live run automatically.
