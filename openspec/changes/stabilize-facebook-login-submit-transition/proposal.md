## Why

Live first-login runs on two imported Facebook AdsPower profiles confirmed the login submit action, then exited 6-7 ms later because Facebook's transient post-submit loading cover made the unchanged login button fail a top-hit check. The browser subsequently reached the supported 2FA page without its owning Edge worker, and every retry attached to the already-active browser without fresh-start mutation authority, so TOTP entry correctly stayed disabled.

A later installed-client run from the email/password login page exposed the next failure in the same chain: the TOTP action left only one digit in the field, surfaced the generic `probe_failed` envelope reason, and exited. Automatic retries then saw a non-empty TOTP field without the prior process's entered-window witness, returned `entered_totp_window_missing`, and repeatedly exited with code 1, making the environment status oscillate through `异常` before retry exhaustion.

The next installed-client run confirmed the complete six-digit TOTP insertion, but the immediate fresh probe ran before Facebook rendered the Continue control. The router flattened that zero-button hydration gap to `blocked_unknown(auth_target_not_found)`, the coordinator exited with code 1, and both environments briefly displayed `异常`. Their restarted workers then attached to already-active browsers, correctly refused to mutate the orphan code, but repeated `totp_refresh_required` forever without an actionable UI state. Review also found that the proven-fresh orphan-clear action could reclassify a complete orphan code as submit-ready during its Native fresh probe, so the intended clear-and-reenter path was not end-to-end safe.

## What Changes

- Keep the existing pre-action rule that a login submit target must be visible, unique, and topmost before Native CDP input.
- During the bounded postcondition for an already-dispatched login or 2FA submit action, treat a temporarily non-topmost target as indeterminate transition evidence rather than proof that the signal disappeared.
- Wait without replaying input until the bound document changes, the exact signal is structurally gone, the unchanged target becomes observable again, or the existing bounded receipt budget expires.
- Preserve fail-closed handling for pre-action occlusion, ambiguous controls, unsupported checkpoints, missing fresh-start authority, and unconfirmed receipts.
- Add regression coverage for the observed click, transient cover, and navigation sequence and for unchanged/ambiguous targets.
- For the Facebook TOTP field only, replace per-character entry with one guarded CDP `Input.insertText` carrying the complete six-digit code; do not use DOM value assignment or JavaScript-generated input/keyboard events.
- Bind the TOTP input by stable structural identity so value-driven layout reflow cannot invalidate the same focused field between entry and readback.
- On a proven fresh browser start, allow a non-empty orphan TOTP field to be cleared without submitting it; on an already-active/unproven browser, retain the browser for manual handling instead of entering a code-1 restart loop.
- Preserve the action receipt's bounded Native reason so a precise TOTP failure is not flattened to the generic protocol envelope reason.
- Treat a temporarily absent Continue control after confirmed full TOTP entry as bounded hydration, while keeping ambiguous or covered controls blocked before any click.
- Keep TOTP clear-only observations bound to the exact non-empty value and re-probe them without manufacturing submit authority, so a proven clear cannot become an accidental submit and cannot erase a value changed after observation.
- Keep an already-active browser in manual-required state when its stale TOTP field becomes empty, refresh the lifecycle reason during retained login waiting, and present enumerated 2FA or exhausted-probe states as `需处理` rather than a process error or an indefinitely occupied launch queue.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-browser-environment`: Clarify post-submit convergence so transient occlusion after a confirmed Native click is not mistaken for signal disappearance or a new fatal pre-action obstruction.

## Impact

- Affected repo: `aidcp-edge`.
- Affected areas: Native Facebook authentication postcondition probing, TOTP input/recovery, and focused router/action/coordinator regression tests.
- No Cloud API, protocol-v2, database, Console, proxy, TOTP generation, browser takeover, deployment, or installer change is intended.
- Validation is code-level only unless the operator separately authorizes another real-account run or desktop packaging.
