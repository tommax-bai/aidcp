# Design — Facebook join/comment resilience

## Verdict on the current approach (do not rewrite)

The stack is well-built and the honesty red line holds: the join executor never fakes `ok` (only a genuine member signal returns success), the comment executor honestly surfaces `identity_unknown` / `editor_not_found` / `verification_ambiguous`, and the judge is strictly fail-closed. Good bones already present and to be preserved: a decisive-observation readiness gate that refuses to stop on `documentReady==='loading'`; edge-task lease + per-account single-flight + join/comment mutex isolating the single shared fingerprint browser; a deterministic-first judge that spends the LLM only on genuine ambiguity; target-level idempotency via `claimNext ... ON CONFLICT(group_url)`; and a join step-timeout budget deliberately sized above edge worst-case.

**Timing budget is aligned — do NOT raise ceilings.** Current values (after the already-landed fixes): edge ready-poll `readyTimeoutMs=30_000`, pre-click settle `2_000`, `waitAfterClickMs=1_500`, post-click `postClickTimeoutMs=45_000` → edge worst-case ≈ 78.5s + thinkMs, under the cloud join step cap `FACEBOOK_GROUP_JOIN_STEP_TIMEOUT_MS=120_000`. The robustness defect is the reason taxonomy and retry wiring, not timeout size.

## Reconciliation with concurrently-landed fixes (2026-07-10)

A parallel session landed join fixes today; this change is scoped to what they did NOT fix. Verified against current HEAD (edge `6848632`, cloud `e246168`):

| Already landed | This change does |
| --- | --- |
| In-page `element.click()` actuation (edge `6848632`); ready 30s / post-click 45s / cloud step 120s; ready-poll skips still-loading (edge `f59f650`); clear-Join-CTA → deterministic instant_join (cloud `d3dcb9d`); multilingual Join-button **location** lexicon (`JOIN/MEMBER/PENDING_CTA_LABELS` + `classifyCtaLabel`) | Nothing — leave as is |
| — | Fix **confirmation** classifiers `hasMemberSignal` (`join-executor.ts:123-132`, EN/ZH `===`), `pending`/`questionnaire` in-page regexes (`join-executor.ts:235-238`, EN/ZH only), cloud judge `hasMemberSignal`/`hasJoinCta` (`facebook-group-join-judge.ts:53-73`) |
| — | Lease-failure guard, tiered backoff, coverage demotion, comment idempotency (untouched by the join fixes) |

## Root causes (the real permanent-loss engines, after adversarial review)

The design's original "fleet-wide gating" framing was **wrong**: at runtime slow-network/unrecognized-copy produce **per-account terminal `failed`**, not fleet-wide join-gating (the `no_button` → gating path at `facebook-group-join-scheduler.ts:331` is effectively dead because `no_button` always carries an observation). The genuine permanent-loss engines are:

1. **Lease-bypass hot-loop** — `runReal`'s two `withLease` calls (`facebook-group-join-scheduler.ts:168,181`) have no try/catch. On a busy/dropping edge the lease client throws; it bypasses `markEdgeFailure` while `markJoining` has already set `status='joining'`, `attempts++`, `cooldown_until=NULL`. The next 60s ContentScheduler tick re-picks the `joining` row with zero backoff and no audit — burning one attempt per tick until `attempts>=maxAttempts` → permanent `failed`. Network drop is the most common transient and the worst-handled path.
2. **Slow-render → LLM → terminal** — when the ready poll exhausts with the Join button not yet found, observe returns `observation_only`; cloud asks the pre-click LLM, which on a partial/loading-derived observation fail-closes to `ambiguous_skip` → `markOutcome('failed')` (`facebook-group-join-scheduler.ts:231`). The `documentReady`/`actionNodeCount` signals that would say "still loading, retry" are computed but dropped at the deadline. (The already-landed `d3dcb9d` deterministic shortcut narrows this to genuinely-unrecognized-CTA cases, which overlap with the multilingual confirm gap.)
3. **Coverage nav-error eviction** — `facebookCoverageOnFailure` passes `demoteNow=true` for `nav_error` (`server.ts:2258`), and `recordCoverageLeftSignal` sets `status='left'` immediately when `demoteNow` is true (`facebook-group-store.ts:~780`), bypassing the `requiredConfirmations=3` threshold that `permission_gated` correctly gets. `left` rows are neither coverage-eligible nor re-claimable → one blip permanently and irreversibly evicts the account from a warmed group.
4. **Half-multilingual confirm** — the single most direct amplifier of the reported copy pain (see below).

## Per-item design

### P0-1 — Comment idempotency (integrity: real duplicate posts)

Failure: `submitComment` fires Enter (`comment-executor.ts:433`) then sleeps `waitAfterSubmitMs=4000` + reload + `waitAfterReloadMs=5000` (≈9s) *after* submit; long comments also spend humanized per-char typing time *before* Enter. Total edge wall time can exceed the flat cloud cap `FACEBOOK_STEP_TIMEOUT_MS=28_000` (`facebook-edge-steps.ts:18`). Cloud then returns `{ok:false,reason:'timeout'}`; `reallySubmitted = submit.ok || submit.reason==='verification_ambiguous'` is false (`comment-scheduler.ts:781`) → no dedup mark → next round re-picks the same permalink (`comment-scheduler.ts:702-705` only skips already-deduped) → **second live comment**.

Fix:
- **Authoritative re-observe before re-post** (arbiter, not a bare-timeout heuristic): before selecting/re-posting a previously-attempted-unconfirmed candidate, drive one own-identity re-observe reusing the existing scoped-verify eval (`comment-executor.ts:631`); skip if an own comment already exists on that post.
- **Length-aware step timeout**: pass `stepTimeoutMs = base + perChar*len + postSubmitFixed(≈9000) + RTT margin` via the existing `stepTimeoutMs` hook (`facebook-edge-steps.ts:27,110`) instead of the flat `28_000`.
- **Do NOT** implement the naive "persist an attempted marker on dispatch and treat any bare timeout as dedup-blocking" — if the edge never reached Enter (editor-not-found/focus-fail) that would silently suppress a legitimate retry (under-post, the opposite failure). The re-observe is the only thing allowed to block a re-post.

Red line: an unconfirmed post stays honestly unconfirmed; we only block a *duplicate real* post. Edge stays thin (re-observe is an atomic eval it already runs); cloud owns the idempotency decision and the derived timeout. No risk-state writes.

### P0-2 — Multilingual member/pending/questionnaire confirmation

Failure: `hasMemberSignal` (`join-executor.ts:123-132`) uses EN/ZH exact `===`; the `pending`/`questionnaire` booleans are EN/ZH-only regexes (`join-executor.ts:235-238`), while `MEMBER_CTA_LABELS`/`PENDING_CTA_LABELS` (~13 locales) exist but are used only for Join-button *location*. A non-EN/ZH successful join burns the full 45s → honest but WRONG `join_failed`; an already-member non-EN/ZH page returns `no_button` instead of `already_member`; even decorated English (`✓ Joined`, `Joined ⌄`) defeats `===`.

Fix: replace `hasMemberSignal`'s literal `===` with NFKC-normalized contains-match against `MEMBER_CTA_LABELS`; derive the in-page `pending`/`questionnaire` booleans from the injected `PENDING_CTA_LABELS` / a member-label list (the classifier already orders member/pending before join, avoiding the `đã tham gia ⊃ tham gia` trap). Mirror in the cloud judge `hasMemberSignal` (`facebook-group-join-judge.ts:53`). Single source of truth already exists — no new vocabulary. A member label must still positively match (never loosens toward fake success).

### P0-3 — Lease-failure guard → honest audited transient

Fix: wrap both `withLease` invocations (`facebook-group-join-scheduler.ts:168,181`) in try/catch; on the lease client's error route to `markEdgeFailure` with a NEW reason (e.g. `lease_unavailable`) that `isRetryableEdgeFailure` accepts AND that is NOT counted against the attempt cap (see P1-5 tiering). Confirm the ContentScheduler 60s heartbeat catches a thrown `triggerScheduled` per-account so one lease error cannot abort the tick for other accounts.

Red line: a transient becomes an honest retryable failure with an audit row instead of a silent hot-loop to permanent-fail; no fake success; risk state untouched (lease-drop is not a captcha/login pause).

### P0-4 — Coverage nav-error requires confirmation

Fix: drop the `demoteNow=true` exemption for `nav_error` at `server.ts:2258`; let `recordCoverageLeftSignal` apply the same `AIDCP_FB_GROUP_LEFT_CONFIRMATIONS` (default 3) threshold used for `permission_gated`, or route `nav_error` to a transient coverage cooldown that leaves `status='joined'`. A member-left signal must be confirmed regardless of reason.

### P1-5 — not_ready taxonomy + tiered backoff

Fix (taxonomy): at the ready-poll deadline, when the page is still loading / below a minimal readiness threshold (`documentReady==='loading'` or `actionNodeCount===0`), emit a distinct `not_ready` outcome carrying `documentReady`+`actionNodeCount` instead of falling through to `observation_only`→LLM. Gate the pre-click LLM behind a minimally-ready observation; below it, retry instead of spending a fail-closed model call. Same idea for post-click exhaustion while still hydrating (`post_not_confirmed_slow`).

Fix (backoff): branch `markRetryableFailure` on `isAccountTransient` (`facebook-group-join-scheduler.ts:82`): account-level (login/captcha) keeps the long 6h cooldown; pure-network transients (`timeout`/`no_observation`/`no_post_observation`/`nav_error*`/`not_ready`/`lease_unavailable`) get a short exponential + **decorrelated jitter** cooldown (minutes) and do NOT increment the attempt cap. Jitter matters because all accounts fire on one 60s hash-offset heartbeat (thundering herd on the 6h boundary today).

Red line: both branches stay honest (never `ok`); edge measures readiness (already in the observation), cloud decides retry-vs-LLM-vs-terminal; risk state machine untouched.

### P1-6 — Cloud judge lexicon drift-guard + member-before-join

Findings: `preClickDeterministic` already evaluates `hasMemberSignal` before `hasJoinCta` (`facebook-group-join-judge.ts:112,125`) — order is correct — BUT the judge's `hasMemberSignal` is itself EN/ZH-only (`:53`), so a VN already-member `đã tham gia` misses the member check, falls to `hasJoinCta` whose lexicon contains `tham gia` → `.includes` matches → false `instant_join` → wasted click + terminal fail. The judge's join lexicon (`:68-73`, ~18 entries) is also drifted from edge (~25; missing Thai/Arabic/Malay/Russian/`entrar no grupo`).

Fix: make the judge's `hasMemberSignal` multilingual (same fix as P0-2, applied cloud-side); reconcile `hasJoinCta` with the edge lexicon. Cross-repo import is not possible (separate packages) — treat it like the `protocol.ts` four-places discipline: keep the second copy but add a **drift-guard regression test** in cloud, or carry the label set in the shared protocol contract. Fail-closed behavior for genuinely-unknown labels is preserved.

### P1-7 — Non-destructive unrecognized-modal handling

Finding: `dismissOptionalModal` presses Escape on any modal not positively classified as a questionnaire (`join-executor.ts:524-525`, guard `if (!modalText || questionnaireRequired) return`). With questionnaire detection EN/ZH-only, a non-EN/ZH membership-questions modal is Escape-dismissed — a destructive action that closes a real join questionnaire (worse than a false-fail). P0-2 largely fixes this as a side effect (multilingual `questionnaireRequired` → guard exempts it); the residual defense-in-depth is: **do not Escape-dismiss a modal you cannot positively classify as an optional survey** — report `questionnaire_required`/ambiguous honestly instead.

## YAGNI cuts (deliberately NOT built at v1 single-disposable-account scale)

- No coordinate-override / LLM-nominated-click protocol channel — the ~25-locale shared lexicon covers the realistic set; revisit only if a genuinely uncovered-locale group is observed.
- No self-learning lexicon (observe→stage→promote of unknown labels) — pointless until the confirm path is fixed; add only if audits show recurring unknown labels.
- No hedged/speculative retries — the single shared fingerprint browser under an exclusive lease makes a second speculative attempt risk double-join/double-comment; sequential retry-with-backoff is correct.
- No saga/compensation engine, no second circuit breaker (the risk state machine `normal→warned→restricted→frozen` already IS the account-level breaker), no multi-account gating service (the loss is per-account terminal, not fleet-wide).
- No general RTT/percentile-adaptive timeouts — only the length-aware comment step timeout (fixes the real duplicate bug) is warranted.
- No raising the join ready/post-click/step ceilings — already aligned (edge worst ≈78.5s < 120s cloud cap).
- No HITL approval queue for auto-join ambiguous cases at single-account scale.

## Test strategy

Follow the "few decisive cases, not one-per-subtask" restraint. Stub-testable (jsdom / pure functions), no browser:
- Multilingual confirm: member/pending/questionnaire classification across a representative locale set incl. the `đã tham gia ⊃ tham gia` trap and decorated-English (`✓ Joined`).
- Lease guard: injected lease-throw → membership gets cooldown+audit, not stranded `joining`; attempt cap not consumed.
- Coverage demotion: single `nav_error` → stays `joined`; N confirmations → `left`.
- Tiered backoff: transient → minutes cooldown, attempts not incremented; account-level → 6h.
- Comment idempotency: submit-then-timeout with own comment present on re-observe → no re-post; length-aware timeout derivation.
- Judge drift-guard regression test (edge vs cloud lexicon parity).
Real-machine items (multi-locale live join, slow-network duplicate reproduction) go to the real-machine acceptance backlog, not stub tests.
