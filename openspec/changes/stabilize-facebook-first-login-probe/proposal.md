## Why

Facebook first-login reconciliation currently begins immediately after the first allowed page attachment. On a fresh AdsPower start, the Facebook target can still be navigating even though `/json/version` and the TypeScript CDP attachment are ready, so the first read-only Native auth probe can fail in milliseconds; the supervisor restart then loses fresh-start policy evidence and permanently refuses the pending login action.

## What Changes

- Treat the first successful Native Facebook auth observation, rather than browser-process or TypeScript attachment readiness alone, as the login reconciler's page-readiness evidence.
- Retry only allowlisted, pre-mutation Native target/CDP probe failures for at most 20 seconds inside the existing bounded login budget, rebuilding the Native owner session before the next probe.
- If the 20-second stabilization window expires, stop automated login actions and preserve the current browser/core generation in the existing manual-login wait instead of triggering a supervisor restart that cannot regain fresh-start proof.
- Preserve fail-closed behavior for protocol, validation, unknown, and action-command failures; never replay an input action or ambiguous receipt.
- Emit bounded non-secret diagnostics for the Native error code and retry/terminal classification instead of collapsing every exception into `native_auth_command_failed`.
- Cover the fresh-start failure/recovery chain and the no-action-replay boundary with focused tests.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-browser-environment`: Define evidence-based startup stabilization for the read-only first-login probe before any Native login action may be considered.

## Impact

- Affected repo: `aidcp-edge`.
- Likely affected areas: Facebook auth coordinator, Native runtime owner-session recovery, startup/auth focused tests, and safe lifecycle logging.
- No Cloud API, protocol-v2, database, Console, AdsPower credential policy, or installer format change is intended.
- Runtime behavior changes and therefore requires focused validation, integration, and DEV delivery under the normal release boundary.
