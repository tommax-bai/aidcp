## Context

The retired TypeScript `FacebookJoinExecutor` is the established behavior oracle. Its current contract navigates to the canonical group page, polls up to 30 seconds for a decisive scoped observation, waits 2 seconds for React hydration before a click, re-resolves and clicks the current in-scope element in page JavaScript, and polls up to 45 seconds for a durable member, pending, or questionnaire state. It also positively scopes candidates to the current group's own heading/action region and never falls back to a page-wide Join control.

The Native implementation currently diverges in three linked places:

- the embedded router resolves only the first heading and checks only a narrow set of descendant link attributes, so a recommendation region can be mistaken for the target region and genuine ambiguity is not represented reliably;
- Rust clicks the coordinates returned by an earlier probe, rather than re-resolving and invoking the React-owned element immediately before actuation;
- the Rust verifier stops after 18.5 seconds, while the host facade and Native session both cap the entire command at 30 seconds.

The Cloud `group.join` step already has a 120-second deadline. No Cloud command field or policy change is needed.

## Goals / Non-Goals

**Goals:**

- Preserve the legacy current-group scope, click, readiness, hydration, verification, and honest terminal semantics in the Native-only path.
- Keep target selection fail-closed and make the actuation target fresh at the irreversible boundary.
- Give only Native Facebook join enough end-to-end time for the established bounds while leaving ordinary Native commands at 30 seconds.
- Prove the behavior with DOM/router tests, Rust unit tests, facade timeout tests, Cargo tests, Edge typecheck, and strict OpenSpec validation.

**Non-Goals:**

- No Cloud protocol, judge, scheduler, pacing, or retry-policy changes.
- No cross-navigation click-target schema such as the deferred `facebook-join-actuation-decouple` design.
- No installer packaging, deployment, artifact injection, or real Facebook join.
- No new configurable timeout knobs or retries.
- No claim of parity with the legacy 18.5-second coordinator-visible commit window. The current host-to-Native protocol does not expose the engine's internal click boundary to `CommitWindowGuard`; adding that lifecycle signal would be a separate protocol change.

## Decisions

### 1. Port the positive current-group region rule into the Native router

The router will derive the target group id from the current page path, inspect every visible primary group-name heading, and walk each heading toward the main region while stopping before an ancestor that contains a different-group reference. Different-group references include `href`, role-link/data attributes, and any element attribute containing `/groups/<id>`. A single positively resolved region is accepted; multiple symmetric candidates fail closed.

Join/member/pending candidates are classified once, annotated with `inTargetScope`, and only scoped candidates may drive the primary CTA, membership state, or actuation. All bounded candidates remain in the observation for diagnosis.

This ports the already-proven legacy rule. A page-wide first-Join fallback and a blacklist-only recommendation filter were rejected because both can select a different group.

### 2. Add a router-internal, re-resolving Join actuation

Rust will request a `join_click` internal router operation after the hydration settle. That operation recomputes current URL, target region, candidates, and disabled state at the actuation boundary; it calls `.click()` only when exactly one enabled in-scope Join control exists. It returns `scope_unresolved`, `no_target_in_scope`, `ambiguous_target`, or `disabled` without dispatch when the target is not safe.

This is intentionally internal to the embedded Facebook adapter and does not extend the Cloud/Edge command schema. Reusing stale probe coordinates was rejected because the legacy real-page evidence shows Facebook's React-owned Join control requires in-page actuation and can move during hydration.

### 3. Restore the established bounded timing as one join-specific budget

The Native join path will use the existing evidence-based bounds:

- readiness polling: 30 seconds;
- hydration settle before actuation: 2 seconds;
- immediate post-click settle: 1.5 seconds;
- durable post-click polling: 45 seconds.

The facade will execute only `group_join` with a 90-second deadline. Facebook Native sessions will use the same 90-second operation ceiling, and the Rust local session validation ceiling will permit it. Other commands keep their existing 30-second deadlines. The 11.5-second margin above the established 78.5-second polling/settling path covers navigation and bounded CDP round trips while staying below Cloud's existing 120-second step deadline. The separate pre-join eight-second generic-ready wait is removed because join readiness polling already owns readiness and the extra wait would stack budgets.

An 18.5-second verification ceiling was rejected because it was a commit-window bound in the legacy executor, not the durable verification contract.

### 4. Preserve effect and product outcome truth

No-click outcomes remain `not_started` or confirmed observations as appropriate. `already_member`, `pending`, and `questionnaire_required` short-circuit before actuation. A click is reported as dispatched only after the in-page operation confirms it invoked the target. Durable member state is confirmed by a positive member signal or the existing composer transition; pending and questionnaire take precedence over structural joined. A dispatched click that cannot be proven becomes `join_verification_ambiguous`, never success.

The longer Native operation checks cancellation during readiness and hydration, immediately before the click, during the immediate settle, and between verification probes. Cancellation before the click returns not-started. Cancellation after the click returns an ambiguous `preempted_by_task` receipt with `clicked=true`, allowing the host's five-second quiesce to converge instead of waiting for the 90-second command deadline.

This intentionally does not reproduce the legacy 18.5-second `window_busy` protection: the Native engine cannot open the host's `CommitWindowGuard` at its internal click boundary without extending the local lifecycle protocol. Immediate post-click cancellation is honest but may give up verification sooner than the legacy path; the click remains ambiguous and is never replayed or reported as joined.

## Risks / Trade-offs

- [A Facebook layout variant cannot positively resolve the target region] → Return retryable `not_ready` and click nothing; retain bounded candidate/scope evidence.
- [The page changes between readiness and actuation] → Recompute the unique scoped target in `join_click`; never use stale coordinates for the click.
- [A long join occupies the Native session longer] → Only `group_join` receives the 90-second command budget; cancellation and the Cloud's existing 120-second step deadline remain intact.
- [In-page `.click()` is less input-like than CDP mouse dispatch] → Limit the exception to the proven Facebook Join control and retain pre/post state verification; other Native writes remain unchanged.
- [Native cancellation after click lacks the legacy commit-window protection] → Stop verification with `clicked=true`, `EffectPhase::Ambiguous`, and `preempted_by_task`; do not replay or report success. A future coordinator-visible Native commit-boundary signal requires its own protocol change.

## Migration Plan

1. Land the control OpenSpec change and Edge implementation in their isolated feature branches.
2. Integrate after the concurrent Native Reels work, resolving shared router/Rust files once and rerunning focused tests, Cargo tests, and typecheck.
3. Rebuild/inject a development Native artifact only in the parent integration task if explicitly required; do not package or release an installer here.
4. Roll back by reverting the Edge commit. There is no database or Cloud migration.

## Open Questions

None. Real-account confirmation remains a separate acceptance boundary and must not be inferred from synthetic DOM tests.
