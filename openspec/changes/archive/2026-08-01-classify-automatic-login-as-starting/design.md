## Context

The Edge core owns Facebook login-page observation and guarded Native actions, while Electron owns the environment lifecycle projection consumed by the rail and health views. Electron currently receives a structured event only when the coordinator enters a manual-required state. If credentials later appear and the retained coordinator resumes automatic login, Electron receives only natural-language activity lines, so the stale manual state remains visible until identity is established or the child exits. A terminal authentication exit can also be masked by an earlier untrusted-binding stop reason and fall back to ordinary offline state.

## Goals / Non-Goals

**Goals:**

- Make autonomous login progress a structured, generation-scoped lifecycle fact.
- Show autonomous password/TOTP actions and their bounded page-transition waits as `登录中` in the existing `启动中` group.
- Show only confirmed manual-required or terminal authentication states in `需要处理`.
- Clear a stale manual projection immediately when the retained coordinator confirms that it can act automatically again.
- Preserve a terminal authentication reason across child exit so it cannot collapse into ordinary offline state.

**Non-Goals:**

- Treating login as proof that account automation is already `运行中` or ready for tasks.
- Reading credential storage from the renderer or inferring progress merely because credentials exist.
- Changing password, TOTP, QR, checkpoint, Native CDP, browser takeover, Cloud binding, or retry policy.
- Packaging or installing a desktop client, or exercising a real account.

## Decisions

### 1. The coordinator emits structured login-flow transitions

The authentication coordinator will expose a callback when a structurally observed actionable login signal enters automatic handling. The core will translate that callback into a generation-scoped local lifecycle IPC event. Explicit manual-required and terminal-failure outcomes remain separate structured events with bounded reasons.

Credential presence alone is rejected as the authority because stored credentials can be unavailable to the active provider, rejected by the page, or blocked behind a checkpoint. Natural-language log parsing is rejected because wording is not a stable state contract.

### 2. Electron keeps one projected login-flow fact

Electron will project one `loginFlow` object with mutually exclusive `automatic`, `manual_required`, or `failed` state and an optional safe reason. A later structured transition replaces the earlier one. Identity establishment and a new process generation clear it; child exit clears transient automatic/manual state but preserves the current generation's terminal failure for the stopped snapshot.

This fact describes authentication progress, not automation intent. It can therefore show a browser-only first-login session as `启动中 · 登录中` without enabling normal account automation or claiming a Cloud connection.

### 3. UI precedence follows operator responsibility

`failed` and `manual_required` map to `需要处理`. `automatic` maps to the existing `启动中` group with the row label `登录中`, even while the normal automation intent remains stopped during first-login setup. Normal task evidence remains the only route to `运行中`.

The automatic state ends on identity establishment, explicit stop/pause generation change, or child exit. This prevents a dead worker from remaining blue while also preventing a live autonomous coordinator from being shown as manual or offline.

### 4. Terminal authentication failure outranks an older binding stop reason

Before an authentication-related code-1 exit, the core sends a structured terminal failure. Electron captures it before stdio drains and child close, then projects the environment into `需要处理` with the short label `异常` and the full safe authentication reason. This current-generation producer evidence outranks an older `binding_untrusted` stop reason for presentation only; it does not weaken the binding gate or authorize Cloud/account actions.

## Risks / Trade-offs

- [A progress callback fires immediately before an automatic action that then fails] → The subsequent structured failure replaces `automatic`, and focused tests cover the transition.
- [A stale child reports progress after restart] → Existing lifecycle-generation validation rejects the message.
- [A terminal reason contains unsafe text] → Core reasons remain bounded enums and Electron validates shape before projecting them.
- [A browser-only login looks like automation was enabled] → The UI uses `启动中 · 登录中`, while automation intent and task readiness remain unchanged.
