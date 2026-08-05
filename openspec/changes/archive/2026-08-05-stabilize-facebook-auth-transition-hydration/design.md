## Context

The real `k1f6n506` run confirmed the TOTP submit action at `10:20:34.034` and then produced read-only `none` observations while Facebook showed its loading transition. The destination checkpoint began navigating at `10:20:41.417`, but Edge classified it as `unsupported_facebook_checkpoint` at `10:20:43.179`; the document was only about 1.76 seconds old and did not become DOM-interactive until about 2.95 seconds. Once stable, the same installed Native engine and CDP target classify the page as `automation_warning_dismiss` with one visible `Dismiss` target.

The earlier login phase has the same shape: AdsPower can fill saved credentials after the Facebook form first appears, while the current 1.5-second grace reports `credential_fill_unavailable` before that bounded provider behavior settles. Both are structural hydration races, not failures of the overall login deadline and not evidence that an already-dispatched Continue click failed.

## Goals / Non-Goals

**Goals:**

- Observe saved-credential filling for 25 seconds before requiring manual login.
- Observe any newly navigated Facebook checkpoint for 15 seconds before treating an otherwise unknown checkpoint as terminal, without binding the destination to TOTP or another specific preceding step.
- Preserve automatic-login startup projection while either transition remains pending.
- Reuse the existing Native `automation_warning_dismiss` signal and trusted pointer action when the stable warning page appears.
- Keep terminal unknown, ambiguous, human-verification, restricted-account, and expired-budget states fail-closed.

**Non-Goals:**

- Increasing the whole login wait or every Native command timeout.
- Retrying or replaying TOTP entry/submit actions.
- Adding generic dialog dismissal, GUI/Computer Use fallback, or text-only clicking.
- Changing Cloud protocol, AdsPower secret access, stable identity, risk state, packaging, installation, or deployment.

## Decisions

### 1. Use separate 25-second credential and 15-second checkpoint windows, not a larger global login timeout

The existing coordinator already waited through the 8.6-second post-submit transition and terminated only when a fresh probe returned a terminal unknown checkpoint. The fix therefore belongs in structural classification: an incomplete known transition remains `none` and is re-probed at the existing cadence until it becomes actionable or its applicable window expires. Saved credential filling receives 25 seconds; a new checkpoint document receives 15 seconds.

Increasing the global login deadline was rejected because it would not change the immediate `blocked_unknown` branch. Retrying all `blocked_unknown` results was rejected because it would weaken fail-closed handling for real unsupported or dangerous states.

### 2. Anchor each window to the current Facebook document age

Native page rules will use the current document's monotonic `performance.now()` age. Empty saved-login fields remain `credential_fill_pending` during the first 25 seconds of that login document. A checkpoint whose known warning structure is absent or still incomplete remains a hydration observation during the first 15 seconds of that checkpoint document.

Wall-clock state in Electron was rejected because it would cross the Native page-semantics boundary and could survive navigation to the wrong document. The document-local clock resets on navigation and binds the wait to the exact page being classified.

### 3. Known terminal evidence still wins immediately

CAPTCHA/human verification, rejected credentials or codes, explicit restriction/lock text, ambiguous warning scopes/controls, and unsafe targets keep their current terminal classifications. The grace only covers absence or incomplete hydration that can safely become the already-supported warning structure; it never authorizes an action.

### 4. Dismiss is an independent auth-page signal and one Native pointer action

Whenever an auth probe sees the warning title, one supported scope, and one visible/topmost `Dismiss` control, the existing `automation_warning_dismiss` signal supplies a fresh signal id and exact point. This rule does not depend on TOTP, login-submit, or any other preceding action. The coordinator dispatches `facebook_auth_dismiss_warning` once, Native uses the trusted pointer path, and postcondition verification requires the signal to disappear or the document to change. No DOM `click()` success claim or action replay is added.

### 5. Lifecycle projection changes by withholding premature terminal events

While Native returns a hydration observation, Edge emits neither `lifecycle.auth_required` nor `lifecycle.auth_failed`. The environment therefore stays in its existing starting/login projection. A genuine empty credential form after 25 seconds still emits `credential_fill_unavailable`; an unknown checkpoint after 15 seconds still emits the existing safe terminal failure.

## Risks / Trade-offs

- [A truly unsupported blank checkpoint is reported up to 15 seconds later] → Known dangerous evidence still fails immediately, no account-scoped work starts, and the bounded delay is preferable to terminating before DOM hydration.
- [Facebook changes the warning text or structure] → After 15 seconds the flow remains fail-closed with safe diagnostics; no generic dismissal is attempted.
- [Document age is unavailable] → Treat the grace as unavailable and preserve current fail-closed behavior rather than invent elapsed time.
- [A control appears but is ambiguous, covered, disabled, or out of scope] → Keep the existing Native target checks and do not click.

## Migration Plan

1. Land the Edge source and focused regression coverage in an isolated worktree.
2. Validate Native/router/coordinator/UI behavior, typecheck, and the strict OpenSpec change.
3. Integrate through the normal fast-forward path only after required gates pass.
4. Packaging, installation, and real-account retry require separate explicit authorization; the current installed client remains unchanged until then.

Rollback is a source revert of the bounded hydration classification. No data or protocol migration is involved.

## Open Questions

None for source implementation. Installed-client and real-account confirmation remain explicit follow-up boundaries.
