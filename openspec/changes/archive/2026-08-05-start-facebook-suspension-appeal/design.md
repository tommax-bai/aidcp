## Context

The observed `Facebook import 5` profile is on `https://www.facebook.com/checkpoint/<numeric-id>/?next=https%3A%2F%2Fwww.facebook.com%2F`. The document is complete and visible. Its suspension copy includes `We suspended your account`, a remaining-days warning, the account-integrity explanation, and an instruction to start an appeal. The DOM contains two `role=button` / `aria-label=Appeal` nodes: one hidden disabled clone and one visible enabled topmost target. No loading indicator is currently present.

The production startup path already serializes independent Facebook auth observations through the Native Page Engine. JavaScript locates and binds a candidate; Rust re-probes the signal, moves the CDP pointer, emits press/release, and verifies a bounded postcondition. The TypeScript coordinator dispatches no direct page input and prevents replay of a signal id.

## Goals / Non-Goals

**Goals:**

- Recognize only the observed account-suspension appeal entry as a new independent startup auth signal.
- Start the appeal with one freshly bound trusted CDP pointer action.
- Wait through the resulting loading transition and confirm only a distinct loaded Facebook checkpoint step.
- Retain the browser as operator-required after the entry advances, without allowing valid cookies to bypass the suspension flow.

**Non-Goals:**

- Selecting or filling any later appeal option, statement, evidence, contact detail, or verification challenge.
- Confirming or submitting an appeal, claiming account restoration, or retrying an ambiguous click.
- Broad support for arbitrary Facebook checkpoints, localized suspension copy not observed here, or screen-coordinate automation.
- Packaging or installing an Edge desktop build as part of source implementation.

## Decisions

### Add one auth signal and one matching command

Add `suspension_appeal_start` and `facebook_auth_start_suspension_appeal` to the existing Native/TypeScript auth registries. This reuses the one-signal/one-action owner, typed receipt, consumed-signal replay guard, and trusted pointer implementation. A separate DOM watcher or direct TypeScript CDP click would introduce a second authority and is rejected.

### Require exact route, content, and the single actionable clone

The router will require Facebook origin, a numeric checkpoint path, a canonical Facebook `next` destination, all observed suspension/appeal content markers, and exactly one visible enabled topmost control whose accessible label is exactly `Appeal`. Visibility filtering intentionally excludes the observed hidden disabled clone before uniqueness is evaluated. The candidate remains bound to target id, document generation, signal kind, DOM evidence, and geometry.

Route-only or label-only detection is rejected because unrelated checkpoints can expose recovery controls, and the observed page itself proves that a raw `Appeal` query is not unique.

### Confirm page advancement, not appeal submission

After the pointer press/release, the Native postcondition verifier will poll for up to the existing long transition budget used by the ad-data review entry. It confirms only when:

- the exact initial suspension signal is gone;
- the page remains on Facebook and is a numeric checkpoint route;
- the replacement page is complete, non-empty, and has no supported loading indicator; and
- the original candidate is no longer the actionable entry.

An unchanged/disabled/covered button, loading shell, unreadable DOM, arbitrary non-checkpoint navigation, cancellation, or timeout is not confirmed. Transition evidence after press remains ambiguous and the signal id is consumed, so no retry occurs.

### Stop at the next operator-owned step

After the Native action is confirmed, the coordinator returns `manual_required` with `facebook_suspension_appeal_step_required` instead of dispatching a second action. Main retains the browser/CDP and blocks identity/Cloud startup while that reason is active. A later generic unsupported checkpoint remains a safe deferred manual state only when preceded by this confirmed reason; CAPTCHA and other failures still fail closed. If the operator later reaches an authenticated non-checkpoint page, the normal fresh probe and identity gate resume.

This contextual deferral is narrower than globally treating checkpoints as manual-success surfaces and preserves recovery after the operator finishes.

## Risks / Trade-offs

- [Facebook changes the English copy or route] -> The signal becomes unsupported and performs no input; add another observed exact variant through a later contract change.
- [A different checkpoint step shares all current markers] -> Require the full suspension/remaining-days/appeal instruction set plus the canonical next destination and exact target semantics.
- [The successor uses the same URL and a long SPA load] -> Poll the structural state and loading indicators rather than relying only on URL/document generation.
- [The action committed but no accepted successor is readable] -> Return ambiguous, consume the signal id, retain honest failure, and never retry.
- [Operator remains on later checkpoint steps] -> Preserve a visible manual-required state and the owned browser; do not let cookies establish a runnable account.

## Migration Plan

Land the Edge source and control artifacts after focused TypeScript/router/Native tests, full required safety tests, typecheck, Rust formatting/clippy/tests, command-postcondition validation, and strict OpenSpec validation. No schema or data migration is required. Rollback is the previous Edge source commit; an installed client remains unchanged unless separately packaged and installed.

## Open Questions

None for the bounded entry action. Automation of any observed successor requires separate user authority and exact live evidence.
