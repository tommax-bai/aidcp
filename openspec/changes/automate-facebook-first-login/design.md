## Context

Imported Facebook profiles can open on a logged-out page after their imported cookie expires. AdsPower still owns the imported username, password, and 2FA key, but edge currently reaches the stable-identity gate before it has any bounded way to assist that first login.

Facebook page understanding and page mutation are Native Page Engine responsibilities. The TypeScript host may coordinate lifecycle and secret brokering, but it must not reintroduce Facebook DOM selectors or direct CDP input outside the Native boundary. Browser-chrome prompts are a separate layer: they must be prevented by AdsPower/Chromium startup policy rather than clicked as if they were page DOM.

The observed Facebook transitions are not a stable wizard. Login submission, 2FA entry/submission, an automated-behavior warning, the Facebook push-notification blocker, and Facebook's Remember Password prompt can be omitted, delayed, or presented in a different order.

## Goals / Non-Goals

**Goals:**

- Assist a logged-out imported Facebook AdsPower profile through only the specifically observed first-login states.
- Model every state as an independent, freshly observed signal mapped to one bounded action.
- Keep Facebook DOM understanding, target resolution, Native CDP input, and postcondition checks in the Native Page Engine.
- Use Facebook server time for TOTP and guarantee at least 10 seconds remain before both code entry and code submission.
- Keep the 2FA key in the Electron main process and expose only one short-lived code plus its validity window to the managed core child.
- Suppress browser password-save and permission prompts before they can become automation dependencies.
- Preserve the existing stable-identity gate as the only authority to start account-scoped work.

**Non-Goals:**

- Solving CAPTCHA, human verification, device confirmation, recovery, account lock, or unfamiliar checkpoints.
- Typing a password from AIDCP. AdsPower first-open filling is the only supported credential-fill mechanism.
- Treating the observed states as a required or contiguous sequence.
- Clicking browser-chrome bubbles through screen coordinates, accessibility automation, or Computer Use.
- Persisting or reporting credentials, 2FA keys, TOTP codes, cookies, or raw AdsPower profile responses.
- Packaging or releasing a desktop installer as part of this change.

## Decisions

### 1. Reconcile independent signals instead of executing a login script

The startup helper will repeatedly ask the Native Page Engine for one exclusive Facebook authentication signal. Representative signals are:

- `authenticated`
- `login_submit_ready`
- `totp_entry_ready`
- `totp_submit_ready`
- `totp_refresh_required`
- `automation_warning_dismiss`
- `push_blocker_close`
- `remember_password_confirm`
- `blocked_human_verification`
- `blocked_unknown`
- `none`

One reconciliation pass may perform at most one action. Every actionable probe returns a non-secret `signalId` bound to the target, document generation, signal kind, and exact candidate. The action must present that id, and Native must fresh-probe the same signal before committing input. After the action, the coordinator discards the observation and probes again; it never assumes which signal comes next. An action is allowed only when its matching signal is still fresh, visible, unique, and topmost. The Native engine dispatches one bounded Native CDP stage action and verifies that the signal disappeared or that a defined page/document postcondition occurred. If the postcondition is absent, the action fails instead of being retried blindly.

The coordinator may dispatch a given `signalId` at most once, and an ambiguous receipt is never replayed. This permits signals to be skipped, delayed, or revisited on a new document while preventing duplicate clicks against an unchanged document. A fixed wizard was rejected because the live sequence is not stable enough to justify transition-by-transition chaining.

### 2. Keep all Facebook page semantics and input in Native Page Engine

The TypeScript host will own only the bounded coordinator, timeout/cancellation, and TOTP broker calls. Native commands will probe the page or execute one signal-specific action. Selectors, structural checks, top-hit testing, `Input.dispatchMouseEvent`, key input, and same-target postconditions remain in the Facebook Native adapter.

The helper is invoked after AdsPower launch, CDP attach, and Native runtime creation, but before the first stable-identity read. The same idempotent helper is reused after a cold-standby browser reattach and before identity is re-established. It is not embedded in the identity reader, because identity reading must remain read-only and must not hide page mutations.

Direct TypeScript CDP page automation was rejected because it would violate the current Native-only Facebook producer/executor boundary and create a second set of page truth.

### 3. Split password fill from TOTP material

Fresh AdsPower starts will request first-open credential filling and disable browser password saving. The Native login action only submits when the exact Facebook login form is visible, unique, and both credential fields are already non-empty. A missing field is a terminal `credential_fill_unavailable` result; edge does not request or type the stored password.

For 2FA, a named Electron-main IPC operation is bound to the current managed child and its exact AdsPower profile id. Electron reads that one profile through AdsPower V2, verifies exactly one matching record, extracts only `fakey`, computes a TOTP for the requested Facebook server-time window, and immediately drops the raw response and key references. Only the six-digit code and non-secret validity timestamps cross the private IPC boundary. Password, username, `fakey`, cookies, proxy fields, and the raw profile body never cross that boundary.

Adding the V2 profile-list operation to the generic child broker was rejected because its raw response contains unrelated sensitive profile material.

### 4. Treat TOTP entry and submission as separate signal/actions

The Native probe obtains a fresh Facebook server `Date` observation from the current origin. Before requesting or entering a code, the coordinator computes remaining lifetime in the 30-second window. If fewer than 10 seconds remain, it performs no page action, waits for the next window, and probes again.

Entering the code is one action with an input readback postcondition. Submitting the already-entered code is a later, independently probed action. The coordinator carries only the non-secret window end. Before submission it rechecks Facebook server time. If fewer than 10 seconds remain or the window changed, it executes a separate clear-input action and returns to the entry signal; it never submits a stale code.

Local wall-clock-only TOTP was rejected because host clock skew and page delays can consume the usable window.

### 5. Separate browser-chrome policy from Facebook page prompts

On a fresh AdsPower start, edge sends `password_filling: "1"` and `password_saving: "0"`. The first allows AdsPower to fill imported credentials; the second disables the browser's Save Password bubble. Existing permission-denial launch arguments and the CDP permission override keep native notification permission UI blocked. A reused already-running browser cannot be claimed to have received fresh-start password policy; login assistance must fail closed if the required startup policy cannot be established.

Facebook's own push-notification alertdialog and Remember Password modal are page DOM. They remain independent Native signals: Close dismisses the exact push blocker, while OK confirms the exact Facebook Remember Password prompt. Neither action is attempted when the matching page signal is absent or ambiguous.

### 6. Preserve bounded startup and stable identity as final authority

The reconciler uses the existing startup login-wait budget and lifecycle cancellation. `authenticated` only ends assistance, and it may be emitted only when the Facebook cookie jar contains both a non-empty `xs` value and a numeric `c_user` value that satisfies the same Facebook-domain and stable-user-id checks as the identity reader. Cookie names, blank placeholder values, or a non-numeric `c_user` are not authentication evidence. The existing identity reader must still produce the stable account id, and existing override/mismatch rules still apply. CAPTCHA, unfamiliar checkpoints, missing credentials, rejected TOTP, ambiguous controls, timeout, and cancellation terminate honestly before Cloud connection or account-scoped work.

### 7. Bound document generations and use explicit 2FA label associations

The document generation remains part of every actionable signal id because a stable CDP target does not prove that the observed page or SPA route is unchanged. Its representation must therefore be stable for one unchanged document/URL state, change after a full navigation or route/query transition, and remain fixed-size regardless of page-controlled URL length. The Native router derives a bounded digest from the full origin, path, and query and combines it with the document time origin; it does not embed the raw query in the observation. The existing protocol size limit remains a defensive validation boundary rather than becoming dependent on Facebook URL length.

Inside an already confirmed Facebook 2FA context, the Native router may recognize a visible editable text input from the exact labels associated by the browser's `HTMLInputElement.labels` relation. This covers both `label[for]`/`input[id]` and a wrapping `label` without hard-coding Facebook's dynamic ids. Nearby or page-wide text is not an association. The candidate must still be unique and topmost; no candidate or multiple matching candidates fails closed.

## Risks / Trade-offs

- **Facebook markup or wording changes** → Exact structural detection fails closed and reports a safe reason; no generic text guessing or fallback click is added.
- **AdsPower changes V2 response shape** → Electron validates response code, cardinality, and exact profile id before extracting `fakey`; any drift blocks 2FA.
- **A code crosses private IPC and the Native command pipe** → It is bounded to one managed child, short-lived, never logged, never persisted, and accompanied only by non-secret window metadata.
- **A browser is already active without the new startup policy** → Edge does not claim password-save suppression; it stops first-login assistance rather than depending on an unobservable browser-chrome prompt.
- **A valid signal reappears later** → The new document/signal observation can be handled once; the same unchanged observation cannot be acted on twice.
- **Server-time sampling fails** → TOTP assistance stops without falling back to unchecked local time.
- **AdsPower or Chromium exposes placeholder auth-cookie entries** → The auth probe applies the same numeric `c_user` validity rule as stable identity and additionally requires a non-empty `xs`; cookie names alone never suppress login assistance.
- **Facebook emits long page-controlled checkpoint queries** → Document generations stay fixed-size and retain full URL-state sensitivity without returning the raw query through the Native protocol.
- **The 2FA input exposes meaning only through an associated label** → Native reads the browser-defined label relation only inside the confirmed 2FA context and still requires one visible, editable, topmost candidate.

## Migration Plan

1. Add the OpenSpec contract and focused tests for the provider body, TOTP broker, signal classification, one-action reconciliation, and fail-closed states.
2. Implement the Electron profile-bound TOTP operation and AdsPower startup policy.
3. Implement Native Facebook probe/action commands and the bounded TypeScript coordinator.
4. Run focused, acceptance, full edge tests, typecheck, and the Native Page Engine build/tests.
5. Perform one final operator-approved live validation from the gated feature source against the third imported stable test profile. If the operator explicitly waives a repeat after reviewing a stopped attempt and its evidence gap, record that waiver without claiming real-account success.
6. After the live gate succeeds or that explicit waiver is recorded, rebase, integrate, and push the edge and control source changes. Packaging remains a separate delivery boundary: source integration alone does not update installed clients. Roll back by reverting the edge commits. Existing manually logged-in profiles remain compatible because `authenticated` is a no-op and stable identity remains authoritative.

## Open Questions

None. Any newly observed Facebook challenge requires a separate evidence-backed contract change rather than expanding this reconciler implicitly.
