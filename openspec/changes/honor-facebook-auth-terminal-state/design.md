## Context

The terminal Facebook authentication branch currently emits `lifecycle.auth_failed` and calls `terminateNow`. That exit helper closes only the CDP session. The existing AdsPower `killAndConfirmDead()` operation already owns browser teardown and confirmation. Separately, `presenceView()` discards historical presence text whenever the runtime is not running, so a retained `loginFlow.failed` status becomes `待命中`.

## Decisions

### D1. Reuse the existing confirmed browser close once

For a terminal Facebook authentication failure, Edge emits the existing failure event, calls the existing owned-browser `killAndConfirmDead()` operation, emits the existing generation-scoped `lifecycle.browser_closed` evidence only when confirmation succeeds, and then exits. A failed confirmation remains the existing browser-unconfirmed condition; this change adds no retry or recovery branch.

Manual-login-required remains a retained live session and is unchanged.

### D2. Prioritize the existing failed login fact in the presence view

When `loginFlow.state === 'failed'`, `presenceView()` returns the existing authentication-failure wording before the generic non-running fallback. No status field or state transition is added.

## Non-Goals

- Redesign startup authentication or lifecycle state machines.
- Add fallback ladders, automatic retries, takeover, binding exceptions, or new user-visible states.
- Change Cloud, Console, protocol v2, risk, persistence, packaging, or deployment.
