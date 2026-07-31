## Context

The Native Facebook auth adapter requires a unique top-hit target before every irreversible click. That pre-action rule is correct. The defect is in the separate post-action observer: after a login or TOTP submit click, it reuses the top-hit-aware target resolver to decide whether the old signal disappeared. When Facebook temporarily covers the clicked button with a loading layer, the resolver returns no candidate with `auth_target_not_topmost`, but the observer leaves the result determinate and compares `null` with the old candidate key. This reports `signalGone=true` on the first poll. The coordinator then immediately re-probes the still-transitioning login document, classifies the same cover as `blocked_unknown`, and terminates before the browser reaches 2FA.

Native already owns a bounded action-postcondition loop under a 30-second command deadline. This change sets that loop to 200 ms for 35 polls, giving the observed Facebook transition up to 7 seconds without adding a new coordinator, retry loop, or protocol field.

## Goals / Non-Goals

**Goals:**

- Preserve the pre-action top-hit gate for login, TOTP, and all other auth controls.
- Make post-submit observation distinguish a temporarily covered known target from a structurally absent target.
- Let the existing bounded Native postcondition polling observe the ensuing document transition without replaying the click.
- Preserve honest ambiguous receipts when no verified transition appears within the existing budget.

**Non-Goals:**

- Clicking through overlays or weakening target uniqueness before an action.
- Extending Active-browser takeover authority or persisting fresh-start proof.
- Changing TOTP generation, key retrieval, server-time rules, login credentials, or supported Facebook checkpoints.
- Packaging an Edge client or performing another real-account login run.

## Decisions

### 1. Keep pre-action and post-action top-hit meanings separate

The existing actionable probe continues to map a non-topmost control to `blocked_unknown`, so Native never clicks a covered target. Only the postcondition observer changes: for login and TOTP submit signals, `auth_target_not_topmost` means the old target is still structurally present but its current hit state cannot prove whether the action advanced. The observer returns an unsatisfied postcondition and lets the existing bounded verifier poll again.

Treating all `auth_target_not_topmost` probes as transitional was rejected because it would hide a real modal or overlay before input. Treating the result as immediate disappearance was rejected because the live evidence demonstrates that it produces a false confirmed receipt.

### 2. Preserve structural disappearance as confirmation

If the bound document changes, the postcondition remains confirmed. If the relevant form or exact submit control is structurally absent without ambiguity, `signalGone` may still confirm the action. If the target is ambiguous or temporarily non-topmost, the observation remains indeterminate and cannot confirm disappearance. Native polls this state every 200 ms for at most 35 polls, yielding a 7-second receipt window within the existing command deadline.

Adding a fixed sleep after click was rejected because it guesses timing and delays every successful transition. The 200 ms polling cadence remains event-convergent, bounded, cancellation-aware, and produces an ambiguous receipt after 7 seconds of unconfirmed observation.

### 3. Lock the distinction with router and action-level regression coverage

Focused tests will retain the existing assertion that a covered login target is non-actionable before dispatch. New postcondition coverage will bind an actionable target first, add a covering element afterward, and assert that the cover does not satisfy `signalGone`. The tests will also cover the equivalent TOTP submit branch and confirm that true removal/document movement remains accepted.

## Risks / Trade-offs

- **A real blocking overlay appears immediately after click** → The verifier waits only within the 7-second receipt window and then returns ambiguous; it never clicks through or replays the signal.
- **Facebook navigation exceeds seven seconds** → The existing action remains ambiguous and fails closed; the change does not promote an unconfirmed transition to success.
- **A submit control is genuinely removed before navigation** → Structural disappearance remains valid confirmation, followed by a fresh probe before any later action.

## Migration Plan

No data or protocol migration is required. Land the Edge source and control change after focused and required gates pass. Desktop packaging and installation remain separate, explicitly authorized release work.

## Open Questions

None for the code-level correction. A future operator-approved live run is still required to prove the complete installed-client login-to-2FA path against Facebook.
