## Context

The Facebook first-login reconciler was introduced before the stable-identity gate and currently starts as soon as AdsPower `/json/version` is reachable and the TypeScript host attaches to one allowed Facebook target. Those facts prove that a browser process and a page target exist, but they do not prove that the target has stopped changing execution contexts or that a new Native Page Engine session can already read cookies and evaluate the auth router.

Observed fresh starts across three profiles all failed their first Native auth command within 30-50 ms. The same browser generations became readable moments later. Exiting on that read-only failure is especially harmful: the supervisor adopts the still-active browser, but the replacement process correctly lacks proof that it applied the fresh-start credential and browser-chrome policy, so it cannot continue an actionable login signal.

## Goals / Non-Goals

**Goals:**

- Define page readiness by a successful typed Native auth observation rather than a fixed delay or browser-process readiness alone.
- Recover boundedly from known target/CDP/engine transport failures while the command being attempted is still a read-only auth probe.
- Keep fresh-start policy evidence in the original process by recovering in place.
- Preserve the existing one-signal/one-action, fresh revalidation, and no-replay guarantees.
- Log only bounded non-secret failure classification.

**Non-Goals:**

- Retrying a Native input command, an ambiguous receipt, or an unchanged signal id.
- Treating every Native error as transient.
- Adding a fixed sleep after AdsPower startup or relying on `document.readyState=complete` as login readiness.
- Carrying fresh-start policy proof across unrelated processes or browser generations.
- Changing AdsPower credential access, TOTP generation, Facebook selectors, Cloud contracts, or stable-identity authority.

## Decisions

### 1. A successful Native auth observation is the readiness gate

The reconciler remains positioned after allowed-target attachment and before identity resolution, but it does not consider the page ready for auth decisions until `facebook_auth_probe` returns a confirmed, typed observation. Browser `/json/version`, TypeScript attachment, and DOM ready state remain necessary infrastructure signals, not sufficient auth-readiness evidence.

A fixed startup delay was rejected because it is both slower on healthy starts and still racy on slower navigation. Requiring two identical coordinator observations was also rejected: Native action execution already fresh-revalidates the signal id immediately before any input, providing the second evidence point without delaying read-only `authenticated` or `none` results.

### 2. Retry only allowlisted failures of the read-only probe

When `facebook_auth_probe` throws a `NativePageEngineError` classified as endpoint/target/CDP/engine transport startup churn, the coordinator will:

1. record only the safe error code and retry count;
2. close/discard the `facebook-startup-auth` owner session;
3. wait with the bounded 250 ms, 500 ms, then 1-second backoff within the existing shared deadline; and
4. open a fresh Native owner session and probe again.

Retries use 250 ms, 500 ms, and then at most 1-second waits. Each read-only probe receives at most a 20-second stabilization window, also capped by the shared login deadline. Invalid request/protocol, ownership, unsupported-command, and engine-internal failures remain terminal because waiting cannot make their contracts valid.

### 3. Never retry an action command exception

The transient allowlist applies only when the command kind is `facebook_auth_probe`. Once an input action is dispatched, an exception can represent an ambiguous receipt. The coordinator therefore returns terminal failure and relies on its existing dispatched-signal-id set to prevent replay. A later read-only probe may itself be retried safely, but the confirmed/ambiguous action is never resubmitted.

### 4. Recover in the same process instead of transferring policy proof

Keeping the original coordinator alive retains the exact `firstLoginPolicyApplied` evidence returned by the fresh AdsPower start. Persisting or transferring that boolean to a replacement child was rejected because the proof would need to be bound to the exact browser instance and launch body; a stale or misbound receipt could authorize login mutation in another generation.

### 5. Diagnostics expose classification, not raw errors

Logs will include the command kind, bounded Native error code, effect phase when present, and retry/terminal disposition. Raw exception messages, Native stderr, URLs, cookies, credentials, TOTP material, and AdsPower responses remain excluded.

### 6. Stabilization exhaustion enters the existing manual-login wait

When allowlisted read-only failures consume the 20-second stabilization window, the reconciler returns `manual_login_required` with the safe reason `auth_probe_unavailable`. The existing startup path keeps the same core, browser, CDP generation, browser controls, and slot alive while dispatching no further automated login action. This prevents the supervisor from adopting the active browser without fresh-start proof and allows an operator-completed login to continue through the stable-identity gate.

Exiting with code 1 was rejected because it deterministically produces the observed restart loop. Transferring fresh-start proof was rejected because the proof is not safely bound across processes. Closing the browser was rejected as the default because no page mutation has occurred and the controlled session remains useful for manual recovery.

## Risks / Trade-offs

- **[The historic failure's exact Native subtype was collapsed by current code]** -> Cover the observed target/CDP/transport classes, emit the safe subtype on the next occurrence, and keep unknown codes terminal.
- **[A persistent endpoint failure could consume the login budget]** -> Cap each stabilization episode at 20 seconds, use bounded backoff, and enter the existing manual wait after exhaustion.
- **[Resetting a Native owner session loses engine-local consumed-signal state]** -> Reset only after a read-only probe exception; the TypeScript coordinator retains dispatched signal ids, and Native still fresh-revalidates before any action.
- **[A page can navigate immediately after a successful observation]** -> Existing signal-id binding and action-time fresh revalidation remain authoritative; no observation alone authorizes input.

## Migration Plan

1. Add focused coordinator tests for transient probe recovery, terminal contract errors, and action non-replay.
2. Implement safe Native error classification and owner-session reset in `aidcp-edge`.
3. Run focused auth/runtime tests, Native gates, full tests, and typecheck.
4. Integrate the validated source to Edge `master`. Packaging, installing, or releasing an Edge client requires separate explicit scope.
5. Verify a future explicitly approved fresh Facebook start shows either a successful first observation or a bounded retry with its safe code; do not perform an extra real-account attempt implicitly as part of code validation.

Rollback is a normal Edge source/runtime rollback to the prior commit. No data migration is required.

## Open Questions

None. The next live fresh-start observation may narrow the transient allowlist, but the safety and retry boundaries are fixed by this design.
