## Why

Live first-login runs on two imported Facebook AdsPower profiles confirmed the login submit action, then exited 6-7 ms later because Facebook's transient post-submit loading cover made the unchanged login button fail a top-hit check. The browser subsequently reached the supported 2FA page without its owning Edge worker, and every retry attached to the already-active browser without fresh-start mutation authority, so TOTP entry correctly stayed disabled.

## What Changes

- Keep the existing pre-action rule that a login submit target must be visible, unique, and topmost before Native CDP input.
- During the bounded postcondition for an already-dispatched login or 2FA submit action, treat a temporarily non-topmost target as indeterminate transition evidence rather than proof that the signal disappeared.
- Wait without replaying input until the bound document changes, the exact signal is structurally gone, the unchanged target becomes observable again, or the existing bounded receipt budget expires.
- Preserve fail-closed handling for pre-action occlusion, ambiguous controls, unsupported checkpoints, missing fresh-start authority, and unconfirmed receipts.
- Add regression coverage for the observed click, transient cover, and navigation sequence and for unchanged/ambiguous targets.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-browser-environment`: Clarify post-submit convergence so transient occlusion after a confirmed Native click is not mistaken for signal disappearance or a new fatal pre-action obstruction.

## Impact

- Affected repo: `aidcp-edge`.
- Affected areas: Native Facebook authentication postcondition probing and focused router/action/coordinator regression tests.
- No Cloud API, protocol-v2, database, Console, proxy, TOTP generation, browser takeover, deployment, or installer change is intended.
- Validation is code-level only unless the operator separately authorizes another real-account run or desktop packaging.
