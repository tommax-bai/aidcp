## Context

The Native Facebook auth adapter requires a unique top-hit target before every irreversible click. That pre-action rule is correct. The defect is in the separate post-action observer: after a login or TOTP submit click, it reuses the top-hit-aware target resolver to decide whether the old signal disappeared. When Facebook temporarily covers the clicked button with a loading layer, the resolver returns no candidate with `auth_target_not_topmost`, but the observer leaves the result determinate and compares `null` with the old candidate key. This reports `signalGone=true` on the first poll. The coordinator then immediately re-probes the still-transitioning login document, classifies the same cover as `blocked_unknown`, and terminates before the browser reaches 2FA.

Native already owns a bounded action-postcondition loop under a 30-second command deadline. This change sets that loop to 200 ms for 35 polls, giving the observed Facebook transition up to 7 seconds without adding a new coordinator, retry loop, or protocol field.

The follow-up installed-client run reached the TOTP page from the email/password login page but retained only one digit. The TOTP path currently re-evaluates a focus guard before every character and binds the input with evidence that includes its geometry. Facebook may reflow the form as soon as the first digit is inserted, so the same focused input can acquire a different geometry-derived key before the second character. The action then becomes ambiguous, while the outer protocol reduces every non-confirmed structured action to `probe_failed`. A restarted coordinator cannot reconstruct the prior in-memory TOTP window and therefore refuses the orphan partial value with `entered_totp_window_missing`.

After atomic insertion shipped, a live run confirmed all six digits and then exposed a separate producer gap: Facebook had not rendered Continue by the next probe, so zero matching buttons became fatal `auth_target_not_found`. The resulting restart deliberately lost the in-memory entered-window witness. The new process therefore retained the unknown code, but an empty field in that unproven session would still become `failed(fresh_start_policy_unavailable)`, and the shell did not project either 2FA manual reason as a blocked state.

## Goals / Non-Goals

**Goals:**

- Preserve the pre-action top-hit gate for login, TOTP, and all other auth controls.
- Make post-submit observation distinguish a temporarily covered known target from a structurally absent target.
- Let the existing bounded Native postcondition polling observe the ensuing document transition without replaying the click.
- Preserve honest ambiguous receipts when no verified transition appears within the existing budget.
- Enter the complete six-digit TOTP value in one guarded CDP insertion and require exact same-field readback before submit.
- Recover an orphan non-empty TOTP value only when fresh-start mutation authority is proven, while retaining unproven browsers for manual handling without a process-error loop.
- Keep bounded Native action reasons visible through the coordinator.
- Keep the coordinator alive while a confirmed, owned TOTP value waits for its Continue control to hydrate.
- Make proven TOTP clearing retain clear-only semantics across the Native fresh probe and refuse if the observed field value changes.
- Keep unproven stale and empty TOTP states manual-required and visible without weakening genuine failed-to-code-1 handling.

**Non-Goals:**

- Clicking through overlays or weakening target uniqueness before an action.
- Extending Active-browser takeover authority or persisting fresh-start proof.
- Changing TOTP generation, key retrieval, server-time rules, login credentials, or supported Facebook checkpoints.
- Packaging an Edge client or performing another real-account login run.
- Changing typing behavior for email, password, comments, posts, or any non-TOTP text field.

## Decisions

### 1. Keep pre-action and post-action top-hit meanings separate

The existing actionable probe continues to map a non-topmost control to `blocked_unknown`, so Native never clicks a covered target. Only the postcondition observer changes: for login and TOTP submit signals, `auth_target_not_topmost` means the old target is still structurally present but its current hit state cannot prove whether the action advanced. The observer returns an unsatisfied postcondition and lets the existing bounded verifier poll again.

Treating all `auth_target_not_topmost` probes as transitional was rejected because it would hide a real modal or overlay before input. Treating the result as immediate disappearance was rejected because the live evidence demonstrates that it produces a false confirmed receipt.

### 2. Preserve structural disappearance as confirmation

If the bound document changes, the postcondition remains confirmed. If the relevant form or exact submit control is structurally absent without ambiguity, `signalGone` may still confirm the action. If the target is ambiguous or temporarily non-topmost, the observation remains indeterminate and cannot confirm disappearance. Native polls this state every 200 ms for at most 35 polls, yielding a 7-second receipt window within the existing command deadline.

Adding a fixed sleep after click was rejected because it guesses timing and delays every successful transition. The 200 ms polling cadence remains event-convergent, bounded, cancellation-aware, and produces an ambiguous receipt after 7 seconds of unconfirmed observation.

### 3. Lock the distinction with router and action-level regression coverage

Focused tests will retain the existing assertion that a covered login target is non-actionable before dispatch. New postcondition coverage will bind an actionable target first, add a covering element afterward, and assert that the cover does not satisfy `signalGone`. The tests will also cover the equivalent TOTP submit branch and confirm that true removal/document movement remains accepted.

### 4. Treat TOTP entry as one paste-like CDP operation

After a fresh Native probe has rebound the unique, visible, topmost TOTP input, Native clicks it through CDP, checks focus once, and sends the complete six-digit code in one `Input.insertText` call. This is paste-like browser input but does not touch the operating-system clipboard and does not assign `element.value` or synthesize JavaScript keyboard/input events. Native then reads the same structurally bound input and confirms only an exact six-digit match.

Only the TOTP path uses this operation. Other text inputs retain their existing typing behavior. The TOTP binding excludes geometry because value-driven layout reflow does not change input identity; uniqueness, visibility, editability, document generation, focus, and pre-action top-hit checks remain mandatory.

### 5. Recover orphan TOTP text without authorizing submission

A non-empty TOTP field without the current coordinator's entered-window witness can never be submitted. If the browser was freshly started under the existing mutation policy, the coordinator may derive the current server window solely to authorize a Native clear action, confirm the field is empty, and request a new broker code. If the browser was already active and fresh-start authority is unproven, the coordinator returns a manual-required state and retains the session instead of exiting with code 1.

The router classifies both partial and six-digit orphan values as refresh-required when no entered-window witness is supplied. This classification authorizes only clearing; submission still requires the coordinator-owned entered window. The coordinator also prefers the bounded Native action receipt reason over the generic non-confirmed protocol envelope reason so future failures remain diagnosable.

### 6. Treat a missing post-entry Continue control as hydration only

Once Native has confirmed an exact six-digit readback and the coordinator supplies its entered-window witness, zero exact Continue controls is a non-actionable `none` observation. The existing bounded coordinator poll waits without input and preserves the entered window. If the control appears, the normal unique/topmost submit gate applies. If the code becomes stale first, the router emits refresh-required and the owned clear-and-reenter path runs.

This exception applies only to zero controls in the supported TOTP context. Multiple matching controls remain ambiguous, and a unique covered control remains non-topmost and blocked. Missing controls are never treated as submission success.

### 7. Keep clear-only freshness separate from submit authority

A TOTP refresh signal id binds both the stable input identity and the current non-empty value inside the existing opaque composite digest; no standalone value or low-entropy code digest is exposed. Native re-probes a clear action without supplying an entered-window witness, so the same unchanged value remains refresh-required rather than being reclassified as submit-ready. The coordinator still decides whether clearing is authorized: either it owns the entered window or the browser has proven fresh-start mutation authority. Native clicks the rebound input, sends CDP key events, and confirms an empty same-field readback.

Passing a synthesized current window into the clear fresh probe was rejected because six digits do not prove which TOTP window produced them; it can accidentally manufacture submit semantics. Omitting value binding was rejected because a user or page could replace the observed value before the clear action.

### 8. Retain unproven TOTP sessions as explicit manual work

An already-active browser without fresh-start authority never receives automatic TOTP input or clearing. Both a residual non-empty field and a subsequently empty TOTP field return manual-required rather than failed. During retained login waiting, Edge republishes a changed manual reason through the existing lifecycle event. Electron accepts only the enumerated credential, 2FA, and exhausted read-only probe manual reasons, releases the serial launch waiter, projects the browser as blocked, and renders `需处理`; unknown coordinator failures still terminate with code 1.

## Risks / Trade-offs

- **A real blocking overlay appears immediately after click** → The verifier waits only within the 7-second receipt window and then returns ambiguous; it never clicks through or replays the signal.
- **Facebook navigation exceeds seven seconds** → The existing action remains ambiguous and fails closed; the change does not promote an unconfirmed transition to success.
- **A submit control is genuinely removed before navigation** → Structural disappearance remains valid confirmation, followed by a fresh probe before any later action.
- **A TOTP insertion or exact readback is ambiguous** → The action remains unconfirmed and the code is never submitted from that receipt.
- **An active browser contains orphan TOTP text** → No automatic mutation occurs; the retained session reports manual handling rather than repeatedly crashing.
- **Facebook delays the Continue control after TOTP insertion** → The coordinator performs bounded read-only polling; ambiguity or occlusion still fails closed and no submit is replayed.
- **The TOTP value changes between refresh observation and clear** → The value-bound signal id changes and Native refuses the stale clear action.
- **An operator clears an orphan code in an active browser** → The empty TOTP page remains manual-required and does not turn into another abnormal child exit.
- **Read-only auth probes exhaust their transient budget** → The retained browser becomes an explicit `需处理` state and releases the serial launch waiter; the known manual condition is not left as an indefinite `启动中` projection.

## Migration Plan

No data or protocol migration is required. Land the Edge source and control change after focused and required gates pass. Desktop packaging and installation remain separate, explicitly authorized release work.

## Open Questions

None for the code-level correction. A future operator-approved live run is still required to prove the complete installed-client login-to-2FA path against Facebook.
